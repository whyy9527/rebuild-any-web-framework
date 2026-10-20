// Validate the encoded surface against independent geometry; never infer scale.
export function captureImageGeometry(png, geometry) {
 if(png.length<24 || png.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('Actual capture is not a PNG header');
 if(!geometry || !Array.isArray(geometry.window_points) || geometry.window_points.length!==2 || !geometry.window_points.every(v=>Number.isFinite(v)&&v>0) || !Number.isFinite(geometry.backing_scale)||geometry.backing_scale<=0)throw Error('Independent capture geometry required');
 const pixels=[png.readUInt32BE(16),png.readUInt32BE(20)];
 const expected=geometry.window_points.map(v=>Math.round(v*geometry.backing_scale));
 return {capture_pixels:pixels,capture_geometry_consistent:JSON.stringify(expected)===JSON.stringify(pixels)};
}

// Identical ARIA text does not establish an identical frontend viewport.
export function captureViewportIdentity(before, after) {
 const valid=v=>v && Number.isFinite(v.width) && v.width>0 && Number.isFinite(v.height) && v.height>0;
 return !!(valid(before) && valid(after) && before.width===after.width && before.height===after.height);
}

export function visibleCaptureClip(metrics) {
 const css=metrics?.cssVisualViewport;
 if(!css || !['pageX','pageY','clientWidth','clientHeight'].every(k=>Number.isFinite(css[k])) || css.clientWidth<=0 || css.clientHeight<=0)throw Error('Independent visible viewport coordinates required');
 return {x:css.pageX,y:css.pageY,width:css.clientWidth,height:css.clientHeight,scale:1};
}
