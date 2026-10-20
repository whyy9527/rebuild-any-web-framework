"""Append source sections/current-placement requirements without rewriting v62.

All-card DOM geometry is an inventory, not proof of scrolling/execution. The
exploratory native build predates this compiler; this is not a preregistered
RSI effect experiment. Original screenshots remain the visual authority.
"""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
E = BASE/'evidence/english-sections-v1'


def build():
    contract = json.loads((BASE/'frontend-english-v62.json').read_text())
    prior = contract['requirements'][:]
    reference = dict(states={})

    def add(state, suffix, kind, evidence, **kw):
        contract['requirements'].append(dict(id=state+'-'+suffix, state=state,
            kind=kind, evidence=evidence, **kw))

    def image_state(state, image, texts, evidence):
        reference['states'][state] = dict(accessible_text=texts, elements={},
            capture=dict(path=image, content_rect_points=[0,0,1200,732],
                         window_points=[1200,732], backing_scale=1))
        add(state, 'whole', 'image_pixels', evidence, reference_image=image, pixels=[1200,732])
        for i,text in enumerate(dict.fromkeys(texts)):
            add(state, 'text-'+str(i), 'accessible_text', evidence, text=text)
        add(state, 'audio', 'pending', evidence,
            description='Original resource receipts do not prove actual aligned application acoustic output')

    layouts = json.loads((E/'layouts-before.json').read_text())
    ev = [str((E/'layouts-before.json').relative_to(ROOT))]
    state = 'profile-return-sections'
    reference['states'][state] = dict(elements={}, accessible_text=[])
    for i,card in enumerate(layouts['cards']):
        stage = i+1
        elements = [('sections-card-'+str(stage),card['rect'])]
        heading = next(n for n in card['nodes'] if n['tag']=='H1')
        elements.append(('sections-heading-'+str(stage),heading['rect']))
        reference['states'][state]['accessible_text'].append(heading['text'])
        add(state, 'inventory-heading-'+str(stage), 'accessible_text', ev, text=heading['text'])
        button = next((n for n in card['nodes'] if n['tag']=='BUTTON'),None)
        if button:
            key = 'sections-continue' if stage==1 else 'sections-jump-'+str(stage)
            elements.append((key,button['rect']))
            add(state, 'inventory-button-'+str(stage), 'accessible_text', ev, text=button['text'])
        for key,rect in elements:
            reference['states'][state]['elements'][key] = dict(rect=rect)
            add(state, 'inventory-'+key, 'element_geometry', ev,
                element=key, rect=rect, tolerance_points=0)
        for j,node in enumerate(card['nodes']):
            if node['tag']=='P' or 'O93KC' in (node['className'] or '').split():
                add(state, 'inventory-card-'+str(stage)+'-text-'+str(j),
                    'accessible_text', ev, text=node['text'])
    # Current challenge records contain accepted UI actions, actual prompt
    # identity and source PNGs. No future/ungraded challenge becomes a fixture.
    index = 0
    for path in sorted(E.glob('placement-batch*.json')):
        run = json.loads(path.read_text())
        content = {q['index']:q['content'] for q in run['session']['challenges']}
        for row in run['observed']:
            if 'feedback' not in row:
                continue
            assert row['identity']['matches'] and not row['rejected']
            key = 'placement-2-q'+str(index)
            for moment in ['before','feedback']:
                image = row['screenshot_'+moment]
                evidence = [str(path.relative_to(ROOT)),image]
                texts = [row['heading']]
                if moment=='before':
                    texts += row['identity']['actual'].get('prompts',[])
                    texts += row.get('word_bank',[]) or row['identity']['actual'].get('choices',[])
                    texts.append('检查')
                else:
                    import re
                    texts += re.findall(r'heading "([^"\n]+)" \[level=2\]',row['feedback'])
                    texts.append('继续')
                name = key+'-'+moment
                image_state(name,image,texts,evidence)
                if moment=='before' and row.get('text_input'):
                    r = row['text_input']['rect']
                    rect = [r[k] for k in ['x','y','width','height']]
                    reference['states'][name]['elements']['answer-input'] = dict(rect=rect)
                    add(name,'input-geometry','element_geometry',evidence,
                        element='answer-input',rect=rect,tolerance_points=0)
            index += 1
    assert index==15
    for i,(file,local_index,text) in enumerate([
        ('placement-batch02.json',0,'万事开头难？可你的表现很不错哦！'),
        ('placement-batch04.json',0,'很不错哦！'),
        ('placement-batch05.json',3,'佩服！')]):
        run = json.loads((E/file).read_text())
        entry = next(r for r in run['interludes'] if r['index']==local_index)
        image = entry['screenshot']
        image_state('placement-encouragement-'+str(i), image,[text,'继续'],
                    [str((E/file).relative_to(ROOT)),image])
    old = BASE/'evidence/english-profile-return-v1/source/section-test-intro.json'
    src = json.loads(old.read_text());image = str(old.with_suffix('.png').relative_to(ROOT))
    image_state('placement-intro',image,[t['text'] for t in src['text_runs']],
                [str(old.relative_to(ROOT)),image])
    for state,stem,texts in [
        ('placement-result','sections-placement-result',['完美！','你练习全对，无错完成本单元','总经验','50','超级棒','100%','回顾本单元','继续']),
        ('placement-score','sections-placement-score',['10','你成功提升了你的英语分数！','继续']),
        ('placement-quests','sections-placement-quests',None),
        ('placement-gems','sections-placement-gems',None),
        ('placement-profile','sections-placement-profile',None),
        ('placement-return','sections-after-unlock',None)]:
        path = E/'source'/(stem+'.json');src = json.loads(path.read_text())
        image = str(path.with_suffix('.png').relative_to(ROOT))
        # Counter digit reels are clipped: use the actual settled screenshot's
        # 50/100 instead of certifying every CSS-visible offscreen digit 0..9.
        if texts is None:
            texts = [t['text'] for t in src['text_runs']]
        image_state(state,image,texts,[str(path.relative_to(ROOT)),image])
    # These actual source states are still unvisited by the native driver.
    # Keep them explicit instead of limiting acceptance to the implemented page.
    for state,stem in [('sections-unlocked-middle','sections-lower-middle'),
                       ('sections-unlocked-end','sections-lower-end'),
                       ('sections-stage2-home','sections-stage2-home')]:
        path=E/'source'/(stem+'.json');src=json.loads(path.read_text())
        image=str(path.with_suffix('.png').relative_to(ROOT))
        evidence=[str(path.relative_to(ROOT)),image]
        image_state(state,image,[t['text'] for t in src['text_runs']],evidence)
        for i,action in enumerate(src['actions']):
            key='source-action-'+str(i)
            reference['states'][state]['elements'][key]={k:action[k] for k in ['rect','role','enabled']}
            add(state,key+'-geometry','element_geometry',evidence,element=key,
                rect=action['rect'],tolerance_points=0)
            if action['role'] is not None:
                add(state,key+'-role','element_role',evidence,element=key,role=action['role'])
            add(state,key+'-enabled','element_boolean',evidence,element=key,
                field='enabled',expected=action['enabled'])
    contract.update(revision='english-v63',parent_revision='english-v62',changes=[
        'All nine source stage cards and DOM geometry retained beyond first viewport',
        'Actual accepted 15-question placement, three encouragements and five-page result chain',
        'Unlocked stage return is a new source state, not silently substituted for the old prepared fixture'])
    assert contract['requirements'][:len(prior)] == prior
    assert len({r['id'] for r in contract['requirements']}) == len(contract['requirements'])
    return contract,reference


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True)
    out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,data in zip(['contract.json','reference.json'],build()):
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
