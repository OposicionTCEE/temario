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
    escribe('UEE_comercio_intrarregional', fe.fig_integracion('UEE', it, x0=1995, x1=2024, xtick='2000,2010,2020'))
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
    paises = [('KGZ', True), ('ARM', True), ('KAZ', True), ('TJK', False), ('UZB', False)]
    color = {'KGZ': 's1', 'ARM': 's2', 'KAZ': 's3', 'TJK': 's4', 'UZB': 's5'}
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
          ['Año'] + [e for e, _ in paises], [(a, *[round(rem[e][a], 2) if a in rem[e] else None for e, _ in paises]) for a in range(1995, ult + 1)])
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
    comunes = (f'{fe.ESTILO}, width=4.9cm, height=4.4cm, xmin=2019, xmax={anios[-1]}, ymode=log, ymin={ymin}, ymax={ymax},'
               ' log ticks with fixed point, xtick={2019,2020,2021,2022,2023,2024}, xticklabels={2019,,2021,,2023,},'
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
    fuel = {e: {a: w[(e, 'TX.VAL.FUEL.ZS.UN', a)] for a in range(2000, 2025) if (e, 'TX.VAL.FUEL.ZS.UN', a) in w} for e in CCG}
    nof = {e: {a: 100 * w[(e, 'TX.VAL.MRCH.CD.WT', a)] * (1 - fuel[e][a] / 100) / w[(e, 'NY.GDP.MKTP.CD', a)] for a in fuel[e]
               if (e, 'TX.VAL.MRCH.CD.WT', a) in w and (e, 'NY.GDP.MKTP.CD', a) in w} for e in CCG}
    ult = max(max(v) for v in fuel.values())
    o = fe.cabecera('CCG', 'diversificacion')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.2cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax=100,'
          ' xtick={2000,2010,2020}, title={(a) Hidrocarburos en las exportaciones}, ylabel={\\% de las mercancías}, clip mode=individual]',
          *fe.etapas('CCG', 0, 100, 2000, ult)]
    for e in CCG:
        o.append(f'    \\addplot[{color[e]}, line width=1.2pt, mark=none] coordinates {{{fe.coords(sorted(fuel[e].items()))}}};')
    o += rotulos([(fuel[e][max(fuel[e])], NOMBRES[e]) for e in CCG], 100, ult + 0.4)
    o.append('  \\end{axis}')
    hi = fe.techo(max(max(v.values()) for v in nof.values()), 10)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.2cm, height=4.4cm, at={{(8.4cm,0cm)}}, xmin=2000, xmax={ult}, ymin=0, ymax={hi},'
          ' xtick={2000,2010,2020}, title={(b) Exportaciones no combustibles}, ylabel={\\% del PIB}, clip mode=individual]',
          *fe.etapas('CCG', 0, hi, 2000, ult)]
    for e in CCG:
        o.append(f'    \\addplot[{color[e]}, line width=1.2pt, mark=none] coordinates {{{fe.coords(sorted(nof[e].items()))}}};')
    o += rotulos([(nof[e][max(nof[e])], NOMBRES[e]) for e in CCG if nof[e]], hi, ult + 0.4)
    o += ['  \\end{axis}', '\\end{tikzpicture}']
    escribe('CCG_diversificacion', o)
    tabla('CCG_diversificacion', 'Peso de los combustibles en las exportaciones de mercancías (%) y exportaciones de mercancías no combustibles (% del PIB) de los miembros del CCG',
          'Banco Mundial (WDI): TX.VAL.FUEL.ZS.UN (combustibles, sección 3 de la CUCI, a partir de UN Comtrade), TX.VAL.MRCH.CD.WT y '
          'NY.GDP.MKTP.CD. No combustibles = exportaciones de mercancías x (1 - parte de los combustibles). Las de Emiratos incluyen '
          'reexportaciones. Cálculo propio (Code/figuras_geoestrategicas.py).',
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


if __name__ == '__main__':
    {'UEE': uee, 'CCG': ccg}[sys.argv[1]]()
