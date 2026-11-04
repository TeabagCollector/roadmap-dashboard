(()=>{'use strict';
if(window.webkit?.messageHandlers?.monitor)return;
const key='roadmap-dashboard-public-preview-v1';let state;
try{state=JSON.parse(localStorage.getItem(key)||'null');}catch{}
state=state||{preferences:{language:new URLSearchParams(location.search).get('lang')||'zh',theme:'system',conversationHeight:300},ledger:structuredClone(window.DASHBOARD_DEMO.ledger)};
const save=()=>{try{localStorage.setItem(key,JSON.stringify(state));}catch{}};
const feed=()=>{const f=structuredClone(window.DASHBOARD_DEMO);f.capturedAt=new Date().toISOString();for(const t of f.threads)t.completedAt=Date.now()/1000-t.ageSeconds;f.ledger=state.ledger;return f;};
const handler={postMessage(body){if(body.action==='ready'){queueMicrotask(()=>{const explicit=new URLSearchParams(location.search).get('lang');if(explicit)state.preferences.language=explicit;window.centralLoadPreferences(state.preferences);window.centralLoadSnapshot(feed());});}
else if(body.action==='preferences'){state.preferences=body.value;save();}
else if(body.action==='ledger'){const q=body.request;if(q.op==='check'){const t=state.ledger.tasks.find(t=>t.id===q.taskId),s=t?.steps.find(s=>s.id===q.stepId);if(s){s.done=!!q.done;s.source='user';s.needsReview=false;state.ledger.revision++;save();window.centralLedgerResult({ok:true,ledger:state.ledger});}}else window.centralError(DashboardI18n.text('演示对话仅在此预览展示。'));}
else if(body.action==='connection'){window.centralConnectionResult(body.request.op==='status'?{ok:true,connection:{connected:false,browser:true}}:{ok:false,error:'browser-preview'});}
else if(body.action==='open'||body.action==='hide')window.centralError(DashboardI18n.text('演示对话仅在此预览展示。'));}};
window.webkit={messageHandlers:{monitor:handler}};setInterval(()=>window.centralLoadSnapshot?.(feed()),3000);
})();
