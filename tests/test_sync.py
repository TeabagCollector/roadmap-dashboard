import importlib.util,json,pathlib,tempfile,unittest,datetime,sqlite3,time
module=pathlib.Path(__file__).resolve().parents[1]/'sync/dashboard.py'
spec=importlib.util.spec_from_file_location('dashboard',module);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class SyncTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);d.migrate(self.root)
 def tearDown(self): self.tmp.cleanup()
 def request(self,**value):
  return d.mutate({'revision':d.mutate({'op':'get'},self.root)['revision'],**value},self.root)
 def plan(self,steps=None):
  return self.request(op='plan',id='t',title='<script>title</script>',threadId='00000000-0000-4000-8000-000000000111',steps=steps or [{'id':'one','text':'Build','status':'completed'}])
 def test_report_is_not_accepted_and_manual_choice_survives(self):
  s=self.plan();step=s['tasks'][0]['steps'][0];self.assertFalse(step['done']);self.assertTrue(step['needsReview'])
  self.request(op='check',taskId='t',stepId='one',done=False)
  self.plan();self.assertFalse(d.mutate({'op':'get'},self.root)['tasks'][0]['steps'][0]['done'])
  with self.assertRaises(ValueError):self.request(op='accept',taskId='t',stepId='one',evidence='test')
 def test_revision_conflict_preserves_user_choice(self):
  s=self.plan();self.request(op='check',taskId='t',stepId='one',done=True)
  with self.assertRaises(ValueError):d.mutate({'op':'check','revision':s['revision'],'taskId':'t','stepId':'one','done':False},self.root)
  self.assertTrue(d.mutate({'op':'get'},self.root)['tasks'][0]['steps'][0]['done'])
 def test_verified_evidence_and_restart(self):
  self.plan();self.request(op='accept',taskId='t',stepId='one',evidence='Native QA passed')
  self.assertEqual(json.loads((self.root/'ledger.json').read_text())['tasks'][0]['steps'][0]['evidence'],'Native QA passed')
 def test_changed_plan_reopens_verified_step(self):
  self.plan();self.request(op='accept',taskId='t',stepId='one',evidence='Earlier verified work')
  self.plan([{'id':'one','text':'Build','status':'in_progress'}]);step=d.mutate({'op':'get'},self.root)['tasks'][0]['steps'][0]
  self.assertFalse(step['done']);self.assertFalse(step['needsReview'])
 def test_append_plan_preserves_verified_review_and_manual_states(self):
  self.plan([{'id':'one','text':'Accepted','status':'completed'},{'id':'review','text':'Reported','status':'completed'},{'id':'manual','text':'Manual','status':'completed'}])
  self.request(op='accept',taskId='t',stepId='one',evidence='Verified original delivery')
  self.request(op='check',taskId='t',stepId='manual',done=False)
  before=d.mutate({'op':'get'},self.root)['tasks'][0]['steps']
  copied=[dict(s) for s in before]+[{'id':'new','text':'Follow-up'}]
  self.plan(copied)
  after=d.mutate({'op':'get'},self.root)['tasks'][0]['steps']
  for old,new in zip(before,after):
   for key in ('reported','done','source','evidence','needsReview'):
    self.assertEqual(old.get(key),new.get(key),(old['id'],key))
  self.assertEqual(after[-1]['reported'],'pending')
 def test_omitted_status_preserves_blocked_step(self):
  self.plan();self.request(op='report',taskId='t',stepId='one',status='blocked',evidence='Waiting for required input')
  self.plan([{'id':'one','text':'Build'}])
  step=d.mutate({'op':'get'},self.root)['tasks'][0]['steps'][0]
  self.assertEqual(step['reported'],'blocked');self.assertFalse(step['done'])
 def test_retired_steps_preserved(self):
  self.plan();self.plan([{'id':'two','text':'Ship'}]);s=d.mutate({'op':'get'},self.root)
  self.assertEqual(s['tasks'][0]['retiredSteps'][0]['id'],'one')
 def test_duplicate_ids_and_failed_write_do_not_change_ledger(self):
  before=(self.root/'ledger.json').read_bytes()
  with self.assertRaises(ValueError):self.plan([{'id':'one','text':'A'},{'id':'one','text':'B'}])
  self.assertEqual((self.root/'ledger.json').read_bytes(),before)
 def event(self,kind,turn='a'):
  return {'timestamp':d.stamp(),'type':'event_msg','payload':{'type':kind,'turn_id':turn}}
 def test_turn_status_and_incorrect_turn_completion(self):
  t=d.Tail();t.ingest(self.event('task_started'));t.ingest(self.event('task_complete','b'));self.assertEqual(t.live_status(time.time()),'active')
  t.ingest(self.event('turn_aborted'));self.assertEqual(t.status,'stopped')
  t.ingest(self.event('task_started'));self.assertEqual(t.live_status(time.time()+181),'unknown')
 def test_large_turn_initial_scan_partial_line_and_truncation(self):
  p=self.root/'log';start=json.dumps(self.event('task_started'))+'\n'
  p.write_text(start+json.dumps({'type':'response_item','payload':{'type':'message','content':'x'*1100000}})+'\n')
  t=d.Tail();t.poll(p);self.assertEqual(t.status,'active')
  done=json.dumps(self.event('task_complete'))
  with p.open('a') as f:f.write(done[:30])
  t.poll(p);self.assertEqual(t.status,'active')
  with p.open('a') as f:f.write(done[30:]+'\n')
  t.poll(p);self.assertEqual(t.status,'idle')
  p.write_text(json.dumps(self.event('turn_aborted'))+'\n');t.poll(p);self.assertEqual(t.status,'stopped')
 def test_only_structured_plan_not_message_guess(self):
  t=d.Tail();t.ingest({'type':'response_item','payload':{'type':'message','content':'update_plan completed'}});self.assertIsNone(t.plan)
  t.ingest({'type':'response_item','payload':{'type':'function_call','name':'update_plan','arguments':json.dumps({'plan':[{'step':'test','status':'in_progress'}]})}});self.assertEqual(t.plan[0]['step'],'test')
 def test_legacy_migration_is_non_destructive(self):
  root=self.root/'migration';root.mkdir();old={'tasks':[{'id':'old','text':'Keep me','done':True}],'pinned':['old']};d.atomic(root/'user-state.json',old);d.migrate(root);d.migrate(root)
  self.assertEqual(d.read(root/'user-state.json',{}),old);s=d.mutate({'op':'get'},root);self.assertEqual(len(s['tasks']),1);self.assertTrue(s['tasks'][0]['steps'][0]['done'])
 def test_live_watcher_to_plan_to_ledger_and_feed(self):
  db=self.root/'state.sqlite';c=sqlite3.connect(db);c.execute('create table threads(id,title,name,cwd,project_id,rollout_path,archived,agent_path,updated_at)');p=self.root/'log'
  p.write_text(json.dumps(self.event('task_started'))+'\n'+json.dumps({'type':'response_item','payload':{'type':'function_call','name':'update_plan','arguments':json.dumps({'plan':[{'step':'Real structured plan','status':'completed'}]})}})+'\n')
  c.execute('insert into threads values(?,?,?,?,?,?,?,?,?)',('00000000-0000-4000-8000-000000000111','old','Actual title','/tmp/project','p',str(p),0,None,1));c.commit();c.close()
  w=d.Watcher(self.root,db);w.tick();self.assertEqual(d.read(self.root/'feed.json',{})['ledger']['tasks'],[])
  self.request(op='follow',thread={'id':'00000000-0000-4000-8000-000000000111','title':'Actual title','project':'project'});w=d.Watcher(self.root,db);w.tick();feed=d.read(self.root/'feed.json',{});self.assertEqual(feed['threads'][0]['status'],'active');self.assertEqual(feed['threads'][0]['title'],'Actual title');self.assertTrue(feed['ledger']['tasks'][0]['steps'][0]['needsReview']);self.assertFalse(feed['ledger']['tasks'][0]['steps'][0]['done'])
  with p.open('a') as f:f.write(json.dumps(self.event('task_complete'))+'\n')
  w.tick();self.assertEqual(d.read(self.root/'feed.json',{})['threads'][0]['status'],'idle')
  c=sqlite3.connect(db);c.execute('create table thread_read_receipts(thread_id,first_unread_turn,last_published_turn)');c.execute('insert into thread_read_receipts values(?,?,?)',('00000000-0000-4000-8000-000000000111','unread-turn','published-turn'));c.commit();w.tick();thread=d.read(self.root/'feed.json',{})['threads'][0];self.assertTrue(thread['isUnread']);self.assertEqual(thread['completedTurn'],'published-turn')
  c.execute('update thread_read_receipts set first_unread_turn=null');c.commit();c.close();w.tick();self.assertFalse(d.read(self.root/'feed.json',{})['threads'][0]['isUnread'])

 def test_desktop_remark_old_thread_scope_restart_and_clear(self):
  db=self.root/'state.sqlite';c=sqlite3.connect(db)
  c.execute('create table threads(id,title,name,cwd,project_id,rollout_path,archived,agent_path,updated_at)')
  c.execute('create table thread_read_receipts(thread_id,first_unread_turn,last_published_turn)')
  p=self.root/'log';p.write_text(json.dumps(self.event('task_complete'))+'\n')
  rows=[('old','Old','Old','/tmp',None,str(p),0,None,0)]
  rows += [(str(i),'Recent','Recent','/tmp',None,str(p),0,None,i+1) for i in range(101)]
  c.executemany('insert into threads values(?,?,?,?,?,?,?,?,?)',rows)
  c.execute('insert into thread_read_receipts values(?,?,?)',('old',None,'turn'));c.commit();c.close()
  state=self.root/'global.json';binding={'identityKey':'account-a','hostKey':'local:host'}
  d.atomic(self.root/'desktop-unread-binding.json',binding)
  doc={'electron-thread-read-state-v1':{'unreadByIdentity':{'account-a':{'local:host':[]},'account-b':{'local:host':['other']}}}}
  d.atomic(state,doc);w=d.Watcher(self.root,db,global_state=state);w.tick()
  self.assertNotIn('old',{t['id'] for t in d.read(self.root/'feed.json',{})['threads']})
  doc['electron-thread-read-state-v1']['unreadByIdentity']['account-a']['local:host']=['old'];d.atomic(state,doc);w.tick()
  old=next(t for t in d.read(self.root/'feed.json',{})['threads'] if t['id']=='old')
  self.assertTrue(old['isUnread']);self.assertTrue(old['isManualUnread']);mark=old['manualUnreadAt']
  d.Watcher(self.root,db,global_state=state).tick()
  self.assertEqual(d.read(self.root/'desktop-unread-observed.json',{})['manualMarks']['old'],mark)
  doc['electron-thread-read-state-v1']['unreadByIdentity']['account-a']['local:host']=[];d.atomic(state,doc);w.tick()
  self.assertEqual(d.read(self.root/'desktop-unread-observed.json',{})['manualMarks'],{})
  self.assertNotIn('other',{t['id'] for t in d.read(self.root/'feed.json',{})['threads']})
 def test_initial_desktop_history_not_promoted_and_wrong_scope_unavailable(self):
  p=self.root/'global.json';d.atomic(self.root/'desktop-unread-binding.json',{'identityKey':'a','hostKey':'local:h'})
  d.atomic(p,{'electron-thread-read-state-v1':{'unreadByIdentity':{'a':{'local:h':['old']},'b':{'local:h':['wrong']}}}})
  reader=d.DesktopUnread(self.root,p);value=reader.read({});self.assertEqual(value['ids'],{'old'});self.assertEqual(value['marks'],{})
  d.atomic(self.root/'desktop-unread-binding.json',{'identityKey':'missing','hostKey':'local:h'});self.assertIsNone(reader.read({}))

class SourceBridgeTests(unittest.TestCase):
 setUp=SyncTests.setUp
 tearDown=SyncTests.tearDown
 request=SyncTests.request
 plan=SyncTests.plan
 def worker_source(self, updates):
  self.plan()
  report=self.root/'worker.json'
  d.atomic(report,{'schema':1,'taskId':'t','ticketId':'ticket-1','updates':updates})
  d.atomic(self.root/'task-sources.json',{'sources':[{'id':'worker','kind':'worker-report','path':str(report),'taskId':'t','ticketId':'ticket-1','allowedStepIds':['one']}]})
  return report
 def test_worker_progress_is_pending_review_and_idempotent(self):
  self.worker_source([{'stepId':'one','status':'completed','evidence':'actual report'}])
  self.assertEqual(d.sync_sources(self.root),[])
  s=d.mutate({'op':'get'},self.root);step=s['tasks'][0]['steps'][0]
  self.assertFalse(step['done']);self.assertTrue(step['needsReview']);rev=s['revision']
  d.sync_sources(self.root);self.assertEqual(d.mutate({'op':'get'},self.root)['revision'],rev)
 def test_worker_cannot_create_unassigned_steps_or_accept(self):
  self.worker_source([{'stepId':'alien','status':'completed'}]);before=(self.root/'ledger.json').read_bytes()
  self.assertTrue(d.sync_sources(self.root));self.assertEqual(before,(self.root/'ledger.json').read_bytes())
 def test_worker_report_preserves_manual_choice(self):
  self.worker_source([{'stepId':'one','status':'completed','evidence':'worker report'}]);self.request(op='check',taskId='t',stepId='one',done=False)
  d.sync_sources(self.root);step=d.mutate({'op':'get'},self.root)['tasks'][0]['steps'][0]
  self.assertFalse(step['done']);self.assertEqual(step['source'],'user')
 def test_source_failure_keeps_existing_tasks(self):
  self.worker_source([{'stepId':'one','status':'completed'}]);(self.root/'worker.json').write_text('{broken')
  before=(self.root/'ledger.json').read_bytes();self.assertTrue(d.sync_sources(self.root));self.assertEqual(before,(self.root/'ledger.json').read_bytes())
if __name__=='__main__':unittest.main()
