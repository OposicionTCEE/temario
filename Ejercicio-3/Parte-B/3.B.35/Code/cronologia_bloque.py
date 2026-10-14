#!/usr/bin/env python3
"""Genera Img/<CLAVE>_cronologia.tikz: cronología normativa de un acuerdo en varios carriles.

Cada hito: (año, texto, posición) con posición 'a' (encima, centrado), 'b' (debajo, centrado),
'ae'/'be' (encima/debajo, alineado a la derecha del punto) o 'aw'/'bw' (alineado a la izquierda).
Fechas comprobadas en octubre de 2026 (fuentes en el pie de la figura y en la bibliografía del tema).
Uso, desde la carpeta del tema:
  python3 Code/cronologia_bloque.py CAN
  bash Code/generar_figura.sh CAN_cronologia
"""
import sys
from pathlib import Path

A0, A1 = 1966, 2027
X0, X1 = 2.75, 15.9   # cm del eje temporal (a la izquierda, las etiquetas de los carriles)

CRONOLOGIAS = {
    'CAN': {
        'fases': [(1969, 1987, (252, 236, 214), 'Regionalismo cerrado'),
                  (1987, 2027, (222, 234, 246), 'Regionalismo abierto')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1969, 'fundación', 'bw'), (1973, 'entra Venezuela', 'aw'),
                (1976, 'sale Chile', 'bw'), (2006, 'sale Venezuela', 'a'), (2023, 'Bolivia, también en MERCOSUR', 'be')]),
            ('Comercio', (233, 160, 40), [
                (1969, 'zona de libre comercio en etapas', 'bw'), (1993, 'zona de libre comercio plena', 'ae'),
                (1995, 'arancel exterior común', 'b'), (2007, 'se permite no aplicarlo', 'a'),
                (2015, 'queda sin efecto', 'b'), (2026, 'guerra arancelaria', 'ae')]),
            ('Inversión extranjera', (200, 76, 58), [
                (1970, 'Decisión 24: control del capital extranjero', 'aw'), (1987, 'Decisión 220: flexibiliza', 'b'),
                (1991, 'Decisión 291: trato nacional', 'aw')]),
            ('Instituciones y personas', (30, 75, 135), [
                (1979, 'Tribunal de Justicia', 'a'), (1987, 'Protocolo de Quito', 'b'),
                (1996, 'Protocolo de Trujillo: nace la CAN', 'a'), (2021, 'Estatuto Migratorio Andino', 'be')]),
        ],
    },
}


def x(anio):
    return X0 + (anio - A0) / (A1 - A0) * (X1 - X0)


def main(clave):
    C = CRONOLOGIAS[clave]
    n = len(C['carriles'])
    paso = 1.15
    ys = [(n - 1 - i) * paso for i in range(n)]
    out = [f'% Generado por Code/cronologia_bloque.py ({clave}).', '\\begin{tikzpicture}[font=\\sffamily]']
    alto = ys[0] + 0.75
    for i, (a, b, rgb, texto) in enumerate(C['fases']):
        out.append('  \\definecolor{fase%d}{RGB}{%d,%d,%d}' % (i, *rgb))
        out.append(f'  \\fill[fase{i}] ({x(a):.2f},-0.6) rectangle ({x(b):.2f},{alto:.2f});')
        out.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize\\itshape, text=black!65] at ({(x(a) + x(b)) / 2:.2f},{alto - 0.03:.2f}) {{{texto}}};')
    for d in range(1970, 2030, 10):
        out.append(f'  \\draw[black!15, line width=0.3pt] ({x(d):.2f},-0.6) -- ({x(d):.2f},{alto - 0.35:.2f});')
    out.append(f'  \\draw[black!70, line width=0.5pt, -{{Stealth[length=4pt]}}] ({X0:.2f},-0.6) -- ({X1 + 0.1:.2f},-0.6);')
    for d in range(1970, 2030, 10):
        out.append(f'  \\draw[black!70] ({x(d):.2f},-0.6) -- ++(0,-0.07) node[below, font=\\sffamily\\scriptsize, inner sep=1.5pt] {{{d}}};')
    for i, ((nombre, rgb, hitos), y) in enumerate(zip(C['carriles'], ys)):
        out.append('  \\definecolor{carril%d}{RGB}{%d,%d,%d}' % (i, *rgb))
        out.append(f'  \\node[anchor=east, align=right, font=\\sffamily\\scriptsize\\bfseries, text=carril{i}] at ({X0 - 0.1:.2f},{y:.2f}) {{{nombre}}};')
        out.append(f'  \\draw[carril{i}, line width=1.4pt] ({x(hitos[0][0]):.2f},{y:.2f}) -- ({X1:.2f},{y:.2f});')
        for anio, texto, pos in hitos:
            px = x(anio)
            out.append(f'  \\fill[white] ({px:.2f},{y:.2f}) circle (1.6pt); \\draw[carril{i}!80!black, line width=0.6pt] ({px:.2f},{y:.2f}) circle (1.6pt);')
            vert, dy = ('south', 0.09) if pos.startswith('a') else ('north', -0.09)
            hor = {'': '', 'e': ' east', 'w': ' west'}[pos[1:]]
            dx = {'': 0, 'e': 0.1, 'w': -0.1}[pos[1:]]
            out.append(f'  \\node[anchor={vert}{hor}, font=\\sffamily\\tiny, inner sep=0.6pt, align=center] '
                       f'at ({px + dx:.2f},{y + dy:.2f}) {{{anio} {texto}}};')
    out.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / f'{clave}_cronologia.tikz'
    destino.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main(sys.argv[1])
