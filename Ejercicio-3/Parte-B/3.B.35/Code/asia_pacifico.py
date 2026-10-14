#!/usr/bin/env python3
"""Genera Img/AsiaPacifico_acuerdos.tikz: pertenencia de las economías de Asia-Pacífico a la ASEAN, el RCEP, el CPTPP y el
Marco Económico del Indo-Pacífico (IPEF), con las solicitudes de adhesión al RCEP y al CPTPP. Sustituye a la antigua Fig1.png.

Situación en octubre de 2026 (fuentes en la bibliografía del tema): Timor Oriental entró en la ASEAN en 2025 y no está en
el RCEP; Reino Unido entró en el CPTPP en diciembre de 2024; Costa Rica concluyó su negociación de adhesión al CPTPP en mayo
de 2026; el RCEP abrió en septiembre de 2026 un grupo de trabajo para Bangladés, Chile, Hong Kong y Sri Lanka.
Uso, desde la carpeta del tema:
  python3 Code/asia_pacifico.py
  bash Code/generar_figura.sh AsiaPacifico_acuerdos
"""
from pathlib import Path

GRUPOS = [  # (región, [(código, nombre)])
    ('ASEAN', [('BRN', 'Brunéi'), ('KHM', 'Camboya'), ('PHL', 'Filipinas'), ('IDN', 'Indonesia'), ('LAO', 'Laos'),
               ('MYS', 'Malasia'), ('MMR', 'Myanmar'), ('SGP', 'Singapur'), ('THA', 'Tailandia'), ('TLS', 'Timor Oriental'),
               ('VNM', 'Vietnam')]),
    ('Asia oriental', [('CHN', 'China'), ('KOR', 'Corea del Sur'), ('HKG', 'Hong Kong'), ('JPN', 'Japón'), ('TWN', 'Taiwán')]),
    ('Asia meridional', [('BGD', 'Bangladés'), ('IND', 'India'), ('LKA', 'Sri Lanka')]),
    ('Oceanía', [('AUS', 'Australia'), ('FJI', 'Fiyi'), ('NZL', 'Nueva Zelanda')]),
    ('América', [('CAN', 'Canadá'), ('CHL', 'Chile'), ('CRI', 'Costa Rica'), ('ECU', 'Ecuador'), ('USA', 'EE.\\,UU.'),
                 ('MEX', 'México'), ('PER', 'Perú'), ('URY', 'Uruguay')]),
    ('Otros', [('ARE', 'Emiratos'), ('GBR', 'Reino Unido'), ('UKR', 'Ucrania')]),
]
FILAS = [  # (acuerdo, miembros, solicitudes)
    ('ASEAN', 'BRN KHM PHL IDN LAO MYS MMR SGP THA TLS VNM', ''),
    ('RCEP', 'BRN KHM PHL IDN LAO MYS MMR SGP THA VNM CHN KOR JPN AUS NZL', 'BGD LKA HKG CHL'),
    ('CPTPP', 'BRN MYS SGP VNM JPN AUS NZL CAN CHL MEX PER GBR', 'CRI URY CHN TWN ECU UKR IDN PHL ARE'),
    ('IPEF', 'BRN PHL IDN MYS SGP THA VNM KOR JPN IND AUS FJI NZL USA', ''),
]
COLORES = {'ASEAN': (200, 76, 58), 'RCEP': (233, 160, 40), 'CPTPP': (30, 75, 135), 'IPEF': (60, 140, 90)}


def main():
    paises = [(g, c, n) for g, lista in GRUPOS for c, n in lista]
    dx, dy, x0 = 0.42, 0.5, 1.4
    o = ['% Generado por Code/asia_pacifico.py.']
    for k, rgb in COLORES.items():
        o.append('\\definecolor{c%s}{RGB}{%d,%d,%d}' % (k, *rgb))
    o.append('\\begin{tikzpicture}[font=\\sffamily]')
    for k, (g, c, n) in enumerate(paises):
        o.append(f'  \\node[rotate=90, anchor=west, font=\\sffamily\\tiny, inner sep=1pt] at ({x0 + k * dx:.3f},0.1) {{{n}}};')
    ybot = -len(FILAS) * dy
    k = 0
    for g, lista in GRUPOS:
        xa, xb = x0 + k * dx - dx / 2, x0 + (k + len(lista) - 1) * dx + dx / 2
        o.append(f'  \\draw[black!50, line width=0.5pt] ({xa + 0.04:.3f},{ybot - 0.12:.3f}) -- ({xb - 0.04:.3f},{ybot - 0.12:.3f});')
        o.append(f'  \\node[anchor=north, font=\\sffamily\\tiny, text=black!70] at ({(xa + xb) / 2:.3f},{ybot - 0.15:.3f}) {{{g}}};')
        if k:
            o.append(f'  \\draw[black!25, line width=0.4pt] ({xa:.3f},0) -- ({xa:.3f},{ybot:.3f});')
        k += len(lista)
    for j, (nombre, miembros, solicitudes) in enumerate(FILAS):
        y = -(j + 0.5) * dy
        mm, ss = set(miembros.split()), set(solicitudes.split())
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize\\bfseries, text=c{nombre}] at ({x0 - 0.25:.2f},{y:.3f}) {{{nombre}}};')
        o.append(f'  \\draw[black!10, line width=0.3pt] ({x0 - dx / 2:.3f},{y:.3f}) -- ({x0 + (len(paises) - 0.5) * dx:.3f},{y:.3f});')
        for k, (g, c, n) in enumerate(paises):
            x = x0 + k * dx
            if c in mm:
                o.append(f'  \\fill[c{nombre}] ({x:.3f},{y:.3f}) circle (0.12);')
            elif c in ss:
                o.append(f'  \\draw[c{nombre}, line width=0.7pt] ({x:.3f},{y:.3f}) circle (0.105);')
    ly = ybot - 0.85
    o.append(f'  \\fill[black!70] ({x0:.2f},{ly:.2f}) circle (0.1); \\node[anchor=west, font=\\sffamily\\scriptsize] at ({x0 + 0.17:.2f},{ly:.2f}) {{miembro (octubre de 2026)}};')
    o.append(f'  \\draw[black!70, line width=0.7pt] ({x0 + 3.6:.2f},{ly:.2f}) circle (0.09); \\node[anchor=west, font=\\sffamily\\scriptsize] at ({x0 + 3.77:.2f},{ly:.2f}) {{solicitud de adhesión o negociación abierta (Costa Rica: negociación concluida en 2026)}};')
    o.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / 'AsiaPacifico_acuerdos.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main()
