import json,glob,statistics as st,csv,sys
from collections import defaultdict
cands=json.load(open('cands.json'))
areas=json.load(open('areas.json')); tko={'坑口','寶琳','將軍澳','康城','調景嶺'}
def area_of(d):
    if d in tko: return '將軍澳'
    for a in ['荃灣','沙田','大圍','觀塘']:
        if d in areas[a]: return '沙田/大圍' if a in ('沙田','大圍') else a
    return '九龍其他'
def period(d):
    if d>='2025-10-28': return 'L12'
    if d>='2024-10-28': return 'P12'
    if d>='2023-10-28': return 'P24'
def half(d):
    if d>='2026-04-28': return 'L6'
    if d>='2025-10-28': return 'P6'
def bed(x):
    b=x.get('bedroomCount')
    if b is None: return None
    return '開放/1房' if b<=1 else ('2房' if b==2 else '3房+')
rows=[]; seen=set()
for d,e in cands:
    f=f"hist/{e.replace('/','_').replace(' ','_')}.json"
    try: data=json.load(open(f))
    except FileNotFoundError: print('missing',e,file=sys.stderr); continue
    for x in data:
        if x['id'] in seen or not x.get('nUnitPrice') or x.get('districtName')!=d or x.get('firstOrSecondHand')=='FirstHand': continue
        big=x.get('bigEstateName') or x.get('estateName') or x.get('buildingName')
        if big!=e: continue
        seen.add(x['id'])
        name=e+(' '+x['estateName'] if e=='日出康城' and x.get('estateName') else '')
        rows.append(dict(area=area_of(d),district=d,estate=name,p=period(x['insDate'][:10]),h=half(x['insDate'][:10]),bed=bed(x),u=x['nUnitPrice'],yr=x.get('opYear')))
print(len(rows),'rows',file=sys.stderr)
def med(xs): return st.median(xs) if xs else None
def chg(g,k,a,b,minn):
    A=[r['u'] for r in g if r[k]==a]; B=[r['u'] for r in g if r[k]==b]
    if len(A)<minn or len(B)<minn: return None,len(A),len(B)
    return (med(A)/med(B)-1)*100,len(A),len(B)
def table(keyf,minn,label):
    g=defaultdict(list)
    for r in rows: g[keyf(r)].append(r)
    out=[]
    for k,v in g.items():
        if None in k: continue
        yoy,nl,np_=chg(v,'p','L12','P12',minn)
        if yoy is None: continue
        y2,_,n24=chg(v,'p','L12','P24',minn)
        h,nl6,np6=chg(v,'h','L6','P6',max(3,minn//2))
        out.append(dict(key=k,n_L12=nl,n_P12=np_,yoy=yoy,vs2y=y2,mom6=h,med=round(med([r['u'] for r in v if r['p']=='L12'])),yr=v[0]['yr']))
    out.sort(key=lambda r:-r['yoy'])
    json.dump(out,open(f'trend_{label}.json','w'),ensure_ascii=False,default=str)
    return out
f=lambda v:'  -  ' if v is None else f'{v:+.1f}%'
for lab,kf,mn in [('area',lambda r:(r['area'],),20),('estate',lambda r:(r['area'],r['estate']),8),('estate_bed',lambda r:(r['area'],r['estate'],r['bed']),6),('area_bed',lambda r:(r['area'],r['bed']),15)]:
    o=table(kf,mn,lab); print(f'\n## {lab} ({len(o)})')
    for r in (o if lab in('area','area_bed') else o[:20]+[{'key':('...',)}]+o[-5:]):
        if 'yoy' not in r: print('...'); continue
        print(' / '.join(r['key']),f"| L12 {r['n_L12']} P12 {r['n_P12']} | 按年 {f(r['yoy'])} | 對兩年前 {f(r['vs2y'])} | 近6月環比 {f(r['mom6'])} | 現尺價 {r['med']} | {r['yr']}")
print('\n## area = median of estate YoY (secondhand)')
est=json.load(open('trend_estate.json')); eb=json.load(open('trend_estate_bed.json'))
for a in ['將軍澳','九龍其他','沙田/大圍','荃灣','觀塘']:
    v=[r['yoy'] for r in est if r['key'][0]==a]
    if v: print(a,len(v),'estates, median YoY',f"{st.median(v):+.1f}%", 'range',f"{min(v):+.1f}..{max(v):+.1f}")
print('\n## bed type = median of estate-bed YoY')
for b in ['開放/1房','2房','3房+']:
    for a in ['將軍澳','九龍其他','沙田/大圍','荃灣','觀塘']:
        v=[r['yoy'] for r in eb if r['key'][0]==a and r['key'][2]==b]
        if len(v)>=2: print(b,a,len(v),f"{st.median(v):+.1f}%")
