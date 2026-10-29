import json,statistics as st,csv
from collections import defaultdict,Counter
rows=json.load(open('sino/all.json')); seen=set(); g=defaultdict(list)
for x in rows:
    if x['id'] in seen: continue
    seen.add(x['id'])
    sc=x.get('scope') or {}
    name=x.get('bigEstateName') or x.get('estateName') or x.get('buildingName') or '?'
    g[(sc.get('terr') or '?', sc.get('webScope') or x.get('districtName') or '?', name)].append(x)
def per(d):
    if d>='2025-10-28': return 'L12'
    if d>='2024-10-28': return 'P12'
    return 'P24'
out=[]
for (terr,ws,e),xs in g.items():
    sh=[x for x in xs if x.get('firstOrSecondHand')!='FirstHand']; fh=len(xs)-len(sh)
    by=defaultdict(list)
    for x in sh: by[per(x['insDate'][:10])].append(x['nUnitPrice'])
    m={k:st.median(v) for k,v in by.items() if len(v)>=5}
    yoy=(m['L12']/m['P12']-1)*100 if 'L12' in m and 'P12' in m else None
    v2=(m['L12']/m['P24']-1)*100 if 'L12' in m and 'P24' in m else None
    beds=Counter(x.get('bedroomCount') for x in sh if x.get('bedroomCount') is not None)
    out.append(dict(region=terr,district=ws,estate=e,opYear=xs[0].get('opYear'),n_3y=len(xs),n_first=fh,n_L12=len(by['L12']),
        unit_L12=round(m['L12']) if 'L12' in m else None,price_L12_m=round(st.median([x['transactionPrice'] for x in sh if per(x['insDate'][:10])=='L12'])/1e6,2) if by['L12'] else None,
        yoy=None if yoy is None else round(yoy,1),vs2y=None if v2 is None else round(v2,1),main_bed=beds.most_common(1)[0][0] if beds else None))
out.sort(key=lambda r:-r['n_3y'])
with open('sino/sino_estates.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(seen),'tx',len(out),'estates')
print('\n## by region/district (secondhand L12 tx, estate-median YoY)')
rg=defaultdict(list)
for r in out: rg[(r['region'],r['district'])].append(r)
for k,v in sorted(rg.items(),key=lambda kv:-sum(r['n_3y'] for r in kv[1]))[:25]:
    y=[r['yoy'] for r in v if r['yoy'] is not None]
    print(k[0],k[1],'estates',len(v),'tx3y',sum(r['n_3y'] for r in v),'YoY med',f"{st.median(y):+.1f}%" if y else '-')
print('\n## top estates by volume')
for r in out[:40]: print(r)
