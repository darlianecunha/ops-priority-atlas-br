# Monta as duas versões do atlas.
#   site/index.html            vitrine pública: só os 20 primeiros berços e a curva anônima (dados/vitrine.json)
#   privado/atlas_completo.html versão completa com o ranking dos 375 berços (dados/data.json). Não publicar.
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
geo = (R/'dados/geo.json').read_text()
D = json.loads((R/'dados/data.json').read_text()); B = D['bercos']
cum, cm, seen, ni = [0], [0], set(), [0]
for b in B:
    cum.append(cum[-1]+b['aux']); cm.append(cm[-1]+b['mwh']); seen.add(b['cd']); ni.append(len(seen))
inst = {}
for b in B: inst.setdefault(b['cd'], dict(cd=b['cd'], inst=b['inst'], uf=b['uf'], lat=b['lat'], lon=b['lon']))
S = {k: D['summary'][k] for k in ['ano','bercos','inst','escalas','mwh','aux','atr','eu','cov','log']}
top = [{k: b[k] for k in ['rk','cd','inst','uf','berco','seg','esc','mwh','aux','atr','eu','multi','cov']} for b in B[:20]]
V = dict(summary=S, segmentos=D['segmentos'], top=top, cum=[round(x) for x in cum], cumM=[round(x) for x in cm], ninst=ni, inst=list(inst.values()))
(R/'dados/vitrine.json').write_text(json.dumps(V, ensure_ascii=False, separators=(',',':')))
t = (R/'scripts/template_vitrine.html').read_text()
(R/'site/index.html').write_text(t.replace('__DATA__', json.dumps(V, ensure_ascii=False, separators=(',',':'))).replace('__GEO__', geo))
t = (R/'scripts/template.html').read_text()
(R/'privado').mkdir(exist_ok=True)
(R/'privado/atlas_completo.html').write_text(t.replace('__DATA__', (R/'dados/data.json').read_text()).replace('__GEO__', geo))
