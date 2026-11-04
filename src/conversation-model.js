(function(root){
  'use strict';
  class ConversationOrder {
    constructor(order=[], completions={}) {
      this.order=[...order];this.completions={...completions};
    }
    update(threads) {
      const currentIds=new Set(threads.map(t=>t.id));
      this.completions=Object.fromEntries(Object.entries(this.completions).filter(([id])=>currentIds.has(id)));
      const visible=threads.filter(t=>t.status==='active'||t.isUnread===true);
      const ids=new Set(visible.map(t=>t.id)), promoted=[];
      // Updating token timestamps or database order never changes our order.
      this.order=this.order.filter(id=>ids.has(id));
      for(const t of visible)if(!this.order.includes(t.id))this.order.push(t.id);
      for(const t of threads){
        const turn=(t.completedTurn||'')+(t.manualUnreadAt?'|manual:'+t.manualUnreadAt:'');
        if(this.completions[t.id]!==undefined&&turn&&turn!==this.completions[t.id]&&ids.has(t.id))promoted.push(t.id);
        this.completions[t.id]=turn;
      }
      if(promoted.length){const p=new Set(promoted);this.order=[...promoted,...this.order.filter(id=>!p.has(id))];}
      const byId=new Map(visible.map(t=>[t.id,t]));
      return this.order.map(id=>byId.get(id));
    }
    state(){return {conversationOrder:[...this.order],completionVersions:{...this.completions}};}
  }
  const RECENT_REPLY_MS=72*60*60*1000;
  function replyTime(thread){
    if(Number.isFinite(thread.completedAt)&&thread.completedAt>0)return thread.completedAt*1000;
    // A persisted Codex publication may be outside the bounded log tail.
    // Its UUIDv7 time is a fallback; activity/token timestamps are never used.
    const id=thread.completedTurn||'';
    if(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-/i.test(id))return parseInt(id.replaceAll('-','').slice(0,12),16);
    return 0;
  }
  function recentReply(thread,now=Date.now()){
    const time=replyTime(thread);
    return time>0&&time>=now-RECENT_REPLY_MS&&time<=now+5*60*1000;
  }
  function partitionConversations(ordered,now=Date.now()){
    const primary=[],historical=[];
    for(const thread of ordered){
      if(thread.status==='active'||(thread.isUnread===true&&(thread.isManualUnread===true||recentReply(thread,now))))primary.push(thread);
      else if(thread.isUnread===true)historical.push(thread);
    }
    return {primary,historical};
  }
  const api={ConversationOrder,partitionConversations,recentReply};
  if(typeof module!=='undefined')module.exports=api;
  else root.DashboardConversationModel=api;
})(typeof window!=='undefined'?window:globalThis);
