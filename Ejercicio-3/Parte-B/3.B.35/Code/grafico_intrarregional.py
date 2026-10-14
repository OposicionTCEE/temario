#!/usr/bin/env python3
"""Genera Img/<GRUPO>_comercio_intrarregional.tikz (pgfplots, dos paneles) a partir de Code/datos/exportaciones_bilaterales.csv.

(a) Cuota de las exportaciones intrarregionales en las exportaciones totales (%), con los hitos del proceso.
(b) Exportaciones intrarregionales y totales (miles de millones de dólares corrientes, escala logarítmica).
Los años en que algún miembro no declara se omiten y la línea une los años vecinos (se indica en el pie de la figura).

Uso, desde la carpeta del tema:
  python3 Code/grafico_intrarregional.py MCCA
  bash Code/generar_figura.sh MCCA_comercio_intrarregional
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402

HITOS = {  # año: texto (se dibujan como líneas verticales en el panel a)
    'MCCA': [(1969, 'Guerra (1969)'), (1980, 'Crisis de los ochenta'),
             (1991, 'SICA (1991)'), (2006, 'DR-CAFTA (2006)'), (2017, 'Unión aduanera (2017)')],
    'CAN': [(1976, 'Sale Chile (1976)'), (1987, 'Protocolo de Quito (1987)'), (1993, 'Zona de libre comercio (1993)'),
            (2006, 'Sale Venezuela (2006)'), (2015, 'Arancel común sin efecto (2015)')],
    'MERCOSUR': [(1991, 'Asunción (1991)'), (1995, 'AEC (1995)'), (1999, 'Devaluación del real (1999)'),
                 (2002, 'Crisis argentina (2002)'), (2012, 'Entra Venezuela (2012)')],
    'NAFTA': [(1989, 'CUSFTA (1989)'), (1994, 'NAFTA (1994)'), (2001, 'China, OMC (2001)'), (2020, 'USMCA (2020)')],
}
COLOR = {'MCCA': (200, 76, 58), 'CAN': (233, 160, 40), 'NAFTA': (30, 75, 135), 'MERCOSUR': (30, 75, 135)}
YMAX = {'MCCA': 45, 'CAN': 30, 'NAFTA': 90, 'MERCOSUR': 45}  # techo del panel (a): deja sitio a las etiquetas de los hitos


def main(grupo):
    filas = dc.lee_csv()
    anios = sorted({a for (e, a, s) in filas if e in dc.GRUPOS[grupo][0]})
    c = dc.cuadro(grupo, anios[0], anios[-1], filas)
    cuota = ' '.join(f'({a},{q:.2f})' if q is not None else f'({a},nan)' for a, _, _, q, _, _ in c)
    intra = ' '.join(f'({a},{i / 1000:.4f})' if q is not None else f'({a},nan)' for a, i, _, q, _, _ in c)
    total = ' '.join(f'({a},{t / 1000:.4f})' if q is not None else f'({a},nan)' for a, _, t, q, _, _ in c)
    r, g, b = COLOR[grupo]
    con_dato = [a for a, _, _, q, _, _ in c if q is not None]
    x0, x1 = min(con_dato), max(con_dato)
    ymax = YMAX[grupo]
    vlines = []
    for anio, texto in HITOS[grupo]:
        vlines.append(f'    \\draw[black!40, densely dashed, line width=0.4pt] (axis cs:{anio},0) -- (axis cs:{anio},{ymax});')
        vlines.append(f'    \\node[rotate=90, anchor=north east, font=\\sffamily\\tiny, text=black!70, inner sep=1.2pt] '
                      f'at (axis cs:{anio},{ymax - 0.4}) {{{texto}}};')
    out = [
        f'% Generado por Code/grafico_intrarregional.py ({grupo}) con Code/datos/exportaciones_bilaterales.csv.',
        f'\\definecolor{{cbloque}}{{RGB}}{{{r},{g},{b}}}',
        '\\begin{tikzpicture}[font=\\sffamily]',
        '  \\begin{axis}[name=a, width=7.9cm, height=6.2cm, xmin=%d, xmax=%d, ymin=0, ymax=%d,' % (x0 - 1, x1 + 1, ymax),
        '      xtick={1960,1970,1980,1990,2000,2010,2020}, x tick label style={/pgf/number format/1000 sep={}},',
        '      ylabel={\\% de las exportaciones totales}, ylabel style={font=\\sffamily\\scriptsize},',
        '      tick label style={font=\\sffamily\\scriptsize}, title={(a) Cuota intrarregional},',
        '      title style={font=\\sffamily\\small}, axis lines*=left, unbounded coords=discard,',
        '      ymajorgrids, grid style={black!8}]',
        f'    \\addplot[cbloque, line width=1.2pt, mark=none] coordinates {{{cuota}}};',
        *vlines,
        '  \\end{axis}',
        '  \\begin{axis}[at={(a.east)}, anchor=west, xshift=1.15cm, width=7.9cm, height=6.2cm, xmin=%d, xmax=%d,' % (x0 - 1, x1 + 1),
        '      ymode=log, log basis y=10, log ticks with fixed point, ytick={0.1,1,10,100,1000}, y tick label style={/pgf/number format/1000 sep={.}, /pgf/number format/use comma}, xtick={1960,1970,1980,1990,2000,2010,2020},',
        '      x tick label style={/pgf/number format/1000 sep={}}, ylabel={miles de millones de USD (escala log.)},',
        '      ylabel style={font=\\sffamily\\scriptsize}, tick label style={font=\\sffamily\\scriptsize},',
        '      title={(b) Exportaciones}, title style={font=\\sffamily\\small}, axis lines*=left, unbounded coords=discard,',
        '      ymajorgrids, grid style={black!8}, legend style={font=\\sffamily\\scriptsize, draw=none, fill=none,',
        '      at={(0.02,0.98)}, anchor=north west}, legend cell align=left]',
        f'    \\addplot[black!55, line width=1pt, mark=none] coordinates {{{total}}};',
        '    \\addlegendentry{Totales}',
        f'    \\addplot[cbloque, line width=1.2pt, mark=none] coordinates {{{intra}}};',
        '    \\addlegendentry{Intrarregionales}',
        '  \\end{axis}',
        '\\end{tikzpicture}',
    ]
    destino = dc.TEMA / 'Img' / f'{grupo}_comercio_intrarregional.tikz'
    destino.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main(sys.argv[1])
