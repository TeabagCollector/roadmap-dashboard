(()=>{'use strict';
const complete=t=>t.steps.length>0&&t.steps.every(s=>s.done);
function ordered(tasks,ids=[]){const byId=new Map(tasks.map(t=>[t.id,t])),out=[];for(const id of ids){if(byId.has(id)){out.push(byId.get(id));byId.delete(id);}}const remaining=[...byId.values()];if(!ids.length)remaining.sort((a,b)=>Number(complete(a))-Number(complete(b)));return out.concat(remaining);}
function move(ids,id,target,after=false){if(id===target||!ids.includes(id)||!ids.includes(target))return ids.slice();const next=ids.filter(x=>x!==id),at=next.indexOf(target)+(after?1:0);next.splice(at,0,id);return next;}
function visibleSteps(steps,hideDone,limit,showAll=false){const filtered=hideDone?steps.filter(s=>!s.done):steps.slice();return {steps:showAll||!limit?filtered:filtered.slice(0,limit),hiddenCompleted:hideDone?steps.filter(s=>s.done).length:0,remaining:showAll||!limit?0:Math.max(0,filtered.length-limit),totalVisible:filtered.length};}
const api={complete,ordered,move,visibleSteps};if(typeof module!=='undefined')module.exports=api;else window.DashboardRoadmapModel=api;
})();
