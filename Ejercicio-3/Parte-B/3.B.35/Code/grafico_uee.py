#!/usr/bin/env python3
"""Genera Img/UEE_destinos.tikz (TikZ puro) y la hoja UEE_destinos de Code/datos_3B35.xlsx: destino de las exportaciones de
cada miembro de la Unión Económica Euroasiática en 2013, 2021 y 2023.

Rusia y Bielorrusia no publican su comercio desde 2022. Para Rusia se usan en los tres años datos espejo (importaciones que
declaran los demás países, Code/datos/espejo.csv), lo que permite comparar; en 2023 falta Bielorrusia como importadora, por
lo que la parte del resto de la UEE está subestimada. Bielorrusia (datos espejo) solo aparece en 2013 y 2021: en 2021 ya
declaraba el 40 % de sus exportaciones sin destino, y en 2023 faltaría Rusia como importadora. Kazajistán, Armenia y
Kirguistán, con sus propios datos (Code/datos/destinos.csv). Ambos ficheros los escribe Code/datos_comercio.py (UEE destinos AÑO y UEE espejo 2013 2023).
Uso, desde la carpeta del tema (con openpyxl):
  /tmp/v/bin/python Code/grafico_uee.py
  bash Code/generar_figura.sh UEE_destinos
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
from grafico_pafta import lee_espejo  # noqa: E402

TEMA = Path(__file__).resolve().parent.parent
UEE = ['RUS', 'BLR', 'KAZ', 'ARM', 'KGZ']
NOMBRES = {'RUS': 'Rusia', 'BLR': 'Bielorrusia', 'KAZ': 'Kazajistán', 'ARM': 'Armenia', 'KGZ': 'Kirguistán'}
FILAS = [('RUS', 2013, 'espejo'), ('RUS', 2021, 'espejo'), ('RUS', 2023, 'espejo'),
         ('BLR', 2013, 'espejo'), ('BLR', 2021, 'espejo'),
         ('KAZ', 2013, 'propios'), ('KAZ', 2021, 'propios'), ('KAZ', 2023, 'propios'),
         ('ARM', 2013, 'propios'), ('ARM', 2021, 'propios'), ('ARM', 2023, 'propios'),
         ('KGZ', 2013, 'propios'), ('KGZ', 2021, 'propios'), ('KGZ', 2023, 'propios')]
DESTINOS = [
    ('Resto de la UEE', 'UEE', (150, 90, 160)),
    ('UE-27', dc.UE27, (90, 150, 90)),
    ('China', ['CHN'], (200, 60, 60)),
    ('India', ['IND'], (233, 160, 40)),
    ('Turquía', ['TUR'], (110, 165, 215)),
    ('Resto del mundo', None, (190, 190, 190)),
]


def main():
    from openpyxl import load_workbook
    esp = lee_espejo()
    propios = {}
    with open(TEMA / 'Code' / 'datos' / 'destinos.csv', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            propios[(r['exportador'], int(r['anio']), r['socio'])] = float(r['valor_usd'])
    res = []
    for e, a, fuente in FILAS:
        d = esp if fuente == 'espejo' else propios
        tot = d.get((e, a, 'WLD'), 0.0)
        fila, usado = [], 0.0
        for _, socios, _ in DESTINOS:
            if socios is None:
                v = tot - usado
            else:
                lista = UEE if socios == 'UEE' else socios
                v = sum(d.get((e, a, s), 0.0) for s in lista if s != e)
                usado += v
            fila.append(100 * v / tot)
        res.append((e, a, fuente, fila, tot))
    wb = load_workbook(dc.XLSX)
    if 'UEE_destinos' in wb.sheetnames:
        del wb['UEE_destinos']
    ws = wb.create_sheet('UEE_destinos')
    ws.append(['Destino de las exportaciones de mercancías de los miembros de la UEE (% del total)'])
    ws.append([f'Fuentes: {dc.FUENTE_WITS} (datos propios) y {dc.FUENTE_ESPEJO} (Rusia). Cálculo propio (Code/grafico_uee.py).'])
    ws.append([])
    ws.append(['Exportador', 'Año', 'Datos'] + [x[0] for x in DESTINOS] + ['Exportaciones (millones USD)'])
    for e, a, fuente, fila, tot in res:
        ws.append([e, a, fuente] + [round(v, 2) for v in fila] + [round(tot / 1e6, 1)])
    wb.save(dc.XLSX)

    o = ['% Generado por Code/grafico_uee.py.']
    for i, (_, _, rgb) in enumerate(DESTINOS):
        o.append('\\definecolor{cd%d}{RGB}{%d,%d,%d}' % (i, *rgb))
    o.append('\\begin{tikzpicture}[font=\\sffamily]')
    ancho, alto, paso, x0 = 12.5, 0.36, 0.44, 2.6
    for i, (ley, _, _) in enumerate(DESTINOS):
        o.append(f'  \\fill[cd{i}] ({x0 + i * 2.1:.2f},0.55) rectangle ++(0.3,0.16); '
                 f'\\node[anchor=west, font=\\sffamily\\scriptsize] at ({x0 + i * 2.1 + 0.33:.2f},0.63) {{{ley}}};')
    y, previo = 0.0, None
    for e, a, fuente, fila, tot in res:
        if previo and e != previo:
            y -= 0.25
        if e != previo:
            o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize\\bfseries] at ({x0 - 0.75:.2f},{y:.2f}) {{{NOMBRES[e]}}};')
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize] at ({x0 - 0.08:.2f},{y:.2f}) {{{a}}};')
        acum = 0.0
        for i, v in enumerate(fila):
            xa, xb = x0 + ancho * acum / 100, x0 + ancho * (acum + v) / 100
            o.append(f'  \\fill[cd{i}, draw=white, line width=0.3pt] ({xa:.3f},{y - alto / 2:.3f}) rectangle ({xb:.3f},{y + alto / 2:.3f});')
            if v >= 5:
                tc = 'black!80' if i in (4, 5) else 'white'
                o.append(f'  \\node[font=\\sffamily\\tiny, text={tc}] at ({(xa + xb) / 2:.3f},{y:.2f}) {{{v:.0f}}};')
            acum += v
        previo = e
        y -= paso
    yb = y + paso - alto / 2 - 0.1
    for t in range(0, 101, 10):
        xx = x0 + ancho * t / 100
        o.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize] at ({xx:.2f},{yb:.2f}) {{{t}}};')
    o.append(f'  \\draw[black!70, line width=0.5pt] ({x0:.2f},{yb:.2f}) -- ({x0 + ancho:.2f},{yb:.2f});')
    o.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize] at ({x0 + ancho / 2:.2f},{yb - 0.35:.2f}) {{\\% de las exportaciones de mercancías}};')
    o.append('\\end{tikzpicture}')
    (TEMA / 'Img' / 'UEE_destinos.tikz').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito Img/UEE_destinos.tikz')
    for e, a, fuente, fila, tot in res:
        print(e, a, fuente, [round(v, 1) for v in fila], round(tot / 1e9, 1))


if __name__ == '__main__':
    main()
