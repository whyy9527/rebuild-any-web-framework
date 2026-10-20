import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {publicChallenge} from './public-reference-challenge.mjs';
import {renderedChallenge} from './rendered-reference-challenge.mjs';

test('current renderer reads a replacement without consulting stale session or private state',()=>{
 const props={challenge:{type:'translate',prompt:'Good morning!'}};
 Object.defineProperty(props,'challengeState',{get(){throw Error('Private state accessed');}});
 const node={__reactFiberObserved:{memoizedProps:{},return:{memoizedProps:props}},
  innerText:'Good morning! 早上好',getAttribute:()=> 'challenge challenge-translate'};
 const row=renderedChallenge(node,publicChallenge.toString());
 assert.equal(row.content.prompt,'Good morning!');
 assert.equal(row.dom_type,'challenge challenge-translate');
});
test('transition mismatch and missing current challenge never fall back to an initial list',()=>{
 const node={__reactFiberObserved:{memoizedProps:{challenge:{type:'speak',prompt:'water'}}},
  innerText:'water',getAttribute:()=> 'challenge challenge-translate'};
 assert.throws(()=>renderedChallenge(node,publicChallenge.toString()),/type mismatch/);
 node.__reactFiberObserved.memoizedProps={};
 assert.throws(()=>renderedChallenge(node,publicChallenge.toString()),/no fallback/);
});

test('shared public projection retains all actually frozen source content',()=>{
 for(const directory of ['english-general-practice-v1','english-general-listening-decline-v1']){
  const session=JSON.parse(readFileSync(new URL('evidence/'+directory+'/session.json',import.meta.url))).session;
  for(const row of session.challenges)assert.deepEqual(publicChallenge(row.content).content,row.content);
 }
});
test('tracking and state values never enter the public content projection',()=>{
 const raw={type:'translate',prompt:'water',id:'private-id',challengeState:{text:'private-response'},
  metadata:{tokens:['private-tracking']},character:{name:'OSCAR',image:{svg:'https://example.test/public.svg'},idleAnimation:{url:'https://example.test/public.riv',userId:'private-user'}}};
 const result=publicChallenge(raw);
 assert.deepEqual(result.content,{type:'translate',prompt:'water',character:{name:'OSCAR',image:{svg:'https://example.test/public.svg'},idleAnimation:{url:'https://example.test/public.riv'}}});
 assert.doesNotMatch(JSON.stringify(result),/private-/);
 assert.ok(result.omitted_keys.includes('challenge.0.challengeState'));
});
test('current challenge observation preserves an existing frame before accessing browser',()=>{
 const dir=mkdtempSync(join(tmpdir(),'current-challenge-'));
 try {
  const output=join(dir,'current');writeFileSync(output+'.png','original');
  const r=spawnSync(process.execPath,[new URL('capture-current-challenge.mjs',import.meta.url).pathname,'--out',output,'--cli',join(dir,'must-not-run'),'--session','owned'],{encoding:'utf8'});
  assert.equal(r.status,1);assert.match(r.stderr,/choose a fresh stem/);
  assert.equal(readFileSync(output+'.png','utf8'),'original');assert.equal(existsSync(output+'.raw.txt'),false);
 }finally{rmSync(dir,{recursive:true,force:true});}
});
