"""Busca los vuelos más baratos (millas y pesos) ida y vuelta.

Uso:
  python buscavuelo.py BUE BRC 2026-11 2026-12 --noches 3-7
"""
import argparse, csv, datetime as dt, functools, re, sys
from pathlib import Path
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
HISTORIAL = Path(__file__).with_name("historial.csv")


@functools.cache
def token_aerolineas():
    # El token anónimo viene embebido en el HTML de la home (dura ~24h).
    home = requests.get("https://www.aerolineas.com.ar/", headers={"User-Agent": UA}, timeout=30).text
    return re.search(r'ACCESS_TOKEN__\s*=\s*"([^"]+)"', home).group(1)


def aerolineas(origen, destino, mes, millas, cabina="Economy"):
    """Devuelve {'ida': {fecha: oferta}, 'vuelta': {...}} para todo el mes. Precio por adulto."""
    def calendario(dia_ida, dia_vuelta):
        m = mes.replace("-", "")
        r = requests.get(
            "https://api.aerolineas.com.ar/v1/flights/offers",
            params=[("adt", 1), ("inf", 0), ("chd", 0), ("flexDates", "true"), ("cabinClass", cabina),
                    ("flightType", "ROUND_TRIP"), ("awardBooking", str(millas).lower()),
                    ("leg", f"{origen}-{destino}-{m}{dia_ida}"), ("leg", f"{destino}-{origen}-{m}{dia_vuelta}")],
            headers={"User-Agent": UA, "Authorization": "Bearer " + token_aerolineas(),
                     "X-Channel-Id": "WEB_AR", "Accept-Language": "es-AR"},
            timeout=60)
        r.raise_for_status()
        return r.json()["calendarOffers"]

    # La API devuelve el mes pero solo con precios a ±15 días de cada fecha consultada y con
    # ida <= vuelta. Por eso: una consulta para tener todas las idas y otra para todas las vueltas.
    out = {}
    for tramo, clave, dias in (("ida", "0", ("16", "28")), ("vuelta", "1", ("01", "16"))):
        out[tramo] = {}
        for o in calendario(*dias).get(clave, []):
            det = o.get("offerDetails")
            if not det or o.get("soldOut"):
                continue
            seg = o["leg"]["segments"]
            out[tramo][o["departure"]] = {
                "precio": det["fare"]["total"],
                "tasas": det["fare"]["taxes"],  # en millas: pesos a pagar aparte
                "vuelo": "+".join(f'{s["airline"]}{s["flightNumber"]}' for s in seg),
                "hora": seg[0]["departure"][11:16],
                "ruta": f'{seg[0]["origin"]}-{seg[-1]["destination"]}',
                "escalas": o["leg"]["stops"],
                "asientos": det["seatAvailability"]["seats"],
            }
    return out


# Para sumar otra aerolínea: función con la misma firma y agregarla acá.
FUENTES = {"aerolineas": aerolineas}


def combinar(ida, vuelta, nmin, nmax, dias_ida=None):
    """Combinaciones ida+vuelta con estadía entre nmin y nmax noches, ordenadas por precio.
    dias_ida: weekdays permitidos para la ida (0=lun ... 3=jue, 4=vie)."""
    combos = []
    for fi, oi in ida.items():
        if dias_ida is not None and dt.date.fromisoformat(fi).weekday() not in dias_ida:
            continue
        for fv, ov in vuelta.items():
            noches = (dt.date.fromisoformat(fv) - dt.date.fromisoformat(fi)).days
            if nmin <= noches <= nmax:
                combos.append((oi["precio"] + ov["precio"], fi, oi, fv, ov, noches))
    return sorted(combos, key=lambda c: c[0])


def buscar_todo(origen, destino, meses):
    """Consulta todas las fuentes en millas y pesos. Devuelve [(fuente, unidad, ida, vuelta)] y guarda historial."""
    ahora = dt.datetime.now().isoformat(timespec="minutes")
    out = []
    with HISTORIAL.open("a", newline="", encoding="utf-8") as f:
        hist = csv.writer(f)
        for fuente, buscar in FUENTES.items():
            for millas, unidad in ((True, "millas"), (False, "ARS")):
                ida, vuelta = {}, {}
                for mes in meses:
                    try:
                        res = buscar(origen, destino, mes, millas)
                    except Exception as e:  # una fuente/mes caído no frena al resto
                        print(f"[{fuente} {unidad} {mes}] error: {e}", file=sys.stderr)
                        continue
                    ida.update(res["ida"]); vuelta.update(res["vuelta"])
                for tramo, ofertas in (("ida", ida), ("vuelta", vuelta)):
                    for fecha, o in ofertas.items():
                        hist.writerow([ahora, fuente, unidad, tramo, fecha, o["precio"], o["vuelo"], o["ruta"], o["asientos"]])
                out.append((fuente, unidad, ida, vuelta))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("origen"); ap.add_argument("destino")
    ap.add_argument("meses", nargs="+", help="YYYY-MM")
    ap.add_argument("--noches", default="2-10", help="rango de estadía, ej 3-7")
    ap.add_argument("--pax", type=int, default=3, help="pasajeros que pagan (para el total)")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--desde", default=None, help="no mostrar idas antes de YYYY-MM-DD")
    ap.add_argument("--finde", action="store_true", help="solo jue->dom y vie->lun")
    a = ap.parse_args()
    nmin, nmax = map(int, a.noches.split("-"))
    dias = {3, 4} if a.finde else None
    if a.finde:
        nmin = nmax = 3  # jue->dom y vie->lun son ambos 3 noches

    for fuente, unidad, ida, vuelta in buscar_todo(a.origen, a.destino, a.meses):
        if a.desde:
            ida = {k: v for k, v in ida.items() if k >= a.desde}
        combos = combinar(ida, vuelta, nmin, nmax, dias)
        print(f"\n=== {fuente.upper()} | {unidad} | {a.origen}<->{a.destino} | {nmin}-{nmax} noches | por adulto (x{a.pax} = total) ===")
        if not combos:
            print("  sin combinaciones disponibles")
        for total, fi, oi, fv, ov, n in combos[:a.top]:
            tasas = f"+ ${oi['tasas'] + ov['tasas']:,} tasas  " if unidad == "millas" else ""
            print(f"  {total:>10,} {unidad:<6} x{a.pax}={total * a.pax:>11,}  {tasas}"
                  f"ida {fi} {oi['hora']} {oi['vuelo']:<7} {oi['ruta']}  "
                  f"vuelta {fv} {ov['hora']} {ov['vuelo']:<7} {ov['ruta']}  ({n}n)".replace(",", "."))


if __name__ == "__main__":
    main()
