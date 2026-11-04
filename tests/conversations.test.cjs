const {test}=require('node:test');const assert=require('node:assert/strict');
const {ConversationOrder}=require('../src/conversation-model.js');
const a=(id,status='active',turn='old',unread=false)=>({id,status,completedTurn:turn,isUnread:unread});
test('token timestamps and incoming database reorder do not move generating conversations',()=>{
 const m=new ConversationOrder();assert.deepEqual(m.update([a('a'),a('b'),a('c')]).map(t=>t.id),['a','b','c']);
 assert.deepEqual(m.update([a('c'),a('a'),a('b')].map((t,i)=>({...t,lastEventAt:100-i}))).map(t=>t.id),['a','b','c']);
});
test('a returned unread reply can move to the top; others keep their order',()=>{
 const m=new ConversationOrder();m.update([a('a'),a('b'),a('c')]);
 const result=m.update([a('a'),a('c','idle','new',true),a('b')]);
 assert.deepEqual(result.map(t=>t.id),['c','a','b']);assert.equal(result[0].isUnread,true);
});
test('new active rows append; reading a reply removes it without inferring task completion',()=>{
 const m=new ConversationOrder();m.update([a('a'),a('b','idle','reply',true)]);
 assert.deepEqual(m.update([a('c'),a('b','idle','reply',true),a('a')]).map(t=>t.id),['a','b','c']);
 assert.deepEqual(m.update([a('b','idle','reply',false),a('c'),a('a')]).map(t=>t.id),['a','c']);
});
test('saved order survives restart and handles replies returned while closed',()=>{
 const m=new ConversationOrder();m.update([a('a'),a('b')]);const saved=m.state();
 const restored=new ConversationOrder(saved.conversationOrder,saved.completionVersions);
 assert.deepEqual(restored.update([a('a'),a('b','idle','new',true)]).map(t=>t.id),['b','a']);
});
test('unknown is not labeled active; only a real unread marker keeps it visible',()=>{
 const m=new ConversationOrder();assert.equal(m.update([a('a','unknown','old',null)]).length,0);
 assert.equal(m.update([a('a','unknown','old',true)]).length,1);
});
const {partitionConversations,recentReply}=require('../src/conversation-model.js');
test('old unread stays folded even if its activity timestamp is current; generation always stays primary',()=>{
 const now=Date.UTC(2026,10,3,8),old={...a('old','idle','old',true),completedAt:(now-7*86400000)/1000,lastEventAt:now/1000};
 const fresh={...a('fresh','idle','reply',true),completedAt:(now-3600000)/1000};
 const active={...old,id:'active',status:'active'};
 const result=partitionConversations([old,fresh,active],now);
 assert.deepEqual(result.primary.map(t=>t.id),['fresh','active']);assert.deepEqual(result.historical.map(t=>t.id),['old']);
 assert.equal(old.isUnread,true);
});
test('unknown completion time is historical; a reply ages out after 72 hours',()=>{
 const now=Date.UTC(2026,10,3,8),unknown=a('unknown','idle','invalid',true),boundary={...a('boundary','idle','reply',true),completedAt:(now-3*86400000)/1000};
 assert.equal(recentReply(boundary,now),true);assert.equal(recentReply(boundary,now+1),false);
 assert.deepEqual(partitionConversations([unknown,boundary],now+1).primary,[]);
});
test('UUIDv7 publication time supports old log tails without using activity',()=>{
 const now=Date.UTC(2026,10,3,8),h=(now-3600000).toString(16).padStart(12,'0'),id=h.slice(0,8)+'-'+h.slice(8)+'-7000-8000-000000000000';
 assert.equal(recentReply({...a('a','idle',id,true),completedAt:0},now),true);
});

test('explicit re-mark of an old reply bypasses age folding until read',()=>{
 const now=Date.UTC(2026,10,4),old={...a('old','idle','same',true),completedAt:(now-10*86400000)/1000,isManualUnread:true,manualUnreadAt:'2026-11-04T00:00:00Z'};
 const m=new ConversationOrder();m.update([a('active'),{...old,isUnread:false,isManualUnread:false,manualUnreadAt:null}]);
 assert.deepEqual(m.update([a('active'),old]).map(t=>t.id),['old','active']);
 assert.deepEqual(partitionConversations([old],now).primary.map(t=>t.id),['old']);
 const saved=m.state(),restored=new ConversationOrder(saved.conversationOrder,saved.completionVersions);
 assert.deepEqual(restored.update([old,a('active')]).map(t=>t.id),['old','active']);
 assert.deepEqual(restored.update([{...old,isUnread:false,isManualUnread:false,manualUnreadAt:null},a('active')]).map(t=>t.id),['active']);
});
