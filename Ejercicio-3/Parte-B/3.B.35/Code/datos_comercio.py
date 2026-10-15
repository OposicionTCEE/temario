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
import urllib.error
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
    'AFCFTA': (['DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CPV', 'CMR', 'CAF', 'TCD', 'COM', 'COG', 'COD', 'CIV', 'DJI',
                'EGY', 'GNQ', 'SWZ', 'ETH', 'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO', 'LBR', 'LBY', 'MDG', 'MWI',
                'MLI', 'MRT', 'MUS', 'MAR', 'MOZ', 'NAM', 'NER', 'NGA', 'RWA', 'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF',
                'SSD', 'SDN', 'TZA', 'TGO', 'TUN', 'UGA', 'ZMB', 'ZWE'],
               'AfCFTA: los 54 signatarios (todos los miembros de la Unión Africana salvo Eritrea), sin la República Árabe Saharaui '
               'Democrática, sin datos de comercio. Muchos países no declaran todos los años: la cuota se calcula sobre los que '
               'declaran (columna Miembros con datos), con su comercio hacia todos los miembros, declaren o no'),
    'ASEAN': (['IDN', 'MYS', 'PHL', 'SGP', 'THA', 'BRN', 'VNM', 'LAO', 'MMR', 'KHM', 'TLS'],
              'ASEAN: Indonesia, Malasia, Filipinas, Singapur y Tailandia (1967); Brunéi (1984), Vietnam (1995), Laos y '
              'Myanmar (1997), Camboya (1999) y Timor Oriental (2025)'),
    'PAFTA': (['ARE', 'BHR', 'KWT', 'OMN', 'QAT', 'SAU', 'EGY', 'IRQ', 'JOR', 'LBN', 'PSE', 'SYR', 'SDN', 'YEM',
               'DZA', 'LBY', 'MAR', 'TUN'],
              'Zona de Libre Comercio Pan-Árabe (GAFTA): los 18 miembros actuales; Argelia desde 2009 y el resto desde 1998 '
              '(simplificación: Sudán, Yemen y Palestina se incorporaron más tarde). Muchos no declaran todos los años: '
              'la cuota se calcula con los que declaran'),
    'UEE': (['RUS', 'BLR', 'KAZ', 'ARM', 'KGZ'],
            'Unión Económica Euroasiática (composición actual): Rusia, Bielorrusia, Kazajistán, Armenia y Kirguistán. '
            'Rusia y Bielorrusia no publican su comercio desde 2022'),
    'RCEP': (['BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'THA', 'VNM', 'CHN', 'JPN', 'KOR', 'AUS', 'NZL'],
             'RCEP: los diez miembros de la ASEAN anteriores a 2025, China, Japón, Corea del Sur, Australia y Nueva Zelanda'),
    'CPTPP': (['AUS', 'BRN', 'CAN', 'CHL', 'JPN', 'MYS', 'MEX', 'NZL', 'PER', 'SGP', 'VNM', 'GBR'],
              'CPTPP: composición actual, con Reino Unido (miembro desde diciembre de 2024)'),
    'UE27': (['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA',
              'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE'],
             'UE-27 (composición actual, solo como referencia de comparación)'),
}
# Bloques con muchos miembros que no declaran: la cuota se calcula con los que declaran
PARCIALES = {'AFCFTA', 'PAFTA', 'ASEAN'}
# Años de pertenencia cuando no coinciden con los de todo el bloque (los demás miembros cuentan siempre)
PERIODOS = {
    'CAN': {'CHL': (1969, 1976), 'VEN': (1973, 2006)},
    'MERCOSUR': {'VEN': (2012, 2016)},
    'ASEAN': {'BRN': (1984, 9999), 'VNM': (1995, 9999), 'LAO': (1997, 9999), 'MMR': (1997, 9999), 'KHM': (1999, 9999),
              'TLS': (2025, 9999)},
    'PAFTA': {'DZA': (2009, 9999)},
}
M49 = {'GTM': 320, 'SLV': 222, 'HND': 340, 'NIC': 558, 'CRI': 188, 'PAN': 591,
       'BOL': 68, 'COL': 170, 'ECU': 218, 'PER': 604, 'CHL': 152, 'VEN': 862,
       'USA': 842, 'CAN': 124, 'MEX': 484, 'CHN': 156, 'ARG': 32, 'BRA': 76, 'PRY': 600, 'URY': 858, 'WLD': 0,
       'ALB': 8, 'BIH': 70, 'MKD': 807, 'MNE': 499, 'SRB': 688, 'MDA': 498,
       'IDN': 360, 'MYS': 458, 'PHL': 608, 'SGP': 702, 'THA': 764, 'BRN': 96, 'VNM': 704, 'LAO': 418, 'MMR': 104,
       'KHM': 116, 'TLS': 626}
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
XLSX = TEMA / 'Code' / 'datos' / 'tablas_figuras.xlsx'   # tablas de cada figura; el libro final lo monta Code/libro_datos.py
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
        except urllib.error.HTTPError as err:
            if err.code == 404:   # WITS: el país no declara ese año; no tiene sentido reintentar
                return ''
            time.sleep(5 * (intento + 1))
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


# WITS usa códigos propios para algunos países (Rumanía es ROM, Serbia SER...): se traducen a ISO3
WITS_ISO = {'ROM': 'ROU', 'SER': 'SRB', 'MNT': 'MNE', 'ZAR': 'COD', 'TMP': 'TLS', 'SUD': 'SDN'}
ISO_WITS = {v: k for k, v in WITS_ISO.items()}


def iso(codigo):
    return WITS_ISO.get(codigo, codigo)


def wits(exportador, anio, socios=None):
    """Exportaciones de un país a sus socios en un año (dólares); con socios=None, a todos. Códigos ISO3 en entrada y salida."""
    url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/%s/year/%d/partner/all'
           '/product/Total/indicator/XPRT-TRD-VL?format=JSON' % (ISO_WITS.get(exportador, exportador).lower(), anio))
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
        socio = iso(valores[int(clave.split(':')[ip])]['id'])
        if socios is None or socio in socios:
            out[socio] = out.get(socio, 0.0) + serie['observations']['0'][0] * 1000.0  # miles de dólares -> dólares
    return out


def comtrade_sa(exportador, anio, socios=None):
    """Alternativa a WITS: exportaciones de un país a todos sus socios en clasificación SA (UN Comtrade, vista previa).
    Los códigos M49 de los socios se traducen a ISO3 con la tabla de referencia de Comtrade (guardada en Code/datos/)."""
    ref = TEMA / 'Code' / 'datos' / 'comtrade_socios.json'
    if not ref.exists():
        ref.write_text(get('https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json'), encoding='utf-8')
    iso = {r['PartnerCode']: r.get('PartnerCodeIsoAlpha3') for r in json.loads(ref.read_text(encoding='utf-8'))['results']}
    iso[0] = 'WLD'
    url = ('https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=%d&period=%d&flowCode=X&cmdCode=TOTAL'
           % (M49[exportador], anio))
    time.sleep(4)
    try:
        datos = json.loads(get(url)).get('data', [])
    except ValueError:
        return {}
    out = {}
    for r in datos:
        if r.get('partner2Code', 0) != 0 or r.get('motCode', 0) != 0 or r.get('customsCode', 'C00') != 'C00':
            continue
        socio = iso.get(r['partnerCode'])
        if socio and (socios is None or socio in socios):
            out[socio] = out.get(socio, 0.0) + r['primaryValue']
    return out


def por_socio(exportador, anio, socios=None):
    """WITS y, si no tiene el país, UN Comtrade (SA). Devuelve (valores por socio, fuente)."""
    r = wits(exportador, anio, socios)
    if r.get('WLD') or exportador not in M49:
        return r, FUENTE_WITS
    return comtrade_sa(exportador, anio, socios), FUENTE_CT_SA


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
            res, fuentes = {}, {}
            from concurrent.futures import ThreadPoolExecutor   # varias consultas a la vez: WITS tarda unos 5 s en cada una
            with ThreadPoolExecutor(max_workers=6) as ex:
                for e, (r, fu) in zip(pendientes, ex.map(lambda p: por_socio(p, anio, socios), pendientes)):
                    res[e], fuentes[e] = r, fu
        for e in pendientes:
            if anio >= CORTE:
                fuente = fuentes[e]
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
        completo = len(con) == len(mm) or (grupo in PARCIALES and len(con) >= len(mm) / 2)
        cuota = 100 * intra / total if total and completo else None
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
    brutos, fuentes = {}, {}
    if ruta.exists():
        with open(ruta, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                brutos[(r['exportador'], int(r['anio']), r['socio'])] = float(r['valor_usd'])
                fuentes[(r['exportador'], int(r['anio']))] = r['fuente']
    mm = miembros(grupo, anio)
    for e in mm:
        if (e, anio, 'WLD') not in brutos:
            valores, fuentes[(e, anio)] = por_socio(e, anio)
            for socio, v in valores.items():
                brutos[(e, anio, socio)] = v
            time.sleep(0.5)
    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exportador', 'anio', 'socio', 'valor_usd', 'fuente'])
        for (e, a, so), v in sorted(brutos.items()):
            w.writerow([e, a, so, f'{v:.0f}', fuentes.get((e, a), FUENTE_WITS)])
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


ESPEJO = TEMA / 'Code' / 'datos' / 'espejo.csv'
FUENTE_ESPEJO = ('WITS (Banco Mundial), indicador MPRT-TRD-VL: importaciones declaradas por cada país desde el exportador '
                 '(datos espejo, en dólares, valor CIF)')


def espejo(grupo, a0, a1):
    """Datos espejo: importaciones que todos los países declaran desde cada miembro del grupo (una consulta por
    exportador y año, con reporter=all). Sirven cuando los exportadores no declaran o declaran sin destino, como el
    petróleo del Golfo. Se guardan en Code/datos/espejo.csv (exportador, año, importador, valor); el importador WLD
    es la suma de todos los que declaran."""
    filas = {}
    if ESPEJO.exists():
        with open(ESPEJO, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                filas[(r['exportador'], int(r['anio']), r['importador'])] = float(r['valor_usd'])
    hechos = {(e, a) for (e, a, i) in filas}

    def una(par):
        e, anio = par
        url = ('https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/all/year/%d/partner/%s'
               '/product/Total/indicator/MPRT-TRD-VL?format=JSON' % (anio, ISO_WITS.get(e, e).lower()))
        try:
            d = json.loads(get(url))
        except ValueError:
            return par, {}
        dims = d['structure']['dimensions']['series']
        ir = [i for i, x in enumerate(dims) if x['id'] == 'REPORTER'][0]
        valores = dims[ir]['values']
        out = {}
        for clave, serie in d['dataSets'][0]['series'].items():
            imp = iso(valores[int(clave.split(':')[ir])]['id'])
            out[imp] = out.get(imp, 0.0) + serie['observations']['0'][0] * 1000.0
        return par, out

    from concurrent.futures import ThreadPoolExecutor
    pendientes = [(e, a) for a in range(a0, a1 + 1) for e in miembros(grupo, a) if (e, a) not in hechos]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for (e, a), out in ex.map(una, pendientes):
            print(a, e, 'ok' if out.get('WLD') else 'sin datos', flush=True)
            for imp, v in out.items():
                filas[(e, a, imp)] = v
    with open(ESPEJO, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exportador', 'anio', 'importador', 'valor_usd', 'fuente'])
        for (e, a, i), v in sorted(filas.items()):
            w.writerow([e, a, i, f'{v:.0f}', FUENTE_ESPEJO])
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
    if len(sys.argv) == 5 and sys.argv[2] == 'espejo':   # p. ej.: PAFTA espejo 1998 2023
        espejo(sys.argv[1], int(sys.argv[3]), int(sys.argv[4]))
        sys.exit()
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
