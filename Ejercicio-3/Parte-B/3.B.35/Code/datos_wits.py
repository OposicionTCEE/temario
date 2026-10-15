#!/usr/bin/env python3
"""Descargas de WITS (Banco Mundial) por grupos de productos y aranceles por socio, para las figuras del bloque de afinidad.

  - comercio: exportaciones (XPRT-TRD-VL) o importaciones (MPRT-TRD-VL) de un país por socio, en un grupo de productos de WITS
    (Total; grupos de la CUCI: Food, AgrRaw, Fuels, OresMtls, manuf; secciones del SA: 01-05_Animal ... 90-99_Miscellan).
  - aranceles: arancel aplicado efectivo (AHS) y de nación más favorecida (MFN), medias ponderadas por el comercio, por socio
    (tradestats-tariff, indicadores AHS-WGHTD-AVRG y MFN-WGHTD-AVRG).
Caché en Code/datos/wits_extra.csv (una fila por país, año, tipo, flujo o indicador, producto y socio; una fila sin socio marca
que WITS no tiene ese dato, para no volver a pedirlo). Consultas en paralelo; WITS no tiene cuota.
Uso: desde otros scripts (from datos_wits import descarga, lee).
"""
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402

CSV = dc.TEMA / 'Code' / 'datos' / 'wits_extra.csv'
CAB = ['tipo', 'pais', 'anio', 'medida', 'producto', 'socio', 'valor']
URL = {'comercio': 'https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/%s/year/%d/partner/all'
                   '/product/%s/indicator/%s?format=JSON',
       'arancel': 'https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-tariff/reporter/%s/year/%d/partner/all'
                  '/product/%s/indicator/%s?format=JSON'}
MEDIDA = {'X': 'XPRT-TRD-VL', 'M': 'MPRT-TRD-VL', 'AHS': 'AHS-WGHTD-AVRG', 'MFN': 'MFN-WGHTD-AVRG'}


def consulta(tipo, pais, anio, medida, producto):
    url = URL[tipo] % (dc.ISO_WITS.get(pais, pais).lower(), anio, producto, MEDIDA[medida])
    try:
        d = json.loads(dc.get(url))
        dims = d['structure']['dimensions']['series']
    except (ValueError, KeyError, TypeError):
        return [[tipo, pais, anio, medida, producto, '', '']]
    ip = [i for i, x in enumerate(dims) if x['id'] == 'PARTNER'][0]
    valores = dims[ip]['values']
    filas = []
    for clave, serie in d['dataSets'][0]['series'].items():
        v = serie['observations']['0'][0]
        if v is None:
            continue
        v = v * 1000.0 if tipo == 'comercio' else v   # comercio en miles de dólares -> dólares
        filas.append([tipo, pais, anio, medida, producto, dc.iso(valores[int(clave.split(':')[ip])]['id']), f'{v:.6g}'])
    return filas or [[tipo, pais, anio, medida, producto, '', '']]


def lee():
    if not CSV.exists():
        return []
    with open(CSV, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def descarga(tareas, hilos=8):
    """tareas: [(tipo, país, año, medida, producto)]; descarga solo las que faltan."""
    previas = lee()
    hechas = {(r['tipo'], r['pais'], int(r['anio']), r['medida'], r['producto']) for r in previas}
    faltan = [t for t in dict.fromkeys(tareas) if t not in hechas]
    filas = [[r[k] for k in CAB] for r in previas]
    print(f'WITS: {len(faltan)} consultas nuevas', flush=True)
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        for i, res in enumerate(ex.map(lambda t: consulta(*t), faltan)):
            filas += res
            if i % 200 == 199:
                print(f'  {i + 1} hechas', flush=True)
                escribe(filas)
    escribe(filas)


def escribe(filas):
    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(CAB)
        w.writerows(filas)


def tabla(tipo, medida, producto):
    """{(país, año): {socio: valor}} de la caché."""
    out = {}
    for r in lee():
        if r['tipo'] == tipo and r['medida'] == medida and r['producto'] == producto and r['socio']:
            out.setdefault((r['pais'], int(r['anio'])), {})[r['socio']] = float(r['valor'])
    return out
