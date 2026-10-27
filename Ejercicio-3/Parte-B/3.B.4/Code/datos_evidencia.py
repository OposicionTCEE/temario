#!/usr/bin/env python3
"""Descarga y prepara los datos del anexo de olas y evidencia del tema 3.B.4 (27/10/2026).

Escribe en Code/datos/ cuatro CSV en formato largo, que leen Code/figuras_evidencia.py y Code/libro_datos.py:
  hsus_fusiones_1895_1970.csv  fusiones registradas en la industria y la minería de EE. UU., series V 38-40 de
                               Historical Statistics of the United States (1975), p. 914, transcritas a mano del
                               escaneado: NELSON (1895-1918), FTC (1919-1970) y EIS (1919-1930).
  unctad_fusiones.csv          fusiones transfronterizas netas (valor y número, por vendedor y por comprador),
                               tablas anexas 5 a 8 del World Investment Report 2026 de la UNCTAD (1990-2025).
  wdi_capitalizacion.csv       capitalización bursátil de las empresas cotizadas nacionales (dólares corrientes),
                               Banco Mundial, WDI (CM.MKT.LCAP.CD).
  sloos_ci_grandes.csv         porcentaje neto de bancos de EE. UU. que endurecen los criterios de los préstamos
                               comerciales e industriales a empresas grandes y medianas (SLOOS, serie SUBLPDCILS_N.Q).
Los ficheros de la UNCTAD se guardan tal cual en Code/datos/unctad/.
Uso, desde la carpeta del tema, con un Python que tenga openpyxl:  python -I Code/datos_evidencia.py
"""
import csv
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

from openpyxl import load_workbook

TEMA = Path(__file__).resolve().parent.parent
DATOS = TEMA / 'Code' / 'datos'
UNCTAD = DATOS / 'unctad'
AGENTE = {'User-Agent': 'Mozilla/5.0'}

# Historical Statistics of the United States, Colonial Times to 1970 (1975), serie V 38 (FTC), V 39-40 (NELSON y EIS).
# (año, número, valor en millones de dólares o None)
NELSON = [(1895, 43, 41), (1896, 26, 25), (1897, 69, 120), (1898, 303, 651), (1899, 1208, 2263), (1900, 340, 442),
          (1901, 423, 2053), (1902, 379, 911), (1903, 142, 298), (1904, 79, 110), (1905, 226, 243), (1906, 128, 378),
          (1907, 87, 185), (1908, 50, 188), (1909, 49, 89), (1910, 142, 257), (1911, 103, 210), (1912, 82, 322),
          (1913, 85, 176), (1914, 39, 160), (1915, 71, 158), (1916, 117, 470), (1917, 195, 679), (1918, 71, 254)]
EIS = [(1919, 159, 777), (1920, 163, 809), (1921, 70, 430), (1922, 122, 502), (1923, 143, 1171), (1924, 149, 466),
       (1925, 257, 721), (1926, 265, 1135), (1927, 306, 727), (1928, 507, 1653), (1929, 587, 1993), (1930, 281, 1757)]
FTC = [(1919, 438), (1920, 760), (1921, 487), (1922, 309), (1923, 311), (1924, 368), (1925, 554), (1926, 856),
       (1927, 870), (1928, 1058), (1929, 1245), (1930, 799), (1931, 464), (1932, 203), (1933, 120), (1934, 101),
       (1935, 130), (1936, 126), (1937, 124), (1938, 110), (1939, 87), (1940, 140), (1941, 111), (1942, 118),
       (1943, 213), (1944, 324), (1945, 333), (1946, 419), (1947, 404), (1948, 223), (1949, 126), (1950, 219),
       (1951, 235), (1952, 288), (1953, 295), (1954, 387), (1955, 683), (1956, 673), (1957, 585), (1958, 589),
       (1959, 835), (1960, 844), (1961, 954), (1962, 853), (1963, 861), (1964, 854), (1965, 1008), (1966, 995),
       (1967, 1496), (1968, 2407), (1969, 2307), (1970, 1351)]

TABLAS_UNCTAD = {  # tabla: (lado, indicador, unidad)
    '05': ('vendedor', 'valor', 'millones USD'), '06': ('comprador', 'valor', 'millones USD'),
    '07': ('vendedor', 'número', 'operaciones'), '08': ('comprador', 'número', 'operaciones')}
ECONOMIAS = {'World': 'Mundo', 'European Union': 'Unión Europea', 'United States': 'Estados Unidos', 'Spain': 'España'}


def bajar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENTE), timeout=120) as r:
        return r.read()


def escribir(nombre, cabecera, filas):
    with open(DATOS / nombre, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cabecera)
        w.writerows(filas)
    print('Escrito', nombre, len(filas), 'filas')


def hsus():
    filas = [('NELSON', a, n, v) for a, n, v in NELSON] + [('EIS', a, n, v) for a, n, v in EIS]
    filas += [('FTC', a, n, '') for a, n in FTC]
    escribir('hsus_fusiones_1895_1970.csv', ['serie', 'año', 'número', 'valor_millones_usd'], filas)


def unctad():
    UNCTAD.mkdir(parents=True, exist_ok=True)
    filas = []
    for t, (lado, indicador, unidad) in TABLAS_UNCTAD.items():
        fichero = UNCTAD / f'wir26_tab{t}.xlsx'
        if not fichero.exists():
            fichero.write_bytes(bajar(f'https://unctad.org/system/files/non-official-document/wir26_tab{t}.xlsx'))
        ws = load_workbook(fichero, data_only=True).worksheets[0]
        años = None
        for r in ws.iter_rows(values_only=True):
            nombre = str(r[0]).strip() if r[0] else ''
            if 'Region/economy' in nombre:
                años = [int(a) for a in r[1:] if isinstance(a, int)]
            elif años and nombre in ECONOMIAS:
                for a, v in zip(años, r[1:1 + len(años)]):
                    if isinstance(v, (int, float)):
                        filas.append((ECONOMIAS[nombre], lado, indicador, a, round(v, 3), unidad))
    escribir('unctad_fusiones.csv', ['economía', 'lado', 'indicador', 'año', 'valor', 'unidad'], filas)


def capitalizacion():
    url = 'https://api.worldbank.org/v2/country/WLD;USA;ESP/indicator/CM.MKT.LCAP.CD?format=json&per_page=300'
    datos = json.loads(bajar(url))[1]
    nombres = {'WLD': 'Mundo', 'USA': 'Estados Unidos', 'ESP': 'España'}
    filas = sorted((nombres[d['countryiso3code']], int(d['date']), d['value'])
                   for d in datos if d['value'] is not None)
    escribir('wdi_capitalizacion.csv', ['economía', 'año', 'valor_usd'], filas)


def sloos():
    z = zipfile.ZipFile(io.BytesIO(bajar('https://www.federalreserve.gov/releases/sloos/data/FRB_SLOOS_xml.zip')))
    xml = z.read('SLOOS_data.xml').decode('utf-8')
    i = xml.find('SERIES_NAME="SUBLPDCILS_N.Q"')
    bloque = xml[xml.rfind('<kf:Series', 0, i):xml.find('</kf:Series>', i)]
    obs = re.findall(r'OBS_VALUE="([^"]*)"[^>]*TIME_PERIOD="([^"]*)"', bloque)
    escribir('sloos_ci_grandes.csv', ['fecha', 'porcentaje_neto'], [(t, float(v)) for v, t in obs])


if __name__ == '__main__':
    DATOS.mkdir(parents=True, exist_ok=True)
    hsus()
    unctad()
    capitalizacion()
    sloos()
