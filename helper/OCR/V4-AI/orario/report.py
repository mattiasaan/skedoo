"""Pagina HTML di revisione: ritaglio accanto alle letture, campi modificabili,
e pulsante che scarica il JSON finale verificato. Un solo file, nessuna dipendenza."""
import base64
import html
import json
from pathlib import Path

_CSS = """
:root{--bg:#f6f5f1;--fg:#1d1d1b;--mut:#6b6a63;--card:#fff;--bd:#ddd9cf;--rosso:#b3261e;--amb:#a05a00;--ok:#1b6e3c;--acc:#1f4fd8}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--mut:#a09f97;--card:#201f1c;--bd:#38362f;--rosso:#ff8a80;--amb:#ffb74d;--ok:#6fcf97;--acc:#8ab4ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:20px 16px 80px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 10px}
.sub{color:var(--mut);margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 14px;margin:10px 0}
.card.rev{border-left:5px solid var(--rosso)}.card.dis{border-left:5px solid var(--amb)}
.top{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.tag{font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid currentColor}
.tag.rev{color:var(--rosso)}.tag.dis{color:var(--amb)}.tag.ok{color:var(--ok)}
img.crop{max-width:100%;image-rendering:auto;border:1px solid var(--bd);border-radius:6px;background:#888;margin:8px 0}
table.l{border-collapse:collapse;font-size:13px;margin:6px 0}table.l td{padding:2px 10px 2px 0;vertical-align:top}
.mot{color:var(--mut);white-space:nowrap}code{font:12px ui-monospace,Consolas,monospace}
.f{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}.f label{display:flex;flex-direction:column;font-size:12px;color:var(--mut)}
input,textarea{font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--bd);border-radius:6px;padding:5px 8px}
input.s{width:90px}input.m{width:150px}textarea{width:100%;min-height:70px}
.ok-row{display:flex;gap:8px;align-items:center;margin-top:6px}
button{font:inherit;padding:8px 16px;border-radius:8px;border:1px solid var(--acc);background:var(--acc);color:#fff;cursor:pointer}
.bar{position:sticky;bottom:0;background:var(--bg);border-top:1px solid var(--bd);padding:10px 16px;display:flex;gap:12px;align-items:center}
.mot-list{color:var(--mut);font-size:13px}.avv{color:var(--amb)}
"""

_JS = r"""
const KEYS=['cambi_aula','entrate','uscite','senza_lezioni_pomeridiane','note'];
function find(id){for(const k of KEYS)for(const it of DATA[k])if(it.unit_id===id)return it;return null}
function val(id){return document.getElementById(id)}
function bind(card){
  const id=card.dataset.id,tipo=card.dataset.tipo;
  const it=tipo==='titolo'?DATA:find(id);
  card.querySelectorAll('[data-f]').forEach(inp=>{
    inp.addEventListener('input',()=>{
      const f=inp.dataset.f,v=inp.value.trim();
      if(tipo==='riga'){
        if(f==='classe')it.classe=v?v.toUpperCase().replace(/\s+/g,''):null;
        if(f==='aula')it.aula=v?v.toUpperCase():null;
        if(f==='da'||f==='a'){const da=card.querySelector('[data-f=da]').value.trim(),a=card.querySelector('[data-f=a]').value.trim();it.orario=(da&&a)?(da+' - '+a):null}
      }else if(tipo==='titolo'){
        if(f==='numero')DATA.data_numero=parseInt(v)||null;else if(f==='giorno')DATA.giorno=v.toUpperCase();else DATA.mese=v.toUpperCase();
        DATA.data=(DATA.data_numero?String(DATA.data_numero).padStart(2,'0'):'')+' '+(DATA.mese||'');
      }else if(tipo==='info'){it.testo=inp.value}
      else{
        if(f==='ora')it.ora=v||null;
        if(f==='classi')it.classi=v.split(/[ ,+]+/).filter(Boolean).map(x=>x.toUpperCase());
        if(f==='note')it.note=inp.value;
      }
    });
  });
}
document.querySelectorAll('.card[data-id]').forEach(bind);
function esporta(){
  const out=JSON.parse(JSON.stringify(DATA));
  let aperti=0;
  document.querySelectorAll('.card.rev,.card.dis').forEach(c=>{
    const conf=c.querySelector('input.conf').checked;
    const id=c.dataset.id,tipo=c.dataset.tipo;
    if(tipo==='titolo'){out.titolo_verifica=conf?'verificato':'da_verificare'}
    else{for(const k of KEYS)for(const it of out[k])if(it.unit_id===id)it.verifica=conf?'verificato':'da_verificare'}
    if(!conf)aperti++;
  });
  out.n_da_verificare=aperti;
  out.stato=aperti===0?'verificato':'da_verificare';
  delete out.controllo;delete out.titolo_unit_id;
  for(const k of KEYS)for(const it of out[k])delete it.unit_id;
  const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=NOME;a.click();
  val('esito').textContent=aperti===0?'JSON verificato scaricato.':('Attenzione: '+aperti+' voci non confermate (restano da_verificare).');
}
"""


def _img_tag(path):
    if not path or not Path(path).is_file():
        return ""
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img class="crop" alt="ritaglio" src="data:image/png;base64,{b64}">'


def _campi(c, res):
    tipo, uid = c["tipo"], c["id"]
    e = html.escape
    if tipo == "titolo":
        return (f'<div class="f"><label>giorno<input class="m" data-f="giorno" value="{e(res.get("giorno") or "")}"></label>'
                f'<label>numero<input class="s" data-f="numero" value="{e(str(res.get("data_numero") or ""))}"></label>'
                f'<label>mese<input class="m" data-f="mese" value="{e(res.get("mese") or "")}"></label></div>')
    it = None
    for k in ("cambi_aula", "entrate", "uscite", "senza_lezioni_pomeridiane", "note"):
        for x in res[k]:
            if x.get("unit_id") == uid:
                it = x
    if it is None:
        return ""
    if tipo == "riga":
        da, a = ("", "")
        if it.get("orario"):
            da, a = it["orario"].split(" - ")
        return (f'<div class="f"><label>classe<input class="s" data-f="classe" value="{e(it.get("classe") or "")}"></label>'
                f'<label>da<input class="s" data-f="da" value="{e(da)}"></label>'
                f'<label>a<input class="s" data-f="a" value="{e(a)}"></label>'
                f'<label>aula<input class="m" data-f="aula" value="{e(it.get("aula") or "")}"></label></div>')
    if tipo in ("entra", "esce"):
        return (f'<div class="f"><label>ora<input class="s" data-f="ora" value="{e(it.get("ora") or "")}"></label>'
                f'<label>classi (separate da spazio)<input class="m" style="width:380px" data-f="classi" value="{e(" ".join(it.get("classi") or []))}"></label></div>'
                f'<label>nota<textarea data-f="note">{e(it.get("note") or "")}</textarea></label>')
    if tipo == "nolez":
        return (f'<div class="f"><label>classi<input class="m" style="width:380px" data-f="classi" value="{e(" ".join(it.get("classi") or []))}"></label></div>')
    return f'<label>testo<textarea data-f="testo">{e(it.get("testo") or "")}</textarea></label>'


def _card(c, res):
    cls = "rev" if c["stato"] == "revisione" else "dis"
    lab = "DA VERIFICARE" if cls == "rev" else "DISSENSO - DA VERIFICARE"
    e = html.escape
    rows = "".join(f'<tr><td class="mot">{e(k)}</td><td><code>{e(v)}</code></td></tr>'
                   for k, v in c["letture"].items())
    motivi = "; ".join(c["motivi"])
    h = (f'<div class="card {cls}" data-id="{e(c["id"])}" data-tipo="{ "info" if c["tipo"] == "info" else c["tipo"] }">'
         f'<div class="top"><span class="tag {cls}">{lab}</span><b>{e(c["tipo"])}</b>'
         f'<span class="mot-list">{e(motivi)}</span></div>'
         f'{_img_tag(c.get("ritaglio"))}<table class="l">{rows}</table>')
    if cls in ("rev", "dis"):
        h += _campi(c, res)
        h += '<div class="ok-row"><label><input type="checkbox" class="conf"> Ho controllato sull\'immagine: il valore qui sopra e\' corretto</label></div>'
    return h + "</div>"


def scrivi_report(res: dict, out_path):
    e = html.escape
    nome = Path(res["_source"]).stem + "_verificato.json"
    daf = [c for c in res["controllo"] if c["stato"] == "revisione"]
    dis = [c for c in res["controllo"] if c["stato"] == "dissenso"]
    parts = [f"<!doctype html><html lang='it'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>Revisione {e(res['_source'])}</title><style>{_CSS}</style><main>",
             f"<h1>Revisione: {e(res['_source'])}</h1>",
             f"<div class='sub'>{e(str(res.get('giorno') or '?'))} {e(str(res.get('data') or ''))} &middot; "
             f"{len(daf)} da verificare &middot; {len(dis)} con dissenso</div>"]
    if res.get("avvisi"):
        parts.append("<h2>Avvisi di coerenza</h2><div class='card avv'>" +
                     "<br>".join(e(a) for a in res["avvisi"]) + "</div>")
    if daf:
        parts.append("<h2>Da verificare (obbligatorio)</h2>")
        parts += [_card(c, res) for c in daf]
    if dis:
        parts.append("<h2>Dissensi (controllo rapido)</h2>")
        parts += [_card(c, res) for c in dis]
    data = json.dumps(res, ensure_ascii=False).replace("</", "<\\/")
    parts.append("</main><div class='bar'><button onclick='esporta()'>Scarica JSON finale</button>"
                 "<span id='esito' class='mot-list'></span></div>"
                 f"<script>const DATA={data};const NOME={json.dumps(nome)};{_JS}</script></html>")
    Path(out_path).write_text("".join(parts), encoding="utf-8")
    return out_path
