import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd, numpy as np
from model import params, SFOC, EF
U = sys.argv[1] if len(sys.argv) > 1 else '/Users/darlianecunha/projetos/01_portos-emissoes/'
SEG = {'Granel Sólido':'GRANEL SÓLIDO','Granel Líquido e Gasoso':'GRANEL LÍQUIDO','Carga Geral':'CARGA GERAL','Carga Conteinerizada':'CONTÊINER'}
ANO = 2025
a = pd.read_csv(U+'artigo.site.co2completo100726/antaq_ea/atracacoes_antaq_2019_2025.csv.gz')
a['seg'] = a.natureza_predominante.map(SEG)
c = a[(a.Ano==ANO)&(a.FlagMCOperacaoAtracacao==1)&a['Tipo de Navegação da Atracação'].isin(['Longo Curso','Cabotagem'])].copy()
log = {'escalas_carga_lc_cab': len(c)}
# 0 base de apoio offshore: embarcações de apoio registradas como carga; arquétipos de navio de carga não se aplicam
off = c['Porto Atracação'].str.contains('Offshore', na=False)
log['base_offshore_excluida'] = int(off.sum()); c = c[~off]
# 1 duplicados: mesmo IMO e mesmo horário de atracação
dup = c.IMO.notna() & c.duplicated(['IMO','Data Atracação'])
log['duplicados_removidos'] = int(dup.sum()); c = c[~dup]
# 2 sem IMO e sem DWT: barcaças e embarcações não identificadas (sem motores auxiliares de navio)
semid = c.IMO.isna() & c.DWT_final.isna()
log['sem_imo_sem_dwt'] = int(semid.sum())
# 3 tempo atracado válido
okt = (c.TAtracado > 0) & (c.TAtracado <= 720)
log['tempo_invalido'] = int((~okt & ~semid).sum())
# referências para imputação (todas as escalas 2019-2025 com DWT e segmento)
ref = a.dropna(subset=['DWT_final','seg'])
segb = ref.groupby('IDBerco').seg.agg(lambda s: s.value_counts().idxmax())
gb = ref.groupby(['IDBerco','seg']).DWT_final
med_b = gb.median()[gb.size() >= 10]  # só berços com navios identificados suficientes
med_i = ref.groupby(['CDTUP','seg']).DWT_final.median()
med_n = ref.groupby('seg').DWT_final.median()
c['imp_seg'] = False; c['imp_dwt'] = False
m = c.seg.isna() & c.IMO.notna()
c.loc[m, 'seg'] = c.loc[m, 'IDBerco'].map(segb); c.loc[m & c.seg.notna(), 'imp_seg'] = True
def dwt_imp(r):
    k = (r.IDBerco, r.seg)
    return med_b.loc[k] if k in med_b.index else np.nan
m = c.DWT_final.isna() & c.IMO.notna() & c.seg.notna()
c.loc[m, 'DWT_final'] = c[m].apply(dwt_imp, axis=1); c.loc[m, 'imp_dwt'] = True
use = ~semid & okt & c.seg.notna() & c.DWT_final.notna()
log['sem_segmento'] = int((~semid & okt & c.seg.isna()).sum())
log['dwt_nao_imputavel'] = int((~semid & okt & c.seg.notna() & c.DWT_final.isna()).sum())
c['usada'] = use
e = c[use].copy()
log['escalas_usadas'] = len(e); log['dwt_imputado'] = int(e.imp_dwt.sum()); log['segmento_imputado'] = int(e.imp_seg.sum())
sme, sae, sbo = SFOC['HFO']; ef = EF['HFO']
P = [params(s, float(w)) for s, w in zip(e.seg, e.DWT_final)]
e['aux_mwh'] = [p['ab'] for p in P] * e.TAtracado / 1000
e['aux_co2_t'] = e.aux_mwh * 1000 * sae / 1e6 * ef
e['atr_co2_t'] = [(p['ab']*sae + p['bb']*sbo) for p in P] * e.TAtracado / 1e6 * ef
mrv = pd.read_excel(U+'IMO/mrv_publicacoes/EU_MRV_publication_2025_v95.xlsx', header=2, usecols=[0])
mrv = set(pd.to_numeric(mrv.iloc[:,0], errors='coerce').dropna().astype(int))
e['eu'] = [int(i) in mrv if pd.notna(i) else np.nan for i in e.IMO]
e.to_pickle('calls2.pkl'); c[['IDAtracacao','IDBerco','CDTUP','Porto Atracação','usada']].to_pickle('base2.pkl')
json.dump(log, open('log_auditoria.json','w'), ensure_ascii=False, indent=1)
print(log)
