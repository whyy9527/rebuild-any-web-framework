import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {challengeIdentity,uncoveredReplayType} from './reference-challenge-identity.mjs';
const read=name=>JSON.parse(readFileSync(new URL('evidence/english-general-practice-v1/'+name,import.meta.url)));
const source=read('session.json').session.challenges;
const row=(file,index)=>read(file).observed.find(r=>r.index===index);

test('actual audio pairs accept shuffling, but missing or duplicated visible targets fail',()=>{
 const c=source[0].content,a=row('replay.json',0).identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 assert.equal(challengeIdentity(c,{...a,choices:[...a.choices].reverse()}).matches,true);
 assert.equal(challengeIdentity(c,{...a,choices:a.choices.slice(1)}).matches,false);
 assert.equal(challengeIdentity(c,{...a,choices:a.choices.map(()=>a.choices[0])}).matches,false);
});
test('same isolation choices cannot hide a different sentence',()=>{
 const c=source[5].content,a=row('replay-from-5.json',5).identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 assert.equal(challengeIdentity({...c,tokens:[{value:'Different sentence.'}]},a).matches,false);
});
test('actual listening playback and completion context both identify the question',()=>{
 for(const i of [11,12]){
  const c=source[i].content,a=row('replay-from-11.json',i).identity.actual;
  assert.equal(challengeIdentity(c,a).matches,true);
  assert.equal(challengeIdentity(c,{...a,playedAudio:[]}).matches,false);
 }
 const c=source[12].content,a=row('replay-from-11.json',12).identity.actual;
 assert.ok(challengeIdentity(c,{...a,text:'another completion'}).reasons.includes('completion_context_changed'));
 // The actual keyboard preference remains a schema mismatch, not a silently
 // accepted empty word bank. The caller observes/toggles modes separately.
 const keyboard=row('replay-from-5.json',6).identity.actual;
 assert.equal(challengeIdentity(source[6].content,keyboard).matches,false);
 assert.equal(uncoveredReplayType('unobservedType','challenge challenge-unobservedType'),true);
});
test('a pre-existing screenshot stops both answer tools before invoking a browser',()=>{
 const dir=mkdtempSync(join(tmpdir(),'practice-collision-'));
 try{
  const prefix=join(dir,'answer'),out=join(dir,'receipt.json'),image=prefix+'-before.png';
  writeFileSync(image,'original frame');
  for(const [script,args] of [['answer-text-reference-live.mjs',['--label','input','--text','value']],['answer-reference-live.mjs',['--words','["value"]']]]){
   const result=spawnSync(process.execPath,[new URL(script,import.meta.url).pathname,'--cli',join(dir,'must-not-run'),'--session','owned','--out',out,'--screenshot-prefix',prefix,...args],{encoding:'utf8'});
   assert.equal(result.status,1);assert.match(result.stderr,/choose fresh/);
   assert.equal(readFileSync(image,'utf8'),'original frame');
   assert.equal(existsSync(out+'.intent.json'),false);assert.equal(existsSync(out+'.raw.txt'),false);
  }
 }finally{rmSync(dir,{recursive:true,force:true});}
});

test('actual placement name and picture completion are supported only with current identity',()=>{
 const readPlacement=name=>JSON.parse(readFileSync(new URL('evidence/english-sections-v1/'+name,import.meta.url)));
 for(const [file,index] of [['placement-batch05.json',0],['placement-batch08.json',0]]){
  const d=readPlacement(file),c=d.session.challenges.find(q=>q.index===index).content;
  const r=d.observed.find(q=>q.index===index);assert.equal(r.rejected,false);
  assert.equal(uncoveredReplayType(c.type,r.dom_type),false);
  assert.equal(challengeIdentity(c,r.identity.actual).matches,true);
  assert.equal(challengeIdentity(c,{...r.identity.actual,text:'different prompt',prompts:[]}).matches,false);
 }
});

// Real second grocery instance: the correct complete sentence is intentionally
// absent from the unfilled DOM; two adjacent missing words share one gap.
test('observed multiword gap identifies scaffold and example without accepting drift',()=>{
 const d=JSON.parse(readFileSync(new URL('evidence/english-shopping-guide-v1/source/grocery-next-current-02.json',import.meta.url)));
 const c=d.session.challenges[0].content,a=d.observed[0].identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 for(const changed of [
  {...a,completionScaffold:{...a.completionScaffold,text:'No, a .'}},
  {...a,completionScaffold:{...a.completionScaffold,blankCount:3}},
  {...a,prompts:['Hi, I need a jacket.']},
  {...a,choices:['need','hat','hat']},
 ])assert.equal(challengeIdentity(c,changed).matches,false);
 assert.equal(challengeIdentity(c,{...a,completionScaffold:null}).matches,false);
});

test('actual fragmented tap sentence keeps lexical and word-bank identity',()=>{
 const d=JSON.parse(readFileSync(new URL('evidence/english-shopping-guide-v1/source/grocery-next-current-05.json',import.meta.url)));
 const c=d.session.challenges.at(-1).content,a=d.observed.at(-1).identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 assert.equal(challengeIdentity(c,{...a,text:a.text.replace('sale','rent')}).matches,false);
 assert.equal(challengeIdentity(c,{...a,choices:['scarf','brother','sugar','sugar']}).matches,false);
});

test('actual unit gapFill requires observed completion context and complete choices',()=>{
 const d=JSON.parse(readFileSync(new URL('evidence/english-unit-placement-v1/source/unit12-batch04.json',import.meta.url)));
 let count=0;
 for(const row of d.observed){
  const c=d.session.challenges.find(q=>q.index===row.index).content;
  if(c.type!=='gapFill')continue;
  const a=row.identity.actual;
  assert.equal(challengeIdentity(c,a).matches,true);
  assert.equal(uncoveredReplayType(c.type,a.type),false);
  assert.equal(challengeIdentity(c,{...a,text:'Different sentence'}).matches,false);
  assert.equal(challengeIdentity(c,{...a,choices:a.choices.slice(1)}).matches,false);
  assert.equal(challengeIdentity(c,{...a,choices:a.choices.map(()=>a.choices[0])}).matches,false);
  assert.equal(challengeIdentity(c,{...a,type:'challenge-assist'}).matches,false);
  count++;
 }
 assert.equal(count,2);
});
