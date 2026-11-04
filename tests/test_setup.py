import importlib.util,io,json,pathlib,sqlite3,sys,tempfile,unittest,contextlib,hashlib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'sync'))
import dashboard as d,setup,client
spec=importlib.util.spec_from_file_location('dashboard_installer',ROOT/'scripts/install.py');installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
class SetupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.base=self.root/'profile';self.home=self.root/'codex';self.home.mkdir()
  self.log=self.home/'rollout.jsonl';self.log.write_text(json.dumps({'type':'event_msg','timestamp':d.stamp(),'payload':{'type':'task_complete','turn_id':'demo-turn','last_agent_message':'not retained'}})+'\n')
  c=sqlite3.connect(self.home/'state_5.sqlite');c.execute('create table threads(id,title,name,cwd,project_id,rollout_path,archived,agent_path,updated_at,thread_source)');c.execute('insert into threads values(?,?,?,?,?,?,?,?,?,?)',('00000000-0000-4000-8000-000000000301','Sample','Sample','/tmp/demo',None,str(self.log),0,None,1,'user'));c.commit();c.close()
 def tearDown(self):self.tmp.cleanup()
 def connect(self):return setup.action({'op':'connect','codexHome':str(self.home)},self.base)
 def test_discovery_is_read_only_and_does_not_enroll(self):
  before=(self.home/'state_5.sqlite').read_bytes(),self.log.read_bytes()
  with patch.dict('os.environ',{'CODEX_HOME':str(self.home)}):result=setup.action({'op':'status'},self.base)
  self.assertTrue(result['discovery']['available']);self.assertFalse(result['connected'])
  self.assertFalse((self.base/'connection.json').exists());self.assertFalse((self.home/'skills').exists())
  self.assertEqual(before,((self.home/'state_5.sqlite').read_bytes(),self.log.read_bytes()))
 def test_one_click_connects_and_enrolls_only_selected_skill(self):
  with patch.dict('os.environ',{'CODEX_HOME':str(self.home)}):result=setup.action({'op':'start-tracking','includeRoadmap':True},self.base)
  self.assertTrue(result['connected']);self.assertTrue(result['trackingInstalled'])
  self.assertFalse((self.home/'AGENTS.md').exists());self.assertFalse((self.home/'hooks.json').exists())
 def test_one_click_without_roadmap_and_missing_source(self):
  with patch.dict('os.environ',{'CODEX_HOME':str(self.home)}):result=setup.action({'op':'start-tracking','includeRoadmap':False},self.base)
  self.assertTrue(result['connected']);self.assertFalse(result['trackingInstalled'])
  fresh=self.root/'another-profile'
  with patch.dict('os.environ',{'CODEX_HOME':str(self.root/'missing')}):
   self.assertFalse(setup.action({'op':'status'},fresh)['discovery']['available'])
   with self.assertRaisesRegex(ValueError,'codex-not-found'):setup.action({'op':'start-tracking'},fresh)
  self.assertFalse((fresh/'connection.json').exists())
 def test_one_click_skill_conflict_preserves_user_content(self):
  path=self.home/'skills/roadmap-dashboard-sync/SKILL.md';path.parent.mkdir(parents=True);path.write_text('user owned')
  with patch.dict('os.environ',{'CODEX_HOME':str(self.home)}):result=setup.action({'op':'start-tracking'},self.base)
  self.assertTrue(result['connected']);self.assertEqual(result['trackingWarning'],'skill-exists');self.assertEqual(path.read_text(),'user owned')
 def test_preflight_failure_does_not_replace_connection(self):
  self.connect();before=(self.base/'connection.json').read_bytes()
  with self.assertRaises(ValueError):setup.action({'op':'connect','codexHome':str(self.root/'missing')},self.base)
  self.assertEqual(before,(self.base/'connection.json').read_bytes())
 def test_shared_ledger_is_live_not_copied_and_sources_unchanged(self):
  self.connect();shared=self.root/'shared';d.migrate(shared)
  before=(self.home/'state_5.sqlite').read_bytes(),self.log.read_bytes()
  setup.action({'op':'link-ledger','path':str(shared/'ledger.json')},self.base)
  request={'op':'plan','revision':d.mutate({'op':'get'},shared)['revision'],'id':'demo-shared','title':'Shared','project':'Example','steps':[{'id':'one','text':'A step','status':'pending'}]}
  d.mutate(request,shared)
  w=d.Watcher(self.base/'live',db=self.home/'state_5.sqlite',ledger_data=shared);w.tick()
  feed=d.read(self.base/'live/feed.json',{});self.assertEqual(feed['ledger']['tasks'][0]['id'],'demo-shared')
  self.assertEqual(d.read(self.base/'live/ledger.json',{})['tasks'],[])
  d.mutate({'op':'check','revision':d.mutate({'op':'get'},shared)['revision'],'taskId':'demo-shared','stepId':'one','done':True},shared);w.tick();self.assertTrue(d.read(self.base/'live/feed.json',{})['ledger']['tasks'][0]['steps'][0]['done'])
  self.assertEqual(before,((self.home/'state_5.sqlite').read_bytes(),self.log.read_bytes()))
 def test_optional_skill_conflict_and_client_follow_connection(self):
  self.connect();target=self.home/'skills/roadmap-dashboard-sync/SKILL.md';target.parent.mkdir(parents=True);target.write_text('user-owned skill')
  with self.assertRaisesRegex(ValueError,'skill-exists'):setup.action({'op':'install-tracking'},self.base)
  self.assertEqual(target.read_text(),'user-owned skill');target.unlink()
  setup.action({'op':'install-tracking'},self.base);self.assertTrue(setup.status(self.base)['trackingInstalled'])
  self.assertFalse((self.home/'hooks.json').exists());self.assertFalse((self.home/'AGENTS.md').exists())
  shared=self.root/'tasks';d.migrate(shared);setup.action({'op':'link-ledger','path':str(shared/'ledger.json')},self.base)
  capture=io.StringIO()
  with patch.object(sys,'argv',['client','request']),patch.object(sys,'stdin',io.StringIO('{"op":"get"}')),contextlib.redirect_stdout(capture):client.main(base=self.base)
  self.assertTrue(json.loads(capture.getvalue())['ok'])
  with patch.object(sys,'argv',['client','request']),patch.object(sys,'stdin',io.StringIO('{"op":"check"}')),contextlib.redirect_stdout(io.StringIO()) as capture:client.main(base=self.base)
  self.assertFalse(json.loads(capture.getvalue())['ok'])
 def test_unread_enrollment_is_explicit_scoped_and_credential_free(self):
  self.connect();tid='00000000-0000-4000-8000-000000000301';p=self.home/'.codex-global-state.json'
  value={'electron-thread-read-state-v1':{'unreadByIdentity':{'a':{'local:h':[]},'b':{'local:h':['other']}}}}
  d.atomic(p,value);setup.action({'op':'unread-begin','threadId':tid},self.base)
  with self.assertRaisesRegex(ValueError,'no-unique'):setup.action({'op':'unread-finish'},self.base)
  value['electron-thread-read-state-v1']['unreadByIdentity']['a']['local:h']=[tid];d.atomic(p,value);before=p.read_bytes()
  setup.action({'op':'unread-finish'},self.base)
  binding=d.read(self.base/'live/desktop-unread-binding.json',{});self.assertEqual(binding['identityKey'],'a');self.assertEqual(before,p.read_bytes())
 def test_disconnect_preserves_tasks_and_switches_source_context(self):
  self.connect();ledger=(self.base/'live/ledger.json').read_bytes();result=setup.action({'op':'disconnect'},self.base)
  self.assertFalse(result['connected']);self.assertEqual(ledger,(self.base/'live/ledger.json').read_bytes())
 def test_installer_user_local_update_and_uninstall_preserve_data(self):
  source=self.root/'package';app=source/'build'/installer.NAME;(app/'Contents').mkdir(parents=True);(app/'Contents/example').write_text('demo executable')
  apps=self.root/'Apps';base=self.root/'runtime'
  with patch.object(installer,'ROOT',source):
   result=installer.install(apps,base,dry_run=True);self.assertTrue(result['dryRun']);self.assertFalse(apps.exists())
   installer.install(apps,base);(base/'ledger.json').write_text('keep');installer.uninstall(apps,base)
  self.assertEqual((base/'ledger.json').read_text(),'keep');self.assertFalse((apps/installer.NAME).exists())
if __name__=='__main__':unittest.main()
