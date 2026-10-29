# 发展商楼盘分布：按屋苑汇总 dev_<code>/ 的成交，输出 dev_<code>_estates.csv，并印出各区统计
# 用法：python3 -I dev_agg.py de183 [输出路径，相对本目录]
import json,glob,csv,sys,os,statistics as st
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
code=sys.argv[1]; OUTF=sys.argv[2] if len(sys.argv)>2 else f'dev_{code}_estates.csv'; L12='2025-11-01'
rows={x['id']:x for f in glob.glob(f'../../../__temp/hk_real_estate/dev_{code}/band_*.json') for x in json.load(open(f))}.values()
chg={r['estate']:r for r in csv.DictReader(open('estates_3y.csv',encoding='utf-8-sig'))}
g=defaultdict(list)
for x in rows:
    sc=x.get('scope') or {}
    g[(sc.get('terr'),sc.get('db'),x.get('districtName'),x.get('bigEstateName') or x.get('estateName') or x.get('buildingName'))].append(x)
out=[]
for (terr,db,hma,est),xs in g.items():
    sh=[x for x in xs if x.get('firstOrSecondHand')=='SecondHand' and not (x.get('specialCase') or {}).get('value')]
    l12=[x['nUnitPrice'] for x in sh if x['insDate'][:10]>=L12]
    c=chg.get(est) if chg.get(est,{}).get('hma')==hma else None
    out.append(dict(terr=terr,district=db,hma=hma,estate=est,n_3y=len(xs),n_firsthand=sum(x.get('firstOrSecondHand')=='FirstHand' for x in xs),
        n_l12_2nd=len(l12),med_unit_l12=round(st.median(l12)) if l12 else None,
        med_price_m=round(st.median(x['transactionPrice'] for x in xs)/1e6,2),opYear=next((x.get('opYear') for x in xs if x.get('opYear')),None),
        adj_chg_3y=c['adj_chg'] if c else None))
out.sort(key=lambda r:(r['terr'] or '',r['district'] or '',-r['n_3y']))
with open(OUTF,'w',newline='',encoding='utf-8-sig') as fo:
    w=csv.DictWriter(fo,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
d=defaultdict(lambda:[0,0])
for r in out: d[(r['terr'],r['district'])][0]+=1; d[(r['terr'],r['district'])][1]+=r['n_3y']
print(len(rows),'trans',len(out),'estates')
for k,v in sorted(d.items(),key=lambda kv:-kv[1][0]): print(*k,*v)
