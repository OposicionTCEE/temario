#!/usr/bin/env python3
"""Genera Img/EFTA_arquitectura.tikz: (a) círculos de integración con la UE; (b) miembros de la EFTA, 1960-2026.

Fechas comprobadas en octubre de 2026 (fuentes en el pie de la figura y en la bibliografía del tema).
Uso, desde la carpeta del tema:
  python3 Code/efta_figura.py
  bash Code/generar_figura.sh EFTA_arquitectura
"""
from pathlib import Path

# (país, entrada en la EFTA, salida de la EFTA o None, destino y año de entrada en la CEE/UE o '', [año de salida de la UE])
MIEMBROS = [
    ('Reino Unido', 1960, 1972, 'CEE, 1973', 2020),
    ('Dinamarca', 1960, 1972, 'CEE, 1973'),
    ('Portugal', 1960, 1985, 'CEE, 1986'),
    ('Austria', 1960, 1994, 'UE, 1995'),
    ('Suecia', 1960, 1994, 'UE, 1995'),
    ('Finlandia', 1961, 1994, 'UE, 1995'),
    ('Noruega', 1960, None, ''),
    ('Suiza', 1960, None, ''),
    ('Islandia', 1970, None, ''),
    ('Liechtenstein', 1991, None, ''),
]
A0, A1, X0, X1 = 1958, 2027, 3.0, 15.6


def x(a):
    return X0 + (a - A0) / (A1 - A0) * (X1 - X0)


def main():
    o = ['% Generado por Code/efta_figura.py.',
         '\\definecolor{cue}{RGB}{70,110,170}', '\\definecolor{cefta}{RGB}{110,165,215}',
         '\\definecolor{cotro}{RGB}{150,150,150}',
         '\\begin{tikzpicture}[font=\\sffamily]']
    # (a) Círculos de integración con la UE
    o += [
        '  \\node[anchor=west, font=\\sffamily\\small] at (0,6.6) {(a) Grados de integración con la UE};',
        '  \\fill[cue!15] (5.0,3.6) ellipse (2.9 and 1.75);',
        '  \\node[font=\\sffamily\\scriptsize\\bfseries, text=cue] at (5.0,3.9) {UE-27};',
        '  \\node[font=\\sffamily\\tiny, text=black!70, align=center] at (5.0,3.35) {unión aduanera y mercado interior};',
        '  \\draw[cue, line width=0.8pt, densely dashed] (6.6,3.6) ellipse (4.75 and 2.35);',
        '  \\node[font=\\sffamily\\scriptsize\\bfseries, text=cue, align=center] at (6.6,5.65) {Espacio Económico Europeo (30)};',
        '  \\node[font=\\sffamily\\tiny, text=black!70, align=center] at (6.6,5.3) {mercado interior sin unión aduanera ni políticas comunes};',
        '  \\fill[cefta, opacity=0.35] (11.2,3.6) ellipse (2.6 and 1.45);',
        '  \\node[font=\\sffamily\\scriptsize\\bfseries, text=cefta!60!black] at (12.4,4.75) {EFTA (4)};',
        '  \\node[font=\\sffamily\\scriptsize, align=center] at (10.0,3.6) {Islandia\\\\Liechtenstein\\\\Noruega};',
        '  \\node[font=\\sffamily\\scriptsize, align=center] at (12.75,3.6) {Suiza};',
        '  \\node[font=\\sffamily\\tiny, text=black!70, align=center] at (12.75,3.05) {acuerdos bilaterales\\\\(1972, 1999, 2004;\\\\Bilaterales III, 2026)};',
        # Otros grados
        '  \\node[draw=cotro, rounded corners=2pt, font=\\sffamily\\tiny, align=left, inner sep=3pt, anchor=north west] '
        '(tur) at (0.0,1.15) {\\textbf{Turquía}: unión aduanera con la UE\\\\desde 1995 (sin agricultura ni servicios)};',
        '  \\node[draw=cotro, rounded corners=2pt, font=\\sffamily\\tiny, align=left, inner sep=3pt, anchor=north west] '
        '(can) at (4.9,1.15) {\\textbf{Candidatos} de los Balcanes occidentales y Moldavia,\\\\socios del CEFTA: antesala de la adhesión};',
        '  \\node[draw=cotro, rounded corners=2pt, font=\\sffamily\\tiny, align=left, inner sep=3pt, anchor=north west] '
        '(ru) at (10.6,1.15) {\\textbf{Reino Unido}: Acuerdo de Comercio y\\\\Cooperación con la UE (2021), libre comercio};',
        '  \\draw[cotro, -{Stealth[length=3pt]}] (tur.north) -- (2.6,2.35);',
        '  \\draw[cotro, -{Stealth[length=3pt]}] (can.north) -- (5.6,1.9);',
        '  \\draw[cotro, -{Stealth[length=3pt]}] (ru.north) -- (8.5,1.6);',
    ]
    # (b) Miembros de la EFTA
    y0, paso = -1.2, 0.42
    o.append(f'  \\node[anchor=west, font=\\sffamily\\small] at (0,{y0 + 0.65:.2f}) {{(b) Miembros de la EFTA y salida hacia la CEE o la UE}};')
    yb = y0 - (len(MIEMBROS) - 1) * paso - 0.35
    for d in range(1960, 2030, 10):
        o.append(f'  \\draw[black!12, line width=0.3pt] ({x(d):.2f},{y0 + 0.25:.2f}) -- ({x(d):.2f},{yb:.2f});')
        o.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize, inner sep=2pt] at ({x(d):.2f},{yb:.2f}) {{{d}}};')
    o.append(f'  \\draw[black!70, line width=0.5pt, -{{Stealth[length=4pt]}}] ({X0:.2f},{yb:.2f}) -- ({X1 + 0.1:.2f},{yb:.2f});')
    for k, (pais, ent, sal, dest, *brexit) in enumerate(MIEMBROS):
        y = y0 - k * paso
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize] at ({X0 - 0.1:.2f},{y:.2f}) {{{pais}}};')
        fin = sal + 1 if sal else 2026
        o.append(f'  \\fill[cefta] ({x(ent):.2f},{y - 0.12:.2f}) rectangle ({x(fin):.2f},{y + 0.12:.2f});')
        if sal:
            fin_ue = brexit[0] + 1 if brexit else 2026
            o.append(f'  \\fill[cue!35] ({x(fin):.2f},{y - 0.12:.2f}) rectangle ({x(fin_ue):.2f},{y + 0.12:.2f});')
            if brexit:
                o.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, text=black!75] at ({x(fin_ue) + 0.05:.2f},{y:.2f}) {{sale de la UE, {brexit[0]}}};')
            o.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, text=black!75] at ({x(fin) + 0.05:.2f},{y:.2f}) {{en la {dest}}};')
    ly = yb - 0.75
    o.append(f'  \\fill[cefta] ({X0:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 0.38:.2f},{ly:.2f}) {{miembro de la EFTA}};')
    o.append(f'  \\fill[cue!35] ({X0 + 3.0:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 3.38:.2f},{ly:.2f}) {{miembro de la CEE o la UE}};')
    o.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, text=black!70] at ({X0 + 6.6:.2f},{ly:.2f}) '
             '{Finlandia, asociada desde 1961 y miembro de pleno derecho desde 1986.};')
    o.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / 'EFTA_arquitectura.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main()
