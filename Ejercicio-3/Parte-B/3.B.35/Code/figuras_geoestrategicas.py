#!/usr/bin/env python3
"""Figuras económicas propias del bloque geoestratégico (3.B.35). Mismo estilo que Code/figuras_afinidad.py: paleta
validada, letra de 8 puntos, 16 cm como máximo, etapas de la cronología al fondo.

  Img/ASEAN_fabrica.tikz               bienes intermedios en las exportaciones según el destino: (a) evolución; (b) 2023.
  Img/ASEAN_preferencia.tikz           arancel aplicado según el origen: (a) evolución; (b) por miembro.
  Img/CCG_diversificacion.tikz         (a) hidrocarburos en las exportaciones; (b) exportaciones no combustibles, % del PIB.
  Img/CCG_complementariedad.tikz       (a) complementariedad entre miembros y con Asia; (b) evolución.
  Img/CCG_seguridad.tikz               peso de EE. UU. y de China en las compras de armas y en las exportaciones del Golfo.
  Img/RCEP_china.tikz                  (a) peso de China y de Japón en el comercio de cada miembro; (b) dependencia asimétrica.
  Img/RCEP_enlaces.tikz                (a) acuerdos previos entre las seis economías; (b) aranceles entre China, Japón y Corea.
  Img/UEE_comercio_intrarregional.tikz cuota intrarregional, intensidad y exportaciones (Code/figuras_economicas.py).
  Img/UEE_remesas.tikz                 remesas recibidas, % del PIB, miembros y no miembros de Asia central.
  Img/UEE_desvio.tikz                  (a) exportaciones de la UE a Armenia, Kazajistán y Kirguistán; (b) de estos a Rusia.
Datos: Code/datos/wits_extra.csv (Code/descargas_geoestrategicas.py), wdi_series.csv, espejo.csv, productos_cuci3.csv,
exportaciones_bilaterales.csv y sipri_armas_ccg.csv (SIPRI Arms Transfers Database); tablas en Code/datos/tablas_figuras.xlsx
(el libro final lo monta Code/libro_datos.py).
Uso, desde la carpeta del tema:  /ruta/a/python-con-openpyxl Code/figuras_geoestrategicas.py [ASEAN|CCG|RCEP|UEE]
"""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402
import figuras_economicas as fe  # noqa: E402
import indicadores_bloque as ib  # noqa: E402
from descargas_geoestrategicas import ASEAN10, CAUCASO_ASIA, FASES  # noqa: E402
from figuras_afinidad import barras_h, escribe, rotulos, tabla  # noqa: E402

NOMBRES = {'RUS': 'Rusia', 'BLR': 'Bielorrusia', 'KAZ': 'Kazajistán', 'ARM': 'Armenia', 'KGZ': 'Kirguistán',
           'TJK': 'Tayikistán', 'UZB': 'Uzbekistán', 'SAU': 'Arabia Saudí', 'ARE': 'Emiratos', 'KWT': 'Kuwait', 'QAT': 'Catar',
           'BHR': 'Bahréin', 'OMN': 'Omán', 'IDN': 'Indonesia', 'MYS': 'Malasia', 'PHL': 'Filipinas', 'SGP': 'Singapur',
           'THA': 'Tailandia', 'BRN': 'Brunéi', 'VNM': 'Vietnam', 'LAO': 'Laos', 'MMR': 'Myanmar', 'KHM': 'Camboya',
           'CHN': 'China', 'JPN': 'Japón', 'KOR': 'Corea del Sur', 'AUS': 'Australia', 'NZL': 'Nueva Zelanda', 'IND': 'India',
           'USA': 'EE.\\,UU.'}
CCG = ['SAU', 'ARE', 'KWT', 'QAT', 'BHR', 'OMN']


# ---------------------------------------------------------------- UEE
def uee():
    f = dc.lee_csv()
    it = ib.intensidad('UEE')
    escribe('UEE_comercio_intrarregional', fe.fig_integracion('UEE', it, x0=1998, x1=2023, xtick='2000,2010,2020'))
    try:
        dc.escribe_hoja('UEE', dc.cuadro('UEE', 1996, 2024, f))
    except ImportError:
        print('Falta openpyxl: no se escribe la hoja UEE_intrarregional')
    tabla('UEE_intensidad', f'Intensidad del comercio intrarregional. {dc.GRUPOS["UEE"][1]}',
          'Cuota: exportaciones a los socios / exportaciones totales (Code/datos_comercio.py). Peso: importaciones de '
          'mercancías de los miembros / importaciones mundiales (Banco Mundial, WDI, TM.VAL.MRCH.CD.WT). '
          'Intensidad = cuota / peso. Rusia y Bielorrusia no publican su comercio desde 2022, por lo que la serie acaba en 2021. '
          'Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año', 'Cuota intrarregional (%)', 'Peso en las importaciones mundiales (%)', 'Intensidad'],
          [(a, round(c, 2), round(p, 4), round(i, 1)) for a, c, p, i in it])
    print('UEE intensidad', [(a, round(c, 1), round(i, 1)) for a, c, p, i in it][::3])
    # remesas
    w = ib.wdi()
    # Kazajistán, país de inmigración, apenas recibe remesas (0,1-0,4 % del PIB): queda en la tabla, no en la figura
    paises = [('KGZ', True), ('ARM', True), ('TJK', False), ('UZB', False)]
    color = {'KGZ': 's1', 'ARM': 's2', 'TJK': 's3', 'UZB': 's4'}
    rem = {e: {a: w[(e, 'BX.TRF.PWKR.DT.GD.ZS', a)] for a in range(1995, 2025) if (e, 'BX.TRF.PWKR.DT.GD.ZS', a) in w} for e, _ in paises}
    ult = max(max(v) for v in rem.values())
    hi = fe.techo(max(max(v.values()) for v in rem.values()), 10)
    o = fe.cabecera('UEE', 'remesas')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=9.6cm, height=4.6cm, at={{(0cm,0cm)}}, xmin=1995, xmax={ult}, ymin=0, ymax={hi},'
          ' xtick={1995,2000,2005,2010,2015,2020}, ylabel={\\% del PIB}, clip mode=individual]',
          *fe.etapas('UEE', 0, hi, 1995, ult)]
    for e, miembro in paises:
        estilo = '' if miembro else ', densely dashed'
        o.append(f'    \\addplot[{color[e]}, line width=1.3pt, mark=none{estilo}] coordinates {{{fe.coords(sorted(rem[e].items()))}}};')
    o += rotulos([(rem[e][ult], NOMBRES[e] + ('' if m else ' (no miembro)')) for e, m in paises if ult in rem[e]], hi, ult + 0.4)
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('UEE_remesas', o)
    tabla('UEE_remesas', 'Remesas personales recibidas, % del PIB: miembros de la UEE con más emigración a Rusia y no miembros de Asia central',
          'Banco Mundial (WDI), BX.TRF.PWKR.DT.GD.ZS. Tayikistán y Uzbekistán no son miembros (Uzbekistán es observador).',
          ['Año'] + [e for e, _ in paises] + ['KAZ'],
          [(a, *[round(rem[e][a], 2) if a in rem[e] else None for e, _ in paises],
            round(w[('KAZ', 'BX.TRF.PWKR.DT.GD.ZS', a)], 2) if ('KAZ', 'BX.TRF.PWKR.DT.GD.ZS', a) in w else None) for a in range(1995, ult + 1)])
    print('remesas', {e: {a: round(rem[e][a], 1) for a in (2005, 2013, 2015, 2021, 2022, 2023, ult) if a in rem[e]} for e, _ in paises})
    # desvío por sanciones
    t = dw.tabla('comercio', 'X', 'Total')
    anios = list(range(2019, 2025))
    completos = [a for a in anios if all((p, a) in t for p in dc.UE27)]
    ue = {d: {a: sum(t[(p, a)].get(d, 0.0) for p in dc.UE27) for a in completos} for d in CAUCASO_ASIA + ['RUS']}
    a_rus = {p: {a: t[(p, a)].get('RUS', 0.0) for a in anios if (p, a) in t and t[(p, a)].get('RUS')} for p in CAUCASO_ASIA}
    base = 2021
    o = fe.cabecera('UEE', 'desvio')
    ymin, ymax = 10, 2000
    anios = completos   # la UE aún no tiene 2024 completo
    comunes = (f'{fe.ESTILO}, width=4.9cm, height=4.4cm, xmin=2019, xmax={anios[-1]}, ymode=log, ymin={ymin}, ymax={ymax},'
               ' log ticks with fixed point, xtick={2019,2020,2021,2022,2023}, xticklabels={2019,,2021,,2023},'
               ' clip mode=individual')
    color = {'ARM': 's1', 'KAZ': 's2', 'KGZ': 's3', 'RUS': 'black!55'}
    o += [f'  \\begin{{axis}}[{comunes}, at={{(0cm,0cm)}}, title={{(a) Exportaciones de la UE-27}}, ylabel={{índice, {base} = 100 (log.)}}]',
          *fe.etapas('UEE', ymin, ymax, 2019, anios[-1]),
          f'    \\draw[black!50, line width=0.4pt] (axis cs:2019,100) -- (axis cs:{anios[-1]},100);']
    fin = []
    for d in CAUCASO_ASIA + ['RUS']:
        s = {a: 100 * v / ue[d][base] for a, v in ue[d].items()}
        o.append(f'    \\addplot[{color[d]}, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(s.items()))}}};')
        fin.append((math.log10(s[max(s)]), f'a {NOMBRES[d]}', max(s)))
    o += [f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{x + 0.15},{10 ** y:.1f}) {{{txt}}};'
          for y, txt, x in separa(fin, 0.13)]
    o.append('  \\end{axis}')
    o += [f'  \\begin{{axis}}[{comunes}, at={{(8.3cm,0cm)}}, title={{(b) Exportaciones a Rusia}}]',
          *fe.etapas('UEE', ymin, ymax, 2019, anios[-1]),
          f'    \\draw[black!50, line width=0.4pt] (axis cs:2019,100) -- (axis cs:{anios[-1]},100);']
    fin = []
    for p in CAUCASO_ASIA:
        s = {a: 100 * v / a_rus[p][base] for a, v in a_rus[p].items()}
        o.append(f'    \\addplot[{color[p]}, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(s.items()))}}};')
        fin.append((math.log10(s[max(s)]), f'de {NOMBRES[p]}', max(s)))
    o += [f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{x + 0.15},{10 ** y:.1f}) {{{txt}}};'
          for y, txt, x in separa(fin, 0.13)]
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('UEE_desvio', o)
    tabla('UEE_desvio', 'Exportaciones de la UE-27 a Armenia, Kazajistán, Kirguistán y Rusia, y exportaciones de los tres primeros a Rusia (millones de USD)',
          'WITS (Banco Mundial): exportaciones declaradas por cada Estado de la UE-27 (sumadas) y por Armenia, Kazajistán y Kirguistán, '
          'dólares corrientes. Solo se suman los años en que declaran los 27. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año'] + [f'UE-27 a {d}' for d in CAUCASO_ASIA + ['RUS']] + [f'{p} a RUS' for p in CAUCASO_ASIA],
          [(a, *[round(ue[d][a] / 1e6, 1) if a in ue[d] else None for d in CAUCASO_ASIA + ['RUS']],
            *[round(a_rus[p][a] / 1e6, 1) if a in a_rus[p] else None for p in CAUCASO_ASIA]) for a in anios])
    print('UE ->', {d: {a: round(v / 1e9, 2) for a, v in ue[d].items()} for d in ue}, 'años completos', completos)
    print('-> RUS', {p: {a: round(v / 1e9, 2) for a, v in a_rus[p].items()} for p in a_rus})


def separa(fin, dmin):
    """Rótulos al final de las líneas (en log10), separados al menos dmin de arriba abajo: [(y, texto, x)]."""
    out, previo = [], None
    for y, txt, x in sorted(fin, reverse=True):
        y = y if previo is None or previo - y > dmin else previo - dmin
        out.append((y, txt, x))
        previo = y
    return out


def coloca(rotulos, d, lo):
    """Posiciones de rótulos [(valor, texto)] de arriba abajo, separados al menos d y sin bajar de lo: [(y, texto)]."""
    r = sorted(rotulos, reverse=True)
    ys = [v for v, _ in r]
    for i in range(1, len(ys)):
        ys[i] = min(ys[i], ys[i - 1] - d)
    ys[-1] = max(ys[-1], lo)
    for i in range(len(ys) - 2, -1, -1):
        ys[i] = max(ys[i], ys[i + 1] + d)
    return [(y, txt) for y, (_, txt) in zip(ys, r)]


# ---------------------------------------------------------------- CCG
def sipri():
    """{proveedor: {año: TIV}} sumando los seis receptores del CCG, y {año: total}."""
    por = defaultdict(lambda: defaultdict(float))
    total = defaultdict(float)
    cab = None
    with open(dc.TEMA / 'Code' / 'datos' / 'sipri_armas_ccg.csv', encoding='utf-8') as fh:
        for fila in csv.reader(fh):
            if not fila:
                continue
            if fila[0] == 'Supplier':
                cab = fila
                continue
            if cab is None or not fila[1:2]:
                continue
            anios = [(j, int(c)) for j, c in enumerate(cab) if c.isdigit()]
            for j, a in anios:
                v = fila[j].strip() if j < len(fila) else ''
                if not v:
                    continue
                if fila[0].startswith('Total exports to'):
                    total[a] += float(v)
                else:
                    por[fila[0]][a] += float(v)
            if fila[0].startswith('Total exports to'):
                cab = None
    return por, total


def ccg():
    w = ib.wdi()
    color = {e: f's{i + 1}' for i, e in enumerate(CCG)}
    # datos espejo (lo que declaran los importadores), porque las series de WDI de Emiratos y Bahréin tienen saltos y ceros
    esp = defaultdict(dict)
    with open(dc.TEMA / 'Code' / 'datos' / 'espejo_productos.csv', newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['importador'] == 'WLD':
                esp[(r['exportador'], int(r['anio']))][r['producto']] = float(r['valor_usd'])
    fuel = {e: {a: 100 * esp[(e, a)]['Fuels'] / esp[(e, a)]['Total'] for a in range(2000, 2024)
                if esp.get((e, a), {}).get('Total') and esp[(e, a)].get('Fuels', 1e30) <= esp[(e, a)]['Total']} for e in CCG}
    # (se descartan los años incoherentes, con más combustibles que total: Kuwait en 2000)
    nof = {e: {a: 100 * (esp[(e, a)]['Total'] - esp[(e, a)]['Fuels']) / w[(e, 'NY.GDP.MKTP.CD', a)] for a in fuel[e]
               if (e, 'NY.GDP.MKTP.CD', a) in w} for e in CCG}
    ult = max(max(v) for v in fuel.values())
    o = fe.cabecera('CCG', 'diversificacion')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=4.8cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax=100,'
          ' xtick={2000,2010,2020}, title={(a) Hidrocarburos en las exportaciones}, ylabel={\\% de las mercancías}, clip mode=individual]',
          *fe.etapas('CCG', 0, 100, 2000, ult)]
    for e in CCG:
        o.append(f'    \\addplot[{color[e]}, line width=1.2pt, mark=none] coordinates {{{fe.coords(sorted(fuel[e].items()))}}};')
    o += rotulos([(fuel[e][max(fuel[e])], NOMBRES[e]) for e in CCG], 100, ult + 0.4)
    o.append('  \\end{axis}')
    hi = fe.techo(max(max(v.values()) for v in nof.values()), 10)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=4.8cm, height=4.4cm, at={{(8.1cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax={hi},'
          ' xtick={2000,2010,2020}, title={(b) Exportaciones no combustibles}, ylabel={\\% del PIB}, clip mode=individual]',
          *fe.etapas('CCG', 0, hi, 2000, ult)]
    for e in CCG:
        o.append(f'    \\addplot[{color[e]}, line width=1.2pt, mark=none] coordinates {{{fe.coords(sorted(nof[e].items()))}}};')
    o += rotulos([(nof[e][max(nof[e])], NOMBRES[e]) for e in CCG if nof[e]], hi, ult + 0.4)
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('CCG_diversificacion', o)
    tabla('CCG_diversificacion', 'Peso de los combustibles en las exportaciones de mercancías (%) y exportaciones de mercancías no combustibles (% del PIB) de los miembros del CCG',
          'Datos espejo de WITS (Banco Mundial): importaciones declaradas por todos los países desde cada miembro, totales y del grupo '
          '«Fuels» (combustibles, capítulo 27 del SA), en dólares CIF (Code/descargas_geoestrategicas.py, Code/datos/espejo_productos.csv); '
          'PIB en dólares corrientes del Banco Mundial (WDI, NY.GDP.MKTP.CD). Se usan los datos espejo porque las series de WDI '
          '(TX.VAL.FUEL.ZS.UN) de Emiratos y Bahréin tienen saltos y ceros. Los importadores suelen anotar las reexportaciones con el país '
          'de origen, no con Emiratos. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año', 'Indicador'] + CCG,
          [(a, ind, *[round(s[e][a], 1) if a in s[e] else None for e in CCG]) for ind, s in (('Combustibles, % de las exportaciones', fuel),
                                                                                          ('No combustibles, % del PIB', nof))
           for a in range(2000, ult + 1)])
    print('combustibles', {e: {a: round(fuel[e][a]) for a in (2000, 2008, 2013, 2016, 2019, 2022, ult) if a in fuel[e]} for e in CCG})
    print('no combustibles %PIB', {e: {a: round(nof[e][a], 1) for a in (2000, 2008, 2013, 2016, 2019, 2022, ult) if a in nof[e]} for e in CCG})
    # seguridad frente a comercio
    por, total = sipri()
    europa = ['United Kingdom', 'France', 'Germany', 'Italy', 'Spain', 'Sweden', 'Belgium', 'Netherlands', 'Switzerland',
              'Austria', 'Finland', 'Bulgaria', 'Slovakia', 'Serbia']
    def ventana(prov, a):
        tot = sum(total.get(b, 0) for b in range(a - 4, a + 1))
        return 100 * sum(sum(por[p].get(b, 0) for p in prov) for b in range(a - 4, a + 1)) / tot if tot else None
    armas = {k: {a: ventana(prov, a) for a in range(1989, 2026)} for k, prov in
             (('USA', ['United States']), ('CHN', ['China']), ('EUR', europa), ('RUS', ['Russia']))}
    esp = defaultdict(dict)
    with open(dc.ESPEJO, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['exportador'] in CCG:
                esp[int(r['anio'])][(r['exportador'], r['importador'])] = float(r['valor_usd'])
    expo = {k: {} for k in ('USA', 'CHN')}
    for a, d in esp.items():
        tot = sum(v for (e, i), v in d.items() if i == 'WLD')
        for k in expo:
            expo[k][a] = 100 * sum(v for (e, i), v in d.items() if i == k) / tot if tot else None
    o = fe.cabecera('CCG', 'seguridad')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=10.2cm, height=4.6cm, at={{(0cm,0cm)}}, xmin=1990, xmax=2025, ymin=0, ymax=80,'
          ' xtick={1990,1995,2000,2005,2010,2015,2020,2025}, ylabel={\\% del total}, clip mode=individual]',
          *fe.etapas('CCG', 0, 80, 1990, 2025)]
    lineas = [('s1', armas['USA'], '', 'EE.\\,UU.: armas'), ('s1', expo['USA'], ', densely dashed', 'EE.\\,UU.: exportaciones'),
              ('s2', armas['CHN'], '', 'China: armas'), ('s2', expo['CHN'], ', densely dashed', 'China: exportaciones'),
              ('s3', armas['EUR'], '', 'Europa: armas')]
    fin = []
    for col, s, est, txt in lineas:
        pts = sorted((a, v) for a, v in s.items() if v is not None and a >= 1990)
        o.append(f'    \\addplot[{col}, line width=1.3pt, mark=none{est}] coordinates {{{fe.coords(pts)}}};')
        fin.append((pts[-1][1], txt, pts[-1][0]))
    for y, txt in coloca([(v, txt) for v, txt, x in fin], 7, 3):
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{2025.4},{y:.1f}) {{{txt}}};')
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('CCG_seguridad', o)
    tabla('CCG_seguridad', 'Peso de EE. UU., China, Europa y Rusia en las importaciones de armas de los seis miembros del CCG (TIV, sumas móviles de cinco años) y peso de EE. UU. y de China en sus exportaciones de mercancías (%)',
          'SIPRI Arms Transfers Database (valores TIV de las transferencias de armas convencionales principales entregadas, consulta del '
          '15/10/2026): suma de los seis receptores, cinco años hasta el indicado; Europa = Reino Unido, Francia, Alemania, Italia, España, '
          'Suecia, Bélgica, Países Bajos, Suiza, Austria, Finlandia, Bulgaria, Eslovaquia y Serbia. Exportaciones: datos espejo de WITS '
          '(importaciones declaradas por cada país desde los seis), Code/datos/espejo.csv. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año', 'Armas: EE. UU. (%)', 'Armas: China (%)', 'Armas: Europa (%)', 'Armas: Rusia (%)', 'Armas: total (TIV, millones)',
           'Exportaciones: EE. UU. (%)', 'Exportaciones: China (%)'],
          [(a, *[round(armas[k][a], 1) if armas[k].get(a) is not None else None for k in ('USA', 'CHN', 'EUR', 'RUS')],
            round(total.get(a, 0)), *[round(expo[k][a], 1) if expo[k].get(a) is not None else None for k in ('USA', 'CHN')])
           for a in range(1989, 2026)])
    print('armas', {k: {a: round(armas[k][a]) for a in (1994, 1999, 2004, 2009, 2014, 2019, 2024, 2025)} for k in armas})
    print('expo', {k: {a: round(expo[k][a]) for a in (1998, 2003, 2008, 2013, 2018, 2023) if a in expo[k]} for k in expo})


def ccg_complementariedad():
    """Complementariedad (MICHAELY, 1996) entre los miembros del CCG y con China, la India y Japón (CUCI de 3 dígitos)."""
    est = ib.estructuras()
    refs = ['CHN', 'IND', 'JPN']
    cols = CCG + refs
    cp = {}
    for a in (2005, 2015, 2022, 2023):
        for i in CCG:
            if (i, a, 'X') not in est:
                continue
            for j in cols:
                if j != i and (j, a, 'M') in est:
                    cp.setdefault(a, {})[(i, j)] = ib.michaely(est[(i, a, 'X')], est[(j, a, 'M')])
    ult = max(cp)
    c = cp[ult]
    o = fe.cabecera('CCG', 'complementariedad')
    cw, ch = 0.78, 0.5
    xm, ytop = 1.0, 3.6
    vmax = max(c.values())
    o.append(f'  \\node[anchor=north, font=\\sffamily\\small, inner sep=0pt] at ({xm + len(cols) * cw / 2:.2f},{ytop - len(CCG) * ch - 0.62:.2f}) '
             f'{{(a) Complementariedad, {ult}}};')
    for jx, j in enumerate(cols):
        o.append(f'  \\node[anchor=south, inner sep=1.5pt] at ({xm + (jx + 0.5) * cw:.2f},{ytop + 0.03:.2f}) {{{j}}};')
    for iy, i in enumerate(CCG):
        y = ytop - (iy + 1) * ch
        o.append(f'  \\node[anchor=east, inner sep=1pt] at ({xm - 0.08:.2f},{y + ch / 2:.2f}) {{{i}}};')
        for jx, j in enumerate(cols):
            x = xm + jx * cw
            if (i, j) in c:
                v = c[(i, j)]
                pct = int(12 + 78 * v / vmax)
                txt = 'white' if pct > 55 else 'black!85'
                o.append(f'  \\fill[s1!{pct}!white] ({x + 0.02:.2f},{y + 0.02:.2f}) rectangle ({x + cw - 0.02:.2f},{y + ch - 0.02:.2f});')
                o.append(f'  \\node[text={txt}, inner sep=0pt] at ({x + cw / 2:.2f},{y + ch / 2:.2f}) {{{v:.0f}}};')
            elif i == j:
                o.append(f'  \\fill[black!6] ({x + 0.02:.2f},{y + 0.02:.2f}) rectangle ({x + cw - 0.02:.2f},{y + ch - 0.02:.2f});')
    xs = xm + len(CCG) * cw
    o.append(f'  \\draw[black!45, line width=0.5pt] ({xs:.2f},{ytop - len(CCG) * ch - 0.05:.2f}) -- ({xs:.2f},{ytop + 0.05:.2f});')
    o.append(f'  \\node[anchor=north west, inner sep=1pt, text=black!70] at ({xm - 0.75:.2f},{ytop - len(CCG) * ch - 0.12:.2f}) '
             '{exportador (filas), importador (columnas); 0-100};')
    medias = []
    for a in sorted(cp):
        fila = [a]
        for grupo_j in (CCG, ['CHN'], ['IND'], ['JPN']):
            xs_ = [x for (i, j), x in cp[a].items() if j in grupo_j]
            fila.append(sum(xs_) / len(xs_) if xs_ else None)
        medias.append(fila)
    hi = fe.techo(max(v for f in medias for v in f[1:] if v is not None), 10)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}{fe.ABAJO}, at={{(10.0cm,0.6cm)}}, width=3.7cm, height=3.0cm, xmin=2003, xmax=2024, ymin=0,'
          f' ymax={hi}, xtick={{2005,2015,2023}}, title={{(b) Complementariedad media}}, clip mode=individual]',
          *fe.etapas('CCG', 0, hi, 2003, 2024)]
    estilos = [('s1', ''), ('s2', ', densely dashed'), ('s3', ', densely dashed'), ('s4', ', densely dashed')]
    nombres = ['entre socios', 'con China', 'con la India', 'con Japón']
    fin = []
    for k, ((col, est_), nom) in enumerate(zip(estilos, nombres)):
        pts = [(f[0], f[1 + k]) for f in medias if f[1 + k] is not None]
        o.append(f'    \\addplot[{col}, line width=1.2pt, mark=*, mark size=1.4pt, mark options={{solid}}{est_}] coordinates {{{fe.coords(pts)}}};')
        fin.append((pts[-1][1], nom))
    for y, txt in coloca(fin, hi * 0.11, hi * 0.04):
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:2024.5,{y:.1f}) {{{txt}}};')
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('CCG_complementariedad', o)
    tabla('CCG_complementariedad', 'Complementariedad comercial (MICHAELY, 1996) entre los miembros del CCG y con China, la India y Japón',
          'UN Comtrade, API pública, grupos de 3 dígitos de la CUCI (Rev. 3 en 2005 y Rev. 4 desde 2007): exportaciones del primer país y '
          'importaciones del segundo, con el mundo. Kuwait y Catar no declaran en 2005. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año', 'Exportador', 'Importador', 'Índice (0-100)'],
          [(a, i, j, round(x, 1)) for a, cc in sorted(cp.items()) for (i, j), x in sorted(cc.items())])
    print('CCG compl', ult, {k: round(v) for k, v in sorted(c.items())})
    print('medias', [(f[0], *[round(v) if v is not None else None for v in f[1:]]) for f in medias])


# ---------------------------------------------------------------- ASEAN
FASES_TXT = {'UNCTAD-SoP1': 'Materias primas', 'UNCTAD-SoP2': 'Intermedios', 'UNCTAD-SoP3': 'Consumo', 'UNCTAD-SoP4': 'Capital'}
DESTINOS = [('ASEAN', None), ('China', ['CHN']), ('Japón y Corea', ['JPN', 'KOR']), ('EE. UU.', ['USA']), ('UE-27', dc.UE27)]


def destino(p, nombre, socios):
    return [s for s in ASEAN10 if s != p] if nombre == 'ASEAN' else socios


def asean():
    fases = {g: dw.tabla('comercio', 'X', g) for g in FASES}
    color = {'ASEAN': 's1', 'China': 's2', 'Japón y Corea': 's3', 'EE. UU.': 's4', 'UE-27': 's5'}
    serie, compo, cobertura = defaultdict(dict), {}, {}
    for a in range(2000, 2024):
        con = [p for p in ASEAN10 if all((p, a) in fases[g] for g in FASES)]
        cobertura[a] = con
        if len(con) < 7:
            continue
        for nombre, socios in DESTINOS:
            v = {g: sum(fases[g][(p, a)].get(s, 0.0) for p in con for s in destino(p, nombre, socios)) for g in FASES}
            tot = sum(v.values())
            if tot:
                serie[nombre][a] = 100 * v['UNCTAD-SoP2'] / tot
                compo[(nombre, a)] = {g: 100 * x / tot for g, x in v.items()}
    anios = sorted(serie['ASEAN'])
    ult = anios[-1]
    o = fe.cabecera('ASEAN', 'fabrica')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax=40,'
          ' xtick={2000,2010,2020}, title={(a) Intermedios en las exportaciones}, ylabel={\\% de cada destino}, clip mode=individual]',
          *fe.etapas('ASEAN', 0, 40, 2000, ult)]
    for nombre, _ in DESTINOS:
        o.append(f'    \\addplot[{color[nombre]}, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(serie[nombre].items()))}}};')
    for y, txt in coloca([(serie[n][ult], 'a ' + n.replace('EE. UU.', 'EE.\\,UU.')) for n, _ in DESTINOS], 3.3, 1.5):
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{ult + 0.4},{y:.1f}) {{{txt}}};')
    o.append('  \\end{axis}')
    etiquetas = [n.replace('EE. UU.', 'EE.\\,UU.') for n, _ in DESTINOS]
    series = [(col, FASES_TXT[g], {n.replace('EE. UU.', 'EE.\\,UU.'): compo[(n, ult)][g] for n, _ in DESTINOS})
              for g, col in reversed(list(zip(FASES, ['black!25', 's7', 's6', 's8'])))]
    o += [l.replace('legend columns=3', 'legend columns=2') for l in
          barras_h(etiquetas, series, '(9.6cm,0cm)', 4.6, 4.4, f'(b) Por fase de elaboración, {ult} (\\%)', apilar=True, xmax=100,
                   valores=False)]
    o.append('\\end{tikzpicture}')
    escribe('ASEAN_fabrica', o)
    tabla('ASEAN_fabrica', 'Exportaciones de los miembros de la ASEAN según el destino y la fase de elaboración (% de cada destino)',
          'WITS (Banco Mundial), exportaciones declaradas por cada miembro por grupos de fase de elaboración de la UNCTAD (UNCTAD-SoP1 '
          'materias primas, SoP2 bienes intermedios, SoP3 de consumo, SoP4 de capital), dólares corrientes. Solo los miembros que '
          'declaran las cuatro fases cada año (al menos siete); UE-27 como suma de sus Estados miembros. Una parte de las '
          'exportaciones de Singapur son reexportaciones. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año', 'Destino', 'Materias primas (%)', 'Intermedios (%)', 'Consumo (%)', 'Capital (%)', 'Miembros que declaran'],
          [(a, n, *[round(compo[(n, a)][g], 1) for g in FASES], ', '.join(cobertura[a])) for a in anios for n, _ in DESTINOS])
    print('intermedios', {n: {a: round(serie[n][a]) for a in (2000, 2005, 2010, 2015, 2020, ult) if a in serie[n]} for n, _ in DESTINOS})
    print('compo', ult, {n: {FASES_TXT[g]: round(compo[(n, ult)][g]) for g in FASES} for n, _ in DESTINOS})
    print('cobertura', {a: len(c) for a, c in cobertura.items()})
    # sin Singapur (reexportaciones)
    a = ult
    con = [p for p in cobertura[a] if p != 'SGP']
    for nombre, socios in DESTINOS:
        v = {g: sum(fases[g][(p, a)].get(s, 0.0) for p in con for s in destino(p, nombre, socios)) for g in FASES}
        print('  sin SGP', nombre, round(100 * v['UNCTAD-SoP2'] / sum(v.values())))
    # margen de preferencia
    ahs, mfn, imp = dw.tabla('arancel', 'AHS', 'Total'), dw.tabla('arancel', 'MFN', 'Total'), dw.tabla('comercio', 'M', 'Total')
    origenes = [('ASEAN', None), ('China', ['CHN']), ('Japón y Corea', ['JPN', 'KOR']), ('UE-27 y EE. UU.', dc.UE27 + ['USA'])]
    col_o = {'ASEAN': 's1', 'China': 's2', 'Japón y Corea': 's3', 'UE-27 y EE. UU.': 's4'}
    ar, nmf, cob = defaultdict(dict), {}, {}
    for a in range(2000, 2024):
        con = [p for p in ASEAN10 if (p, a) in ahs and (p, a) in imp]
        cob[a] = con
        if len(con) < 7:
            continue
        for nombre, socios in origenes:
            num = den = 0.0
            for p in con:
                for s in destino(p, nombre, socios):
                    t, m = ahs[(p, a)].get(s), imp[(p, a)].get(s, 0.0)
                    if t is not None and m:
                        num, den = num + t * m, den + m
            if den:
                ar[nombre][a] = num / den
        num = den = 0.0
        for p in con:
            if (p, a) in mfn:
                for s, t in mfn[(p, a)].items():
                    m = imp[(p, a)].get(s, 0.0)
                    if m and s not in ASEAN10:
                        num, den = num + t * m, den + m
        if den:
            nmf[a] = num / den
    anios = sorted(ar['ASEAN'])
    ult = anios[-1]
    hi = fe.techo(max(max(s.values()) for s in ar.values()), 2)
    o = fe.cabecera('ASEAN', 'preferencia')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax={hi},'
          ' xtick={2000,2010,2020}, title={(a) Arancel aplicado según el origen}, ylabel={\\%, media ponderada}, clip mode=individual]',
          *fe.etapas('ASEAN', 0, hi, 2000, ult)]
    for nombre, _ in origenes:
        o.append(f'    \\addplot[{col_o[nombre]}, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(ar[nombre].items()))}}};')
    for y, txt in coloca([(ar[n][max(ar[n])], n.replace('EE. UU.', 'EE.\\,UU.')) for n, _ in origenes], hi * 0.08, hi * 0.03):
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{ult + 0.4},{y:.2f}) {{{txt}}};')
    o.append('  \\end{axis}')
    # (b) por miembro, último año con datos de cada uno
    por = {}
    for p in ASEAN10:
        anio = max((a for a in range(2015, 2024) if (p, a) in ahs and (p, a) in imp), default=None)
        if anio is None:
            continue
        def media(socios, tabla_t):
            num = den = 0.0
            for s in socios:
                t, m = tabla_t[(p, anio)].get(s), imp[(p, anio)].get(s, 0.0)
                if t is not None and m:
                    num, den = num + t * m, den + m
            return num / den if den else None
        por[p] = (anio, media([s for s in ASEAN10 if s != p], ahs), media(['CHN'], ahs),
                  media(dc.UE27 + ['USA'], ahs) if (p, anio) in ahs else None)
    orden = sorted(por, key=lambda p: -(por[p][3] or 0))
    etiquetas = [NOMBRES[p] for p in orden]
    o += barras_h(etiquetas, [('s1', 'de la ASEAN', {NOMBRES[p]: por[p][1] or 0 for p in orden}),
                              ('s2', 'de China', {NOMBRES[p]: por[p][2] or 0 for p in orden}),
                              ('s4', 'de la UE-27 y EE.\\,UU.', {NOMBRES[p]: por[p][3] or 0 for p in orden})],
                  '(10.2cm,0cm)', 3.9, 4.4, '(b) Por miembro, último año (\\%)', valores=False, xmax=12)
    o.append('\\end{tikzpicture}')
    escribe('ASEAN_preferencia', o)
    tabla('ASEAN_preferencia', 'Arancel aplicado por los miembros de la ASEAN según el origen de las importaciones (%, media ponderada por las importaciones)',
          'WITS (Banco Mundial), tradestats-tariff: arancel aplicado efectivo (AHS) medio ponderado por socio, agregado con las '
          'importaciones de cada miembro desde cada socio; NMF = arancel de nación más favorecida medio ponderado de las importaciones '
          'desde fuera de la ASEAN. Solo los miembros con datos cada año (al menos siete). Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Año'] + [f'Desde {n} (%)' for n, _ in origenes] + ['NMF, fuera de la ASEAN (%)', 'Miembros con datos'],
          [(a, *[round(ar[n][a], 2) if a in ar[n] else None for n, _ in origenes], round(nmf[a], 2) if a in nmf else None,
            ', '.join(cob[a])) for a in range(2000, 2024) if len(cob[a]) >= 7]
          + [(f'{por[p][0]} ({p})', *[round(x, 2) if x is not None else None for x in por[p][1:]], None, None, None) for p in orden])
    print('arancel', {n: {a: round(ar[n][a], 1) for a in (2000, 2005, 2010, 2015, 2020, ult) if a in ar[n]} for n, _ in origenes})
    print('NMF', {a: round(nmf[a], 1) for a in (2000, 2005, 2010, 2015, 2020, ult) if a in nmf}, 'cobertura', {a: len(c) for a, c in cob.items()})
    print('por miembro', {p: tuple(round(x, 1) if isinstance(x, float) else x for x in v) for p, v in por.items()})


# ---------------------------------------------------------------- RCEP
ACUERDOS_RCEP = {   # primer acuerdo de libre comercio en vigor entre cada par antes del RCEP (año, nombre)
    ('ASEAN', 'China'): (2005, 'ACFTA'), ('ASEAN', 'Japón'): (2008, 'AJCEP'), ('ASEAN', 'Corea'): (2007, 'AKFTA'),
    ('ASEAN', 'Australia'): (2010, 'AANZFTA'), ('ASEAN', 'N. Zelanda'): (2010, 'AANZFTA'),
    ('China', 'Japón'): (None, ''), ('China', 'Corea'): (2015, 'bilateral'), ('China', 'Australia'): (2015, 'bilateral'),
    ('China', 'N. Zelanda'): (2008, 'bilateral'), ('Japón', 'Corea'): (None, ''), ('Japón', 'Australia'): (2015, 'bilateral'),
    ('Japón', 'N. Zelanda'): (2018, 'CPTPP'), ('Corea', 'Australia'): (2014, 'bilateral'), ('Corea', 'N. Zelanda'): (2015, 'bilateral'),
    ('Australia', 'N. Zelanda'): (1983, 'ANZCERTA'),
}
SEIS = ['ASEAN', 'China', 'Japón', 'Corea', 'Australia', 'N. Zelanda']


def comercio_total(p, anios):
    """(año, {socio: exportaciones + importaciones}) del primer año de la lista con los dos flujos declarados."""
    x, m = dw.tabla('comercio', 'X', 'Total'), dw.tabla('comercio', 'M', 'Total')
    for a in anios:
        if (p, a) in x and (p, a) in m:
            d = defaultdict(float)
            for t in (x[(p, a)], m[(p, a)]):
                for s, v in t.items():
                    d[s] += v
            return a, d
    return None, {}


def rcep():
    miembros = [p for p in dc.GRUPOS['RCEP'][0] if p != 'CHN']
    ini, fin, cuota = {}, {}, {}
    for p in miembros:
        a0, d0 = comercio_total(p, (2000, 2001))
        a1, d1 = comercio_total(p, (2023, 2022, 2021))
        if a0 and d0.get('WLD'):
            ini[p] = (a0, 100 * d0.get('CHN', 0) / d0['WLD'], 100 * d0.get('JPN', 0) / d0['WLD'])
        if a1 and d1.get('WLD'):
            fin[p] = (a1, 100 * d1.get('CHN', 0) / d1['WLD'], 100 * d1.get('JPN', 0) / d1['WLD'])
    ac, dch = comercio_total('CHN', (2023, 2022))
    for p in miembros:
        cuota[p] = 100 * dch.get(p, 0) / dch['WLD']
    # la ASEAN como un todo: suma de los diez
    orden = sorted([p for p in miembros if p in fin], key=lambda p: -fin[p][1])
    o = fe.cabecera('RCEP', 'china')
    # (a) dumbbell: peso de China y de Japón en el comercio de cada miembro, hacia 2000 y hacia 2023
    x0, ancho, paso = 2.35, 5.0, 0.3
    xmax = 40
    def X(v):
        return x0 + ancho * v / xmax
    ytop = 0.0
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at (0,{ytop + 0.35:.2f}) {{(a) Peso en el comercio de cada miembro (\\%)}};')
    yb = ytop - (len(orden) - 1) * paso
    for v in range(0, xmax + 1, 10):
        o.append(f'  \\draw[black!12, line width=0.3pt] ({X(v):.2f},{ytop + 0.12:.2f}) -- ({X(v):.2f},{yb - 0.12:.2f});')
        o.append(f'  \\node[anchor=north, inner sep=1.5pt, text=black!70] at ({X(v):.2f},{yb - 0.14:.2f}) {{{v}}};')
    for i, p in enumerate(orden):
        y = ytop - i * paso
        o.append(f'  \\node[anchor=east, inner sep=1pt] at ({x0 - 0.1:.2f},{y:.2f}) {{{NOMBRES[p]}}};')
        for k, col, dy in ((2, 's1', -0.055), (1, 's2', 0.055)):
            if p == 'JPN' and k == 2:   # el peso de Japón en su propio comercio no tiene sentido
                continue
            if p in ini:
                o.append(f'  \\draw[{col}!55, line width=1.2pt] ({X(ini[p][k]):.2f},{y + dy:.2f}) -- ({X(fin[p][k]):.2f},{y + dy:.2f});')
                o.append(f'  \\draw[{col}, fill=white, line width=0.7pt] ({X(ini[p][k]):.2f},{y + dy:.2f}) circle (1.9pt);')
            o.append(f'  \\fill[{col}] ({X(fin[p][k]):.2f},{y + dy:.2f}) circle (1.9pt);')
    yl = yb - 0.75
    o += [f'  \\fill[s2] (0.2,{yl:.2f}) circle (1.9pt); \\node[anchor=west, inner sep=1pt] at (0.32,{yl:.2f}) {{China}};',
          f'  \\fill[s1] (1.55,{yl:.2f}) circle (1.9pt); \\node[anchor=west, inner sep=1pt] at (1.67,{yl:.2f}) {{Japón}};',
          f'  \\draw[black!60, fill=white, line width=0.7pt] (3.0,{yl:.2f}) circle (1.9pt); \\node[anchor=west, inner sep=1pt] at (3.12,{yl:.2f}) {{2000}};',
          f'  \\fill[black!60] (4.15,{yl:.2f}) circle (1.9pt); \\node[anchor=west, inner sep=1pt] at (4.27,{yl:.2f}) {{2023}};']
    # (b) dependencia asimétrica (HIRSCHMAN, 1945)
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at ({9.55:.2f},{ytop + 0.35:.2f}) {{(b) Dependencia asimétrica, {fin[orden[0]][0]}}};')
    # mismas filas que (a): dos barras por miembro, sin repetir los nombres
    xb0, anchob = 9.55, 4.6
    def XB(v):
        return xb0 + anchob * v / xmax
    for v in range(0, xmax + 1, 10):
        o.append(f'  \\draw[black!12, line width=0.3pt] ({XB(v):.2f},{ytop + 0.12:.2f}) -- ({XB(v):.2f},{yb - 0.12:.2f});')
        o.append(f'  \\node[anchor=north, inner sep=1.5pt, text=black!70] at ({XB(v):.2f},{yb - 0.14:.2f}) {{{v}}};')
    for i, p in enumerate(orden):
        y = ytop - i * paso
        o.append(f'  \\fill[s2] ({xb0:.2f},{y + 0.01:.2f}) rectangle ({XB(fin[p][1]):.2f},{y + 0.11:.2f});')
        o.append(f'  \\fill[black!35] ({xb0:.2f},{y - 0.11:.2f}) rectangle ({XB(cuota[p]):.2f},{y - 0.01:.2f});')
        if cuota[p] > 0:
            o.append(f'  \\node[anchor=west, inner sep=1pt, text=black!70] at ({XB(fin[p][1]) + 0.05:.2f},{y + 0.06:.2f}) '
                     f'{{\\scriptsize {fin[p][1] / cuota[p]:.0f} veces}};')
    o.append(f'  \\draw[black!45, line width=0.4pt] ({xb0:.2f},{ytop + 0.15:.2f}) -- ({xb0:.2f},{yb - 0.15:.2f});')
    o += [f'  \\fill[s2] ({xb0 - 0.6:.2f},{yl - 0.07:.2f}) rectangle ({xb0 - 0.2:.2f},{yl + 0.07:.2f}); '
          f'\\node[anchor=west, inner sep=1pt] at ({xb0 - 0.15:.2f},{yl:.2f}) {{China en su comercio}};',
          f'  \\fill[black!35] ({xb0 + 2.9:.2f},{yl - 0.07:.2f}) rectangle ({xb0 + 3.3:.2f},{yl + 0.07:.2f}); '
          f'\\node[anchor=west, inner sep=1pt] at ({xb0 + 3.35:.2f},{yl:.2f}) {{él en el de China}};']
    o.append('\\end{tikzpicture}')
    escribe('RCEP_china', o)
    tabla('RCEP_china', 'Peso de China y de Japón en el comercio (exportaciones más importaciones) de cada miembro del RCEP, hacia 2000 y hacia 2023, y peso de cada miembro en el comercio de China (%)',
          'WITS (Banco Mundial): exportaciones e importaciones declaradas por cada miembro por socio (2000, o 2001 si falta; 2023, o el último '
          'año disponible) y por China (2023). Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Miembro', 'Año inicial', 'China, inicio (%)', 'Japón, inicio (%)', 'Año final', 'China, final (%)', 'Japón, final (%)',
           'El miembro en el comercio de China (%)'],
          [(p, *(ini[p] if p in ini else (None, None, None)), *fin[p], round(cuota[p], 2)) for p in orden])
    print('RCEP', {p: (ini.get(p), fin[p], round(cuota[p], 1)) for p in orden})
    # enlaces nuevos
    ahs, mfn = dw.tabla('arancel', 'AHS', 'Total'), dw.tabla('arancel', 'MFN', 'Total')
    pares = [('JPN', 'CHN', 's2', 'Japón a China'), ('JPN', 'KOR', 's3', 'Japón a Corea'),
             ('CHN', 'JPN', 's1', 'China a Japón'), ('KOR', 'JPN', 's4', 'Corea a Japón')]
    tar = {(i, j): {a: ahs[(i, a)][j] for a in range(2018, 2024) if (i, a) in ahs and j in ahs[(i, a)]} for i, j, _, _ in pares}
    nm = {(i, j): {a: mfn[(i, a)][j] for a in range(2018, 2024) if (i, a) in mfn and j in mfn[(i, a)]} for i, j, _, _ in pares}
    o = fe.cabecera('RCEP', 'enlaces')
    n, c = len(SEIS), 1.22
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at (0,{0.62:.2f}) {{(a) Acuerdos previos al RCEP}};')
    for k, nombre in enumerate(SEIS[1:]):
        o.append(f'  \\node[anchor=south, inner sep=1pt, text=black!75] at ({1.55 + (k + 0.5) * c:.2f},0.05) {{{nombre}}};')
    for i, a in enumerate(SEIS[:-1]):
        y = -(i + 0.5) * 0.52
        o.append(f'  \\node[anchor=east, inner sep=1pt] at (1.5,{y:.2f}) {{{a}}};')
        for k, b in enumerate(SEIS[1:]):
            if k < i:
                continue
            anio, nom = ACUERDOS_RCEP[(a, b)]
            x = 1.55 + k * c
            nuevo = anio is None
            fill = 's2!80' if nuevo else 'black!8'
            txt = '\\textbf{RCEP}' if nuevo else f'{anio}'
            o.append(f'  \\fill[{fill}] ({x + 0.03:.2f},{y - 0.24:.2f}) rectangle ({x + c - 0.03:.2f},{y + 0.24:.2f});')
            o.append(f'  \\node[inner sep=0pt, text={"white" if nuevo else "black!85"}, align=center, font=\\sffamily\\footnotesize] '
                     f'at ({x + c / 2:.2f},{y + (0 if nuevo else 0.07):.2f}) {{{txt}}};')
            if not nuevo and nom != 'bilateral':
                o.append(f'  \\node[inner sep=0pt, text=black!60, font=\\sffamily\\scriptsize] at ({x + c / 2:.2f},{y - 0.12:.2f}) {{{nom}}};')
    # (b) margen de preferencia = arancel NMF - arancel aplicado, con las mismas ponderaciones; antes de 2022, cero en los cuatro pares
    margen = {(i, j): {a: nm[(i, j)][a] - tar[(i, j)][a] for a in tar[(i, j)] if a in nm[(i, j)]} for i, j, _, _ in pares}
    etiquetas = [txt for _, _, _, txt in pares]
    o += barras_h(etiquetas, [('s2!45', '2022', {txt: margen[(i, j)].get(2022, 0) for i, j, _, txt in pares}),
                              ('s2', '2023', {txt: margen[(i, j)].get(2023, 0) for i, j, _, txt in pares})],
                  '(11.6cm,-3.05cm)', 2.9, 3.15, '(b) Margen de preferencia (puntos)', xmax=1, leyenda=True, valores=False)
    o = [l.replace('xbar,', 'xbar, /pgf/number format/use comma,') if 'Margen de preferencia' in l else l for l in o]
    o.append('\\end{tikzpicture}')
    escribe('RCEP_enlaces', o)
    tabla('RCEP_enlaces', 'Acuerdos de libre comercio en vigor entre las seis economías del RCEP antes de 2022 y aranceles aplicados entre China, Japón y Corea (%)',
          'Acuerdos: OMC (base de datos de acuerdos comerciales regionales) y textos de los acuerdos; año de entrada en vigor. Aranceles: '
          'WITS (Banco Mundial), tradestats-tariff, arancel aplicado efectivo (AHS) y de nación más favorecida (NMF) medios ponderados '
          'por el comercio, por socio. Cálculo propio (Code/figuras_geoestrategicas.py).',
          ['Par o importador a origen', 'Año o indicador', '2018', '2019', '2020', '2021', '2022', '2023'],
          [(f'{a}-{b}', f'{v[0] or "RCEP (2022)"} {v[1]}'.strip(), None, None, None, None, None, None) for (a, b), v in ACUERDOS_RCEP.items()]
          + [(txt, ind, *[round(s[a], 2) if a in s else None for a in range(2018, 2024)])
             for i, j, _, txt in pares for ind, s in (('AHS', tar[(i, j)]), ('NMF', nm[(i, j)]))])
    print('aranceles', {txt: (tar[(i, j)], nm[(i, j)]) for i, j, _, txt in pares})


if __name__ == '__main__':
    {'UEE': uee, 'CCG': ccg, 'CCG2': ccg_complementariedad, 'ASEAN': asean, 'RCEP': rcep}[sys.argv[1]]()
