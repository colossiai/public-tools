# 发展商屋苑 3 年表现：合并 <dir>/<prefix>_estates.csv 与全港 3 年表（MINN=10），输出 <prefix>_estates_3y.csv 和三份 top 20
# 用法：python3 -I dev_rank.py shk shk
# 前置：python3 -I dev_fetch.py de183 && python3 -I dev_agg.py de183 shk/shk_estates.csv
#       MINN=10 OUT=../../../__temp/hk_real_estate/min10 uv run --with numpy python -I all_hk_rank.py
import csv,os,re,sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),sys.argv[1])); P=sys.argv[2]
MIN10='../../../../__temp/hk_real_estate/min10/estates_3y.csv'
S={(r['estate'],r['hma']):r for r in csv.DictReader(open(f'{P}_estates.csv',encoding='utf-8-sig'))}
hk={(r['estate'],r['hma']):i+1 for i,r in enumerate(csv.DictReader(open('../estates_3y.csv',encoding='utf-8-sig')))}  # MINN=20 全港排名
rows=[]
for r in csv.DictReader(open(MIN10,encoding='utf-8-sig')):
    k=(r['estate'],r['hma'])
    if k not in S: continue
    r.pop('quarterly',None); r.pop('type',None)
    r['built']=int(re.sub(r'\D','',r['opYear']) or 0) or None
    r['low_sample']=min(int(r['n_base']),int(r['n_last']))<20
    r['hk_rank']=hk.get(k)
    r['n_firsthand_3y']=S[k]['n_firsthand']
    rows.append(r)
rows.sort(key=lambda r:-float(r['adj_chg']))
cols=['terr','district','hma','estate','built','n_base','n_last','low_sample','med_base','med_last','median_chg','adj_chg','hk_rank','med_area','n_total','n_firsthand_3y']
def write(f,rs):
    with open(f,'w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=['rank']+cols,extrasaction='ignore'); w.writeheader()
        for i,r in enumerate(rs): w.writerow(dict(r,rank=i+1))
write(f'{P}_estates_3y.csv',rows)
ok=[r for r in rows if not r['low_sample']]
band=lambda r:10000<=int(r['med_last'])<=20000
write(f'{P}_top20.csv',ok[:20])
write(f'{P}_top20_10k_20k.csv',[r for r in ok if band(r)][:20])
write(f'{P}_top20_10k_20k_2005plus.csv',[r for r in rows if band(r) and (r['built'] or 0)>=2005][:20])
print(len(rows),P,'estates (>=10/period),',len(ok),'with >=20/period')
