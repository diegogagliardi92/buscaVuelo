# BuscaVuelo

Busca fines de semana largos (jueves → domingo / viernes → lunes) al mejor precio en **millas** y en **pesos** en Aerolíneas Argentinas.

## Uso

Requiere Python 3 y `requests` (`pip install requests`).

- **Interfaz web:** doble clic en `BuscaVuelo.bat` o `python app.py` → abre http://localhost:8765
- **Consola:** `python buscavuelo.py BUE BRC 2026-11 2026-12 --finde --pax 3`

Cada búsqueda se guarda en `historial.csv`. Precios por adulto.

## Sumar otra aerolínea

Escribir una función con la firma de `aerolineas(origen, destino, mes, millas)` en `buscavuelo.py` y agregarla a `FUENTES`.
