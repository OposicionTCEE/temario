#!/usr/bin/env python3
"""Genera Img/CEFTA_miembros.tikz: miembros del CEFTA (1993-2026), su salida hacia la UE y la fase de adhesión de los actuales.

Fechas comprobadas en octubre de 2026 (Consejo de la UE, Comisión Europea y Secretaría del CEFTA; fuentes en la bibliografía).
Uso, desde la carpeta del tema:
  python3 Code/cefta_figura.py
  bash Code/generar_figura.sh CEFTA_miembros
"""
from pathlib import Path

# (país, entrada en el CEFTA, salida del CEFTA = entrada en la UE o None)
ANTIGUOS = [
    ('Polonia', 1993, 2004), ('Hungría', 1993, 2004), ('Chequia', 1993, 2004), ('Eslovaquia', 1993, 2004),
    ('Eslovenia', 1996, 2004), ('Rumanía', 1997, 2007), ('Bulgaria', 1999, 2007), ('Croacia', 2003, 2013),
]
# (país, entrada en el CEFTA, año de candidatura, año de apertura de negociaciones, situación en octubre de 2026)
ACTUALES = [
    ('Macedonia del Norte', 2006, 2005, 2022, 'sin capítulos abiertos (reforma constitucional)'),
    ('Montenegro', 2007, 2010, 2012, '21 capítulos cerrados; cierre previsto a finales de 2026'),
    ('Serbia', 2007, 2012, 2014, 'bloqueada desde 2021 (grupo 3 sin abrir)'),
    ('Albania', 2007, 2014, 2022, '4 capítulos cerrados'),
    ('Moldavia', 2007, 2022, 2024, 'abre nuevos grupos de capítulos (2026)'),
    ('Bosnia y Herzegovina', 2007, 2022, None, 'apertura acordada en 2024, sin conferencia'),
    ('Kosovo', 2007, None, None, 'solicitud en 2022; candidato potencial'),
]
A0, A1, X0, X1 = 1991, 2027, 3.4, 12.6


def x(a):
    return X0 + (a - A0) / (A1 - A0) * (X1 - X0)


def main():
    o = ['% Generado por Code/cefta_figura.py.',
         '\\definecolor{cue}{RGB}{70,110,170}', '\\definecolor{ccefta}{RGB}{233,160,40}',
         '\\begin{tikzpicture}[font=\\sffamily]']
    paso = 0.42
    filas = len(ANTIGUOS) + len(ACTUALES) + 1   # una fila de separación
    y0 = 0.0
    yb = y0 - (filas - 1) * paso - 0.35
    for d in range(1995, 2030, 5):
        o.append(f'  \\draw[black!12, line width=0.3pt] ({x(d):.2f},{y0 + 0.3:.2f}) -- ({x(d):.2f},{yb:.2f});')
        o.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize, inner sep=2pt] at ({x(d):.2f},{yb:.2f}) {{{d}}};')
    o.append(f'  \\draw[black!70, line width=0.5pt, -{{Stealth[length=4pt]}}] ({X0:.2f},{yb:.2f}) -- ({X1 + 0.1:.2f},{yb:.2f});')
    o.append(f'  \\node[anchor=west, font=\\sffamily\\scriptsize\\bfseries] at (0,{y0 + 0.45:.2f}) {{Miembros del CEFTA original (1992)}};')
    for k, (pais, ent, sal) in enumerate(ANTIGUOS):
        y = y0 - k * paso
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize] at ({X0 - 0.1:.2f},{y:.2f}) {{{pais}}};')
        o.append(f'  \\fill[ccefta] ({x(ent):.2f},{y - 0.12:.2f}) rectangle ({x(sal):.2f},{y + 0.12:.2f});')
        o.append(f'  \\fill[cue!40] ({x(sal):.2f},{y - 0.12:.2f}) rectangle ({x(2026):.2f},{y + 0.12:.2f});')
        o.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, text=black!75] at ({x(sal) + 0.05:.2f},{y:.2f}) {{en la UE, {sal}}};')
    ys = y0 - len(ANTIGUOS) * paso
    o.append(f'  \\node[anchor=west, font=\\sffamily\\scriptsize\\bfseries] at (0,{ys - 0.05:.2f}) {{Miembros del CEFTA 2006}};')
    o.append(f'  \\node[anchor=west, font=\\sffamily\\scriptsize\\bfseries] at ({X1 + 0.35:.2f},{ys - 0.05:.2f}) {{Adhesión a la UE, octubre de 2026}};')
    for k, (pais, ent, cand, neg, sit) in enumerate(ACTUALES):
        y = ys - (k + 1) * paso
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize] at ({X0 - 0.1:.2f},{y:.2f}) {{{pais}}};')
        o.append(f'  \\fill[ccefta] ({x(ent):.2f},{y - 0.12:.2f}) rectangle ({x(2026):.2f},{y + 0.12:.2f});')
        if cand:
            o.append(f'  \\node[diamond, fill=cue, inner sep=1.6pt] at ({x(cand + 0.5):.2f},{y:.2f}) {{}};')
        if neg:
            o.append(f'  \\node[circle, fill=cue!60!black, draw=white, line width=0.4pt, inner sep=1.7pt] at ({x(neg + 0.5):.2f},{y:.2f}) {{}};')
        o.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, text=black!80] at ({X1 + 0.35:.2f},{y:.2f}) {{{sit}}};')
    # Kosovo: representado por la UNMIK hasta 2024
    yk = ys - len(ACTUALES) * paso
    o.append(f'  \\fill[pattern={{Lines[angle=45, distance=2.2pt, line width=0.5pt]}}, pattern color=white] '
             f'({x(2007):.2f},{yk - 0.12:.2f}) rectangle ({x(2024.8):.2f},{yk + 0.12:.2f});')
    # Leyenda
    ly = yb - 0.75
    o.append(f'  \\fill[ccefta] ({X0:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 0.38:.2f},{ly:.2f}) {{miembro del CEFTA}};')
    o.append(f'  \\fill[cue!40] ({X0 + 2.4:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 2.78:.2f},{ly:.2f}) {{miembro de la UE}};')
    o.append(f'  \\node[diamond, fill=cue, inner sep=1.6pt] at ({X0 + 4.85:.2f},{ly:.2f}) {{}}; '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 5.0:.2f},{ly:.2f}) {{candidato a la UE}};')
    o.append(f'  \\node[circle, fill=cue!60!black, inner sep=1.7pt] at ({X0 + 7.05:.2f},{ly:.2f}) {{}}; '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 7.2:.2f},{ly:.2f}) {{negociaciones de adhesión abiertas}};')
    o.append(f'  \\fill[ccefta] ({X0 + 10.35:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\fill[pattern={{Lines[angle=45, distance=2.2pt, line width=0.5pt]}}, pattern color=white] '
             f'({X0 + 10.35:.2f},{ly - 0.08:.2f}) rectangle ++(0.35,0.16); '
             f'\\node[anchor=west, font=\\sffamily\\tiny] at ({X0 + 10.73:.2f},{ly:.2f}) {{Kosovo, representado por la UNMIK}};')
    o.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / 'CEFTA_miembros.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main()
