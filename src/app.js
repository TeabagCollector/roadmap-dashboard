(() => {
'use strict';
const tr=DashboardI18n.text,field=DashboardI18n.field;
const $=s=>document.querySelector(s), el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
const send=body=>window.webkit?.messageHandlers?.monitor?.postMessage(body);
let feed=null,signature='',hideDone=false,busy=false;
const expanded=new Map(),infoOpen=new Set();
let preferences={theme:'system',conversationHeight:300,hideCompleted:false,language:'zh'};
let ordering=new DashboardConversationModel.ConversationOrder(),conversationSignature='',recentSignature='',historySignature='';
const themes=[['system','跟随系统','#b8c1ca'],['light','浅色','#ffffff'],['dark','深色','#22272e'],['warm','暖纸','#efe1c7'],['sage','青灰','#bbd4c4']];
function savePreferences(){send({action:'preferences',value:{...preferences,...ordering.state()}});}
function splitBounds(){
 const occupied=$('header').getBoundingClientRect().height+$('.list-heading').getBoundingClientRect().height+$('footer').getBoundingClientRect().height+$('#splitter').getBoundingClientRect().height+$('#feedback').getBoundingClientRect().height;
 return {min:120,max:Math.max(120,innerHeight-occupied-125)};
}
function applySplit(height,persist=false){
 const bounds=splitBounds(),actual=Math.max(bounds.min,Math.min(bounds.max,height));
 document.documentElement.style.setProperty('--conversation-height',actual+'px');
 $('#splitter').setAttribute('aria-valuemin',String(bounds.min));$('#splitter').setAttribute('aria-valuemax',String(Math.round(bounds.max)));$('#splitter').setAttribute('aria-valuenow',String(Math.round(actual)));
 if(persist){preferences.conversationHeight=actual;savePreferences();}
}
function applyTheme(theme,persist=false){
 preferences.theme=themes.some(t=>t[0]===theme)?theme:'system';document.documentElement.dataset.theme=preferences.theme;
 $('#theme-options').replaceChildren(...themes.map(([id,label,color])=>{const b=el('button',null,tr(label)),dot=el('span','theme-swatch');dot.style.background=color;b.prepend(dot);b.dataset.theme=id;b.setAttribute('aria-pressed',String(preferences.theme===id));b.onclick=()=>{applyTheme(id,true);$('#theme-panel').hidden=true;$('#theme').setAttribute('aria-expanded','false');};return b;}));
 if(persist)savePreferences();
}
window.centralLoadPreferences=value=>{
 preferences={...preferences,...value};DashboardI18n.setLanguage(preferences.language);DashboardI18n.apply();window.dispatchEvent(new Event('dashboard-language'));$('#language').textContent=preferences.language==='en'?'中':'EN';hideDone=!!preferences.hideCompleted;ordering=new DashboardConversationModel.ConversationOrder(value.conversationOrder||[],value.completionVersions||{});
 applyTheme(preferences.theme);applySplit(preferences.conversationHeight);$('#hide-done').textContent=hideDone?tr('显示已完成'):tr('隐藏已完成');$('#hide-done').setAttribute('aria-pressed',String(hideDone));
 if(feed){conversationSignature='';renderConversations();renderTasks();}
};

function feedback(text){$('#feedback').textContent=tr(text);}
function open(t){send({action:'open',id:t.id,kind:t.kind||'codex'});}
function request(req){if(busy)return;busy=true;send({action:'ledger',request:{...req,revision:feed.ledger.revision}});}
function linked(t){const task=feed.ledger.tasks.find(x=>x.threadId===t.id);if(!task)return;expanded.set(task.id,true);renderTasks();const box=[...document.querySelectorAll('.task')].find(x=>x.dataset.id===task.id);box?.scrollIntoView({block:'nearest'});box?.classList.add('highlight');}
function follow(t){if(feed.ledger.tasks.some(x=>x.threadId===t.id)){linked(t);return;}if(busy)return;busy=true;send({action:'ledger',request:{op:'follow',thread:t,revision:feed.ledger.revision}});}
function row(t,stale=false,historical=false){
 const r=el('div','conversation'+(historical?' historical':'')),generating=t.status==='active'&&!stale,unread=t.isUnread===true;
 r.dataset.threadId=t.id;
 const dot=el('span','dot'+(generating?'':unread?' unread':' unknown')),main=el('div','conversation-main'),b=el('button','conversation-title',field(t,'title'));
 b.onclick=()=>open(t);b.dataset.conversationId=t.id;
 main.append(b,el('div','project',field(t,'project')));
 const state=historical?tr('历史未读标记'):t.isManualUnread?(generating?tr('生成中 · 手动未读'):tr('手动标为未读')):generating?((unread&&DashboardConversationModel.recentReply(t))?tr('生成中 · 尚有新回复'):tr('生成中')):unread?(stale?tr('状态待确认 · 未读'):tr('已回复 · 未读')):((stale||t.status==='unknown')?tr('运行状态待确认'):t.status==='stopped'?tr('已停止'):tr('空闲'));
 main.append(el('div','reply-badge'+(generating?' generating':''),state));
 const l=el('button','link-task',feed.ledger.tasks.some(x=>x.threadId===t.id)?'↳':'＋');l.setAttribute('aria-label',tr('查看或关联 ')+field(t,'title')+tr(' 的清单'));l.onclick=()=>follow(t);r.append(dot,main,l);return r;
}
function renderConversations(){
 const stale=!feed.live||Date.now()-Date.parse(feed.capturedAt)>12000,prior=JSON.stringify(ordering.state()),allOrdered=ordering.update(feed.threads),{primary:ordered,historical}=DashboardConversationModel.partitionConversations(allOrdered),current=JSON.stringify(ordering.state());
 const active=stale?0:ordered.filter(t=>t.status==='active').length,unread=ordered.filter(t=>t.isUnread===true&&!t.isManualUnread&&DashboardConversationModel.recentReply(t)).length,manual=ordered.filter(t=>t.isUnread===true&&t.isManualUnread).length;
 $('#count').textContent=stale?'—':DashboardI18n.counts(active,unread,manual);
 $('#sync-time').textContent=feed.demo?tr('预览 · 虚构数据'):stale?tr('连接待恢复'):tr('本机 · 实时');
 const key=JSON.stringify([stale,ordered.map(t=>[t.id,field(t,'title'),field(t,'project'),t.status,t.isUnread,t.completedTurn,t.isManualUnread,t.manualUnreadAt]),feed.ledger.tasks.map(t=>t.threadId)]);
 if(key!==conversationSignature){
  const scroll=$('#conversations').scrollTop,focused=document.activeElement?.dataset.conversationId;
  $('#running').replaceChildren(...ordered.map(t=>row(t,stale)));
  if(!ordered.length)$('#running').append(el('div','empty',stale?tr('连接中断，暂不判断状态'):tr('没有正在生成、手动标记或最近 72 小时内的未读新回复')));
  $('#conversations').scrollTop=scroll;conversationSignature=key;
  if(focused)[...document.querySelectorAll('[data-conversation-id]')].find(b=>b.dataset.conversationId===focused)?.focus({preventScroll:true});
 }
 $('#history-unread').hidden=historical.length===0;$('#history-count').textContent=String(historical.length);
 const historyKey=JSON.stringify([stale,historical.map(t=>[t.id,field(t,'title'),field(t,'project'),t.isUnread,t.completedTurn])]);
 if(historyKey!==historySignature){$('#history-list').replaceChildren(...historical.map(t=>row(t,stale,true)));historySignature=historyKey;}
 const visible=new Set(allOrdered.map(t=>t.id)),recent=feed.threads.filter(t=>!visible.has(t.id)).slice(0,12),recentKey=JSON.stringify(recent.map(t=>[t.id,field(t,'title'),t.status,t.isUnread]));
 if(recentKey!==recentSignature){$('#other').replaceChildren(...recent.map(t=>row(t,stale)));recentSignature=recentKey;}
 $('#source-description').textContent=stale?tr('本机事件读取已暂停；保留清单，运行状态待确认。'):tr('主区域显示生成中、主动重新标为未读和最近 72 小时的未读新回复；普通历史标记默认折叠。手动标记使用已核验的本机桌面身份；这里不改原对话已读状态。');
 if(feed.demo)$('#source-description').textContent=tr('预览使用虚构任务，不读取你的对话，不调用模型。');
 if(feed.errors?.length)$('#source-description').textContent+=' '+feed.errors.map(tr).join('; ');
 if(prior!==current)savePreferences();
}
function renderTasks(){const scroll=$('#checklist').scrollTop,focused=document.activeElement?.dataset.focus,list=$('#tasks');list.replaceChildren();for(const task of [...feed.ledger.tasks].sort((a,b)=>Number(a.steps.length>0&&a.steps.every(s=>s.done))-Number(b.steps.length>0&&b.steps.every(s=>s.done)))){const done=task.steps.length>0&&task.steps.every(s=>s.done);if(hideDone&&done)continue;const box=el('article','task'+(done?' all-done':''));box.dataset.id=task.id;const head=el('div','task-head'),parent=el('input');parent.type='checkbox';parent.checked=done;parent.disabled=true;parent.setAttribute('aria-label',field(task,'title')+tr('：全部步骤完成后勾选'));const main=el('div','task-main'),toggle=el('button','task-toggle'),isOpen=expanded.has(task.id)?expanded.get(task.id):task.defaultExpanded!==false;toggle.setAttribute('aria-expanded',String(isOpen));toggle.dataset.focus='task-'+task.id;toggle.append(el('span','task-title',field(task,'title')),el('span','task-count',task.steps.length?`${task.steps.filter(s=>s.done).length} / ${task.steps.length}`:tr('待关联计划')),el('span','chevron',isOpen?'⌄':'›'));toggle.onclick=()=>{expanded.set(task.id,!isOpen);renderTasks();};main.append(toggle,el('div','project',field(task,'project')));if(field(task,'note'))main.append(el('div','task-note',field(task,'note')));if(task.threadId){const src=el('button','task-source',tr('↗ 原对话'));src.onclick=()=>open({id:task.threadId});main.append(src);}head.append(parent,main);box.append(head);const roadmap=el('div','roadmap');roadmap.hidden=!isOpen;
for(const step of task.steps){const key=task.id+':'+step.id,stepRow=el('div','step'+(step.done?' done':'')),rh=el('div','step-head'),check=el('input');check.type='checkbox';check.checked=!!step.done;check.id='check-'+key;check.dataset.focus=key;check.onchange=()=>{const wanted=check.checked;check.checked=!!step.done;request({op:'check',taskId:task.id,stepId:step.id,done:wanted});};const sm=el('div','step-main'),label=el('label',null,field(step,'text'));label.htmlFor=check.id;sm.append(label);if(!step.done&&(step.needsReview||['in_progress','blocked'].includes(step.reported)))sm.append(el('div','badge',step.needsReview?tr('已上报 · 待核验'):step.reported==='blocked'?tr('有阻塞 · 查看详情'):tr('正在推进')));const info=el('button','info','ⓘ');info.setAttribute('aria-label',tr('查看 ')+field(step,'text')+tr(' 的完成条件与证据'));info.setAttribute('aria-expanded',String(infoOpen.has(key)));info.onclick=()=>{infoOpen.has(key)?infoOpen.delete(key):infoOpen.add(key);renderTasks();};rh.append(check,sm,info);stepRow.append(rh);const detail=el('div','step-details');detail.hidden=!infoOpen.has(key);detail.append(el('p',null,tr('完成条件：')+(field(step,'criterion')||tr('由你确认'))),el('p',null,tr('记录：')+(field(step,'evidence')||field(step,'reportEvidence')||tr('尚无完成验证'))));if(field(step,'reportEvidence'))detail.append(el('p',null,tr('执行回执：')+field(step,'reportEvidence')));stepRow.append(detail);roadmap.append(stepRow);}
if(!task.steps.length)roadmap.append(el('div','no-plan',tr('尚未收到这段对话的实际计划；不会根据标题猜测进度。')));box.append(roadmap);list.append(box);}if(!list.children.length)list.append(el('div','task empty',hideDone?tr('没有未完成的任务'):tr('从对话旁的 ＋ 关联，或让 agent 登记当前计划。')));$('#checklist').scrollTop=scroll;if(focused){[...document.querySelectorAll('[data-focus]')].find(x=>x.dataset.focus===focused)?.focus({preventScroll:true});}}
window.centralLoadSnapshot=value=>{if(!value||value.schema!==2||!Array.isArray(value.threads)||!Array.isArray(value.ledger?.tasks)){feedback(tr('同步格式不匹配，保留上一份清单。'));return;}if(feed&&value.ledgerContext!==feed.ledgerContext){feed=null;ordering=new DashboardConversationModel.ConversationOrder();signature='';conversationSignature='';recentSignature='';historySignature='';expanded.clear();}if(feed&&value.ledger.revision<feed.ledger.revision)value={...value,ledger:feed.ledger};feed=value;renderConversations();const next=JSON.stringify(value.ledger);if(next!==signature){signature=next;renderTasks();}};
window.centralLedgerResult=result=>{busy=false;if(result.ok){feed.ledger=result.ledger;signature=JSON.stringify(result.ledger);renderTasks();renderConversations();feedback(tr('已保存'));}else{feedback(result.error||tr('未能保存，原记录仍保留'));}};
window.centralError=feedback;
$('#theme').onclick=()=>{const hidden=!$('#theme-panel').hidden;$('#theme-panel').hidden=hidden;$('#theme').setAttribute('aria-expanded',String(!hidden));};
document.addEventListener('pointerdown',event=>{if(!$('#theme-panel').hidden&&!$('#theme-panel').contains(event.target)&&!$('#theme').contains(event.target)){$('#theme-panel').hidden=true;$('#theme').setAttribute('aria-expanded','false');}});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){$('#theme-panel').hidden=true;$('#theme').setAttribute('aria-expanded','false');}});
let splitDrag=null;
$('#splitter').onpointerdown=event=>{splitDrag={y:event.clientY,height:$('#conversations').getBoundingClientRect().height};event.currentTarget.setPointerCapture(event.pointerId);document.body.classList.add('resizing');event.preventDefault();};
$('#splitter').onpointermove=event=>{if(splitDrag)applySplit(splitDrag.height+event.clientY-splitDrag.y);};
$('#splitter').onpointerup=event=>{if(splitDrag){applySplit($('#conversations').getBoundingClientRect().height,true);splitDrag=null;document.body.classList.remove('resizing');if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);}};
$('#splitter').onpointercancel=()=>{splitDrag=null;document.body.classList.remove('resizing');};
$('#splitter').onkeydown=event=>{const bounds=splitBounds(),height=$('#conversations').getBoundingClientRect().height;const target={ArrowUp:height-20,ArrowDown:height+20,Home:bounds.min,End:bounds.max}[event.key];if(target!==undefined){event.preventDefault();applySplit(target,true);}};
const splitObserver=new ResizeObserver(()=>applySplit(preferences.conversationHeight));[document.body,$('footer'),$('#feedback')].forEach(node=>splitObserver.observe(node));
$('#language').onclick=()=>{preferences.language=preferences.language==='en'?'zh':'en';DashboardI18n.setLanguage(preferences.language);DashboardI18n.apply();window.dispatchEvent(new Event('dashboard-language'));$('#language').textContent=preferences.language==='en'?'中':'EN';applyTheme(preferences.theme);$('#hide-done').textContent=hideDone?tr('显示已完成'):tr('隐藏已完成');conversationSignature='';historySignature='';recentSignature='';if(feed){renderConversations();renderTasks();}savePreferences();};
DashboardI18n.apply();applyTheme(preferences.theme);applySplit(preferences.conversationHeight);
$('#hide').onclick=()=>send({action:'hide'});$('#hide-done').onclick=()=>{hideDone=!hideDone;$('#hide-done').setAttribute('aria-pressed',String(hideDone));$('#hide-done').textContent=hideDone?tr('显示已完成'):tr('隐藏已完成');preferences.hideCompleted=hideDone;savePreferences();if(feed)renderTasks();};setInterval(()=>{if(feed)renderConversations();},3000);send({action:'ready'});window.dispatchEvent(new Event('dashboard-ready'));
})();
