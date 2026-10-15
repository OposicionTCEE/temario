#!/usr/bin/env python3
"""Lista de descargas de WITS para las figuras económicas del bloque geoestratégico (ASEAN, CCG, RCEP, UEE).

  ASEAN: exportaciones por socio según la fase de elaboración de la UNCTAD (materias primas, bienes intermedios, de consumo
         y de capital) y totales, 2000-2023 (Fábrica Asia); aranceles aplicados y de nación más favorecida por socio, con
         las importaciones para ponderar, 2000-2023 (margen de preferencia).
  RCEP:  exportaciones e importaciones totales por socio de los quince miembros en 2000-2001 y 2021-2023 (peso de China y
         de Japón en su comercio); aranceles aplicados y NMF de China, Japón y Corea por socio, 2018-2023 (enlaces nuevos).
  UEE:   exportaciones totales por socio de los Estados de la UE-27 y de Armenia, Kazajistán y Kirguistán, 2019-2024
         (desvío por sanciones).
El comercio intrarregional de la UEE (exportaciones bilaterales, 1996-2012) lo descarga Code/datos_comercio.py.
Uso, desde la carpeta del tema:  python3 Code/descargas_geoestrategicas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402

FASES = ['UNCTAD-SoP1', 'UNCTAD-SoP2', 'UNCTAD-SoP3', 'UNCTAD-SoP4']   # materias primas, intermedios, consumo, capital
ASEAN10 = [p for p in dc.GRUPOS['ASEAN'][0] if p != 'TLS']
CAUCASO_ASIA = ['ARM', 'KAZ', 'KGZ']


def tareas():
    t = []
    for p in ASEAN10:
        for a in range(2000, 2024):
            t += [('comercio', p, a, 'X', g) for g in ['Total'] + FASES]
            t += [('arancel', p, a, 'AHS', 'Total'), ('arancel', p, a, 'MFN', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in dc.GRUPOS['RCEP'][0]:
        for a in (2000, 2001, 2021, 2022, 2023):
            t += [('comercio', p, a, 'X', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in ('CHN', 'JPN', 'KOR'):
        for a in range(2018, 2024):
            t += [('arancel', p, a, 'AHS', 'Total'), ('arancel', p, a, 'MFN', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in dc.UE27 + CAUCASO_ASIA:
        for a in range(2019, 2025):
            t.append(('comercio', p, a, 'X', 'Total'))
    return t


ESPEJO_PRODUCTO = dc.TEMA / 'Code' / 'datos' / 'espejo_productos.csv'


def espejo_producto(exportadores, anios, producto):
    """Datos espejo de un grupo de productos de WITS: importaciones que todos los países declaran desde cada exportador
    (como Code/datos_comercio.py espejo, que solo pide el total). Code/datos/espejo_productos.csv: exportador, año,
    producto, importador, valor; el importador WLD es la suma de los que declaran."""
    import csv
    import json
    from concurrent.futures import ThreadPoolExecutor
    filas = {}
    if ESPEJO_PRODUCTO.exists():
        with open(ESPEJO_PRODUCTO, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                filas[(r['exportador'], int(r['anio']), r['producto'], r['importador'])] = float(r['valor_usd'])
    hechos = {(e, a, p) for (e, a, p, i) in filas}

    def una(par):
        e, anio = par
        url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/all/year/%d/partner/%s'
               '/product/%s/indicator/MPRT-TRD-VL?format=JSON' % (anio, dc.ISO_WITS.get(e, e).lower(), producto))
        try:
            d = json.loads(dc.get(url))
            dims = d['structure']['dimensions']['series']
        except (ValueError, KeyError, TypeError):
            return par, {}
        ir = [i for i, x in enumerate(dims) if x['id'] == 'REPORTER'][0]
        valores = dims[ir]['values']
        out = {}
        for clave, serie in d['dataSets'][0]['series'].items():
            v = serie['observations']['0'][0]
            if v is not None:
                imp = dc.iso(valores[int(clave.split(':')[ir])]['id'])
                out[imp] = out.get(imp, 0.0) + v * 1000.0
        return par, out
    faltan = [(e, a) for e in exportadores for a in anios if (e, a, producto) not in hechos]
    print(f'espejo {producto}: {len(faltan)} consultas', flush=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        for (e, a), out in ex.map(una, faltan):
            for i, v in out.items():   # WLD lo da WITS (suma de los que declaran), sin agregados regionales repetidos
                filas[(e, a, producto, i)] = v
    with open(ESPEJO_PRODUCTO, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exportador', 'anio', 'producto', 'importador', 'valor_usd', 'fuente'])
        for (e, a, p, i), v in sorted(filas.items()):
            w.writerow([e, a, p, i, f'{v:.0f}', 'WITS (Banco Mundial), MPRT-TRD-VL: importaciones declaradas por cada país desde el '
                        'exportador (datos espejo, CIF)'])


if __name__ == '__main__':
    dw.descarga(tareas())
    for prod in ('Total', 'Fuels'):
        espejo_producto(['SAU', 'ARE', 'KWT', 'QAT', 'BHR', 'OMN'], range(2000, 2024), prod)
