#!/usr/bin/env python3
"""Figuras económicas de la EFTA (3.B.35), con los datos de Code/datos_efta.py.

  Img/EFTA_ue.tikz            Dos vías hacia la UE: parte de la UE-27 en (a) las exportaciones y (b) las importaciones
                              de bienes de Noruega e Islandia (EEE) y de Suiza (acuerdos bilaterales), 1996-2023; sin
                              hidrocarburos en Noruega ni piedras y metales preciosos en Suiza.
  Img/EFTA_agricultura.tikz   Protección agraria: (a) PSE en % de los ingresos agrarios, 1986-2024; (b) coeficiente de
                              protección nominal del productor (precio interior / precio mundial), media 2022-2024.
Mismo estilo que Code/figuras_economicas.py (paleta validada, letra de 8 puntos, 16 cm). Escribe una hoja por figura
en Code/datos_3B35.xlsx.
Uso, desde la carpeta del tema:
  /ruta/a/python-con-openpyxl Code/grafico_efta.py
  bash Code/generar_figura.sh EFTA_ue ; bash Code/generar_figura.sh EFTA_agricultura
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_efta as de  # noqa: E402
import figuras_economicas as fe  # noqa: E402
import indicadores_bloque as ib  # noqa: E402

PAISES = ['NOR', 'ISL', 'CHE']
NOMBRE = {'NOR': 'Noruega', 'ISL': 'Islandia', 'CHE': 'Suiza', 'EU': 'UE', 'OECD': 'OCDE'}
COLOR = {'NOR': 's1', 'ISL': 's3', 'CHE': 's2', 'EU': 's4', 'OECD': 'black!55'}
RESTA = {('NOR', 'X'): '27-27_Fuels', ('CHE', 'X'): '68-71_StoneGlas', ('CHE', 'M'): '68-71_StoneGlas'}


def cuotas_ue():
    v = {}
    for r in de.dc_lee(de.CSV_UE):
        v[(r['pais'], int(r['anio']), r['flujo'], r['producto'], r['socio'])] = float(r['valor_usd'])
    out = defaultdict(list)   # (país, flujo): [(año, % UE)]
    for p in PAISES:
        for f in ('X', 'M'):
            for a in range(1996, 2024):
                tot = {s: v.get((p, a, f, 'Total', s)) for s in ('UE27', 'WLD')}
                if None in tot.values() or not tot['WLD']:
                    continue
                if (p, f) in RESTA:
                    menos = {s: v.get((p, a, f, RESTA[(p, f)], s), 0.0) for s in ('UE27', 'WLD')}
                    tot = {s: tot[s] - menos[s] for s in tot}
                out[(p, f)].append((a, 100 * tot['UE27'] / tot['WLD']))
    return out


def pse():
    out = defaultdict(dict)
    for r in de.dc_lee(de.CSV_PSE):
        out[(r['pais'], r['medida'])][int(r['anio'])] = float(r['valor'])
    return out


def rotulos(series, techo_eje, x):
    """Rótulos al final de las líneas, de arriba abajo y separados al menos un 9 % del eje."""
    o, previo = [], None
    for v, texto in sorted(series, reverse=True):
        y = v if previo is None or previo - v > techo_eje * 0.09 else previo - techo_eje * 0.09
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{x},{y:.1f}) {{{texto}}};')
        previo = y
    return o


def fig_ue(c):
    o = fe.cabecera('EFTA', 'ue')
    for k, (f, titulo) in enumerate((('X', '(a) Exportaciones de bienes a la UE'), ('M', '(b) Importaciones de bienes desde la UE'))):
        o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.2cm, height=4.2cm, at={{({k * 8.2}cm,0cm)}}, xmin=1995, xmax=2024, ymin=0,'
              f' ymax=100, xtick={{2000,2010,2020}}, title={{{titulo}}}, ylabel={{\\% del total}}, clip mode=individual]',
              '    \\draw[black!45, densely dashed, line width=0.4pt] (axis cs:2002,0) -- (axis cs:2002,100);',
              '    \\node[anchor=north west, inner sep=1.5pt, text=black!70] at (axis cs:2002,99) {Bilaterales I};']
        for p in PAISES:
            o.append(f'    \\addplot[{COLOR[p]}, line width=1.3pt, mark=none] coordinates {{{fe.coords(c[(p, f)])}}};')
        o += rotulos([(c[(p, f)][-1][1], NOMBRE[p]) for p in PAISES], 100, 2023.6)
        o.append('  \\end{axis}')
    o.append('\\end{tikzpicture}')
    return o


def fig_agricultura(s):
    o = fe.cabecera('EFTA', 'agricultura')
    orden = ['NOR', 'ISL', 'CHE', 'EU', 'OECD']
    ult = max(max(s[(p, 'PSEP')]) for p in orden)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=6.3cm, height=4.2cm, at={{(0cm,0cm)}}, xmin=1986, xmax={ult}, ymin=0, ymax=100,'
          ' xtick={1990,2000,2010,2020}, title={(a) Apoyo al productor (PSE)}, ylabel={\\% de los ingresos agrarios},'
          ' clip mode=individual]']
    for p in orden:
        estilo = ', densely dashed' if p == 'OECD' else ''
        o.append(f'    \\addplot[{COLOR[p]}, line width=1.3pt, mark=none{estilo}] coordinates {{'
                 + fe.coords(sorted(s[(p, 'PSEP')].items())) + '};')
    o += rotulos([(s[(p, 'PSEP')][ult], NOMBRE[p]) for p in orden], 100, ult + 0.6)
    o.append('  \\end{axis}')
    anios = [ult - 2, ult - 1, ult]
    npc = [(p, sum(s[(p, 'PNPC')][a] for a in anios) / 3) for p in orden]
    etiquetas = ','.join(NOMBRE[p] for p, _ in npc)
    o += [f'  \\begin{{axis}}[{fe.ESTILO.replace("ymajorgrids", "xmajorgrids")}, at={{(10.6cm,0cm)}}, width=4.6cm, height=4.2cm,'
          f' xbar, bar width=7pt, y dir=reverse, symbolic y coords={{{etiquetas}}}, ytick=data, xmin=0.9, xmax={max(v for _, v in npc) * 1.18:.2f},'
          f' enlarge y limits=0.15, title={{(b) Protección de precios, {anios[0]}-{anios[-1]}}},'
          ' nodes near coords, nodes near coords style={font=\\sffamily\\footnotesize, text=black!75, /pgf/number format/fixed,'
          ' /pgf/number format/precision=2, /pgf/number format/use comma, /pgf/number format/assume math mode=true}, point meta=x]',
          # 1 = precio interior igual al mundial (sin protección)
          '    \\draw[black!60, line width=0.5pt] ({axis cs:1,OCDE} |- {rel axis cs:0,0}) -- ({axis cs:1,OCDE} |- {rel axis cs:0,1});',
          '    \\addplot[draw=none, fill=s1] coordinates {' + ' '.join(f'({v:.3f},{NOMBRE[p]})' for p, v in npc) + '};',
          '  \\end{axis}', '\\end{tikzpicture}']
    return o, npc


def main():
    c = cuotas_ue()
    s = pse()
    (dc.TEMA / 'Img' / 'EFTA_ue.tikz').write_text('\n'.join(fig_ue(c)) + '\n', encoding='utf-8')
    lineas, npc = fig_agricultura(s)
    (dc.TEMA / 'Img' / 'EFTA_agricultura.tikz').write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    try:
        ib.hoja('EFTA_UE', 'Parte de la UE-27 en el comercio de bienes de Noruega, Islandia y Suiza (%)',
                'WITS (Banco Mundial), a partir de UN Comtrade; UE-27 como suma de sus Estados miembros. Sin hidrocarburos '
                '(SA 27) en las exportaciones de Noruega y sin piedras y metales preciosos (SA 68-71) en el comercio de Suiza. '
                'Cálculo propio (Code/grafico_efta.py).',
                ['Año'] + [f'{NOMBRE[p]}, {"exportaciones" if f == "X" else "importaciones"}' for p in PAISES for f in ('X', 'M')],
                [(a, *[round(dict(c[(p, f)]).get(a), 1) if a in dict(c[(p, f)]) else None for p in PAISES for f in ('X', 'M')])
                 for a in range(1996, 2024)])
        s_ult = max(max(s[(p, 'PSEP')]) for p in NOMBRE)
        ib.hoja('EFTA_PSE', 'Apoyo al productor agrario (PSE, % de los ingresos agrarios brutos) y protección nominal (NPC)',
                'OCDE, Agricultural Policy Monitoring and Evaluation (dataflow OECD.TAD.ARP DSD_AGR_POLIND@DF_PSE).',
                ['Año'] + [f'PSE {NOMBRE[p]}' for p in NOMBRE] + [f'NPC {NOMBRE[p]}' for p in NOMBRE],
                [(a, *[s[(p, 'PSEP')].get(a) for p in NOMBRE], *[s[(p, 'PNPC')].get(a) for p in NOMBRE]) for a in range(1986, s_ult + 1)])
    except ImportError:
        print('Falta openpyxl: no se escribe el Excel')
    for p in PAISES:
        print(p, 'X', [(a, round(v)) for a, v in c[(p, 'X')] if a in (1996, 2002, 2010, 2023)],
              'M', [(a, round(v)) for a, v in c[(p, 'M')] if a in (1996, 2002, 2010, 2023)])
    for p in NOMBRE:
        print(p, 'PSE', {a: round(s[(p, 'PSEP')][a]) for a in (1986, 2000, 2010) if a in s[(p, 'PSEP')]}, round(s[(p, 'PSEP')][max(s[(p, 'PSEP')])]), max(s[(p, 'PSEP')]))
    print('NPC', [(p, round(v, 2)) for p, v in npc])


if __name__ == '__main__':
    main()
