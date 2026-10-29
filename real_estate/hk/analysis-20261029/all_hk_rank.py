# 全港屋苑 3 年表现：2025-11~2026-10 vs 2023-11~2024-10（2023-10 之前数据不全），二手、实用尺价
# 指标：median_chg = 中位尺价变化；adj_chg = 屋苑内回归 log(尺价) ~ 期间 + 座数 + 楼层 + log面积，扣除成交组合变化；按 adj_chg 排序
import json,glob,csv,os,sys,statistics as st
from collections import defaultdict,Counter
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
RAW=sys.argv[1] if len(sys.argv)>1 else '../../../__temp/hk_real_estate/raw'; D=os.environ.get('OUT','.'); os.makedirs(D,exist_ok=True)
L12='2025-11-01'; B_HI='2024-11-01'; B_LO='2023-11-01'; MINN=int(os.environ.get('MINN',20))
rows=[]; seen=set()
for f in sorted(glob.glob(f'{RAW}/band_*.json')):
    for x in json.load(open(f)):
        if x['id'] in seen: continue
        seen.add(x['id']); rows.append(x)
print(len(rows),'unique rows',file=sys.stderr)
def est(x): return x.get('bigEstateName') or x.get('estateName') or x.get('buildingName')
flat=[]
for x in rows:
    u=x.get('nUnitPrice'); d=(x.get('insDate') or '')[:10]
    if not u or not d or x.get('firstOrSecondHand')!='SecondHand' or (x.get('specialCase') or {}).get('value'): continue
    sc=x.get('scope') or {}
    flat.append(dict(id=x['id'],date=d,terr=sc.get('terr'),db=sc.get('db'),hma=x.get('districtName'),estate=est(x),
        building=x.get('buildingName'),floor=x.get('yAxis'),area=x.get('nArea'),price=x.get('transactionPrice'),u=u,
        bed=x.get('bedroomCount'),opYear=x.get('opYear'),cuntcode=x.get('cuntcode')))
with open(f'{D}/transactions_secondhand.csv','w',newline='',encoding='utf-8-sig') as fo:
    w=csv.DictWriter(fo,fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)
print(len(flat),'secondhand rows',file=sys.stderr)
g=defaultdict(list)
for r in flat: g[(r['terr'],r['db'],r['hma'],r['estate'])].append(r)
def per(d): return 'L' if d>=L12 else ('B' if B_LO<=d<B_HI else None)
FL={'低層':0,'中層':1,'高層':2}
def adj(xs):
    xs=[r for r in xs if per(r['date']) and r['area']]
    if len(xs)<2*MINN: return None
    blds=sorted({r['building'] for r in xs}); bi={b:i for i,b in enumerate(blds)}
    X=[];y=[]
    for r in xs:
        v=[1.0, 1.0 if per(r['date'])=='L' else 0.0, np.log(r['area']), *[1.0 if FL.get(r['floor'])==k else 0.0 for k in (1,2)]]
        v+=[1.0 if bi[r['building']]==i else 0.0 for i in range(1,len(blds))]
        X.append(v); y.append(np.log(r['u']))
    X=np.array(X); y=np.array(y)
    if np.linalg.matrix_rank(X)<X.shape[1]: X=X[:,:5]
    b=np.linalg.lstsq(X,y,rcond=None)[0]
    return (np.exp(b[1])-1)*100
out=[]
for k,xs in g.items():
    L=[r['u'] for r in xs if per(r['date'])=='L']; B=[r['u'] for r in xs if per(r['date'])=='B']
    if len(L)<MINN or len(B)<MINN: continue
    top_share=max(Counter(L).values())/len(L)  # 宏福苑火灾后政府按 $8,000/$10,500 收购之类的非市场成交
    if top_share>=0.3: print('skip non-market',k[3],len(L),f'{top_share:.0%}',file=sys.stderr); continue
    q=defaultdict(list)
    for r in xs: q[r['date'][:4]+'Q'+str((int(r['date'][5:7])-1)//3+1)].append(r['u'])
    out.append(dict(terr=k[0],district=k[1],hma=k[2],estate=k[3],n_total=len(xs),n_base=len(B),n_last=len(L),
        med_base=round(st.median(B)),med_last=round(st.median(L)),median_chg=round((st.median(L)/st.median(B)-1)*100,1),
        adj_chg=None if (a:=adj(xs)) is None else round(a,1),
        type='公屋/租置(邨)' if k[3].endswith('邨') else ('居屋(苑,粗略)' if k[3].endswith('苑') else '私樓'),med_area=round(st.median([r['area'] for r in xs if r['area']] or [0])),opYear=xs[0]['opYear'],
        quarterly=json.dumps({p:round(st.median(v)) for p,v in sorted(q.items())})))
out=[r for r in out if r['adj_chg'] is not None]; out.sort(key=lambda r:-r['adj_chg'])  # 按组合调整后的变化排序
cols=[c for c in out[0] if c!='quarterly']+['quarterly']
with open(f'{D}/estates_3y.csv','w',newline='',encoding='utf-8-sig') as fo:
    w=csv.DictWriter(fo,fieldnames=cols); w.writeheader(); w.writerows(out)
mkt_l=st.median([r['u'] for r in flat if per(r['date'])=='L']); mkt_b=st.median([r['u'] for r in flat if per(r['date'])=='B'])
print(f'estates ranked: {len(out)} (each period >= {MINN}); market median {mkt_b:.0f} -> {mkt_l:.0f} ({(mkt_l/mkt_b-1)*100:+.1f}%); estate median adj chg {st.median([r["adj_chg"] for r in out]):+.1f}%')
fmt=lambda r:f"{r['estate']}（{r['district']}/{r['hma']}） {r['n_base']}→{r['n_last']}宗 {r['med_base']}→{r['med_last']} 調整 {r['adj_chg']:+.1f}% 中位 {r['median_chg']:+.1f}% {r['type']} {r['opYear']}"
for name,sel in [('top30',out[:30]),('bottom30',out[-30:][::-1])]:
    with open(f'{D}/{name}.csv','w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=cols[:-1],extrasaction='ignore'); w.writeheader(); w.writerows(sel)
    print(f'\n## {name}'); [print(i+1,fmt(r)) for i,r in enumerate(sel)]
