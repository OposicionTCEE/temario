#!/usr/bin/env python3
"""Monta Code/datos_3B35.xlsx, el libro único con todos los datos del tema 3.B.35 (petición del usuario, 15/10/2026).

Siete hojas, todas en formato largo y con filtros, para buscar por proyecto, país, indicador, serie o tratamiento:
  Léeme           qué hay en cada hoja, cómo se regenera y qué script hace cada figura.
  Fuentes         cada fuente con su código: institución, base de datos, enlace y cobertura.
  Tratamientos    cada tratamiento con su código: definición, fórmula, exclusiones.
  Indicadores     todas las series de las figuras y de los cuadros: proyecto, país, socio o desglose, indicador,
                  serie, año, valor, unidad, fuente, tratamiento y figura donde se usa.
  Cifras_citadas  cada cifra del texto con su fuente (Code/cifras_citadas.py).
  Comercio_bruto  los datos de comercio descargados, tal cual (UN Comtrade y WITS).
  Otros_brutos    los demás datos descargados, tal cual (Banco Mundial, aranceles de WITS, OCDE, SIPRI).
Las tablas de cada figura las escriben sus scripts en Code/datos/tablas_figuras.xlsx (fichero intermedio); los datos
brutos están en los CSV de Code/datos/. Este script lo reúne todo; hay que volver a ejecutarlo tras cambiar una figura.
Uso, desde la carpeta del tema:  /ruta/a/python-con-openpyxl Code/libro_datos.py
"""
import csv
import re
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import indicadores_bloque as ib  # noqa: E402

TEMA = dc.TEMA
DATOS = TEMA / 'Code' / 'datos'
TABLAS = DATOS / 'tablas_figuras.xlsx'
LIBRO = TEMA / 'Code' / 'datos_3B35.xlsx'

FUENTES = [  # (código, institución, base de datos, enlace, cobertura y uso)
    ('COMTRADE', 'Naciones Unidas', 'UN Comtrade, API pública de vista previa', 'https://comtradeapi.un.org',
     'Comercio de mercancías por socio y producto (CUCI Rev. 1 hasta 1995, Rev. 3 de 1996 a 2006 y Rev. 4 desde 2007); '
     'comercio total de 1962 a 1995. Consultada en octubre de 2026.'),
    ('COMTRADE_SA', 'Naciones Unidas', 'UN Comtrade, clasificación SA', 'https://comtradeapi.un.org',
     'Comercio total cuando WITS no tiene el país (Serbia, Montenegro).'),
    ('WITS', 'Banco Mundial', 'World Integrated Trade Solution (WITS), estadísticas de comercio', 'https://wits.worldbank.org',
     'Comercio de mercancías por socio y grupo de productos, a partir de UN Comtrade, desde 1996. Consultada en octubre de 2026.'),
    ('WITS_ESPEJO', 'Banco Mundial', 'WITS, importaciones declaradas por los socios (datos espejo)', 'https://wits.worldbank.org',
     'Importaciones de cada país desde un exportador (CIF), para exportadores que declaran sin destino (petróleo del Golfo, Rusia).'),
    ('WDI', 'Banco Mundial', 'Indicadores del Desarrollo Mundial (WDI)', 'https://data.worldbank.org',
     'PIB, PIB per cápita (dólares constantes de 2015 y PPA de 2021), importaciones de mercancías, población.'),
    ('OCDE_PSE', 'OCDE', 'Agricultural Policy Monitoring and Evaluation: Producer Support Estimate',
     'https://sdmx.oecd.org/public/rest/data/OECD.TAD.ARP,DSD_AGR_POLIND@DF_PSE,', 'PSE en % de los ingresos agrarios y NPC del productor.'),
    ('OICA', 'Organización Internacional de Constructores de Automóviles', 'Production statistics',
     'https://www.oica.net/category/production-statistics/', 'Producción de vehículos de motor por país.'),
    ('USMCA', 'USTR', 'Texto del USMCA (capítulo 4 y apéndice de productos automotores)',
     'https://ustr.gov/trade-agreements/free-trade-agreements/united-states-mexico-canada-agreement', 'Reglas de origen del automóvil.'),
    ('WITS_ARANCEL', 'Banco Mundial', 'WITS, aranceles por socio (tradestats-tariff)', 'https://wits.worldbank.org',
     'Arancel aplicado efectivo (AHS) y de nación más favorecida (MFN), medias ponderadas por el comercio, por socio.'),
    ('SIPRI', 'Stockholm International Peace Research Institute', 'SIPRI Arms Transfers Database', 'https://www.sipri.org/databases/armstransfers',
     'Entregas de armas convencionales principales por proveedor y receptor, en millones de TIV (indicador de tendencia), 1985-2025. '
     'Consulta del 15/10/2026 (Code/datos/sipri_armas_ccg.csv).'),
    ('OMC_RTA', 'Organización Mundial del Comercio', 'Regional Trade Agreements Database', 'https://rtais.wto.org',
     'Año de entrada en vigor de los acuerdos de libre comercio entre las economías del RCEP.'),
    ('VARIAS', '—', 'Fuentes citadas una a una', '—', 'Hoja Cifras_citadas: la fuente de cada cifra figura en su fila.'),
]

TRATAMIENTOS = [  # (código, nombre, definición)
    ('T01', 'Cuota intrarregional', 'Exportaciones de los miembros a los demás miembros / exportaciones totales, con los miembros de cada '
     'año. Se omite el año si algún miembro no declara.'),
    ('T02', 'Cuota con los que declaran', 'En bloques con muchos miembros que no declaran (AfCFTA, PAFTA, ASEAN), la cuota se calcula con '
     'los que declaran, si son al menos la mitad.'),
    ('T03', 'Intensidad del comercio intrarregional', 'Cuota intrarregional / peso de los miembros en las importaciones mundiales de '
     'mercancías (WDI). 1 = comercian entre sí lo que predice su tamaño. Corrige el tamaño, no la distancia.'),
    ('T04', 'UE-27', 'Suma de los 27 Estados miembros actuales, también en años anteriores a su adhesión.'),
    ('T05', 'Datos espejo', 'Importaciones declaradas por los socios (CIF) en lugar de las exportaciones declaradas por el exportador.'),
    ('T06', 'Revisiones de la CUCI encadenadas', 'Rev. 1 hasta 1995, Rev. 3 de 1996 a 2006 y Rev. 4 desde 2007 (las que da la API); '
     'a 1 dígito, las secciones son comparables.'),
    ('T07', 'Manufacturas', 'Secciones 5 a 8 de la CUCI sin la división 68 (metales no ferrosos), como en la UNCTAD.'),
    ('T08', 'Complementariedad comercial', 'MICHAELY (1996): 100 (1 - suma |m_jk - x_ik| / 2), con grupos de 3 dígitos de la CUCI; '
     'se excluyen las declaraciones con menos de 100 grupos.'),
    ('T09', 'Saldo con el bloque', 'Exportaciones a los socios menos importaciones desde ellos, medidas con las exportaciones que '
     'declaran los socios (FOB), en % del PIB. En las figuras, media móvil centrada de 3 años.'),
    ('T10', 'Reparto de las manufacturas', 'Parte de cada miembro en las exportaciones de manufacturas (T07) dentro del bloque.'),
    ('T11', 'Destino de las exportaciones', '% de las exportaciones de cada miembro por destino (bloque, EE. UU., China, UE-27, Reino '
     'Unido, resto).'),
    ('T12', 'Sin productos que distorsionan', 'Sin hidrocarburos (SA 27) en las exportaciones de Noruega; sin piedras y metales '
     'preciosos (SA 68-71) en el comercio de Suiza.'),
    ('T13', 'Convergencia de renta', 'PIB per cápita en PPA en % del de EE. UU.; PIB per cápita en dólares constantes, índice 1993 = 100.'),
    ('T14', 'Protección agraria', 'PSE: transferencias a los productores en % de los ingresos agrarios brutos; NPC: precio percibido '
     'por el productor / precio en frontera.'),
    ('T15', 'Peso en la economía mundial', 'Suma de los miembros / total mundial (PIB, exportaciones de bienes y servicios, población).'),
    ('T16', 'Tipo de cambio real bilateral', 'Tipo de cambio peso/real (cociente de los tipos frente al dólar) por el deflactor del PIB '
     'de Brasil sobre el de Argentina (WDI no tiene el IPC argentino); índice 1995 = 100; sube = peso más barato.'),
    ('T17', 'Convergencia con la UE', 'PIB per cápita en PPA en % del agregado UE-27 de WDI (EUU).'),
    ('T18', 'Manufacturas (WITS)', 'Grupo «manuf» de WITS: CUCI 5 a 8 sin las divisiones 667 y 68.'),
    ('T19', 'Complementariedad aproximada', 'MICHAELY (1996) con las 16 secciones del SA de WITS (más grueso que con 3 dígitos de la CUCI).'),
    ('T20', 'Arancel según el origen', 'AHS y MFN por socio ponderados por las importaciones desde cada socio, agrupando los socios '
     'según el origen: en el AfCFTA, misma comunidad con libre comercio (CEDEAO, CEEAC, EAC, COMESA, SADC, UEMOA, CEMAC), resto de '
     'África y fuera de África; en la ASEAN, miembros, China, Japón y Corea, UE-27 y EE. UU. (al menos siete miembros con datos).'),
    ('T22', 'Fase de elaboración', 'Grupos de la UNCTAD en WITS (materias primas, bienes intermedios, de consumo y de capital): parte de '
     'cada fase en las exportaciones a cada destino, con los miembros que declaran las cuatro fases.'),
    ('T23', 'Margen de preferencia', 'Arancel NMF menos arancel aplicado (AHS), con las mismas ponderaciones de comercio, por importador '
     'y origen; antes de un acuerdo es cero.'),
    ('T24', 'Dependencia asimétrica', 'HIRSCHMAN (1945): peso de China en el comercio (exportaciones más importaciones) de cada miembro, '
     'frente al peso del miembro en el comercio de China; el cociente dice cuántas veces es mayor la dependencia del miembro.'),
    ('T25', 'Sumas móviles de cinco años', 'Parte de cada proveedor en las entregas de armas (TIV) de los cinco años hasta el indicado, '
     'para suavizar la irregularidad de los grandes contratos.'),
    ('T26', 'Índice 2021 = 100', 'Valor de cada año / valor de 2021 x 100, el último año antes de la invasión de Ucrania.'),
    ('T27', 'Hidrocarburos con datos espejo', 'Parte del grupo «Fuels» de WITS (capítulo 27 del SA) en las importaciones que todos los '
     'países declaran desde cada miembro; exportaciones no combustibles = total - Fuels, en % del PIB. Se descartan los años con más '
     'combustibles que total.'),
    ('T21', 'Sin combustibles', 'Exportaciones totales menos las del grupo «Fuels» de WITS (CUCI 3).'),
    ('T28', 'Peso mutuo con la UE', 'Comercio de mercancías de los 27 con el bloque en % de su comercio con fuera de la UE (lo que '
     'declaran los Estados miembros), y en % del comercio total de mercancías de los miembros del bloque (WDI); aproximado: '
     'importaciones de la UE CIF y exportaciones del bloque FOB.'),
    ('T00', 'Sin tratamiento', 'Dato tal como lo publica la fuente.'),
]

# Hoja intermedia -> (fuentes, tratamientos, figura); el proyecto sale del prefijo del nombre de la hoja
META = [
    # primero las hojas con nombre exacto; después, las reglas generales por sufijo
    (r'^UEE_destinos$', 'WITS, WITS_ESPEJO', 'T04, T05, T11', 'UEE_destinos'),
    (r'^CCG_destinos$', 'WITS_ESPEJO', 'T04, T05, T11', 'CCG_destinos'),
    (r'^EFTA_UE$', 'WITS', 'T04, T12', 'EFTA_ue'),
    (r'^EFTA_PSE$', 'OCDE_PSE', 'T14', 'EFTA_agricultura'),
    (r'^NAFTA_vehiculos$', 'OICA, USMCA', 'T00', 'NAFTA_automovil'),
    (r'^USA_importaciones$', 'WITS', 'T00', 'USA_importaciones'),
    (r'^MERCOSUR_tipo_cambio$', 'WDI, COMTRADE, WITS', 'T16, T01', 'MERCOSUR_tipo_cambio'),
    (r'^CEFTA_convergencia$', 'WDI', 'T17', 'CEFTA_convergencia'),
    (r'^CEFTA_ancla$', 'WITS', 'T04', 'CEFTA_ancla'),
    (r'^AFCFTA_composicion$', 'WITS', 'T02, T18', 'AfCFTA_composicion'),
    (r'^AFCFTA_materias$', 'WITS', 'T19', 'AfCFTA_materias'),
    (r'^AFCFTA_aranceles$', 'WITS_ARANCEL, WITS', 'T20', 'AfCFTA_aranceles'),
    (r'^PAFTA_sin_petroleo$', 'WITS', 'T02, T21', 'PAFTA_sin_petroleo'),
    (r'^PAFTA_composicion$', 'WITS', 'T18', 'PAFTA_composicion'),
    (r'^ASEAN_fabrica$', 'WITS', 'T22, T04', 'ASEAN_fabrica'),
    (r'^ASEAN_preferencia$', 'WITS_ARANCEL, WITS', 'T20, T04', 'ASEAN_preferencia'),
    (r'^CCG_diversificacion$', 'WITS_ESPEJO, WDI', 'T05, T27', 'CCG_diversificacion'),
    (r'^CCG_complementariedad$', 'COMTRADE', 'T06, T08', 'CCG_complementariedad'),
    (r'^CCG_seguridad$', 'SIPRI, WITS_ESPEJO', 'T25, T05', 'CCG_seguridad'),
    (r'^RCEP_china$', 'WITS', 'T24', 'RCEP_china'),
    (r'^RCEP_enlaces$', 'WITS_ARANCEL', 'T23', 'RCEP_enlaces (b)'),
    (r'^RCEP_acuerdos$', 'OMC_RTA', 'T00', 'RCEP_enlaces (a)'),
    (r'^UEE_remesas$', 'WDI', 'T00', 'UEE_remesas'),
    (r'^UEE_desvio$', 'WITS', 'T04, T26', 'UEE_desvio'),
    (r'^UE_peso_mutuo$', 'WITS, WDI', 'T04, T28', 'Relación con la UE (texto de cada acuerdo)'),
    (r'_intrarregional$', 'COMTRADE, WITS', 'T01', '{G}_comercio_intrarregional (a, c) o cuadro comparativo'),
    (r'_intensidad$', 'COMTRADE, WITS, WDI', 'T01, T03', '{G}_comercio_intrarregional (b)'),
    (r'_composicion$', 'COMTRADE', 'T06, T07', '{G}_composicion'),
    (r'_complementariedad$', 'COMTRADE', 'T06, T08', '{G}_complementariedad (a, b)'),
    (r'_saldos$', 'COMTRADE, WITS, WDI', 'T09', '{G}_complementariedad (c)'),
    (r'_reparto_manuf$', 'COMTRADE', 'T06, T07, T10', '{G}_complementariedad (d)'),
    (r'_destinos_\d{4}$', 'WITS', 'T04, T11', '{G}_destinos o texto'),
    (r'^Megaacuerdos', 'WDI', 'T15', 'Megaacuerdos_peso'),
    (r'^PAFTA_', 'WITS_ESPEJO', 'T02, T05', 'PAFTA_comercio'),
]
PROYECTO = {'MCCA': 'MCCA', 'CAN': 'CAN', 'EFTA': 'EFTA', 'NAFTA': 'NAFTA/USMCA', 'USA': 'NAFTA/USMCA', 'MERCOSUR': 'MERCOSUR',
            'CEFTA': 'CEFTA', 'AFCFTA': 'AfCFTA', 'PAFTA': 'PAFTA', 'ASEAN': 'ASEAN', 'CCG': 'CCG', 'RCEP': 'RCEP',
            'CPTPP': 'CPTPP', 'UEE': 'UEE', 'UE27': 'UE-27 (referencia)', 'UE': 'Relación con la UE', 'Megaacuerdos': 'RCEP, CPTPP, UE, USMCA, ASEAN'}
FICHERO = {'AFCFTA': 'AfCFTA'}   # prefijo de los ficheros de figura cuando no coincide con el de la hoja
DIM_PAIS = {'País', 'Miembro', 'Exportador', 'Subregión', 'Acuerdo', 'Bloque', 'Grupo'}
DIM_SOCIO = {'Importador', 'Destino', 'Socio'}
DIM_DESGLOSE = {'Faltan', 'Datos', 'Datos que faltan', 'Exportadores con datos espejo', 'Miembros'}
ISO = set(dc.M49) | {'USA', 'CAN', 'MEX', 'CHN', 'NOR', 'ISL', 'CHE', 'RUS', 'BLR', 'KAZ', 'ARM', 'KGZ', 'ARE', 'SAU', 'EU', 'OECD',
                     'TJK', 'UZB', 'AUS', 'NZL'}
NOMBRE_ISO = {'Noruega': 'NOR', 'Islandia': 'ISL', 'Suiza': 'CHE', 'EE. UU.': 'USA', 'EE.\\,UU.': 'USA', 'México': 'MEX',
              'Canadá': 'CAN', 'UE': 'EU', 'OCDE': 'OECD', 'Guatemala': 'GTM', 'El Salvador': 'SLV', 'Honduras': 'HND',
              'Nicaragua': 'NIC', 'Costa Rica': 'CRI', 'Bolivia': 'BOL', 'Colombia': 'COL', 'Ecuador': 'ECU', 'Perú': 'PER'}
POR_SOCIO = r'_destinos|^PAFTA_subregiones|^USA_importaciones'   # tablas con un destino u origen por columna

COLUMNAS = ['Proyecto', 'País o agregado', 'Socio o desglose', 'Indicador', 'Serie', 'Año', 'Valor', 'Unidad', 'Fuente',
            'Tratamiento', 'Figura o uso', 'Hoja de origen']


def unidad(texto):
    t = texto.lower()
    if '% del pib' in t:
        return '% del PIB'
    if '%' in t or 'cuota' in t or 'parte' in t:
        return '%'
    if 'millones' in t and 'usd' in t or 'millones de dólares' in t:
        return 'millones de USD'
    if 'índice' in t:
        return 'índice'
    if 'unidades' in t or 'vehículos' in t:
        return 'unidades'
    return ''


def filas_de_tabla(nombre, ws):
    """Convierte una tabla intermedia (título, fuente, [nota], línea en blanco, cabecera, datos) en filas largas."""
    filas = [list(r) for r in ws.iter_rows(values_only=True)]
    if not filas:
        return []
    titulo = str(filas[0][0] or nombre)
    cab_i = next((i for i in range(1, len(filas)) if not any(c not in (None, '') for c in filas[i - 1])
                  and sum(c not in (None, '') for c in filas[i]) >= 2), None)
    if cab_i is None:
        return []
    cab = [str(c) if c is not None else '' for c in filas[cab_i]]
    datos = [f for f in filas[cab_i + 1:] if any(c not in (None, '') for c in f)]
    es_dim = [all(isinstance(f[j], str) or f[j] is None for f in datos if j < len(f)) for j in range(len(cab))]
    prefijo = nombre.split('_')[0]
    grupo = prefijo if prefijo in dc.GRUPOS else prefijo
    fuente, trat, fig = '', '', ''
    for patron, fu, tr, fi in META:
        if re.search(patron, nombre):
            fuente, trat, fig = fu, tr, fi.replace('{G}', FICHERO.get(grupo, grupo))
            break
    if nombre.endswith('_intrarregional') and grupo in dc.PARCIALES:
        trat = 'T01, T02'
    anio_hoja = re.search(r'_(\d{4})$', nombre)
    out = []
    for f in datos:
        pais, socio, desglose, anio = '', '', [], int(anio_hoja.group(1)) if anio_hoja else None
        for j, c in enumerate(cab):
            if j >= len(f) or f[j] in (None, ''):
                continue
            if c == 'Año':
                anio = f[j]
            elif es_dim[j]:
                if c in DIM_DESGLOSE:
                    desglose.append(f'{c}: {f[j]}')
                elif c in DIM_PAIS or (not pais and c not in DIM_SOCIO):
                    pais = pais or f[j]
                elif c in DIM_SOCIO:
                    socio = f[j]
                else:
                    desglose.append(f'{c}: {f[j]}')
        for j, c in enumerate(cab):
            if j >= len(f) or es_dim[j] or c == 'Año' or f[j] in (None, '') or isinstance(f[j], str):
                continue
            p, s, serie = pais, socio, c
            if re.search(POR_SOCIO, nombre):          # columnas = destinos u orígenes
                s, serie = c, 'por destino u origen'
                p = p or ('USA' if nombre.startswith('USA_') else '')
            elif c in ISO:                             # columnas = países
                p, serie = c, ''
            elif c in NOMBRE_ISO:
                p, serie = NOMBRE_ISO[c], ''
            else:
                m = re.match(r'^(PSE|NPC) (.+)$', c) or re.match(r'^(.+), (exportaciones|importaciones)$', c)
                if m and (m.group(2) in NOMBRE_ISO or m.group(1) in NOMBRE_ISO):
                    nom, serie = (m.group(2), m.group(1)) if m.group(2) in NOMBRE_ISO else (m.group(1), m.group(2))
                    p = NOMBRE_ISO[nom]
            u = unidad(c) or unidad('; '.join(desglose)) or unidad(titulo) or ('millones de USD' if nombre.endswith('_composicion') else '')
            u = 'coeficiente' if serie == 'NPC' else u
            out.append([PROYECTO.get(prefijo, prefijo), p or PROYECTO.get(prefijo, prefijo), '; '.join([s] + desglose).strip('; '),
                        titulo, serie, anio, f[j], u, fuente, trat, fig, nombre])
    return out


def convergencia():
    """Serie de la figura NAFTA_convergencia (la calcula Code/figuras_economicas.py sin escribir tabla)."""
    w = ib.wdi()
    out = []
    for e in ('MEX', 'CAN'):
        for a in range(1990, 2026):
            if (e, 'NY.GDP.PCAP.PP.KD', a) in w and ('USA', 'NY.GDP.PCAP.PP.KD', a) in w:
                out.append(['NAFTA/USMCA', e, 'USA', 'PIB per cápita en PPA en % del de EE. UU.', 'PPA, dólares internacionales de 2021',
                            a, round(100 * w[(e, 'NY.GDP.PCAP.PP.KD', a)] / w[('USA', 'NY.GDP.PCAP.PP.KD', a)], 2), '%', 'WDI', 'T13',
                            'NAFTA_convergencia (a)', 'calculado en Code/libro_datos.py'])
    for e in ('USA', 'CAN', 'MEX'):
        base = w.get((e, 'NY.GDP.PCAP.KD', 1993))
        for a in range(1980, 2026):
            if base and (e, 'NY.GDP.PCAP.KD', a) in w:
                out.append(['NAFTA/USMCA', e, '', 'PIB per cápita real, índice 1993 = 100', 'dólares constantes de 2015', a,
                            round(100 * w[(e, 'NY.GDP.PCAP.KD', a)] / base, 2), 'índice', 'WDI', 'T13', 'NAFTA_convergencia (b)',
                            'calculado en Code/libro_datos.py'])
    return out


def lee_csv(nombre):
    with open(DATOS / nombre, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def fuente_bruta(texto):
    t = texto or ''
    if 'espejo' in t or 'MPRT' in t:
        return 'WITS_ESPEJO'
    if 'WITS' in t:
        return 'WITS'
    if 'SA' in t and 'Comtrade' in t:
        return 'COMTRADE_SA'
    return 'COMTRADE'


def comercio_bruto():
    """[Fuente, Clasificación, Tipo de dato, Reportero, Socio, Flujo, Producto, Año, Valor (USD)]."""
    for r in lee_csv('exportaciones_bilaterales.csv'):
        yield [fuente_bruta(r['fuente']), 'Total', 'Exportaciones declaradas por el exportador', r['exportador'], r['socio'], 'X',
               'Total', int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('destinos.csv'):
        yield [fuente_bruta(r['fuente']), 'Total', 'Exportaciones declaradas por el exportador (destinos)', r['exportador'],
               r['socio'], 'X', 'Total', int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('espejo.csv'):
        yield ['WITS_ESPEJO', 'Total', 'Importaciones declaradas por el socio (espejo, CIF)', r['importador'], r['exportador'], 'M',
               'Total', int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('composicion_cuci.csv'):
        yield ['COMTRADE', r['clasificacion'], 'Exportaciones por sección de la CUCI', r['exportador'], r['socio'], 'X',
               'Sección ' + r['seccion'], int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('division68_cuci.csv'):
        yield ['COMTRADE', r['clasificacion'], 'Exportaciones de metales no ferrosos', r['exportador'], r['socio'], 'X',
               'División 68', int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('productos_cuci3.csv'):
        yield ['COMTRADE', r['clasificacion'], 'Comercio con el mundo por grupo de 3 dígitos', r['pais'], 'WLD', r['flujo'],
               'Grupo ' + r['producto'], int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('wits_extra.csv'):
        if r['socio'] and r['tipo'] == 'comercio':
            yield ['WITS', 'grupos de WITS', 'Comercio por socio y grupo de productos', r['pais'], r['socio'], r['medida'],
                   r['producto'], int(r['anio']), float(r['valor'])]
    for r in lee_csv('espejo_productos.csv'):
        yield ['WITS_ESPEJO', 'grupos de WITS', 'Importaciones declaradas por el socio (espejo, CIF), por grupo de productos',
               r['importador'], r['exportador'], 'M', r['producto'], int(r['anio']), float(r['valor_usd'])]
    for r in lee_csv('efta_ue.csv'):
        yield ['WITS', 'SA (grupos de WITS)', 'Comercio con la UE-27 y con el mundo', r['pais'], r['socio'], r['flujo'],
               r['producto'], int(r['anio']), float(r['valor_usd'])]


def otros_brutos():
    """[Fuente, País, Indicador, Código, Año, Valor]."""
    nombres = {'NY.GDP.MKTP.CD': 'PIB (USD corrientes)', 'TM.VAL.MRCH.CD.WT': 'Importaciones de mercancías (USD corrientes)',
               'NY.GDP.PCAP.KD': 'PIB per cápita (USD constantes de 2015)', 'NY.GDP.PCAP.PP.KD': 'PIB per cápita (PPA, 2021)',
               'NE.EXP.GNFS.CD': 'Exportaciones de bienes y servicios (USD corrientes)', 'SP.POP.TOTL': 'Población',
               'PSEP': 'PSE (% de los ingresos agrarios brutos)', 'PNPC': 'NPC del productor',
               'TX.VAL.FUEL.ZS.UN': 'Combustibles (% de las exportaciones de mercancías)',
               'TX.VAL.MRCH.CD.WT': 'Exportaciones de mercancías (USD corrientes)',
               'BX.GSR.NFSV.CD': 'Exportaciones de servicios (USD corrientes)',
               'BX.TRF.PWKR.DT.GD.ZS': 'Remesas personales recibidas (% del PIB)',
               'BX.TRF.PWKR.CD.DT': 'Remesas personales recibidas (USD corrientes)'}
    for r in lee_csv('wdi_series.csv'):
        yield ['WDI', r['pais'], nombres.get(r['indicador'], r['indicador']), r['indicador'], int(r['anio']), float(r['valor'])]
    for r in lee_csv('wdi_2023.csv'):
        yield ['WDI', r['pais'], nombres.get(r['indicador'], r['indicador']), r['indicador'], 2023, float(r['valor'])]
    for r in lee_csv('wits_extra.csv'):
        if r['socio'] and r['tipo'] == 'arancel':
            yield ['WITS_ARANCEL', r['pais'], f"Arancel {r['medida']} ponderado frente a {r['socio']} (%)", r['medida'], int(r['anio']),
                   float(r['valor'])]
    for r in lee_csv('pse_ocde.csv'):
        yield ['OCDE_PSE', r['pais'], nombres.get(r['medida'], r['medida']), r['medida'], int(r['anio']), float(r['valor'])]
    yield from sipri_bruto()


def sipri_bruto():
    """Entregas de armas a cada miembro del CCG por proveedor (SIPRI, millones de TIV), tal como las da la consulta."""
    cab, filas = None, []
    with open(DATOS / 'sipri_armas_ccg.csv', encoding='utf-8') as f:
        bloque = []
        for fila in csv.reader(f):
            if fila and fila[0] == 'Supplier':
                cab, bloque = fila, []
            elif fila and cab and fila[0].startswith('Total exports to'):
                receptor = fila[0].replace('Total exports to ', '')
                for prov in bloque + [fila]:
                    for j, c in enumerate(cab):
                        if c.isdigit() and j < len(prov) and prov[j].strip():
                            nombre = 'Total' if prov is fila else prov[0]
                            filas.append(['SIPRI', receptor, f'Armas entregadas por {nombre} (millones de TIV)', 'TIV', int(c),
                                          float(prov[j])])
                cab = None
            elif fila and cab:
                bloque.append(fila)
    return filas


def hoja(wb, nombre, cabecera, filas, anchos):
    ws = wb.create_sheet(nombre)
    ws.freeze_panes = 'A2'
    ws.append([WriteOnlyCell(ws, value=c) for c in cabecera])
    ws.row_dimensions  # noqa: B018 (las celdas de cabecera llevan su estilo)
    for i, a in enumerate(anchos):
        ws.column_dimensions[chr(65 + i)].width = a
    n = 0
    for f in filas:
        ws.append(f)
        n += 1
    ws.auto_filter.ref = f'A1:{chr(64 + len(cabecera))}{n + 1}'
    return n


def main():
    tablas = load_workbook(TABLAS, read_only=True)
    indicadores, cifras = [], None
    for ws in tablas.worksheets:
        if ws.title == 'Cifras_citadas':
            cifras = [list(r) for r in ws.iter_rows(values_only=True)]
        elif ws.title != 'Exportaciones_bilaterales':
            indicadores += filas_de_tabla(ws.title, ws)
    indicadores += convergencia()
    indicadores.sort(key=lambda f: (str(f[0]), str(f[3]), str(f[1]), str(f[2]), str(f[4]), str(f[5])))

    wb = Workbook(write_only=True)
    leeme = [
        ['Datos del tema 3.B.35 (procesos de integración fuera de la UE)'],
        ['Libro único con todos los datos del tema. Lo monta Code/libro_datos.py a partir de las tablas de cada figura '
         '(Code/datos/tablas_figuras.xlsx) y de los datos brutos descargados (CSV de Code/datos/).'],
        [],
        ['Hoja', 'Contenido'],
        ['Fuentes', 'Cada fuente con su código (columna Fuente de las demás hojas).'],
        ['Tratamientos', 'Cada tratamiento con su código (columna Tratamiento de la hoja Indicadores).'],
        ['Indicadores', 'Todas las series de las figuras y de los cuadros, en formato largo. Filtrar por Proyecto, País, Indicador, '
         'Serie, Año o Tratamiento; la columna Figura o uso dice dónde aparece cada serie.'],
        ['Cifras_citadas', 'Cada cifra citada en el texto, con su fuente.'],
        ['Comercio_bruto', 'Datos de comercio descargados, sin tratar: una fila por reportero, socio, flujo, producto y año (USD).'],
        ['Otros_brutos', 'Banco Mundial, aranceles de WITS, OCDE y SIPRI, sin tratar.'],
        [],
        ['Script', 'Qué hace'],
        ['Code/datos_comercio.py', 'Comercio total bilateral (UN Comtrade hasta 1995, WITS desde 1996), destinos y datos espejo.'],
        ['Code/datos_producto.py', 'Comercio por secciones y grupos de la CUCI (UN Comtrade) y series del Banco Mundial.'],
        ['Code/datos_efta.py', 'Comercio de la EFTA con la UE (WITS) y PSE de la OCDE.'],
        ['Code/indicadores_bloque.py', 'Intensidad, composición, complementariedad, saldos y reparto de las manufacturas.'],
        ['Code/figuras_economicas.py, Code/grafico_*.py', 'Figuras económicas (Img/*.tikz).'],
        ['Code/descargas_afinidad.py, Code/descargas_geoestrategicas.py, Code/datos_wits.py', 'Descargas de WITS por grupos de productos, '
         'aranceles por socio y datos espejo por grupo (bloques de afinidad y geoestratégico).'],
        ['Code/figuras_afinidad.py, Code/figuras_geoestrategicas.py', 'Figuras económicas de los bloques de afinidad y geoestratégico.'],
        ['Code/cronologia_acuerdo.py, Code/gobernanza.py, Code/mapa_bloque.py', 'Cronologías, gobernanza y mapas (sin datos numéricos).'],
        ['Code/relacion_ue.py', 'Peso mutuo entre la UE y cada bloque (párrafos de relación con la UE).'],
        ['Code/libro_datos.py', 'Este libro.'],
    ]
    ws = wb.create_sheet('Léeme')
    ws.column_dimensions['A'].width = 52
    ws.column_dimensions['B'].width = 110
    for f in leeme:
        ws.append([WriteOnlyCell(ws, value=c) for c in f])
    hoja(wb, 'Fuentes', ['Código', 'Institución', 'Base de datos', 'Enlace', 'Cobertura y uso'], FUENTES, [14, 30, 50, 60, 90])
    hoja(wb, 'Tratamientos', ['Código', 'Nombre', 'Definición'], TRATAMIENTOS, [10, 34, 130])
    n_ind = hoja(wb, 'Indicadores', COLUMNAS, indicadores, [16, 16, 20, 50, 34, 7, 12, 14, 22, 14, 34, 24])
    if cifras:
        ws = wb.create_sheet('Cifras_citadas')
        ws.freeze_panes = 'A5'
        for f in cifras:
            ws.append(f)
    n_com = hoja(wb, 'Comercio_bruto', ['Fuente', 'Clasificación', 'Tipo de dato', 'Reportero', 'Socio', 'Flujo', 'Producto', 'Año',
                                        'Valor (USD)'], comercio_bruto(), [14, 16, 44, 10, 10, 6, 16, 7, 16])
    n_otr = hoja(wb, 'Otros_brutos', ['Fuente', 'País', 'Indicador', 'Código', 'Año', 'Valor'], otros_brutos(), [12, 8, 46, 20, 7, 18])
    wb.save(LIBRO)
    print(f'{LIBRO.name}: Indicadores {n_ind} filas, Comercio_bruto {n_com}, Otros_brutos {n_otr}')


if __name__ == '__main__':
    main()
