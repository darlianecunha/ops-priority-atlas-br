import json, sys
import pandas as pd, numpy as np
e = pd.read_pickle('calls2.pkl'); base = pd.read_pickle('base2.pkl'); log = json.load(open('log_auditoria.json'))
U = sys.argv[1] if len(sys.argv) > 1 else '/Users/darlianecunha/projetos/01_portos-emissoes/'
a = pd.read_csv(U+'artigo.site.co2completo100726/antaq_ea/atracacoes_antaq_2019_2025.csv.gz', usecols=['IDAtracacao','IMO','DWT_final'])
base = base.merge(a, on='IDAtracacao', how='left')
base = base[~(base.IMO.isna() & base.DWT_final.isna())]          # barcaças e embarcações sem identificação ficam fora do denominador
den = base.groupby('IDBerco').size().rename('den')
segmap = {'CONTÊINER':'Contêiner','GRANEL LÍQUIDO':'Granel líquido','GRANEL SÓLIDO':'Granel sólido','CARGA GERAL':'Carga geral'}
e['imp'] = e.imp_dwt | e.imp_seg
# navios simultâneos no mesmo berço
def multi(g):
    s = pd.to_datetime(g['Data Atracação']).values; t = pd.to_datetime(g['Data Desatracação']).values
    ev = sorted([(x, 1) for x in s] + [(x, -1) for x in t]); cur = 0; last = None; h2 = 0.0
    for x, d in ev:
        if last is not None and cur >= 2: h2 += (x - last) / np.timedelta64(1, 'h')
        cur += d; last = x
    return h2
g = e.groupby(['CDTUP','Porto Atracação','Tipo da Autoridade Portuária','SGUF','IDBerco','Berço'])
b = g.agg(esc=('IDAtracacao','size'), horas=('TAtracado','sum'), mwh=('aux_mwh','sum'), aux=('aux_co2_t','sum'),
          atr=('atr_co2_t','sum'), eu=('eu','mean'), imp=('imp','mean'), coord=('Coordenadas','first')).reset_index()
b['seg'] = e.groupby('IDBerco').apply(lambda x: x.groupby('seg').aux_co2_t.sum().idxmax()).reindex(b.IDBerco).map(segmap).values
b['h2'] = e.groupby('IDBerco').apply(multi).reindex(b.IDBerco).values
b = b.merge(den, left_on='IDBerco', right_index=True, how='left')
b['cov'] = (b.esc / b.den * 100).clip(upper=100)
b['ocup'] = b.horas / 8760 * 100
b = b.sort_values('aux', ascending=False).reset_index(drop=True)
rows = []
for i, r in b.iterrows():
    lon, lat = [float(v) for v in str(r.coord).split(',')]
    rows.append(dict(rk=i+1, cd=r.CDTUP, inst=r['Porto Atracação'], tipo=r['Tipo da Autoridade Portuária'], uf=r.SGUF,
        berco=str(r['Berço']).strip(), seg=r.seg, esc=int(r.esc), ocup=round(float(r.ocup), 1), mwh=round(float(r.mwh)),
        aux=round(float(r.aux)), atr=round(float(r.atr)), eu=round(float(r.eu)*100, 1), cov=round(float(r['cov'])),
        imp=round(float(r.imp)*100), multi=bool(r.ocup > 100 or r.h2 > 0.2*8760), lat=round(lat, 4), lon=round(lon, 4)))
seg = e.groupby('seg').agg(esc=('IDAtracacao','size'), mwh=('aux_mwh','sum'), aux=('aux_co2_t','sum'), atr=('atr_co2_t','sum'), eu=('eu','mean')).reset_index()
seg['seg'] = seg.seg.map(segmap); seg = seg.sort_values('aux', ascending=False)
nid = log['escalas_carga_lc_cab'] - log['base_offshore_excluida'] - log['duplicados_removidos'] - log['sem_imo_sem_dwt']
summ = dict(ano=2025, bercos=len(b), inst=int(b.CDTUP.nunique()), escalas=int(len(e)), mwh=round(float(e.aux_mwh.sum())),
    aux=round(float(e.aux_co2_t.sum())), atr=round(float(e.atr_co2_t.sum())), eu=round(float(e.eu.mean()*100), 1),
    cov=round(len(e)/nid*100, 1), baixa=int((b['cov'] < 80).sum()), multi=int(sum(r['multi'] for r in rows)), log=log)
out = dict(summary=summ, segmentos=[dict(seg=r.seg, esc=int(r.esc), mwh=round(r.mwh), aux=round(r.aux), atr=round(r.atr), eu=round(r.eu*100, 1)) for r in seg.itertuples()], bercos=rows)
json.dump(out, open('../dados/data.json','w'), ensure_ascii=False, separators=(',',':'))
print(json.dumps({k:v for k,v in summ.items() if k!='log'}, ensure_ascii=False))
B = pd.DataFrame(rows); print(B.head(8)[['rk','inst','berco','esc','ocup','aux','cov','imp','multi']].to_string())
print(B[B['cov']<80].sort_values('aux',ascending=False).head(10)[['rk','inst','berco','esc','cov']].to_string())
print(B[B.multi][['rk','inst','berco','ocup']].to_string())
it = B[B.inst=='Itaqui']; print('Itaqui', it.esc.sum(), it.aux.sum())
