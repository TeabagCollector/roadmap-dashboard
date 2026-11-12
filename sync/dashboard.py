#!/usr/bin/env python3
"""Local-only Dashboard ledger + read-only Codex rollout adapter. No network."""
import argparse, contextlib, datetime as dt, fcntl, hashlib, json, os
from pathlib import Path
import sqlite3, sys, time, uuid

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('DASHBOARD_DATA_DIR', Path.home() / 'Library/Application Support/RoadmapDashboardPreview/live'))

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with tmp.open('w') as f:
        os.chmod(tmp, 0o600)
        json.dump(value, f, ensure_ascii=False)
    os.replace(tmp, path)

def read(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default

@contextlib.contextmanager
def ledger(data=DATA):
    data.mkdir(parents=True, exist_ok=True)
    with (data / 'ledger.lock').open('a') as lock:
        os.chmod(data / 'ledger.lock', 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = data / 'ledger.json'
        state = read(path, {'schema': 2, 'revision': 0, 'tasks': []})
        before = json.dumps(state, sort_keys=True)
        yield state
        if json.dumps(state, sort_keys=True) != before:
            state['revision'] += 1
            state['updatedAt'] = stamp()
            atomic(path, state)

def clean(value, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError('需要非空且长度合适的文字')
    return value.strip()

def mutate(request, data=DATA):
    op = request.get('op')
    with ledger(data) as state:
        if op == 'get':
            return state
        if request.get('revision') != state['revision']:
            raise ValueError('清单已在别处更新；已保留最新版本，请重新读取后操作')
        tasks = state['tasks']
        if op == 'plan':
            task_id = clean(request['id'], 160)
            task = next((t for t in tasks if t['id'] == task_id), None)
            steps = request['steps']
            if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
                raise ValueError('计划需要 1–100 个步骤')
            ids = [clean(s['id'], 160) for s in steps]
            if len(set(ids)) != len(ids):
                raise ValueError('步骤 ID 不能重复')
            if not task:
                if len(tasks) >= 500:
                    raise ValueError('清单已满')
                task = {'id': task_id, 'steps': [], 'history': []}
                tasks.append(task)
            task['title'] = clean(request['title'])
            task['project'] = clean(request.get('project', '未分组'))
            if 'note' in request:
                task['note'] = clean(request['note'], 1000)
            if 'defaultExpanded' in request:
                task['defaultExpanded'] = bool(request['defaultExpanded'])
            if 'sourceRefs' in request:
                refs = request['sourceRefs']
                if not isinstance(refs, list) or len(refs) > 20:
                    raise ValueError('来源引用过多')
                task['sourceRefs'] = [clean(r, 1000) for r in refs]
            thread = request.get('threadId')
            if thread:
                uuid.UUID(thread)
                task['threadId'] = thread
            old = {s['id']: s for s in task['steps']}
            new = []
            for source in steps:
                step = dict(old.get(source['id'], {'id': source['id'], 'done': False}))
                step['text'] = clean(source['text'])
                step['criterion'] = clean(source.get('criterion') or '完成后记录验证结果')
                previous_reported = step.get('reported')
                # A partial plan edit must not reopen accepted or blocked work.
                # Only an explicitly supplied status changes an existing step.
                step['reported'] = source.get('status', step.get('reported', 'pending'))
                if step['reported'] not in ('pending', 'in_progress', 'completed', 'blocked'):
                    raise ValueError('不支持的步骤状态')
                if 'status' in source or source['id'] not in old:
                    # An agent plan reports progress; it cannot silently erase a manual choice.
                    if step['reported'] == 'completed' and not step.get('done'):
                        step['needsReview'] = True
                    elif step['reported'] != 'completed':
                        step['needsReview'] = False
                        if previous_reported == 'completed' and step.get('done') and step.get('source') != 'user':
                            step.update(done=False, source='reopened-plan', evidence='计划重新打开本步骤，需重新核验')
                new.append(step)
            removed = [s for s in task['steps'] if s['id'] not in ids]
            if removed:
                task.setdefault('retiredSteps', []).extend(removed)
            task['steps'] = new
            task['planRevision'] = task.get('planRevision', 0) + 1
            task['history'].append({'at': stamp(), 'source': 'agent-plan', 'revision': state['revision'] + 1})
        elif op == 'report':
            task = next(t for t in tasks if t['id'] == request['taskId'])
            step = next(s for s in task['steps'] if s['id'] == request['stepId'])
            status = request['status']
            if status not in ('pending', 'in_progress', 'completed', 'blocked'):
                raise ValueError('不支持的上报状态')
            step['reported'] = status
            step['reportEvidence'] = clean(request.get('evidence') or '暂无完成证据', 2000)
            if status == 'completed' and not step.get('done'):
                step['needsReview'] = True
            elif status != 'completed':
                step['needsReview'] = False
            if status in ('pending', 'in_progress', 'blocked') and step.get('done') and step.get('source') != 'user':
                step.update(done=False, source='reopened-report', evidence='新报告重新打开：' + step['reportEvidence'])
            task['history'].append({'at': stamp(), 'source': 'worker-report', 'stepId': step['id'], 'status': status, 'evidence': step['reportEvidence']})
        elif op == 'follow':
            thread = request['thread']
            uuid.UUID(thread['id'])
            if not any(t.get('threadId') == thread['id'] for t in tasks):
                if len(tasks) >= 500:
                    raise ValueError('清单已满')
                tasks.append({'id': 'plan-' + thread['id'], 'title': clean(thread['title']), 'project': clean(thread['project']), 'threadId': thread['id'], 'steps': [], 'history': []})
        elif op in ('check', 'accept'):
            task = next(t for t in tasks if t['id'] == request['taskId'])
            step = next(s for s in task['steps'] if s['id'] == request['stepId'])
            if op == 'accept':
                if step.get('source') == 'user':
                    raise ValueError('这一步由用户手动确认过，请保留其选择')
                evidence = clean(request.get('evidence'), 2000)
                done, source = True, 'verified'
            else:
                if not isinstance(request.get('done'), bool):
                    raise ValueError('完成标记必须是布尔值')
                done, source = request['done'], 'user'
                evidence = '你在 Dashboard 中手动' + ('确认完成' if done else '重新打开')
            step.update(done=done, source=source, evidence=evidence, needsReview=False, updatedAt=stamp())
            step.pop('evidence_en', None)  # never retain stale demo translations after a real edit
            task['history'].append({'at': stamp(), 'stepId': step['id'], 'done': done, 'source': source, 'evidence': evidence})
        else:
            raise ValueError('不支持的清单操作')
    return read(data / 'ledger.json', {})

def migrate(data=DATA):
    if (data / 'ledger.json').exists():
        return
    old = read(data / 'user-state.json', {})
    with ledger(data) as state:
        for t in old.get('tasks', []):
            if not isinstance(t, dict) or not t.get('text'):
                continue
            task = {'id': 'legacy-' + str(t.get('id', uuid.uuid4())), 'title': t['text'], 'project': '原有清单', 'history': [], 'steps': [{'id': 'item', 'text': t['text'], 'done': bool(t.get('done')), 'source': 'user', 'evidence': '从原有清单保留'}]}
            key = str(t.get('threadKey', '')).split(':')[-1]
            try:
                uuid.UUID(key)
                task['threadId'] = key
            except ValueError:
                pass
            state['tasks'].append(task)
        state['migrated'] = True

class Tail:
    def __init__(self):
        self.offset = 0
        self.identity = None
        self.run = None
        self.status = 'unknown'
        self.last = 0
        self.plan = None
        self.completed_turn = None
        self.completed_at = 0

    def seed_lifecycle(self, f, size):
        # A long turn can exceed the ordinary tail window. Search backwards for
        # a structured lifecycle record, not for words in a message/tool output.
        position, suffix = size, b''
        lower = max(0, size - 32 * 1024 * 1024)
        while position > lower:
            start = max(lower, position - 131072)
            f.seek(start)
            block = f.read(position - start) + suffix
            lines = block.split(b'\n')
            suffix = lines.pop(0) if start else b''
            for line in reversed(lines):
                if b'event_msg' not in line or not any(k in line for k in (b'task_started', b'task_complete', b'turn_aborted')):
                    continue
                try:
                    value = json.loads(line)
                    if value.get('type') == 'event_msg' and value.get('payload', {}).get('type') in ('task_started', 'task_complete', 'turn_aborted'):
                        self.ingest(value)
                        return
                except (ValueError, TypeError):
                    pass
            position = start

    def ingest(self, event):
        payload = event.get('payload', {})
        try:
            event_time = dt.datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00')).timestamp()
            self.last = max(self.last, event_time)
        except (ValueError, TypeError):
            pass
        if event.get('type') == 'event_msg':
            kind = payload.get('type')
            turn = payload.get('turn_id', payload.get('root_turn_id'))
            if kind == 'task_started':
                self.run, self.status = turn, 'active'
            elif kind in ('task_complete', 'turn_aborted') and (not self.run or turn == self.run):
                self.status = 'idle' if kind == 'task_complete' else 'stopped'
            if kind == 'task_complete':
                self.completed_turn = turn
                self.completed_at = payload.get('completed_at') or self.last
            item = payload.get('item', {}) if kind == 'item_completed' else {}
            if str(item.get('type', '')).lower() in ('plan', 'planupdate') and isinstance(item.get('plan'), list):
                self.plan = item['plan']
        if event.get('type') == 'response_item' and payload.get('type') == 'function_call' and payload.get('name', '').split('.')[-1] == 'update_plan':
            try:
                plan = json.loads(payload['arguments']).get('plan')
                if isinstance(plan, list):
                    self.plan = plan
            except (ValueError, KeyError):
                pass

    def poll(self, path):
        with Path(path).open('rb') as f:
            st = os.fstat(f.fileno())
            identity = (st.st_dev, st.st_ino)
            if self.identity != identity or st.st_size < self.offset:
                self.__init__()
                self.identity = identity
                self.seed_lifecycle(f, st.st_size)
                # Tail a bounded window; missing start remains unknown, never fabricated idle.
                self.offset = max(0, st.st_size - 1024 * 1024)
                f.seek(self.offset)
                if self.offset:
                    f.readline()
                    self.offset = f.tell()
            f.seek(self.offset)
            for _ in range(10000):
                line = f.readline()
                if not line or not line.endswith(b'\n'):
                    break
                self.offset = f.tell()
                try:
                    self.ingest(json.loads(line))
                except (ValueError, TypeError, AttributeError):
                    pass

    def live_status(self, now):
        return 'unknown' if self.status == 'active' and now - self.last > 180 else self.status

class DesktopUnread:
    """Read only a verified desktop identity/host scope; never union accounts.

    Persist observed additions so an explicit re-mark can outlive the reply-age
    filter. Existing historical flags at first observation remain historical.
    """
    def __init__(self, data, path):
        self.data, self.path = data, path

    def read(self, receipts):
        binding = read(self.data / 'desktop-unread-binding.json', {})
        identity, host = binding.get('identityKey'), binding.get('hostKey')
        if not identity or not isinstance(host, str) or not host.startswith('local:'): return None
        doc = read(self.path, {})
        scoped = doc.get('electron-thread-read-state-v1', {}).get('unreadByIdentity', {}).get(identity, {})
        values = scoped.get(host)
        if not isinstance(values, list): return None
        ids = {v for v in values if isinstance(v, str)}
        path = self.data / 'desktop-unread-observed.json'
        previous = read(path, {})
        scope = identity + '/' + host
        marks = previous.get('manualMarks', {}) if previous.get('scope') == scope else {}
        marks = {k: v for k, v in marks.items() if k in ids}
        if previous.get('scope') == scope:
            for tid in ids - set(previous.get('unreadIds', [])):
                if not receipts.get(tid, {}).get('first_unread_turn'):
                    marks[tid] = stamp()
        state = {'scope': scope, 'unreadIds': sorted(ids), 'manualMarks': marks}
        if state != previous: atomic(path, state)
        return {'ids': ids, 'marks': marks}

class Watcher:
    def __init__(self, data=DATA, db=None, global_state=None, ledger_data=None):
        self.data = data
        self.ledger_data = ledger_data or data
        self.db = db or Path.home() / '.codex/state_5.sqlite'
        self.tails = {}
        self.plan_hash = {}
        self.pilot_gate = None
        state_path = global_state or (Path.home() / '.codex/.codex-global-state.json' if db is None else None)
        self.desktop_unread = DesktopUnread(data, state_path) if state_path else None

    def tick(self):
        now = time.time()
        snapshot = read(self.data / 'snapshot.json', {})
        projects = {str(p['id']): p.get('label', p.get('name', p.get('title', ''))) for p in snapshot.get('projects', [])}
        threads, errors = [], []
        errors.extend(sync_sources(self.data))
        try:
            with contextlib.closing(sqlite3.connect(self.db.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
                db.row_factory = sqlite3.Row
                tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
                columns = {r[1] for r in db.execute('pragma table_info(threads)')}
                main_filter = " and thread_source='user'" if 'thread_source' in columns else ''
                receipts = {r['thread_id']: dict(r) for r in db.execute('select thread_id,first_unread_turn,last_published_turn from thread_read_receipts')} if 'thread_read_receipts' in tables else {}
                desktop = self.desktop_unread.read(receipts) if self.desktop_unread else None
                display_title="coalesce(nullif(name,''),title)" if 'name' in columns else "title"
                select = "select id," + display_title + " as title,cwd,project_id,rollout_path from threads where archived=0 and agent_path is null" + main_filter
                records = list(db.execute(select + " order by updated_at desc limit 100"))
                # A re-mark need not touch updated_at, so include older flagged chats.
                if desktop and desktop['ids']:
                    existing = {r['id'] for r in records}
                    extra_ids = sorted(desktop['ids'] - existing)
                    for offset in range(0, len(extra_ids), 400):
                        group = extra_ids[offset:offset + 400]
                        records.extend(db.execute(select + " and id in (" + ','.join('?' for _ in group) + ")", group))
            for r in records:
                t = self.tails.setdefault(r['id'], Tail())
                try:
                    t.poll(r['rollout_path'])
                    status = t.live_status(now)
                except (OSError, TypeError):
                    status = 'unknown'
                captured = next((x for x in snapshot.get('threads', []) if x['id'] == r['id']), {})
                project = projects.get(str(r['project_id'])) or projects.get(str(captured.get('projectId'))) or Path(r['cwd']).name or '未分组'
                receipt = receipts.get(r['id'])
                threads.append({'id': r['id'], 'title': r['title'], 'kind': 'codex', 'project': project, 'status': status, 'lastEventAt': t.last,
                    'isUnread': r['id'] in desktop['ids'] if desktop is not None else bool(receipt['first_unread_turn']) if receipt else None,
                    'isManualUnread': bool(desktop and r['id'] in desktop['marks']),
                    'manualUnreadAt': desktop['marks'].get(r['id']) if desktop else None,
                    'unreadSource': 'local-desktop-scoped-state' if desktop is not None else 'local-codex-receipt' if receipt else 'unavailable',
                    'completedTurn': receipt['last_published_turn'] if receipt else t.completed_turn,
                    'completedAt': t.completed_at})
                if t.plan:
                    signature = hashlib.sha256(json.dumps(t.plan, sort_keys=True).encode()).hexdigest()
                    if self.plan_hash.get(r['id']) != signature:
                        steps = []
                        for s in t.plan:
                            if isinstance(s, dict) and isinstance(s.get('step'), str):
                                text = s['step']
                                steps.append({'id': hashlib.sha256(text.encode()).hexdigest()[:16], 'text': text, 'status': s.get('status', 'pending')})
                        if steps:
                            state = mutate({'op': 'get'}, self.ledger_data)
                            existing = next((x for x in state['tasks'] if x.get('threadId') == r['id']), None)
                            # A manually maintained linked plan owns its steps; don't replace it.
                            tid = 'plan-' + r['id']
                            # A structured plan alone may describe a casual analysis.
                            # New enrollment comes from the working agent's explicit
                            # ledger registration, or the user's Follow action.
                            if existing and existing['id'] == tid:
                                try:
                                    mutate({'op': 'plan', 'revision': state['revision'], 'id': tid, 'title': r['title'], 'project': project, 'threadId': r['id'], 'steps': steps}, self.ledger_data)
                                except ValueError:
                                    continue
                        self.plan_hash[r['id']] = signature
            live = True
        except (sqlite3.Error, OSError) as error:
            errors.append('本机对话来源暂不可读取；运行状态未确认')
            live = False
        state = mutate({'op': 'get'}, self.ledger_data)
        atomic(self.data / 'feed.json', {'schema': 2, 'capturedAt': stamp(), 'ledgerContext': hashlib.sha256(str(self.ledger_data.resolve()).encode()).hexdigest(), 'live': live, 'threads': threads, 'ledger': state, 'errors': errors, 'chatgptLive': False})

def sync_sources(data=DATA, nonblocking=False):
    data.mkdir(parents=True, exist_ok=True)
    with (data / 'source-sync.lock').open('a') as lock:
        os.chmod(data / 'source-sync.lock', 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        except BlockingIOError:
            return []
        return _sync_sources(data)

def _sync_sources(data=DATA):
    """Operator-registered files only. Worker reports can never accept a step."""
    config = read(data / 'task-sources.json', {'sources': []})
    cursors = read(data / 'source-cursors.json', {})
    changed, errors = False, []
    for source in config.get('sources', []):
        try:
            path = Path(source['path'])
            # Reading does not execute any file or follow instructions in its text.
            if path.stat().st_size > 1000000:
                raise ValueError('source too large')
            raw = path.read_bytes()
            signature = hashlib.sha256(raw).hexdigest()
            if cursors.get(source['id']) == signature:
                continue
            value = json.loads(raw)
            state = mutate({'op': 'get'}, data)
            if source['kind'] == 'worker-report':
                if value.get('ticketId') != source['ticketId'] or value.get('taskId') != source['taskId']:
                    raise ValueError('report binding mismatch')
                updates = value.get('updates', [])
                if not updates or len(updates) > 50:
                    raise ValueError('invalid worker updates')
                # Validate the whole report before applying any record.
                if any(u.get('stepId') not in source['allowedStepIds'] or u.get('status') not in ('pending', 'in_progress', 'completed', 'blocked') for u in updates):
                    raise ValueError('worker step outside assignment')
                for u in updates:
                    state = mutate({'op': 'get'}, data)
                    mutate({'op': 'report', 'revision': state['revision'], 'taskId': source['taskId'], 'stepId': u['stepId'], 'status': u['status'], 'evidence': u.get('evidence') or str(path)}, data)
            else:
                raise ValueError('unsupported source kind')
            cursors[source['id']] = signature
            changed = True
        except (OSError, ValueError, KeyError, TypeError, StopIteration):
            errors.append('任务来源暂未同步：' + str(source.get('id', '未知来源')))
    if changed:
        atomic(data / 'source-cursors.json', cursors)
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['watch', 'once', 'request'])
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--ledger-data', type=Path)
    parser.add_argument('--codex-home', type=Path)
    args = parser.parse_args()
    try:
        migrate(args.ledger_data or args.data)
        if args.command == 'request':
            print(json.dumps({'ok': True, 'ledger': mutate(json.load(sys.stdin), args.ledger_data or args.data)}, ensure_ascii=False))
        else:
            home=args.codex_home
            watch = Watcher(args.data, db=home/'state_5.sqlite' if home else None, global_state=home/'.codex-global-state.json' if home else None, ledger_data=args.ledger_data)
            parent_pid = os.getppid()
            while os.getppid() == parent_pid:
                watch.tick()
                if args.command == 'once':
                    break
                time.sleep(2)
    except (ValueError, KeyError, StopIteration, OSError, sqlite3.Error) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
