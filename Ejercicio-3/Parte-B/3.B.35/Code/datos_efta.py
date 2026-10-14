#!/usr/bin/env python3
"""Datos de las figuras económicas de la EFTA (3.B.35): integración con la UE y protección agraria.

  - Comercio de bienes de Noruega, Islandia y Suiza con la UE-27 (suma de sus Estados miembros) y con el mundo, WITS
    (Banco Mundial, a partir de UN Comtrade), 1996-2023, en dólares corrientes. Para que la comparación no la dominen
    dos productos, se restan los hidrocarburos de Noruega (capítulo 27 del SA, grupo «27-27_Fuels» de WITS) y las
    piedras y metales preciosos de Suiza, sobre todo oro (capítulos 68-71, grupo «68-71_StoneGlas»).
  - Estimación de apoyo al productor (PSE, en % de los ingresos agrarios brutos) y coeficiente de protección nominal
    del productor (NPC) de la OCDE (dataflow OECD.TAD.ARP DSD_AGR_POLIND@DF_PSE), 1986 en adelante.
Caché en Code/datos/efta_ue.csv y Code/datos/pse_ocde.csv.
Uso, desde la carpeta del tema:  python3 Code/datos_efta.py
"""
import csv
import io
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402

DATOS = dc.TEMA / 'Code' / 'datos'
CSV_UE = DATOS / 'efta_ue.csv'
CSV_PSE = DATOS / 'pse_ocde.csv'
# (país, flujo, producto): producto 'Total' o el grupo que se resta
CONSULTAS = [('NOR', 'X', 'Total'), ('NOR', 'X', '27-27_Fuels'), ('NOR', 'M', 'Total'),
             ('CHE', 'X', 'Total'), ('CHE', 'X', '68-71_StoneGlas'), ('CHE', 'M', 'Total'), ('CHE', 'M', '68-71_StoneGlas'),
             ('ISL', 'X', 'Total'), ('ISL', 'M', 'Total')]


def wits(pais, anio, flujo, producto):
    ind = 'XPRT-TRD-VL' if flujo == 'X' else 'MPRT-TRD-VL'
    url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/%s/year/%d/partner/all'
           '/product/%s/indicator/%s?format=JSON' % (pais.lower(), anio, producto, ind))
    try:
        d = json.loads(dc.get(url))
    except ValueError:
        return None
    dims = d['structure']['dimensions']['series']
    ip = [i for i, x in enumerate(dims) if x['id'] == 'PARTNER'][0]
    valores = dims[ip]['values']
    socio = {}
    for clave, serie in d['dataSets'][0]['series'].items():
        socio[dc.iso(valores[int(clave.split(':')[ip])]['id'])] = serie['observations']['0'][0] * 1000.0
    return {'UE27': sum(socio.get(e, 0.0) for e in dc.UE27), 'WLD': socio.get('WLD', 0.0)}


def comercio(a0=1996, a1=2023):
    previas = dc_lee(CSV_UE)
    hechas = {(r['pais'], int(r['anio']), r['flujo'], r['producto']) for r in previas}
    tareas = [(p, a, f, pr) for a in range(a0, a1 + 1) for p, f, pr in CONSULTAS if (p, a, f, pr) not in hechas]
    filas = [[r[k] for k in ('pais', 'anio', 'flujo', 'producto', 'socio', 'valor_usd')] for r in previas]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for (p, a, f, pr), res in zip(tareas, ex.map(lambda t: wits(*t), tareas)):
            if res:
                filas += [[p, a, f, pr, s, f'{v:.0f}'] for s, v in res.items()]
    with open(CSV_UE, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['pais', 'anio', 'flujo', 'producto', 'socio', 'valor_usd'])
        w.writerows(filas)
    print('comercio con la UE:', len(filas), 'filas')


def dc_lee(ruta):
    if not ruta.exists():
        return []
    with open(ruta, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def pse():
    url = ('https://sdmx.oecd.org/public/rest/data/OECD.TAD.ARP,DSD_AGR_POLIND@DF_PSE,/NOR+CHE+ISL+EU+OECD.A.PSEP+PNPC..'
           '?startPeriod=1986&format=csvfilewithlabels')
    filas = [r for r in csv.DictReader(io.StringIO(dc.get(url))) if r['COMMODITY'] == 'CPC_EX_TO']
    with open(CSV_PSE, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['pais', 'medida', 'anio', 'valor'])
        for r in filas:
            w.writerow([r['REF_AREA'], r['MEASURE'], r['TIME_PERIOD'], r['OBS_VALUE']])
    print('PSE:', len(filas), 'filas')


if __name__ == '__main__':
    pse()
    comercio()
