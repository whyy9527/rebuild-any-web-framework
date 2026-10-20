// Current visible DOM renderer only; no initial session or challengeState fallback.
export const renderedChallenge = (n,sanitizer)=>{
  const publicOnly=(0,eval)('('+sanitizer+')');
  let fiber=n[Object.keys(n).find(k=>k.startsWith('__reactFiber'))];
  for(let depth=0;fiber&&depth<16;depth++,fiber=fiber.return){
   const raw=fiber.memoizedProps?.challenge;
   if(!raw||typeof raw.type!=='string')continue;
   const dom_type=n.getAttribute('data-test');
   if(!dom_type.split(/\s+/).includes('challenge-'+raw.type))throw Error('Rendered/current challenge type mismatch; inspect transition before observing again');
   return {dom_type,visible_text:n.innerText,...publicOnly(raw)};
  }
  throw Error('Current public challenge not found on visible renderer; no fallback to initial session');
 };
