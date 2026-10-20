import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {captureImageGeometry} from './capture-image-geometry.mjs';
const read=name=>JSON.parse(readFileSync(new URL('evidence/english-unit12-lesson3-v1/source/'+name+'.json',import.meta.url)));
const image=name=>readFileSync(new URL('evidence/english-unit12-lesson3-v1/source/'+name+'.png',import.meta.url));
test('real cropped surface is rejected despite matching DOM snapshots',()=>{
 const s=read('q5-before');assert.equal(s.capture_state_consistent,true);
 const r=captureImageGeometry(image('q5-before'),s.capture_geometry);
 assert.deepEqual(r.capture_pixels,[2384,1410]);assert.equal(r.capture_geometry_consistent,false);
 assert.deepEqual(s.capture_geometry.window_points,[1200,732]);assert.equal(s.capture_geometry.backing_scale,2);
});
test('real explicit CDP clip matches independently measured physical geometry',()=>{
 const s=read('fourth-lesson-popup-fixed');const r=captureImageGeometry(image('fourth-lesson-popup-fixed'),s.capture_geometry);
 assert.deepEqual(r.capture_pixels,[2400,1464]);assert.equal(r.capture_geometry_consistent,true);
 assert.equal(captureImageGeometry(image('fourth-lesson-popup-fixed'),{...s.capture_geometry,backing_scale:1}).capture_geometry_consistent,false);
});
test('invalid image or absent independent measurement cannot become a reference',()=>{
 assert.throws(()=>captureImageGeometry(Buffer.from('not a screenshot'),read('q5-before').capture_geometry));
 assert.throws(()=>captureImageGeometry(image('q5-before'),{}));
});

test('real screenshot viewport mutation is rejected even with identical ARIA',async()=>{
 const {captureViewportIdentity}=await import('./capture-image-geometry.mjs');
 const s=JSON.parse(readFileSync(new URL('evidence/english-unit12-lesson4-v1/source/q10-closed.json',import.meta.url)));
 assert.equal(s.snapshot,s.snapshot_after_capture);
 assert.deepEqual(s.viewport,{width:1200,height:732});assert.deepEqual(s.viewport_after_capture,{width:1192,height:705});
 assert.equal(captureViewportIdentity(s.viewport,s.viewport_after_capture),false);
 const stable=JSON.parse(readFileSync(new URL('evidence/english-unit12-lesson4-v1/source/q12-before.json',import.meta.url)));
 assert.equal(captureViewportIdentity(stable.viewport,stable.viewport_after_capture),true);
 assert.notDeepEqual(stable.configured_viewport,stable.viewport);
 assert.equal(captureViewportIdentity(null,stable.viewport),false);
});

test('real scrolled home requires document clip origin, despite valid PNG size',async()=>{
 const {visibleCaptureClip}=await import('./capture-image-geometry.mjs');
 const s=JSON.parse(readFileSync(new URL('evidence/english-unit12-lesson4-v1/source/home-after.json',import.meta.url)));
 assert.equal(s.capture_geometry_consistent,true);
 assert.deepEqual(visibleCaptureClip(s.capture_layout_metrics),{x:0,y:679.5,width:1192,height:705,scale:1});
 assert.throws(()=>visibleCaptureClip({}));
});
