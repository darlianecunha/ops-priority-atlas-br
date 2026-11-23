import pandas as pd, numpy as np, json
b=pd.read_pickle('berths.pkl')
b['classe']=np.select([b.cum<=0.25,b.cum<=0.5,b.cum<=0.75],['A','B','C'],'D')
# shift so the berth crossing the threshold belongs to the class it completes
prev=b.cum.shift(fill_value=0)
b['classe']=np.select([prev<0.25,prev<0.5,prev<0.75],['A','B','C'],'D')
segmap={'CONTÊINER':'Contêiner','GRANEL LÍQUIDO':'Granel líquido','GRANEL SÓLIDO':'Granel sólido','CARGA GERAL':'Carga geral'}
def ll(c):
    lon,lat=[float(v) for v in str(c).split(',')]; return round(lat,4),round(lon,4)
rows=[]
for i,r in b.iterrows():
    lat,lon=ll(r.coord)
    rows.append(dict(rk=i+1,cd=r.CDTUP,inst=r['Porto Atracação'],tipo=r['Tipo da Autoridade Portuária'],uf=r.SGUF,
      berco=str(r['Berço']).strip(),seg=segmap[r.seg_dom],esc=int(r.escalas),ocup=round(float(r.ocup_pct),1),
      mwh=round(float(r.aux_mwh)),aux=round(float(r.aux_t)),atr=round(float(r.atr_t)),
      eu=None if pd.isna(r.eu_pct) else round(float(r.eu_pct),1),cl=r.classe,lat=lat,lon=lon))
d=pd.read_pickle('calls.pkl'); y=d[d.Ano==2025]
seg=y.groupby('seg').agg(esc=('IDAtracacao','size'),mwh=('aux_mwh','sum'),aux=('aux_co2_t','sum'),atr=('co2_atracado_t','sum'),eu=('eu','mean')).reset_index()
seg['seg']=seg.seg.map(segmap); seg=seg.sort_values('aux',ascending=False)
summ=dict(ano=2025,bercos=len(b),inst=int(b.CDTUP.nunique()),escalas=int(len(y)),mwh=round(float(y.aux_mwh.sum())),
  aux=round(float(y.aux_co2_t.sum())),atr=round(float(y.co2_atracado_t.sum())),eu=round(float(y.eu.mean()*100),1),
  nA=int((b.classe=='A').sum()),nB=int((b.classe=='B').sum()),nC=int((b.classe=='C').sum()),
  ocup100=int((b.ocup_pct>100).sum()))
out=dict(summary=summ,segmentos=[dict(seg=r.seg,esc=int(r.esc),mwh=round(r.mwh),aux=round(r.aux),atr=round(r.atr),eu=round(r.eu*100,1)) for r in seg.itertuples()],bercos=rows)
json.dump(out,open('../dados/data.json','w'),ensure_ascii=False,separators=(',',':'))
print(json.dumps(summ,ensure_ascii=False)); print(out['segmentos'])
print(pd.Series([r['cl'] for r in rows]).value_counts())
a=b[b.classe=='A']; print(a.groupby('seg_dom').size(), a.CDTUP.nunique())
