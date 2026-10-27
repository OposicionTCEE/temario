#!/usr/bin/env python3
"""Monta Code/datos_3B4.xlsx, el libro único con todos los datos del tema 3.B.4 (27/10/2026).

Seis hojas, en formato largo y con filtros:
  Léeme           qué hay en cada hoja y cómo se regenera.
  Fuentes         cada fuente con su código: institución, base de datos, enlace y cobertura.
  Tratamientos    cada tratamiento con su código: definición y fórmula.
  Indicadores     las series de cada panel de las figuras (Code/datos/tablas_figuras.csv).
  Cifras_citadas  cada cifra del texto con su fuente.
  Brutos          los datos descargados o transcritos, tal cual (Code/datos/*.csv).
Orden: python -I Code/datos_evidencia.py (descargas), python3 -I Code/figuras_evidencia.py (figuras y tablas),
python -I Code/libro_datos.py (este libro, con un Python que tenga openpyxl).
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

TEMA = Path(__file__).resolve().parent.parent
DATOS = TEMA / 'Code' / 'datos'
LIBRO = TEMA / 'Code' / 'datos_3B4.xlsx'

FUENTES = [  # (código, institución, base de datos, enlace, cobertura y uso)
    ('HSUS', 'U.S. Bureau of the Census', 'Historical Statistics of the United States, Colonial Times to 1970 (1975), '
     'series V 38-40, p. 914',
     'https://www2.census.gov/library/publications/1975/compendia/hist_stats_colonial-1970/hist_stats_colonial-1970p2-chV.pdf',
     'Fusiones registradas en la industria y la minería de EE. UU.: NELSON (1895-1918), EIS (1919-1930) y FTC (1919-1970). '
     'Transcritas a mano del escaneado el 27/10/2026.'),
    ('UNCTAD', 'UNCTAD', 'World Investment Report 2026, tablas anexas 5 a 8',
     'https://unctad.org/topic/investment/world-investment-report',
     'Fusiones transfronterizas netas, valor (millones de dólares) y número, por economía vendedora y compradora, 1990-2025.'),
    ('WDI', 'Banco Mundial', 'Indicadores del desarrollo mundial, CM.MKT.LCAP.CD',
     'https://data.worldbank.org/indicator/CM.MKT.LCAP.CD',
     'Capitalización bursátil de las empresas cotizadas nacionales, dólares corrientes. Consulta del 27/10/2026.'),
    ('SLOOS', 'Reserva Federal', 'Senior Loan Officer Opinion Survey, serie SUBLPDCILS_N.Q',
     'https://www.federalreserve.gov/data/sloos.htm',
     'Porcentaje neto de bancos que endurecen los criterios de los préstamos comerciales e industriales a empresas grandes '
     'y medianas, trimestral desde 1990. Consulta del 27/10/2026.'),
    ('VARIAS', '—', 'Fuentes citadas una a una', '—', 'Hoja Cifras_citadas: la fuente de cada cifra figura en su fila.'),
]

TRATAMIENTOS = [  # (código, nombre, definición)
    ('T01', 'Series históricas sin empalmar', 'NELSON (1895-1918) y FTC (1919-1970) se representan por separado: su '
     'cobertura difiere y no se empalman (GOLBE y WHITE, 1988, discuten los problemas de empalme).'),
    ('T02', 'Valor en miles de millones', 'Valor de la UNCTAD (millones de dólares) / 1.000. Número de operaciones tal cual.'),
    ('T03', 'Valor sobre capitalización', '100 × valor mundial de las fusiones transfronterizas netas (UNCTAD, vendedor) / '
     'capitalización bursátil mundial (WDI), mismo año.'),
    ('T04', 'Media anual de la SLOOS', 'Media de los cuatro trimestres del año; solo años completos.'),
    ('T05', 'Variación anual', '100 × (número del año / número del año anterior − 1), número mundial de fusiones '
     'transfronterizas netas (UNCTAD, vendedor). Panel (b) de anx_ciclo: correlación con T04 y recta de mínimos cuadrados.'),
]

CIFRAS = [  # (apartado, dato, valor, unidad, periodo, fuente)
    ('Cuerpo, 2.1', 'Respuesta de la inversión por adquisiciones a la q, frente a la interna', 2.6, 'veces', '—',
     'JOVANOVIC y ROUSSEAU (2002)'),
    ('Cuerpo, 2.1', 'Parte de los beneficios de las empresas más adquirentes', 40, '%', '1980-2020', 'ALFAGEME (2025)'),
    ('Cuerpo, 2.2', 'Despidos sobre la prima media en las tomas de control hostiles', '10-20', '%', '1984-1986',
     'BHAGAT, SHLEIFER y VISHNY (1990)'),
    ('Cuerpo, 2.2', 'Activos vendidos que acabaron en empresas similares', 72, '%', '1984-1986', 'BHAGAT, SHLEIFER y VISHNY (1990)'),
    ('Cuerpo, 2.2', 'Parte de las empresas que deben fusionarse para que la fusión sea rentable (COURNOT lineal)', 80, '%', '—',
     'SALANT, SWITZER y REYNOLDS (1983)'),
    ('Cuerpo, 2.3', 'Valor destruido por cada dólar de liquidez sobrante', 7, 'centavos', '—', 'HARFORD (1999)'),
    ('Cuerpo, 2.3', 'Operaciones con pérdidas para los accionistas en que gana el consejero delegado', 75, '%', '—',
     'HARFORD y LI (2007)'),
    ('Anexo', 'Rentabilidad anormal de la empresa comprada (tres días)', 16, '%', '1973-1998', 'ANDRADE, MITCHELL y STAFFORD (2001)'),
    ('Anexo', 'Rentabilidad anormal del comprador (tres días)', -0.7, '%', '1973-1998', 'ANDRADE, MITCHELL y STAFFORD (2001)'),
    ('Anexo', 'Rentabilidad anormal del conjunto (tres días)', 1.8, '%', '1973-1998', 'ANDRADE, MITCHELL y STAFFORD (2001)'),
    ('Anexo', 'Rentabilidad anormal de la empresa comprada (un mes)', 9, '%', '1998-2000', 'CAMPA y HERNANDO (2004)'),
    ('Anexo', 'Rentabilidad anormal de la empresa comprada', 9.13, '%', 'quinta ola', 'MARTYNOVA y RENNEBOOG (2011)'),
    ('Anexo', 'Rentabilidad anormal del comprador', 0.53, '%', 'quinta ola', 'MARTYNOVA y RENNEBOOG (2011)'),
    ('Anexo', 'Rentabilidad media del comprador en el anuncio', 1.1, '%', '1980-2001', 'MOELLER, SCHLINGEMANN y STULZ (2004)'),
    ('Anexo', 'Pérdida media del comprador por operación', -25.2, 'millones USD', '1980-2001',
     'MOELLER, SCHLINGEMANN y STULZ (2004)'),
    ('Anexo', 'Pérdida de los accionistas de los compradores', 240, 'miles de millones USD', '1998-2001',
     'MOELLER, SCHLINGEMANN y STULZ (2005)'),
    ('Anexo', 'Rentabilidad anormal a cinco años, compras con acciones', -25, '%', '1970-1989', 'LOUGHRAN y VIJH (1997)'),
    ('Anexo', 'Rentabilidad anormal a cinco años, ofertas en efectivo', 61.7, '%', '1970-1989', 'LOUGHRAN y VIJH (1997)'),
    ('Anexo', 'Caída de la cotización de Hewlett-Packard hasta la junta', -21.6, '%', '09/2001-03/2002', 'CNNMONEY (2002)'),
    ('Anexo', 'Rachas en la serie anual de fusiones (esperadas / observadas)', '23 / 5', 'rachas', '1940-1985',
     'GOLBE y WHITE (1988)'),
    ('Anexo', 'Parte del valor añadido industrial de las 200 mayores empresas', '30 / 41 / 44', '%', '1947 / 1963 / 1982',
     'GOLBE y WHITE (1988), tabla 9.2'),
    ('Anexo', 'Parte del empleo privado de las 100 mayores empresas', '18,8 / 15,1', '%', '1970 / 1984',
     'GOLBE y WHITE (1988), tabla 9.4'),
    ('Anexo', 'Parte de los activos del 1 % mayor de las sociedades', '70 / 97', '%', 'años treinta / 2018',
     'KWON, MA y ZIMMERMANN (2024)'),
    ('Anexo', 'Parte de los activos del 0,1 % mayor de las sociedades', '47 / 88', '%', 'años treinta / 2018',
     'KWON, MA y ZIMMERMANN (2024)'),
    ('Anexo', 'Cajas de ahorros (entidades o grupos)', '45 / 11', 'entidades', '2009 / 2014', 'CECA (2015)'),
    ('Anexo', 'Reducción de oficinas y de plantilla de las cajas', '36,7 / 33,4', '%', 'hasta 2014', 'CECA (2015)'),
    ('Anexo', 'Valor mundial de las operaciones anunciadas', 5.8, 'billones USD', 2021, 'REUTERS (2021), datos de Refinitiv'),
    ('Anexo', 'Valor de las operaciones en EE. UU. / capitalización (mínimos y máximos)', '2-4 / 9-12', '%', 'ciclos hasta 2015',
     'CRETIN, DIEUDONNÉ y BOUACHA (2015)'),
    ('Anexo', 'Tasa media de fracaso de las operaciones', 7, '%', 'hasta 2015', 'CRETIN, DIEUDONNÉ y BOUACHA (2015)'),
    ('Anexo', 'Correlación SLOOS / variación del número de operaciones', -0.65, '—', '1991-2025',
     'Cálculo propio (hoja Indicadores, anx_ciclo (b))'),
]

LEEME = [
    ('Qué es', 'Libro único con todos los datos del tema 3.B.4: figuras con datos del anexo de olas y evidencia y cifras citadas.'),
    ('Fuentes', 'Código, institución, base de datos, enlace y cobertura de cada fuente.'),
    ('Tratamientos', 'Código y definición de cada cálculo aplicado a los datos.'),
    ('Indicadores', 'Series de cada panel de las figuras anx_olas_datos y anx_ciclo, con su tratamiento.'),
    ('Cifras_citadas', 'Cada cifra del texto con su fuente.'),
    ('Brutos', 'Datos descargados o transcritos, tal cual (Code/datos/*.csv; los Excel de la UNCTAD, en Code/datos/unctad/).'),
    ('Cómo se regenera', 'python -I Code/datos_evidencia.py; python3 -I Code/figuras_evidencia.py; '
     'bash Code/generar_figura.sh anx_olas_datos; bash Code/generar_figura.sh anx_ciclo; python -I Code/libro_datos.py '
     '(con openpyxl).'),
]


def hoja(wb, nombre, cabecera, filas, anchos):
    ws = wb.create_sheet(nombre)
    ws.append(cabecera)
    for c in ws[1]:
        c.font = Font(bold=True)
    for f in filas:
        ws.append(list(f))
    for i, ancho in enumerate(anchos):
        ws.column_dimensions[chr(65 + i)].width = ancho
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(vertical='top', wrap_text=isinstance(c.value, str) and len(c.value) > 40)
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = 'A2'


def leer(nombre):
    with open(DATOS / nombre, encoding='utf-8') as f:
        r = csv.reader(f)
        next(r)
        return list(r)


def numero(x):
    try:
        return float(x) if '.' in x else int(x)
    except ValueError:
        return x


wb = Workbook()
wb.remove(wb.active)
hoja(wb, 'Léeme', ['Hoja', 'Contenido'], LEEME, [18, 120])
hoja(wb, 'Fuentes', ['Código', 'Institución', 'Base de datos', 'Enlace', 'Cobertura y uso'], FUENTES, [10, 24, 40, 50, 70])
hoja(wb, 'Tratamientos', ['Código', 'Nombre', 'Definición'], TRATAMIENTOS, [10, 28, 110])
fuente_figura = {'anx_olas_datos (a)': 'HSUS', 'anx_olas_datos (b)': 'UNCTAD', 'anx_olas_datos (c)': 'UNCTAD',
                 'anx_ciclo (a)': 'UNCTAD; WDI'}
indicadores = []
for figura, serie, economia, año, valor, unidad, trat in leer('tablas_figuras.csv'):
    fuente = fuente_figura.get(figura, 'SLOOS' if 'SLOOS' in serie else 'UNCTAD')
    indicadores.append((figura, serie, economia, int(año), numero(valor), unidad, fuente, trat))
hoja(wb, 'Indicadores', ['Figura', 'Serie', 'Economía', 'Año', 'Valor', 'Unidad', 'Fuente', 'Tratamiento'], indicadores,
     [20, 60, 16, 8, 12, 22, 14, 12])
hoja(wb, 'Cifras_citadas', ['Apartado', 'Dato', 'Valor', 'Unidad', 'Periodo', 'Fuente'], CIFRAS, [12, 70, 12, 20, 18, 45])
brutos = []
for f, fuente in [('hsus_fusiones_1895_1970.csv', 'HSUS'), ('unctad_fusiones.csv', 'UNCTAD'),
                  ('wdi_capitalizacion.csv', 'WDI'), ('sloos_ci_grandes.csv', 'SLOOS')]:
    with open(DATOS / f, encoding='utf-8') as fh:
        r = csv.reader(fh)
        cab = next(r)
        for fila in r:
            brutos.append((f, fuente, '; '.join(f'{c}={v}' for c, v in zip(cab, fila))))
hoja(wb, 'Brutos', ['Fichero', 'Fuente', 'Registro'], brutos, [28, 10, 110])
wb.save(LIBRO)
print('Escrito', LIBRO.relative_to(TEMA), {ws.title: ws.max_row - 1 for ws in wb.worksheets})
