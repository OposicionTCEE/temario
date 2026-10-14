#!/usr/bin/env python3
"""Descarga las exportaciones bilaterales de los miembros de un bloque y calcula su comercio intrarregional.

Fuentes (exportaciones de mercancías declaradas por el país exportador, en dólares corrientes):
  - 1962-1995: UN Comtrade, clasificación CUCI Rev. 1 (API pública de vista previa; una consulta por año),
    https://comtradeapi.un.org/public/v1/preview/C/A/S1?reporterCode=..&period=..&partnerCode=..&flowCode=X&cmdCode=TOTAL
  - 1996 en adelante: WITS (Banco Mundial), indicador XPRT-TRD-VL (miles de dólares), a partir de UN Comtrade,
    https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/<iso>/year/<año>/partner/all/product/Total/indicator/XPRT-TRD-VL?format=JSON
Un par de países que no aparece cuando el exportador sí declara se toma como comercio nulo
(por ejemplo, El Salvador-Honduras tras la guerra de 1969).
Los datos brutos se guardan en Code/datos/exportaciones_bilaterales.csv (se reutilizan: solo se descarga lo que falta).
El cuadro resultante se escribe como una hoja de Code/datos_3B35.xlsx, con la fuente en la propia hoja.

Uso, desde la carpeta del tema (necesita openpyxl: python3 -m venv /tmp/v && /tmp/v/bin/pip install openpyxl):
  /tmp/v/bin/python Code/datos_comercio.py MCCA 1962 2024
  /tmp/v/bin/python Code/datos_comercio.py CAN destinos 2023   (destino de las exportaciones de cada miembro)
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

GRUPOS = {
    # nombre: (miembros ISO3 de cualquier época, descripción)
    'MCCA': (['GTM', 'SLV', 'HND', 'NIC', 'CRI'],
             'Mercado Común Centroamericano: Guatemala, El Salvador, Honduras, Nicaragua y Costa Rica'),
    'EFTA': (['ISL', 'NOR', 'CHE'],
             'EFTA: Islandia, Noruega y Suiza (Liechtenstein comparte territorio aduanero con Suiza y no declara por separado)'),
    'CAN': (['BOL', 'COL', 'ECU', 'PER', 'CHL', 'VEN'],
            'Comunidad Andina (Pacto Andino hasta 1996): Bolivia, Colombia, Ecuador y Perú; Chile hasta 1976; Venezuela de 1973 a 2006'),
    'MERCOSUR': (['ARG', 'BRA', 'PRY', 'URY', 'VEN'],
                 'MERCOSUR: Argentina, Brasil, Paraguay y Uruguay; Venezuela de 2012 a 2016 (suspendida desde entonces); '
                 'Bolivia, miembro desde 2024, aún sin datos (la serie empieza antes del Tratado de Asunción)'),
    'NAFTA': (['USA', 'CAN', 'MEX'], 'NAFTA/USMCA: Estados Unidos, Canadá y México (la serie empieza antes del acuerdo, para ver su efecto)'),
    'CEFTA': (['ALB', 'BIH', 'MKD', 'MNE', 'SRB', 'MDA'],
              'CEFTA 2006: Albania, Bosnia y Herzegovina, Macedonia del Norte, Montenegro, Serbia y Moldavia '
              '(Kosovo, representado por la UNMIK, no declara su comercio a UN Comtrade; Croacia salió en 2013)'),
}
# Años de pertenencia cuando no coinciden con los de todo el bloque (los demás miembros cuentan siempre)
PERIODOS = {
    'CAN': {'CHL': (1969, 1976), 'VEN': (1973, 2006)},
    'MERCOSUR': {'VEN': (2012, 2016)},
}
M49 = {'GTM': 320, 'SLV': 222, 'HND': 340, 'NIC': 558, 'CRI': 188, 'PAN': 591,
       'BOL': 68, 'COL': 170, 'ECU': 218, 'PER': 604, 'CHL': 152, 'VEN': 862,
       'USA': 842, 'CAN': 124, 'MEX': 484, 'CHN': 156, 'ARG': 32, 'BRA': 76, 'PRY': 600, 'URY': 858, 'WLD': 0,
       'ALB': 8, 'BIH': 70, 'MKD': 807, 'MNE': 499, 'SRB': 688, 'MDA': 498}
# Estados miembros de la UE (27) para agregar el destino UE con WITS, que no da el agregado
UE27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL',
        'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']


def miembros(grupo, anio):
    """Miembros del bloque en un año dado."""
    per = PERIODOS.get(grupo, {})
    return [e for e in GRUPOS[grupo][0] if per.get(e, (0, 9999))[0] <= anio <= per.get(e, (0, 9999))[1]]
CORTE = 1996  # desde este año, WITS (no tiene 1994-1995 para estos países); antes, Comtrade CUCI Rev. 1

TEMA = Path(__file__).resolve().parent.parent
CSV = TEMA / 'Code' / 'datos' / 'exportaciones_bilaterales.csv'
XLSX = TEMA / 'Code' / 'datos_3B35.xlsx'
FUENTE_CT = 'UN Comtrade (CUCI Rev. 1)'
FUENTE_WITS = 'WITS (Banco Mundial) a partir de UN Comtrade'
FUENTE_CT_SA = 'UN Comtrade (SA), cuando WITS no tiene el país (Serbia, Montenegro)'


def lee_csv():
    filas = {}
    if CSV.exists():
        with open(CSV, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                filas[(r['exportador'], int(r['anio']), r['socio'])] = (float(r['valor_usd']), r['fuente'])
    return filas


def guarda_csv(filas):
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exportador', 'anio', 'socio', 'valor_usd', 'fuente'])
        for (e, a, s), (v, fu) in sorted(filas.items()):
            w.writerow([e, a, s, f'{v:.0f}', fu])


def get(url):
    for intento in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh) datos_comercio.py'})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode('utf-8')
        except Exception:
            time.sleep(5 * (intento + 1))
    return ''


def comtrade(exportadores, anio, socios):
    """Una consulta por año para todos los exportadores; devuelve {exportador: {socio: valor}} o None."""
    url = ('https://comtradeapi.un.org/public/v1/preview/C/A/S1?reporterCode=%s&period=%d&partnerCode=%s'
           '&flowCode=X&cmdCode=TOTAL' % (','.join(str(M49[e]) for e in exportadores), anio,
                                          ','.join(str(M49[s]) for s in socios)))
    texto = get(url)
    inv = {v: k for k, v in M49.items()}
    try:
        datos = json.loads(texto).get('data', [])
    except ValueError:
        return None
    out = {}
    for r in datos:
        if r['reporterCode'] in inv and r['partnerCode'] in inv:
            out.setdefault(inv[r['reporterCode']], {})[inv[r['partnerCode']]] = r['primaryValue']
    return out


def wits(exportador, anio, socios=None):
    """Exportaciones de un país a sus socios en un año (dólares); con socios=None, a todos."""
    url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/%s/year/%d/partner/all'
           '/product/Total/indicator/XPRT-TRD-VL?format=JSON' % (exportador.lower(), anio))
    texto = get(url)
    try:
        d = json.loads(texto)
    except ValueError:
        return {}
    dims = d['structure']['dimensions']['series']
    ip = [i for i, x in enumerate(dims) if x['id'] == 'PARTNER'][0]
    valores = dims[ip]['values']
    out = {}
    for clave, serie in d['dataSets'][0]['series'].items():
        socio = valores[int(clave.split(':')[ip])]['id']
        if socios is None or socio in socios:
            out[socio] = serie['observations']['0'][0] * 1000.0  # miles de dólares -> dólares
    return out


def descarga(grupo, a0, a1):
    socios = GRUPOS[grupo][0] + ['WLD']
    filas = lee_csv()
    for anio in range(a0, a1 + 1):
        pendientes = [e for e in miembros(grupo, anio) if (e, anio, 'WLD') not in filas]
        if not pendientes:
            continue
        if anio < CORTE:
            res = comtrade(pendientes, anio, socios)
            time.sleep(4)
            if res is None:
                print('sin respuesta', anio, flush=True)
                continue
            fuente = FUENTE_CT
        else:
            res, fuente = {}, FUENTE_WITS
            for e in pendientes:
                res[e] = wits(e, anio, socios)
                time.sleep(0.5)
        for e in pendientes:
            r = res.get(e, {})
            if not r.get('WLD'):
                print(anio, e, 'sin datos', flush=True)
                continue
            for s in socios:
                if s != e:
                    filas[(e, anio, s)] = (r.get(s, 0.0), fuente)
            print(anio, e, 'ok', flush=True)
        guarda_csv(filas)
    return filas


def cuadro(grupo, a0, a1, filas):
    out = []
    for anio in range(a0, a1 + 1):
        intra = total = 0.0
        con = []
        mm = miembros(grupo, anio)
        for e in mm:
            w = filas.get((e, anio, 'WLD'), (0.0, ''))[0]
            if not w:
                continue
            con.append(e)
            total += w
            intra += sum(filas.get((e, anio, s), (0.0, ''))[0] for s in mm if s != e)
        cuota = 100 * intra / total if total and len(con) == len(mm) else None
        out.append((anio, intra / 1e6, total / 1e6, cuota, len(con), ', '.join(sorted(set(mm) - set(con)))))
    return out


def escribe_hoja(grupo, filas_cuadro):
    from openpyxl import Workbook, load_workbook
    wb = load_workbook(XLSX) if XLSX.exists() else Workbook()
    if wb.sheetnames == ['Sheet']:
        del wb['Sheet']
    nombre = f'{grupo}_intrarregional'
    if nombre in wb.sheetnames:
        del wb[nombre]
    ws = wb.create_sheet(nombre)
    ws.append([f'Exportaciones intrarregionales del {grupo}: {GRUPOS[grupo][1]}'])
    ws.append([f'Fuente: {FUENTE_CT} (1962-{CORTE - 1}) y {FUENTE_WITS} (desde {CORTE}); exportaciones declaradas '
               'por el exportador, dólares corrientes. Cálculo propio (Code/datos_comercio.py).'])
    ws.append(['La cuota solo se calcula cuando declaran todos los miembros; si falta alguno, se deja vacía.'])
    ws.append([])
    ws.append(['Año', 'Exportaciones intrarregionales (millones USD)', 'Exportaciones totales (millones USD)',
               'Cuota intrarregional (%)', 'Miembros con datos', 'Faltan'])
    for f in filas_cuadro:
        ws.append([f[0], round(f[1], 1), round(f[2], 1), None if f[3] is None else round(f[3], 2), f[4], f[5]])
    wb.save(XLSX)


def destinos(grupo, anio):
    """Destino de las exportaciones de cada miembro actual en un año: bloque, EE. UU., China, UE-27, Reino Unido y resto.
    Guarda los datos brutos por socio en Code/datos/destinos.csv y el resumen en la hoja <GRUPO>_destinos_<año>."""
    ruta = TEMA / 'Code' / 'datos' / 'destinos.csv'
    brutos = {}
    if ruta.exists():
        with open(ruta, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                brutos[(r['exportador'], int(r['anio']), r['socio'])] = float(r['valor_usd'])
    mm = miembros(grupo, anio)
    for e in mm:
        if (e, anio, 'WLD') not in brutos:
            for socio, v in wits(e, anio).items():
                brutos[(e, anio, socio)] = v
            time.sleep(0.5)
    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exportador', 'anio', 'socio', 'valor_usd', 'fuente'])
        for (e, a, so), v in sorted(brutos.items()):
            w.writerow([e, a, so, f'{v:.0f}', FUENTE_WITS])
    resumen = []
    for e in mm:
        tot = brutos.get((e, anio, 'WLD'), 0.0)
        if not tot:
            resumen.append((e, None, None, None, None, None, None))
            continue
        blo = sum(brutos.get((e, anio, s), 0.0) for s in mm if s != e)
        usa = brutos.get((e, anio, 'USA'), 0.0)
        chn = brutos.get((e, anio, 'CHN'), 0.0)
        ue = sum(brutos.get((e, anio, s), 0.0) for s in UE27)
        gbr = brutos.get((e, anio, 'GBR'), 0.0)
        resumen.append((e, 100 * blo / tot, 100 * usa / tot, 100 * chn / tot, 100 * ue / tot,
                        100 * (tot - blo - usa - chn - ue - gbr) / tot, 100 * gbr / tot))
    from openpyxl import Workbook, load_workbook
    wb = load_workbook(XLSX) if XLSX.exists() else Workbook()
    nombre = f'{grupo}_destinos_{anio}'
    if nombre in wb.sheetnames:
        del wb[nombre]
    ws = wb.create_sheet(nombre)
    ws.append([f'Destino de las exportaciones de mercancías de los miembros del {grupo} en {anio} (% del total)'])
    ws.append([f'Fuente: {FUENTE_WITS}; UE = suma de los 27 Estados miembros. Cálculo propio (Code/datos_comercio.py); '
               'datos brutos por socio en Code/datos/destinos.csv.'])
    ws.append([])
    ws.append(['Exportador', f'{grupo} (resto de miembros)', 'EE. UU.', 'China', 'UE-27', 'Resto del mundo (sin Reino Unido)', 'Reino Unido'])
    for fila in resumen:
        ws.append([fila[0]] + [None if x is None else round(x, 2) for x in fila[1:]])
    wb.save(XLSX)
    return resumen


def importaciones(importador, a0, a1, socios):
    """Importaciones de mercancías declaradas por un país desde varios socios (WITS, MPRT-TRD-VL), con hoja propia."""
    filas = []
    for anio in range(a0, a1 + 1):
        url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/%s/year/%d/partner/all'
               '/product/Total/indicator/MPRT-TRD-VL?format=JSON' % (importador.lower(), anio))
        try:
            d = json.loads(get(url))
        except ValueError:
            print(anio, 'sin datos', flush=True)
            continue
        dims = d['structure']['dimensions']['series']
        ip = [i for i, x in enumerate(dims) if x['id'] == 'PARTNER'][0]
        valores = dims[ip]['values']
        v = {}
        for clave, serie in d['dataSets'][0]['series'].items():
            v[valores[int(clave.split(':')[ip])]['id']] = serie['observations']['0'][0] * 1000.0
        filas.append([anio] + [round(v.get(s, 0.0) / 1e6, 1) for s in socios + ['WLD']])
        print(anio, 'ok', flush=True)
        time.sleep(0.5)
    from openpyxl import Workbook, load_workbook
    wb = load_workbook(XLSX) if XLSX.exists() else Workbook()
    nombre = f'{importador}_importaciones'
    if nombre in wb.sheetnames:
        del wb[nombre]
    ws = wb.create_sheet(nombre)
    ws.append([f'Importaciones de mercancías de {importador} por origen (millones de dólares corrientes)'])
    ws.append([f'Fuente: {FUENTE_WITS}, indicador MPRT-TRD-VL (importaciones declaradas por el importador). '
               'Cálculo propio (Code/datos_comercio.py).'])
    ws.append([])
    ws.append(['Año'] + socios + ['Total (WLD)'])
    for f in filas:
        ws.append(f)
    wb.save(XLSX)
    return filas


def escribe_brutos():
    """Copia los datos brutos del CSV en la hoja Exportaciones_bilaterales del Excel, con su fuente."""
    from openpyxl import Workbook, load_workbook
    wb = load_workbook(XLSX) if XLSX.exists() else Workbook()
    if wb.sheetnames == ['Sheet']:
        del wb['Sheet']
    if 'Exportaciones_bilaterales' in wb.sheetnames:
        del wb['Exportaciones_bilaterales']
    ws = wb.create_sheet('Exportaciones_bilaterales')
    ws.append(['Exportaciones bilaterales de mercancías declaradas por el exportador (dólares corrientes).'])
    ws.append([f'Fuente: {FUENTE_CT} hasta {CORTE - 1}; {FUENTE_WITS} desde {CORTE}. Socio WLD = total mundial.'])
    ws.append([])
    ws.append(['Exportador', 'Año', 'Socio', 'Valor (USD)', 'Fuente'])
    for (e, a, so), (v, fu) in sorted(lee_csv().items()):
        ws.append([e, a, so, round(v), fu])
    wb.save(XLSX)


if __name__ == '__main__':
    if len(sys.argv) == 6 and sys.argv[2] == 'importaciones':   # p. ej.: USA importaciones 1994 2024 MEX,CAN,CHN
        for fila in importaciones(sys.argv[1], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5].split(',')):
            print(fila)
        sys.exit()
    if len(sys.argv) == 4 and sys.argv[2] == 'destinos':
        for fila in destinos(sys.argv[1], int(sys.argv[3])):
            print(fila)
        sys.exit()
    g, a0, a1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    filas = descarga(g, a0, a1)
    c = cuadro(g, a0, a1, filas)
    for f in c:
        print(f[0], None if f[3] is None else round(f[3], 1), f[4], f[5])
    try:
        escribe_hoja(g, c)
        escribe_brutos()
        print('Hoja escrita en', XLSX)
    except ImportError:
        print('Falta openpyxl: no se escribe el Excel')
