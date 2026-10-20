import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {currentFlowDecision,keyboardTranslationValue} from './reference-current-step.mjs';
const labels={check:'检查',continue:'继续'};
const read=path=>JSON.parse(readFileSync(new URL(path,import.meta.url)));
test('actual captured introduction can continue, result/profile cannot',()=>{
 const capture=read('evidence/english-isolation-presentation-v1/source-probe/challenge-intro.json');
 const facts={path:capture.path,dialog_count:0,challenge_count:0,heading_count:0,
  body_text:capture.snapshot,continue_count:1,continue_enabled:true};
 assert.equal(currentFlowDecision(facts,labels).kind,'interlude');
 for(const text of ['来创建你的个人档案吧！','你又获取了一颗红心！','学习完成'])
  assert.equal(currentFlowDecision({...facts,body_text:text},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,dialog_count:1},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,path:'/learn'},labels).kind,'uncovered_state');
});
test('old feedback and ambiguous challenge cannot be treated as a fresh question',()=>{
 const facts={path:'/practice',dialog_count:0,body_text:'正确！',heading_count:1,
  challenge_count:1,challenge_visible:true,next_text:'继续'};
 assert.equal(currentFlowDecision(facts,labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,next_text:'检查'},labels).kind,'challenge');
 assert.equal(currentFlowDecision({...facts,next_text:'检查',challenge_count:2},labels).kind,'uncovered_state');
});
test('actual keyboard challenge has a solution without fabricating a word bank',()=>{
 const c=read('evidence/english-isolation-presentation-v1/source-probe/current-challenge-after-intro.json').content;
 assert.equal(keyboardTranslationValue(c,{textbox_count:1,textbox_enabled:true,bank_count:0}),'tea with sugar');
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:0,bank_count:0}),/actual enabled text field/);
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:2,textbox_enabled:true,bank_count:0}),/actual enabled text field/);
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:1,textbox_enabled:true,bank_count:1}),/no word bank/);
 assert.equal(keyboardTranslationValue({...c,choices:['茶']},{textbox_count:1,textbox_enabled:true,bank_count:0}),null);
});
test('actual level-review entry starts only its observed exercise route',()=>{
 const capture=read('evidence/english-home-frontier-v1/source/lesson-challenge-entry.json');
 const buttons=capture.visible.filter(row=>row.tag==='BUTTON'&&row.text==='开始挑战 +20 经验');
 assert.equal(buttons.length,1);
 const facts={path:capture.path,dialog_count:0,challenge_count:0,heading_count:0,body_text:capture.snapshot,
  review_entry_count:buttons.length,review_entry_enabled:buttons[0].enabled};
 assert.deepEqual(currentFlowDecision(facts,labels),{kind:'review_entry',text:'开始挑战 +20 经验'});
 for(const override of [{path:'/learn'},{review_entry_count:2},{review_entry_enabled:false},
  {body_text:'来创建你的个人档案吧！'},{dialog_count:1}])
  assert.equal(currentFlowDecision({...facts,...override},labels).kind,'uncovered_state');
});

test('actual reverse translation uses the entire accepted sentence, not only blank tokens',()=>{
 const run=read('evidence/english-home-frontier-v1/source/lesson-after-reverse.json');
 let cases=0;
 for(let i=0;i<run.session.challenges.length;i++) {
  const c=run.session.challenges[i].content,row=run.observed[i];
  if(c.type!=='completeReverseTranslation')continue;
  assert.equal(row.rejected,false);assert.equal(row.identity.matches,true);
  const facts={textbox_count:1,textbox_enabled:true,textbox_value:'',bank_count:0};
  assert.equal(keyboardTranslationValue(c,facts),row.text_input.value);
  assert.notEqual(keyboardTranslationValue(c,facts),c.displayTokens.filter(t=>t.isBlank).map(t=>t.text).join(''));
  assert.throws(()=>keyboardTranslationValue(c,{...facts,textbox_value:'unfinished'}),/empty enabled/);
  assert.throws(()=>keyboardTranslationValue(c,{...facts,bank_count:1}),/no word bank/);
  cases++;
 }
 assert.equal(cases,4);
});

// Stage2 actual current-mode replay stopped at this previously unknown message.
test('actual placement encouragement is an interlude only on the observed exercise route',()=>{
 const run=read('evidence/english-sections-v1/placement-batch01.json');
 const facts=run.stopped.facts;
 assert.equal(run.answered,1);assert.equal(run.accepted,1);
 assert.deepEqual(currentFlowDecision(facts,labels),{kind:'interlude',text:'万事开头难？可你的表现很不错哦！'});
 assert.equal(currentFlowDecision({...facts,path:'/learn'},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,dialog_count:1},labels).kind,'uncovered_state');
});

test('structural placement encouragement accepts new messages but refuses settlement continue',()=>{
 for(const file of ['placement-batch04.json','placement-batch05.json']) {
  const d=read('evidence/english-sections-v1/'+file);
  const f=d.interludes[0].facts;
  assert.deepEqual(currentFlowDecision(f,labels),{kind:'interlude',text:f.encouragement_messages[0]});
  for(const override of [{duo_count:0},{progress_count:0},{quit_count:0},{continue_count:2}])
   assert.equal(currentFlowDecision({...f,...override},labels).kind,'uncovered_state');
 }
 const name=read('evidence/english-sections-v1/placement-batch08.json').session.challenges[0].content;
 assert.equal(keyboardTranslationValue(name,{textbox_count:1,textbox_enabled:true,bank_count:0}),'four');
 const final=read('evidence/english-sections-v1/placement-batch08.json').stopped;
 assert.equal(currentFlowDecision(final.facts,labels).kind,'uncovered_state');
});

test('actual unit-12 route and roleless quit overlay cannot be confused with ready exercise',()=>{
 const d=read('evidence/english-unit-placement-v1/source/unit12-batch02.json');
 const f=d.interludes[0].facts;
 assert.equal(f.path,'/lesson/unit/12/test');
 assert.equal(currentFlowDecision(f,labels).kind,'interlude');
 for(const path of ['/lesson/unit/0/test','/lesson/unit/12/other','/learn'])
  assert.equal(currentFlowDecision({...f,path},labels).kind,'uncovered_state');
 const ready={...f,challenge_count:1,challenge_visible:true,next_text:'检查',dialog_count:0};
 assert.equal(currentFlowDecision(ready,labels).kind,'challenge');
 assert.equal(currentFlowDecision({...ready,quit_confirmation_count:1},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision(read('evidence/english-unit-placement-v1/source/unit12-batch05.json').stopped.facts,labels).kind,'uncovered_state');
});
