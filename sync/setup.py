#!/usr/bin/env python3
"""Explicit local setup. No auth-file reads, source writes, hooks or network."""
import contextlib,copy,json,os,sqlite3,sys,shlex
from pathlib import Path
sys.dont_write_bytecode=True
import dashboard as d

def default_base():
    return Path.home()/'Library/Application Support/RoadmapDashboardPreview'

def config(base):return d.read(base/'connection.json',{})
def validate_ledger(folder):
    path=folder/'ledger.json'
    if not path.is_file() or path.stat().st_size>10_000_000:raise ValueError('ledger-invalid')
    value=d.read(path,{})
    if value.get('schema')!=2 or not isinstance(value.get('tasks'),list) or not isinstance(value.get('revision'),int):raise ValueError('ledger-invalid')
    if any(not isinstance(t,dict) or not isinstance(t.get('steps'),list) for t in value['tasks']):raise ValueError('ledger-invalid')
    return value

def probe(home):
    path=(home/'state_5.sqlite').resolve()
    if not path.is_file():raise ValueError('codex-not-found')
    with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('pragma query_only=on')
        columns={r[1] for r in db.execute('pragma table_info(threads)')}
        if not {'id','title','cwd','project_id','rollout_path','archived','agent_path','updated_at'}.issubset(columns):raise ValueError('codex-schema-unsupported')
        name="coalesce(nullif(name,''),title)" if 'name' in columns else 'title'
        clause=" and thread_source='user'" if 'thread_source' in columns else ''
        rows=db.execute('select id,'+name+' from threads where archived=0 and agent_path is null'+clause+' order by updated_at desc limit 100').fetchall()
    return {'chatCount':len(rows),'chats':[{'id':r[0],'title':r[1]} for r in rows]}

def status(base):
    cfg=config(base)
    result={'connected':False,'mode':'demo','base':str(base),'codexHome':cfg.get('codexHome',str(Path.home()/'.codex')),'ledgerDirectory':cfg.get('ledgerDirectory',str(base/'live')),'trackingInstalled':False,'manualUnreadBound':(base/'live/desktop-unread-binding.json').exists()}
    if cfg.get('enabled'):
        try:
            result.update(probe(Path(result['codexHome'])));validate_ledger(Path(result['ledgerDirectory']))
            result.update(connected=True,mode='live')
        except (ValueError,sqlite3.Error,OSError) as e:result['problem']=str(e)
    installation=d.read(base/'tracking-installation.json',{})
    if installation:
        path=Path(installation['path'])
        result['trackingInstalled']=path.is_file() and 'roadmap-dashboard-managed-v1' in path.read_text()
    return result

def scoped_state(home):
    doc=d.read(home/'.codex-global-state.json',{})
    return doc.get('electron-thread-read-state-v1',{}).get('unreadByIdentity',{})

def action(request,base):
    base=base.expanduser().resolve();base.mkdir(parents=True,exist_ok=True);os.chmod(base,0o700)
    op=request.get('op','status');cfg=config(base)
    if op=='connect':
        home=Path(request.get('codexHome') or cfg.get('codexHome') or Path.home()/'.codex').expanduser().resolve()
        probe(home)
        ledger=Path(request.get('ledgerDirectory') or cfg.get('ledgerDirectory') or base/'live').expanduser().resolve()
        if request.get('ledgerDirectory'):validate_ledger(ledger)
        else:d.migrate(ledger)
        d.atomic(base/'connection.json',{'enabled':True,'codexHome':str(home),'ledgerDirectory':str(ledger),'updatedAt':d.stamp()})
    elif op=='disconnect':
        cfg['enabled']=False;d.atomic(base/'connection.json',cfg)
    elif op=='link-ledger':
        if not cfg.get('enabled'):raise ValueError('connect-first')
        path=Path(request['path']).expanduser().resolve()
        folder=path.parent if path.is_file() else path
        validate_ledger(folder);cfg['ledgerDirectory']=str(folder);d.atomic(base/'connection.json',cfg)
    elif op=='own-ledger':
        if not cfg.get('enabled'):raise ValueError('connect-first')
        d.migrate(base/'live');cfg['ledgerDirectory']=str(base/'live');d.atomic(base/'connection.json',cfg)
    elif op=='install-tracking':
        if not status(base)['connected']:raise ValueError('connect-first')
        home=Path(cfg['codexHome']);folder=home/'skills/roadmap-dashboard-sync';path=folder/'SKILL.md'
        marker='<!-- roadmap-dashboard-managed-v1 -->'
        if path.exists() and marker not in path.read_text():raise ValueError('skill-exists')
        root=Path(__file__).resolve().parent
        # Installed private launcher follows the current connection on every call.
        folder.mkdir(parents=True,exist_ok=True)
        script='import sys\nsys.dont_write_bytecode=True\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(root))+')\nimport client\nclient.main(base=Path('+repr(str(base))+'))\n'
        (folder/'dashboard_client.py').write_text(script)
        template=(root.parent/'skills/roadmap-dashboard-sync/SKILL.md').read_text()
        template+='\n'+marker+'\n\nInstalled local client: `'+shlex.quote(sys.executable)+' '+shlex.quote(str(folder/'dashboard_client.py'))+' request`. Pass request JSON on stdin. `status` reveals the current task directory. This local path is private installation metadata, never part of a public source archive.\n'
        path.write_text(template)
        for p in [path,folder/'dashboard_client.py']:os.chmod(p,0o600)
        d.atomic(base/'tracking-installation.json',{'path':str(path),'installedAt':d.stamp()})
    elif op=='unread-begin':
        if not status(base)['connected']:raise ValueError('connect-first')
        home=Path(cfg['codexHome']);tid=request['threadId']
        if tid not in {t['id'] for t in probe(home)['chats']}:raise ValueError('chat-not-found')
        d.atomic(base/'unread-enrollment.json',{'threadId':tid,'before':scoped_state(home)})
    elif op=='unread-finish':
        pending=d.read(base/'unread-enrollment.json',{});tid=pending.get('threadId')
        if not tid:raise ValueError('unread-start-first')
        after=scoped_state(Path(cfg['codexHome']));matches=[]
        for identity,hosts in after.items():
            for host,ids in hosts.items():
                before=pending['before'].get(identity,{}).get(host,[])
                if host.startswith('local:') and tid in ids and tid not in before:matches.append((identity,host))
        if len(matches)!=1:raise ValueError('unread-no-unique-change')
        identity,host=matches[0]
        d.atomic(base/'live/desktop-unread-binding.json',{'identityKey':identity,'hostKey':host,'verifiedAt':d.stamp()})
        before=pending['before'].get(identity,{}).get(host,[])
        d.atomic(base/'live/desktop-unread-observed.json',{'scope':identity+'/'+host,'unreadIds':before,'manualMarks':{}})
        (base/'unread-enrollment.json').unlink()
    elif op!='status':raise ValueError('unsupported-action')
    return status(base)

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=default_base());args=p.parse_args()
    try:print(json.dumps({'ok':True,'connection':action(json.load(sys.stdin),args.base)},ensure_ascii=False))
    except (ValueError,OSError,KeyError,sqlite3.Error) as e:print(json.dumps({'ok':False,'error':str(e)}))
if __name__=='__main__':main()
