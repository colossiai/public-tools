import json,statistics as st,csv
from collections import defaultdict
BASE=10791; LO,HI=BASE*0.95,BASE*1.05; MINN=5
areas=json.load(open('areas.json'))
tko={'坑口','寶琳','將軍澳','康城','調景嶺'}
order=['荃灣','沙田','大圍','觀塘','九龍']
def area_of(dist):
    for a in order:
        names=set(areas[a])-(tko if a=='九龍' else set())
        if dist in names: return '九龍(其他)' if a=='九龍' else a
rows=json.load(open('band.json'))
seen=set(); g=defaultdict(list)
for x in rows:
    if x['id'] in seen or not x.get('nUnitPrice'): continue
    seen.add(x['id'])
    a=area_of(x.get('districtName'))
    if not a: continue
    est=x.get('bigEstateName') or x.get('estateName') or x.get('buildingName')
    g[(a,x['districtName'],est)].append(x)
res=[]
for (a,dist,est),xs in g.items():
    p=[x['nUnitPrice'] for x in xs]
    if len(p)<MINN: continue
    med=st.median(p)
    if LO<=med<=HI:
        res.append(dict(area=a,district=dist,estate=est,n=len(p),median=round(med),diff=f"{(med/BASE-1)*100:+.1f}%",
            med_price_m=round(st.median(x['transactionPrice'] for x in xs)/1e6,2),med_area=round(st.median(x['nArea'] for x in xs if x.get('nArea'))),
            last=max(x['insDate'] for x in xs)[:10]))
res.sort(key=lambda r:(order.index(r['area'].replace('(其他)','')),-r['n']))
with open('result.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
cur=None
for r in res:
    if r['area']!=cur: cur=r['area']; print(f"\n## {cur}")
    print(f"{r['estate']}（{r['district']}） n={r['n']} 中位呎價={r['median']} {r['diff']} 中位價={r['med_price_m']}M 中位面積={r['med_area']}呎")
print(len(res),'estates; band',round(LO),round(HI))
