"""Interfaz web local para buscar fines de semana largos (jue->dom / vie->lun).

Uso: python app.py  (abre http://localhost:8765)
"""
import datetime as dt, html, re, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from buscavuelo import buscar_todo, combinar

PUERTO = 8765
PATRONES = {"jue": 3, "vie": 4}  # weekday de la ida
CIUDADES = {"BUE": "Buenos Aires", "BRC": "Bariloche", "CPC": "San Martín de los Andes", "EQS": "Esquel",
            "MDZ": "Mendoza", "IGR": "Iguazú", "FTE": "El Calafate", "USH": "Ushuaia", "SLA": "Salta",
            "JUJ": "Jujuy", "TUC": "Tucumán", "COR": "Córdoba", "NQN": "Neuquén", "REL": "Trelew",
            "PMY": "Puerto Madryn", "MDQ": "Mar del Plata", "ROS": "Rosario", "CRD": "Comodoro Rivadavia"}
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
NO_HAY = 10**15  # para ordenar: sin disponibilidad va al final

CSS = """
:root{--bg:#f4f6fa;--card:#fff;--txt:#17202b;--muted:#667085;--line:#e4e8ef;--pri:#0b5cad;--pri-soft:#e8f1fb;
--ok:#137a3f;--ok-soft:#e9f7ef;--shadow:0 1px 2px #0000000d,0 4px 16px #0000000a}
@media (prefers-color-scheme:dark){:root{--bg:#0f141b;--card:#171e27;--txt:#e6ebf1;--muted:#98a2b3;--line:#263140;
--pri:#5aa2ef;--pri-soft:#1a2c42;--ok:#3fa672;--ok-soft:#15301f;--shadow:none}}
*{box-sizing:border-box}
body{margin:0;font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--txt)}
header{background:linear-gradient(120deg,#0b5cad,#0a3f7a);color:#fff;padding:28px 16px 68px}
header h1,header p{margin:0 auto;max-width:1100px}
header h1{font-size:26px} header p{margin-top:6px;opacity:.85}
main{max-width:1100px;margin:-48px auto 40px;padding:0 16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
form.card{padding:18px;display:grid;grid-template-columns:1fr auto 1fr 1fr 1fr 100px;gap:14px;align-items:end}
label{display:flex;flex-direction:column;gap:5px;font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
input{font:inherit;color:var(--txt);background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:9px 11px;width:100%}
input:focus{outline:2px solid var(--pri);border-color:transparent}
input.iata{text-transform:uppercase;font-weight:700;font-size:17px}
.swap{border:1px solid var(--line);background:var(--card);color:var(--txt);border-radius:50%;width:40px;height:40px;cursor:pointer;font-size:17px}
.fila2{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{flex-direction:row;text-transform:none;letter-spacing:0;font-size:14px}
.chip input{position:absolute;opacity:0;width:0}
.chip span{padding:8px 14px;border-radius:999px;border:1px solid var(--line);cursor:pointer;color:var(--txt);user-select:none}
.chip input:checked+span{background:var(--pri-soft);border-color:var(--pri);color:var(--pri)}
.chip input:focus-visible+span{outline:2px solid var(--pri)}
button.go{font:inherit;font-weight:700;background:var(--pri);color:#fff;border:0;border-radius:10px;padding:11px 26px;cursor:pointer}
button.go:disabled{opacity:.7;cursor:wait}
.resumen{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:18px 0}
.resumen .card{padding:16px 18px;border-left:4px solid var(--ok)}
.resumen small{color:var(--muted);font-weight:700;text-transform:uppercase;font-size:12px}
.resumen .big{font-size:28px;font-weight:800;margin:2px 0}
.barra{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin:6px 0 10px}
.seg{display:inline-flex;align-items:center;gap:8px}
.seg>span{font-size:13px;color:var(--muted)}
.seg div{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--card)}
.seg button{font:inherit;font-size:14px;border:0;background:none;color:var(--txt);padding:8px 14px;cursor:pointer}
.seg button+button{border-left:1px solid var(--line)}
.seg button.on{background:var(--pri);color:#fff;font-weight:600}
.muted{color:var(--muted)}
table{width:100%;border-collapse:collapse}
th{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);text-align:left;padding:12px 14px;border-bottom:1px solid var(--line)}
td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
tr.top{background:var(--ok-soft)}
.fecha{font-weight:700;white-space:nowrap}
.tag{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--pri-soft);color:var(--pri);margin-top:4px}
.tag.best{background:var(--ok);color:#fff}
.precio{font-weight:800;font-size:17px}
.sub{font-size:13px;color:var(--muted)}
.na{color:var(--muted);font-size:13px}
.vuelos{font-size:13px;color:var(--muted);white-space:nowrap}
a.btn{display:inline-block;font-size:12px;font-weight:700;color:var(--pri);border:1px solid var(--pri);border-radius:8px;padding:2px 9px;text-decoration:none;margin-top:6px}
.err{color:#c62828;font-weight:600;padding:14px 18px;margin-top:18px}
.spin{display:inline-block;width:14px;height:14px;border:2px solid #fff8;border-top-color:#fff;border-radius:50%;animation:g .8s linear infinite;vertical-align:-2px;margin-right:8px}
@keyframes g{to{transform:rotate(360deg)}}
@media (max-width:760px){
 form.card{grid-template-columns:1fr auto 1fr}
 form.card label.m{grid-column:span 3}
 button.go{width:100%}
 thead{display:none} table,tbody,tr,td{display:block;width:100%}
 tr{border-bottom:1px solid var(--line);padding:8px 0} td{border:0;padding:5px 16px}
 td[data-l]::before{content:attr(data-l);display:block;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase}
 .vuelos{white-space:normal}
}
"""

JS = """
const tb=document.querySelector('#res tbody');
function ordenar(k){
  if(!tb)return;
  document.querySelectorAll('.seg button').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
  [...tb.rows].sort((a,b)=>(+a.dataset[k])-(+b.dataset[k])).forEach(r=>tb.appendChild(r));
  try{localStorage.setItem('orden',k)}catch(e){}
}
document.querySelectorAll('.seg button').forEach(b=>b.onclick=()=>ordenar(b.dataset.k));
let o='ars';try{o=localStorage.getItem('orden')||'ars'}catch(e){}
ordenar(o);
document.getElementById('swap').onclick=()=>{const a=document.getElementsByName('origen')[0],b=document.getElementsByName('destino')[0];[a.value,b.value]=[b.value,a.value]};
document.querySelector('form').onsubmit=e=>{const b=e.target.querySelector('.go');b.innerHTML='<span class=spin></span>Buscando…';setTimeout(()=>b.disabled=true)};
"""


def meses_entre(desde, hasta):
    y, m = map(int, desde.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= hasta and len(out) < 12:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def fines_de_semana(resultados, dias_ida):
    """Une millas y pesos (de todas las fuentes) en una fila por fin de semana, quedándose con el más barato."""
    filas = {}
    for fuente, unidad, ida, vuelta in resultados:
        for total, fi, oi, fv, ov, _ in combinar(ida, vuelta, 3, 3, dias_ida):
            fila = filas.setdefault((fi, fv), {"ida": fi, "vuelta": fv})
            if unidad not in fila or total < fila[unidad]["total"]:
                fila[unidad] = {"total": total, "fuente": fuente, "oi": oi, "ov": ov,
                                "tasas": oi["tasas"] + ov["tasas"]}
    return sorted(filas.values(), key=lambda f: f["ida"])


def fmt(n):
    return f"{n:,}".replace(",", ".")


def fecha_corta(iso):
    d = dt.date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d:%d/%m}"


def link_aerolineas(origen, destino, fi, fv, millas):
    q = [("adt", 1), ("inf", 0), ("chd", 0), ("flexDates", "true"), ("cabinClass", "Economy"),
         ("flightType", "ROUND_TRIP"), ("leg", f"{origen}-{destino}-{fi.replace('-', '')}"),
         ("leg", f"{destino}-{origen}-{fv.replace('-', '')}")] + ([("awardBooking", "true")] if millas else [])
    return "https://www.aerolineas.com.ar/flex-dates-calendar?" + urlencode(q)


def celda(fila, unidad, pax, origen, destino, mejor):
    titulo = "Millas" if unidad == "millas" else "Pesos"
    c = fila.get(unidad)
    if not c:
        return f'<td data-l="{titulo}" class="na">Sin disponibilidad</td>'
    if unidad == "millas":
        precio, sub = f"{fmt(c['total'])} millas", f"+ ${fmt(c['tasas'])} en pesos · x{pax} = {fmt(c['total'] * pax)} millas"
    else:
        precio, sub = f"${fmt(c['total'])}", f"x{pax} = ${fmt(c['total'] * pax)}"
    best = '<span class="tag best">Más barato</span> ' if c["total"] == mejor else ""
    url = html.escape(link_aerolineas(origen, destino, fila["ida"], fila["vuelta"], unidad == "millas"))
    return (f'<td data-l="{titulo}"><div class="precio">{precio}</div><div class="sub">{sub}</div>'
            f'{best}<a class="btn" href="{url}" target="_blank" rel="noopener">Ver en Aerolíneas ↗</a></td>')


def celda_vuelos(fila):
    c = fila.get("ARS") or fila["millas"]
    t = lambda o: html.escape(f"{o['vuelo']} · {o['hora']} · {o['ruta']}")
    return f'<td data-l="Vuelos" class="vuelos">Ida: {t(c["oi"])}<br>Vuelta: {t(c["ov"])}</td>'


def pagina(q, cuerpo=""):
    hoy = dt.date.today()
    desde = q.get("desde", f"{hoy:%Y-%m}")
    hasta = q.get("hasta", f"{(hoy.replace(day=1) + dt.timedelta(days=95)):%Y-%m}")
    opts = "".join(f'<option value="{k}">{v}</option>' for k, v in CIUDADES.items())
    chk = lambda k: "checked" if k in q.get("patrones", ["jue", "vie"]) else ""
    e = lambda k, d: html.escape(q.get(k, d))
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>BuscaVuelo</title><style>{CSS}</style></head><body>
<header><h1>✈️ BuscaVuelo</h1><p>Fines de semana largos al mejor precio, en millas y en pesos</p></header>
<main>
<form class="card" action="/">
 <label>Origen<input class="iata" name="origen" list="c" value="{e('origen', 'BUE')}" required pattern="[A-Za-z]{{3}}" maxlength="3"></label>
 <button type="button" class="swap" id="swap" title="Invertir origen y destino" aria-label="Invertir origen y destino">⇄</button>
 <label>Destino<input class="iata" name="destino" list="c" value="{e('destino', 'BRC')}" required pattern="[A-Za-z]{{3}}" maxlength="3"></label>
 <label class="m">Desde<input type="month" name="desde" value="{html.escape(desde)}" required></label>
 <label class="m">Hasta<input type="month" name="hasta" value="{html.escape(hasta)}" required></label>
 <label class="m">Pasajeros<input type="number" name="pax" min="1" max="9" value="{e('pax', '3')}"></label>
 <datalist id="c">{opts}</datalist>
 <div class="fila2">
  <div class="chips">
   <label class="chip"><input type="checkbox" name="patrones" value="jue" {chk('jue')}><span>Jueves → Domingo</span></label>
   <label class="chip"><input type="checkbox" name="patrones" value="vie" {chk('vie')}><span>Viernes → Lunes</span></label>
  </div>
  <button class="go" name="buscar" value="1">Buscar vuelos</button>
 </div>
</form>
{cuerpo}
</main><script>{JS}</script></body></html>"""


def resultados_html(q):
    origen, destino = q.get("origen", "").upper(), q.get("destino", "").upper()
    if not (re.fullmatch("[A-Z]{3}", origen) and re.fullmatch("[A-Z]{3}", destino)):
        return '<div class="card err">Origen y destino deben ser códigos de 3 letras (ej. BUE, BRC).</div>'
    pax = max(1, min(9, int(q.get("pax", "1") or 1)))
    dias = {PATRONES[p] for p in q.get("patrones", []) if p in PATRONES}
    if not dias:
        return '<div class="card err">Elegí al menos un tipo de fin de semana.</div>'
    hoy = f"{dt.date.today()}"
    filas = [f for f in fines_de_semana(buscar_todo(origen, destino, meses_entre(q["desde"], q["hasta"])), dias)
             if f["ida"] >= hoy]
    if not filas:
        return '<div class="card err">No se encontraron vuelos para esas fechas.</div>'

    mejor = {u: min((f[u]["total"] for f in filas if u in f), default=None) for u in ("ARS", "millas")}
    tarjetas = []
    for u, titulo in (("ARS", "Más barato en pesos"), ("millas", "Menos millas")):
        f = next((f for f in filas if u in f and f[u]["total"] == mejor[u]), None)
        if f:
            c = f[u]
            big = f"${fmt(c['total'])}" if u == "ARS" else f"{fmt(c['total'])} millas"
            extra = f"${fmt(c['total'] * pax)} para {pax}" if u == "ARS" else f"+ ${fmt(c['tasas'])} en pesos, por persona"
            tarjetas.append(f'<div class="card"><small>{titulo}</small><div class="big">{big}</div>'
                            f'<div>{fecha_corta(f["ida"])} → {fecha_corta(f["vuelta"])}</div><div class="sub">{extra}</div></div>')

    trs = []
    for f in filas:
        tipo = "Jue → Dom" if dt.date.fromisoformat(f["ida"]).weekday() == 3 else "Vie → Lun"
        top = any(u in f and f[u]["total"] == mejor[u] for u in mejor)
        trs.append(f'<tr class="{"top" if top else ""}" data-fecha="{dt.date.fromisoformat(f["ida"]).toordinal()}" '
                   f'data-ars="{f["ARS"]["total"] if "ARS" in f else NO_HAY}" '
                   f'data-millas="{f["millas"]["total"] if "millas" in f else NO_HAY}">'
                   f'<td data-l="Fin de semana"><div class="fecha">{fecha_corta(f["ida"])} → {fecha_corta(f["vuelta"])}</div>'
                   f'<span class="tag">{tipo}</span></td>'
                   f'{celda(f, "ARS", pax, origen, destino, mejor["ARS"])}'
                   f'{celda(f, "millas", pax, origen, destino, mejor["millas"])}{celda_vuelos(f)}</tr>')

    ruta = f"{html.escape(CIUDADES.get(origen, origen))} ↔ {html.escape(CIUDADES.get(destino, destino))}"
    return (f'<div class="resumen">{"".join(tarjetas)}</div>'
            f'<div class="barra"><span class="muted">{ruta} · {len(filas)} fines de semana · precio por adulto, ida y vuelta</span>'
            f'<div class="seg"><span>Ordenar por</span><div><button data-k="ars">Pesos</button>'
            f'<button data-k="millas">Millas</button><button data-k="fecha">Fecha</button></div></div></div>'
            f'<div class="card"><table id="res"><thead><tr><th>Fin de semana</th><th>Pesos</th><th>Millas</th>'
            f'<th>Vuelos (el más barato del día)</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/":
            self.send_error(404); return
        q = {k: (v if k == "patrones" else v[0]) for k, v in parse_qs(u.query).items()}
        try:
            cuerpo = resultados_html(q) if "buscar" in q else ""
        except Exception as e:
            cuerpo = f'<div class="card err">Error: {html.escape(str(e))}</div>'
        body = pagina(q, cuerpo).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    print(f"BuscaVuelo en http://localhost:{PUERTO}  (Ctrl+C para cerrar)")
    threading.Timer(1, webbrowser.open, [f"http://localhost:{PUERTO}"]).start()
    srv.serve_forever()
