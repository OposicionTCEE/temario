#!/usr/bin/env python3
"""Genera Img/NAFTA_automovil.tikz: (a) reglas de origen del automóvil en el NAFTA y el USMCA;
(b) reparto de la producción de vehículos de Norteamérica entre EE. UU., Canadá y México, 1999 y 2024.

Datos:
  (a) Texto del USMCA (capítulo 4 y su apéndice sobre productos automotores), plenamente aplicable desde 2023:
      contenido regional de los turismos 62,5 % (NAFTA) y 75 % (USMCA); contenido de valor laboral (salario >= 16 $/h)
      40 % en turismos y 45 % en camiones ligeros; 70 % de las compras de acero y aluminio originarias de la región.
  (b) OICA, producción de vehículos de motor (turismos y comerciales): 1999 (tabla de 1999 de OICA) y 2024
      (OICA vía statbase.org).
También escribe la hoja NAFTA_vehiculos de Code/datos_3B35.xlsx (necesita openpyxl).
Uso, desde la carpeta del tema:  /tmp/v/bin/python Code/nafta_figura.py && bash Code/generar_figura.sh NAFTA_automovil
"""
from pathlib import Path

PRODUCCION = {  # año: (EE. UU., Canadá, México), unidades
    1999: (13024978, 3058813, 1549925),
    2024: (10522394, 1339288, 4202724),
}
REGLAS = [  # (concepto, NAFTA, USMCA)
    ('Contenido regional\\\\(turismos)', 62.5, 75),
    ('Contenido laboral\\\\($\\geq 16$ \\$/h)', 0, 40),
    ('Acero y aluminio\\\\de la región', 0, 70),
]
TEMA = Path(__file__).resolve().parent.parent


def hoja():
    from openpyxl import Workbook, load_workbook
    x = TEMA / 'Code' / 'datos' / 'tablas_figuras.xlsx'
    wb = load_workbook(x) if x.exists() else Workbook()
    if 'NAFTA_vehiculos' in wb.sheetnames:
        del wb['NAFTA_vehiculos']
    ws = wb.create_sheet('NAFTA_vehiculos')
    ws.append(['Producción de vehículos de motor en Norteamérica (unidades) y reglas de origen del automóvil'])
    ws.append(['Fuente: OICA (1999: tabla de producción de 1999; 2024: OICA vía statbase.org); reglas: texto del USMCA.'])
    ws.append([])
    ws.append(['Año', 'EE. UU.', 'Canadá', 'México', 'Total', 'Cuota de México (%)'])
    for a, (u, c, m) in PRODUCCION.items():
        ws.append([a, u, c, m, u + c + m, round(100 * m / (u + c + m), 1)])
    ws.append([])
    ws.append(['Regla de origen', 'NAFTA (%)', 'USMCA (%)'])
    for n, a, b in REGLAS:
        ws.append([n.replace('\\\\', ' ').replace('$\\geq 16$ \\$/h', '>= 16 USD/h'), a, b])
    wb.save(x)


def main():
    o = ['% Generado por Code/nafta_figura.py.',
         '\\definecolor{cnafta}{RGB}{150,170,200}', '\\definecolor{cusmca}{RGB}{30,75,135}',
         '\\definecolor{cusa}{RGB}{30,75,135}', '\\definecolor{ccan}{RGB}{200,60,60}', '\\definecolor{cmex}{RGB}{60,140,90}',
         '\\begin{tikzpicture}[font=\\sffamily]']
    # (a) Reglas de origen: barras agrupadas (altura 4 cm = 100 %)
    h, base = 4.0, 0.0
    o.append('  \\node[anchor=west, font=\\sffamily\\small] at (0,5.0) {(a) Reglas de origen del automóvil (\\%)};')
    o.append(f'  \\draw[black!70, line width=0.5pt] (0.3,{base}) -- (7.6,{base});')
    for t in (25, 50, 75, 100):
        y = base + h * t / 100
        o.append(f'  \\draw[black!12] (0.3,{y:.2f}) -- (7.6,{y:.2f}); \\node[anchor=east, font=\\sffamily\\tiny] at (0.3,{y:.2f}) {{{t}}};')
    for k, (n, a, b) in enumerate(REGLAS):
        x0 = 0.8 + k * 2.35
        for j, (v, col) in enumerate([(a, 'cnafta'), (b, 'cusmca')]):
            xa = x0 + j * 0.75
            if v:
                o.append(f'  \\fill[{col}] ({xa:.2f},{base}) rectangle ({xa + 0.65:.2f},{base + h * v / 100:.2f});')
                o.append(f'  \\node[anchor=south, font=\\sffamily\\tiny] at ({xa + 0.325:.2f},{base + h * v / 100:.2f}) {{{str(v).replace(".", ",")}}};')
            else:
                o.append(f'  \\node[anchor=south, font=\\sffamily\\tiny, text=black!55] at ({xa + 0.325:.2f},{base:.2f}) {{no}};')
        o.append(f'  \\node[anchor=north, align=center, font=\\sffamily\\tiny] at ({x0 + 0.7:.2f},{base - 0.05:.2f}) {{{n}}};')
    o.append('  \\fill[cnafta] (4.2,4.55) rectangle ++(0.3,0.18); \\node[anchor=west, font=\\sffamily\\tiny] at (4.53,4.64) {NAFTA};')
    o.append('  \\fill[cusmca] (5.4,4.55) rectangle ++(0.3,0.18); \\node[anchor=west, font=\\sffamily\\tiny] at (5.73,4.64) {USMCA};')
    # (b) Producción de vehículos: barras apiladas al 100 %
    o.append('  \\node[anchor=west, font=\\sffamily\\small] at (8.6,5.0) {(b) Producción de vehículos de Norteamérica (\\%)};')
    for k, (anio, (u, c, m)) in enumerate(PRODUCCION.items()):
        tot = u + c + m
        x0 = 9.6 + k * 2.6
        acum = 0.0
        for v, col, nom in [(u, 'cusa', 'EE.\\,UU.'), (c, 'ccan', 'Canadá'), (m, 'cmex', 'México')]:
            p = 100 * v / tot
            o.append(f'  \\fill[{col}] ({x0:.2f},{h * acum / 100:.2f}) rectangle ({x0 + 1.3:.2f},{h * (acum + p) / 100:.2f});')
            o.append(f'  \\node[font=\\sffamily\\tiny, text=white] at ({x0 + 0.65:.2f},{h * (acum + p / 2) / 100:.2f}) '
                     f'{{{nom} {str(round(p, 1)).replace(".", ",")}}};')
            acum += p
        o.append(f'  \\node[anchor=north, font=\\sffamily\\scriptsize] at ({x0 + 0.65:.2f},-0.05) {{{anio}}};')
        o.append(f'  \\node[anchor=south, font=\\sffamily\\tiny, text=black!70] at ({x0 + 0.65:.2f},{h + 0.05:.2f}) '
                 f'{{{str(round(tot / 1e6, 1)).replace(".", ",")} millones}};')
    o.append('\\end{tikzpicture}')
    (TEMA / 'Img' / 'NAFTA_automovil.tikz').write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito Img/NAFTA_automovil.tikz')


if __name__ == '__main__':
    main()
    try:
        hoja()
        print('Hoja NAFTA_vehiculos escrita')
    except ImportError:
        print('Falta openpyxl: no se escribe la hoja')
