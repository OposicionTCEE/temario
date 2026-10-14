#!/usr/bin/env python3
"""Descarga el comercio por productos de los miembros de un bloque (UN Comtrade, CUCI) y series del Banco Mundial.

Sirve a las figuras económicas del tema (composición, complementariedad, intensidad y saldos):
  - composicion: exportaciones de cada miembro al mundo y a cada socio por secciones de la CUCI (1 dígito), una
    consulta por año. La API pública de vista previa de UN Comtrade ofrece la CUCI Rev. 1 hasta 1995, la Rev. 3 de
    1996 a 2006 y la Rev. 4 desde 2007; a 1 dígito, las secciones son comparables entre revisiones.
  - productos: exportaciones e importaciones de cada miembro con el mundo por grupos de la CUCI (3 dígitos) en los
    años que se indiquen (complementariedad comercial; cada año se calcula dentro de una misma revisión).
  - wdi: series anuales del Banco Mundial (PIB, importaciones de mercancías...) de los miembros y del mundo.
Caché en Code/datos/ (solo se descarga lo que falta; un año que la API devuelve vacío se vuelve a pedir otra vez).
Uso, desde la carpeta del tema:
  python3 Code/datos_producto.py MCCA composicion 1962 2023
  python3 Code/datos_producto.py MCCA productos 1965 1975 1985 1995 2005 2015 2023
  python3 Code/datos_producto.py USA,CHN importaciones 1965 1975 1985 1995 2005 2015 2023   (mercados de referencia)
  python3 Code/datos_producto.py MCCA division68 1962 2023   (metales no ferrosos, para restarlos de las manufacturas)
  python3 Code/datos_producto.py MCCA wdi
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402

DATOS = dc.TEMA / 'Code' / 'datos'
CSV_COMP = DATOS / 'composicion_cuci.csv'
CSV_PROD = DATOS / 'productos_cuci3.csv'
CSV_68 = DATOS / 'division68_cuci.csv'
CSV_WDI = DATOS / 'wdi_series.csv'
WDI = {'NY.GDP.MKTP.CD': 'PIB (USD corrientes)', 'TM.VAL.MRCH.CD.WT': 'Importaciones de mercancías (USD corrientes)',
       'NY.GDP.PCAP.KD': 'PIB per cápita (USD constantes de 2015)',
       'NY.GDP.PCAP.PP.KD': 'PIB per cápita (PPA, USD internacionales constantes de 2021)'}


def revision(anio):
    return 'S1' if anio <= 1995 else ('S3' if anio <= 2006 else 'S4')


def comtrade(anio, reporteros, socios, flujo, nivel):
    """Filas agregadas (sin desglose por modo de transporte ni régimen aduanero) de la API de vista previa."""
    url = ('https://comtradeapi.un.org/public/v1/preview/C/A/%s?reporterCode=%s&period=%d&partnerCode=%s'
           '&flowCode=%s&cmdCode=%s' % (revision(anio), ','.join(str(dc.M49[r]) for r in reporteros), anio,
                                         ','.join(str(dc.M49[s]) for s in socios), flujo, nivel))
    for espera in (0, 20, 60):
        time.sleep(espera + 5)
        try:
            datos = json.loads(dc.get(url)).get('data', [])
        except ValueError:
            datos = []
        if datos:
            break
    if len(datos) >= 500:
        print(f'  aviso: {anio} {reporteros} {flujo} {nivel}: 500 filas, puede faltar información')
    inv = {v: k for k, v in dc.M49.items()}
    return [r for r in datos if r.get('partner2Code', 0) in (0, None) and r.get('motCode', 0) in (0, None)
            and r.get('customsCode', 'C00') in ('C00', None) and r['reporterCode'] in inv and r['partnerCode'] in inv], inv


def lee(ruta):
    if not ruta.exists():
        return []
    with open(ruta, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def escribe(ruta, cabecera, filas):
    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cabecera)
        w.writerows(filas)


def composicion(grupo, a0, a1):
    previas = lee(CSV_COMP)
    hechas = {(r['exportador'], int(r['anio'])) for r in previas}
    filas = [[r[k] for k in ('exportador', 'anio', 'socio', 'seccion', 'valor_usd', 'clasificacion')] for r in previas]
    todos = dc.GRUPOS[grupo][0]
    for anio in range(a0, a1 + 1):
        faltan = [e for e in todos if (e, anio) not in hechas]
        if not faltan:
            continue
        datos, inv = comtrade(anio, faltan, ['WLD'] + todos, 'X', 'AG1')
        for r in datos:
            filas.append([inv[r['reporterCode']], anio, inv[r['partnerCode']], r['cmdCode'], f"{r['primaryValue']:.0f}",
                          'CUCI ' + revision(anio)])
        print(anio, len(datos), 'filas', flush=True)
        escribe(CSV_COMP, ['exportador', 'anio', 'socio', 'seccion', 'valor_usd', 'clasificacion'], filas)


def division68(grupo, a0, a1):
    """Exportaciones de metales no ferrosos (división 68 de la CUCI) al mundo y a cada socio: la definición de
    manufacturas de la UNCTAD (secciones 5 a 8) los excluye, y pesan mucho en los países mineros (cobre, estaño, zinc)."""
    previas = lee(CSV_68)
    hechas = {(r['exportador'], int(r['anio'])) for r in previas}
    filas = [[r[k] for k in ('exportador', 'anio', 'socio', 'valor_usd', 'clasificacion')] for r in previas]
    todos = dc.GRUPOS[grupo][0]
    for anio in range(a0, a1 + 1):
        faltan = [e for e in todos if (e, anio) not in hechas]
        if not faltan:
            continue
        datos, inv = comtrade(anio, faltan, ['WLD'] + todos, 'X', '68')
        for r in datos:
            filas.append([inv[r['reporterCode']], anio, inv[r['partnerCode']], f"{r['primaryValue']:.0f}", 'CUCI ' + revision(anio)])
        for e in faltan:   # sin fila: no exporta metales no ferrosos ese año (se anota un cero para no volver a pedirlo)
            if datos and not any(inv[r['reporterCode']] == e for r in datos):
                filas.append([e, anio, 'WLD', '0', 'CUCI ' + revision(anio)])
        print(anio, len(datos), 'filas', flush=True)
        escribe(CSV_68, ['exportador', 'anio', 'socio', 'valor_usd', 'clasificacion'], filas)


def productos(paises, anios, flujos=('X', 'M')):
    previas = lee(CSV_PROD)
    hechas = {(r['pais'], int(r['anio']), r['flujo']) for r in previas}
    filas = [[r[k] for k in ('pais', 'anio', 'flujo', 'producto', 'valor_usd', 'clasificacion')] for r in previas]
    for anio in anios:
        for pais in (paises(anio) if callable(paises) else paises):
            for flujo in flujos:
                if (pais, anio, flujo) in hechas:
                    continue
                datos, inv = comtrade(anio, [pais], ['WLD'], flujo, 'AG3')
                for r in datos:
                    filas.append([pais, anio, flujo, r['cmdCode'], f"{r['primaryValue']:.0f}", 'CUCI ' + revision(anio)])
                print(anio, pais, flujo, len(datos), 'filas', flush=True)
                escribe(CSV_PROD, ['pais', 'anio', 'flujo', 'producto', 'valor_usd', 'clasificacion'], filas)


def wdi(grupo):
    previas = lee(CSV_WDI)
    hechas = {(r['pais'], r['indicador']) for r in previas}
    filas = [[r[k] for k in ('pais', 'indicador', 'anio', 'valor')] for r in previas]
    for pais in dc.GRUPOS[grupo][0] + ['WLD']:
        for ind in WDI:
            if (pais, ind) in hechas:
                continue
            url = f'https://api.worldbank.org/v2/country/{pais}/indicator/{ind}?date=1960:2024&format=json&per_page=100'
            try:
                serie = json.loads(dc.get(url))[1] or []
            except (ValueError, IndexError):
                serie = []
            for x in serie:
                if x['value'] is not None:
                    filas.append([pais, ind, x['date'], x['value']])
            print(pais, ind, len(serie), flush=True)
            escribe(CSV_WDI, ['pais', 'indicador', 'anio', 'valor'], filas)


if __name__ == '__main__':
    g, que, *resto = sys.argv[1:]
    if que == 'composicion':
        composicion(g, int(resto[0]), int(resto[1]))
    elif que == 'division68':
        division68(g, int(resto[0]), int(resto[1]))
    elif que == 'productos':
        productos(lambda a: dc.miembros(g, a), [int(a) for a in resto])   # solo los miembros de cada año
    elif que == 'importaciones':   # mercados de referencia, solo importaciones: USA,CHN importaciones 1965 ... 2023
        productos(g.split(','), [int(a) for a in resto], ('M',))
    else:
        wdi(g)
