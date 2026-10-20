// Compare API expectations with independently read current UI before any answer.
// Option order can be shuffled; multiplicity must remain the same.
export function challengeIdentity(expected, actual) {
  const normalize = value => String(value ?? '').normalize('NFKC').replace(/\s+/g, ' ').trim();
  const multiset = values => values.map(normalize).sort();
  const choices = expected.type === 'match'
    ? expected.pairs.flatMap(p => [p.fromToken, p.learningToken])
    : expected.type === 'listenMatch' ? expected.pairs.map(p => p.translation)
    : expected.type === 'listenIsolation' ? expected.options.map(p => p.text)
    : (expected.choices ?? []).map(c => typeof c === 'string' ? c : c.phrase ?? c.text);
  const reasons = [];
  const prompt = expected.prompt ?? (expected.type === 'listenIsolation' ? expected.tokens.map(t => t.value).join('') : null);
  if (!actual.type.split(/\s+/).includes('challenge-' + expected.type)) reasons.push('type_changed');
  const expectedBank = multiset(choices), actualBank = multiset(actual.choices);
  if (JSON.stringify(expectedBank) !== JSON.stringify(actualBank)) reasons.push('choice_set_changed');
  // The visible container is broader than a dedicated prompt node. This is
  // evidence of presence, not exact prompt equality; retain that limitation.
  const exactPrompts = actual.prompts ?? [];
  const audioPrompt = ['listenTap','listen','listenComplete'].includes(expected.type);
  if (audioPrompt) {
    if (!expected.tts || !(actual.playedAudio ?? []).includes(expected.tts)) reasons.push('audio_identity_unverified');
    if (expected.type === 'listenComplete') {
      const visibleSentence = expected.displayTokens.filter(t => !t.isBlank).map(t => t.text).join('');
      if (!normalize(actual.text).includes(normalize(visibleSentence))) reasons.push('completion_context_changed');
    }
  } else if (expected.type==='orderTapComplete') {
    const scaffold=actual.completionScaffold;
    const compact=value=>normalize(value).replace(/\s/g,'');
    const context=(expected.displayTokens??[]).filter(t=>!t.isBlank).map(t=>t.text).join('');
    let runs=0,inBlank=false;
    for(const token of expected.displayTokens??[]){if(token.isBlank){if(!inBlank)runs++;inBlank=true;}else if(token.text.trim()){inBlank=false;}}
    if(!scaffold||!context.trim()||compact(scaffold.text)!==compact(context)||scaffold.blankCount!==runs)reasons.push('completion_structure_changed');
    if(!expected.example||!exactPrompts.some(p=>normalize(p)===normalize(expected.example)))reasons.push('completion_example_changed');
  } else if (prompt && exactPrompts.length && !exactPrompts.some(p => normalize(p) === normalize(prompt))) reasons.push('prompt_changed');
  else if (prompt && !exactPrompts.length && !normalize(actual.text).includes(normalize(prompt))) reasons.push('prompt_not_visible');
  if (['tapComplete','gapFill'].includes(expected.type)) {
    const context=(expected.displayTokens??[]).filter(t=>!t.isBlank).map(t=>t.text).join('');
    if (!context.trim() || !normalize(actual.text).replace(/\s/g,'').includes(normalize(context).replace(/\s/g,''))) reasons.push('completion_context_changed');
  }
  return {matches: reasons.length === 0, reasons, expected: {type: expected.type, prompt, choices},
    actual, prompt_check: ['tapComplete','gapFill'].includes(expected.type) ? 'Normalized completion-context presence and complete choice multiplicity; exact blank placement not yet proven' : expected.type==='orderTapComplete' ? 'Exact visible scaffold (whitespace ignored), blank runs, example and complete word-bank multiplicity; full answer is not yet visible' : audioPrompt ? 'exact source URL from current-question explicit playback; acoustic output not verified' : exactPrompts.length ? 'normalized equality with independently read visible hint container' : 'normalized presence in current challenge text; exact prompt identity not yet proven'};
}

// Unsupported same-type UI is a coverage gap, not evidence of content drift.
export function uncoveredReplayType(expectedType, actualType) {
  const supported = ['select','assist','dialogue','gapFill','translate','listenTap','orderTapComplete','match','listenMatch','listenIsolation','listenComplete','listen','completeReverseTranslation','tapComplete','name'];
  return !supported.includes(expectedType) && actualType.split(/\s+/).includes('challenge-' + expectedType);
}
