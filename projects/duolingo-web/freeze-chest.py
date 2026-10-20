"""Compile actual first-path chest states; freeze frontend before candidate changes."""
import argparse,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
EV=BASE/'evidence/english-chest-v1'
def build():
    parent=json.loads((BASE/'frontend-english-v38.json').read_text())
    contract=json.loads(json.dumps(parent));contract.update(revision='english-v39',parent_revision='english-v38',changes=['Actual leaderboard interruption, chest opening, +15 observed gem change, persisted open state and next Practice entry.'])
    reference=json.loads((BASE/'evidence/english-eighth-integration-v1/reference.json').read_text())
    resources={}
    def resource(url):
        name='en-chest-'+hashlib.sha256(url.encode()).hexdigest()[:20]
        resources[name]=dict(url=url,kind='image',name=name,source_file=name+'.svg',render_width=80,render_height=90)
        return name
    sources={stem:json.loads((EV/'source'/f'{stem}.json').read_text()) for stem in ['before','after-escape','dismissed','after-click','reloaded','practice-entry']}
    for stem,source in sources.items():
        key='chest-'+stem; path=str((EV/'source'/f'{stem}.json').relative_to(ROOT));png=str((EV/'source'/f'{stem}.png').relative_to(ROOT))
        state=dict(snapshot=source['snapshot'],accessible_text=[],elements={},capture=dict(path=png,content_rect_points=[0,0,1200,732],backing_scale=1,window_points=[1200,732]));reference['states'][key]=state
        def add(label,kind,**fields):contract['requirements'].append(dict(id=key+'-'+label+'-'+kind,state=key,kind=kind,evidence=[path],**fields))
        def text(label,value):state['accessible_text'].append(value);add(label,'accessible_text',text=value)
        chest=[r for r in source['visible'] if r['tag']=='BUTTON' and any('/images/path/' in im['src'] and im['rect']['width']==80 for im in r['images'])][0]
        state['elements']['path-chest']=dict(rect=chest['rect'],role='button',enabled=chest['enabled'])
        add('control','element_geometry',element='path-chest',rect=chest['rect'],tolerance_points=0)
        add('control','element_role',element='path-chest',role='button')
        add('control','element_boolean',element='path-chest',field='enabled',expected=chest['enabled'])
        if stem in ['before','after-escape']:text('interruption','排行榜已解锁！')
        text('gems','525' if stem in ['after-click','reloaded','practice-entry'] else '510')
        if stem=='practice-entry':
            text('practice-unit','第 1/2 单元');text('practice-start','开始 +10 经验')
        add('whole','image_pixels',reference_image=png,pixels=[1200,732])
    before=sources['dismissed'];after=sources['reloaded']
    def chestrow(d):return next(r for r in d['visible'] if r['tag']=='BUTTON' and any('/images/path/' in im['src'] and im['rect']['width']==80 for im in r['images']))
    a=chestrow(before);b=chestrow(after)
    assert a['enabled'] and not b['enabled'] and 'button "510"' in before['snapshot'] and 'button "525"' in after['snapshot']
    fixture=json.loads((BASE/'fixture-reference-en-zh-v12.json').read_text());course=fixture['data']['candidate_course'];home=course['home']
    home['pathChest']=dict(id='unit-1-chest',afterLessonIDs=[l['id'] for l in course['lessons']],beforeGems=510,afterGems=525,
        readyResource=resource(a['images'][0]['src']),openedResource=resource(b['images'][0]['src']),
        readyCenters=[56.5,133.3515625,231.2265625,329.1015625,405.953125],openedCenters=[56.5,133.3515625,231.2265625,343.1015625,433.953125],readyHeight=498.1484375,openedHeight=526.1484375,readyImageOffset=5,openedImageOffset=-6)
    snap=json.loads(json.dumps(home['progressSnapshots'][-1]));snap.update(completedLessons=8,streak=2,gems=510,leagueCountdown='4 小时');home['progressSnapshots'].append(snap)
    fixture['provenance']=dict(source='v12 lessons unchanged; actual first-path chest and eight-completion snapshot',evidence=[str((EV/'README.md').relative_to(ROOT))],unknown='Other chest amounts, animations/audio timing, subsequent Practice challenges and leaderboard interruption recurrence')
    assert course['lessons']==json.loads((BASE/'fixture-reference-en-zh-v12.json').read_text())['data']['candidate_course']['lessons']
    assert contract['requirements'][:2321]==parent['requirements']
    return contract,reference,fixture,list(resources.values())
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=False)
    for name,value in zip(['contract.json','reference.json','fixture.json','resources.json'],build()):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
