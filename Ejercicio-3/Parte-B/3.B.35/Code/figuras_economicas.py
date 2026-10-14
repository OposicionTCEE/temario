#!/usr/bin/env python3
"""Figuras económicas de un bloque (3.B.35), con los indicadores de Code/indicadores_bloque.py.

  Img/<G>_comercio_intrarregional.tikz  (a) cuota intrarregional, (b) intensidad, (c) exportaciones (escala log.)
  Img/<G>_composicion.tikz              (a) manufacturas en las exportaciones dentro y fuera del bloque;
                                        (b) composición por secciones de la CUCI en el último año
  Img/<G>_complementariedad.tikz        (a) complementariedad entre socios y con los mercados de referencia, último año;
                                        (b) su evolución; (c) saldo de cada miembro con el bloque (% del PIB);
                                        (d) reparto de las exportaciones de manufacturas dentro del bloque
Las series temporales llevan al fondo las etapas de la cronología del acuerdo (Code/cronologia_acuerdo.py), con los
mismos colores. Paleta categórica de referencia validada (orden fijo; dataviz), letra de 8 puntos, 16 cm de ancho.
Uso, desde la carpeta del tema:
  /ruta/a/python-con-openpyxl Code/figuras_economicas.py MCCA
  bash Code/generar_figura.sh MCCA_comercio_intrarregional   (y MCCA_composicion, MCCA_complementariedad)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cronologia_acuerdo as ca  # noqa: E402
import datos_comercio as dc  # noqa: E402
import indicadores_bloque as ib  # noqa: E402

NOMBRES = {'GTM': 'Guatemala', 'SLV': 'El Salvador', 'HND': 'Honduras', 'NIC': 'Nicaragua', 'CRI': 'Costa Rica',
           'BOL': 'Bolivia', 'COL': 'Colombia', 'ECU': 'Ecuador', 'PER': 'Perú', 'CHL': 'Chile', 'VEN': 'Venezuela',
           'USA': 'EE.\\,UU.', 'CHN': 'China'}
PALETA = ['2A78D6', 'EB6834', '1BAF7A', 'EDA100', 'E87BA4', '008300', '6250D6', 'E34948']
REFERENCIAS = {'MCCA': ['USA'], 'CAN': ['USA', 'CHN']}
ESTILO = ('scale only axis, axis lines*=left, set layers, tick label style={font=\\sffamily\\footnotesize, '
          '/pgf/number format/assume math mode=true}, '
          'label style={font=\\sffamily\\footnotesize}, title style={font=\\sffamily\\small, anchor=south, yshift=-2pt}, '
          'ymajorgrids, grid style={black!10}, x tick label style={/pgf/number format/1000 sep={}}, '
          'y tick label style={/pgf/number format/use comma, /pgf/number format/1000 sep={.}}, clip=true, '
          'unbounded coords=discard')


def cabecera(grupo, nombre_fig):
    o = [f'% Generado por Code/figuras_economicas.py ({grupo}) con Code/datos_3B35.xlsx.',
         '\\begin{tikzpicture}[font=\\sffamily\\footnotesize]']
    o += ['  \\definecolor{s%d}{HTML}{%s}' % (i + 1, c) for i, c in enumerate(PALETA)]
    for k, rgb in ca.ETAPAS.items():
        o.append('  \\definecolor{et%s}{RGB}{%d,%d,%d}' % (k, *rgb))
    return o


def etapas(grupo, y0, y1, x0=1962, x1=2024):
    """Fondo con las etapas de la cronología, entre y0 e y1 y dentro del eje (la capa de fondo no se recorta)."""
    o = ['    \\begin{pgfonlayer}{axis background}']
    for a, b, tipo, _ in ca.CRONOLOGIAS[grupo]['etapas']:
        a, b = max(a, x0), min(b, x1)
        if a < b:
            o.append(f'      \\fill[et{tipo}] (axis cs:{a},{y0}) rectangle (axis cs:{b},{y1});')
    o.append('    \\end{pgfonlayer}')
    return o


def techo(v, paso):
    return paso * math.ceil(v * 1.08 / paso)


def coords(pares):
    return ' '.join(f'({a},{y:.4f})' for a, y in pares)


def fig_integracion(grupo, it, x0=1962, x1=2024):
    filas = dc.lee_csv()
    anios = sorted({a for (e, a, s) in filas if e in dc.GRUPOS[grupo][0]})
    cuadro = [f for f in dc.cuadro(grupo, anios[0], anios[-1], filas) if f[3] is not None]
    ymax_a = techo(max(f[3] for f in cuadro), 5)
    ymax_b = techo(max(i for _, _, _, i in it), 20)
    o = cabecera(grupo, 'integracion')
    w, h, paso = 3.75, 4.0, 5.3
    comunes = f'{ESTILO}, width={w}cm, height={h}cm, xmin={x0}, xmax={x1}, xtick={{1960,1980,2000,2020}}'
    # (a) cuota
    o += [f'  \\begin{{axis}}[{comunes}, at={{(0,0)}}, ymin=0, ymax={ymax_a}, title={{(a) Cuota intrarregional}},'
          f' ylabel={{\\% de las exportaciones}}]', *etapas(grupo, 0, ymax_a),
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{coords((f[0], f[3]) for f in cuadro)}}};',
          '  \\end{axis}']
    # (b) intensidad
    o += [f'  \\begin{{axis}}[{comunes}, at={{({paso}cm,0cm)}}, ymin=0, ymax={ymax_b}, title={{(b) Intensidad}},'
          f' ylabel={{cuota / peso en el comercio mundial}}]', *etapas(grupo, 0, ymax_b),
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{coords((a, i) for a, _, _, i in it)}}};',
          '  \\end{axis}']
    # (c) exportaciones, escala logarítmica
    tot = [(f[0], f[2] / 1000) for f in cuadro]
    intra = [(f[0], f[1] / 1000) for f in cuadro]
    lo = 10 ** math.floor(math.log10(min(y for _, y in intra)))
    hi = 10 ** math.ceil(math.log10(max(y for _, y in tot)))
    o += [f'  \\begin{{axis}}[{comunes}, at={{({2 * paso}cm,0cm)}}, ymode=log, ymin={lo}, ymax={hi}, log ticks with fixed point,'
          f' title={{(c) Exportaciones}}, ylabel={{miles de millones de USD (log.)}}]', *etapas(grupo, lo, hi),
          f'    \\addplot[black!55, line width=1.1pt, mark=none] coordinates {{{coords(tot)}}};',
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{coords(intra)}}};',
          f'    \\node[anchor=south east, inner sep=1pt, text=black!75] at (axis cs:{tot[-1][0]},{tot[-1][1] * 1.15:.4f}) {{totales}};',
          f'    \\node[anchor=north east, inner sep=1pt, text=black!75] at (axis cs:{intra[-1][0]},{intra[-1][1] / 1.25:.4f}) {{a los socios}};',
          '  \\end{axis}', '\\end{tikzpicture}']
    return o


def fig_composicion(grupo, comp, cm, x0=1962, x1=2024):
    o = cabecera(grupo, 'composicion')
    ymax = 100
    top = max(cm, key=lambda x: x[1])
    o += [f'  \\begin{{axis}}[{ESTILO}, width=5.6cm, height=4.4cm, xmin={x0}, xmax={x1}, ymin=0, ymax={ymax},'
          ' xtick={1960,1970,1980,1990,2000,2010,2020}, title={(a) Manufacturas en las exportaciones},'
          ' ylabel={\\% de cada destino}, at={(0cm,0cm)}]', *etapas(grupo, 0, ymax),
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{coords((a, d) for a, d, f in cm)}}};',
          f'    \\addplot[s2, line width=1.3pt, mark=none] coordinates {{{coords((a, f) for a, d, f in cm)}}};',
          # rótulos junto a cada línea, donde no hay otra: «a los socios» sobre su máximo y «fuera» al principio, abajo
          f'    \\node[anchor=south, inner sep=1.5pt, text=black!80] at (axis cs:{top[0]},{top[1] + 2:.1f}) {{a los socios}};',
          f'    \\node[anchor=south west, inner sep=1.5pt, text=black!80] at (axis cs:{cm[0][0]},{max(f for a, d, f in cm if a < cm[0][0] + 20) + 3:.1f}) {{fuera del bloque}};',
          '  \\end{axis}']
    ult = max(comp)
    d, f = comp[ult]
    cats = []
    for secs, nombre in ib.SECCIONES:
        vd = 100 * sum(d[s] for s in secs) / sum(d.values())
        vf = 100 * sum(f[s] for s in secs) / sum(f.values())
        cats.append((nombre, vd, vf))
    ylab = ','.join(n for n, _, _ in cats)
    xmax = techo(max(max(vd, vf) for _, vd, vf in cats), 10)
    o += [f'  \\begin{{axis}}[{ESTILO.replace("ymajorgrids", "xmajorgrids")}, at={{(9.9cm,0cm)}}, anchor=south west, width=4.45cm, height=4.4cm,'
          f' xbar, bar width=4.2pt, y dir=reverse, symbolic y coords={{{ylab}}}, ytick=data, xmin=0, xmax={xmax},'
          f' enlarge y limits=0.07, title={{(b) Composición, {ult} (\\%)}},'
          ' nodes near coords, nodes near coords style={font=\\sffamily\\footnotesize, text=black!75, /pgf/number format/fixed,'
          ' /pgf/number format/precision=0, /pgf/number format/assume math mode=true}, point meta=x,'
          ' legend style={font=\\sffamily\\footnotesize, draw=none, fill=none, at={(0.5,-0.13)}, anchor=north, legend columns=2,'
          ' /tikz/every even column/.append style={column sep=0.3cm}}, legend cell align=left, area legend, reverse legend]',
          # primero «fuera», que pgfplots pone debajo: así «a los socios» queda encima en cada categoría
          '    \\addplot[draw=none, fill=s2] coordinates {' + ' '.join(f'({vf:.1f},{n})' for n, _, vf in cats) + '};',
          '    \\addplot[draw=none, fill=s1] coordinates {' + ' '.join(f'({vd:.1f},{n})' for n, vd, _ in cats) + '};',
          '    \\legend{fuera del bloque, a los socios}',
          '  \\end{axis}', '\\end{tikzpicture}']
    return o


def fig_complementariedad(grupo, cp, sd, rm, x0=1962, x1=2024):
    miembros_hoy = dc.miembros(grupo, 2023)
    refs = REFERENCIAS[grupo]
    color = {e: f's{i + 1}' for i, e in enumerate(dc.GRUPOS[grupo][0])}
    o = cabecera(grupo, 'complementariedad')
    # (a) matriz del último año
    ult = max(cp)
    c = cp[ult]
    cols = miembros_hoy + refs
    cw, ch = 0.78, 0.46
    xm, ytop = 2.0, 9.2
    vmax = max(c.values())
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at (0,{ytop + 1.55:.2f}) {{(a) Complementariedad, {ult}}};')
    for jx, j in enumerate(cols):
        o.append(f'  \\node[anchor=south west, rotate=40, inner sep=1pt] at ({xm + (jx + 0.3) * cw:.2f},{ytop + 0.05:.2f}) {{{NOMBRES[j]}}};')
    for iy, i in enumerate(miembros_hoy):
        y = ytop - (iy + 1) * ch
        o.append(f'  \\node[anchor=east, inner sep=1pt] at ({xm - 0.08:.2f},{y + ch / 2:.2f}) {{{NOMBRES[i]}}};')
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
    xs = xm + len(miembros_hoy) * cw
    o.append(f'  \\draw[black!45, line width=0.5pt] ({xs:.2f},{ytop - len(miembros_hoy) * ch - 0.05:.2f}) -- ({xs:.2f},{ytop + 0.05:.2f});')
    o.append(f'  \\node[anchor=north west, inner sep=1pt, text=black!70] at ({xm - 1.95:.2f},{ytop - len(miembros_hoy) * ch - 0.12:.2f}) '
             '{exportador (filas), importador (columnas); 0-100};')
    # (b) evolución de la media
    medias = []
    for a in sorted(cp):
        mm = dc.miembros(grupo, a)
        intra = [x for (i, j), x in cp[a].items() if j in mm]
        fila = [a, sum(intra) / len(intra) if intra else None]
        for r in refs:
            xr = [x for (i, j), x in cp[a].items() if j == r]
            fila.append(sum(xr) / len(xr) if xr else None)
        medias.append(fila)
    ymax_b = techo(max(v for f in medias for v in f[1:] if v is not None), 10)
    o += [f'  \\begin{{axis}}[{ESTILO}, at={{(9.3cm,{ytop - 2.95:.2f}cm)}}, width=6.1cm, height=3.0cm, xmin={x0}, xmax={x1}, ymin=0,'
          f' ymax={ymax_b}, xtick={{1960,1970,1980,1990,2000,2010,2020}}, title={{(b) Complementariedad media}}]',
          *etapas(grupo, 0, ymax_b),
          '    \\addplot[s1, line width=1.3pt, mark=*, mark size=1.6pt] coordinates {' + coords((f[0], f[1]) for f in medias if f[1] is not None) + '};']
    estilos_ref = ['black!60', 's7']
    for k, r in enumerate(refs):
        o.append(f'    \\addplot[{estilos_ref[k]}, line width=1.1pt, densely dashed, mark=*, mark size=1.4pt, mark options={{solid}}] coordinates {{'
                 + coords((f[0], f[2 + k]) for f in medias if f[2 + k] is not None) + '};')
    ultimo = medias[-1]
    o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{ultimo[0]},{ultimo[1]:.1f}) {{entre socios}};')
    for k, r in enumerate(refs):
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{ultimo[0]},{ultimo[2 + k]:.1f}) {{con {NOMBRES[r]}}};')
    o.append('  \\end{axis}')
    # (c) saldos en % del PIB
    vals = [v for _, r in sd for v in r.values()]
    lo, hi = math.floor(min(vals) / 2) * 2, math.ceil(max(vals) / 2) * 2
    o += [f'  \\begin{{axis}}[{ESTILO}, at={{(1.1cm,0cm)}}, width=5.9cm, height=4.0cm, xmin={x0}, xmax={x1}, ymin={lo}, ymax={hi},'
          ' xtick={1960,1970,1980,1990,2000,2010,2020}, title={(c) Saldo con el resto del bloque}, ylabel={\\% del PIB}]',
          *etapas(grupo, lo, hi), f'    \\draw[black!60, line width=0.5pt] (axis cs:{x0},0) -- (axis cs:{x1},0);']
    for e in dc.GRUPOS[grupo][0]:
        pts = [(a, r[e]) for a, r in sd if e in r]
        if pts:
            o.append(f'    \\addplot[{color[e]}, line width=1.1pt, mark=none] coordinates {{{coords(pts)}}};')
    o.append('  \\end{axis}')
    # (d) reparto de las exportaciones de manufacturas dentro del bloque (áreas apiladas)
    anios = sorted(rm)
    o += [f'  \\begin{{axis}}[{ESTILO}, at={{(9.3cm,0cm)}}, width=6.1cm, height=4.0cm, xmin={anios[0]}, xmax={anios[-1]}, ymin=0, ymax=100,'
          ' xtick={1960,1970,1980,1990,2000,2010,2020}, title={(d) Reparto de las manufacturas vendidas a los socios},'
          ' ylabel={\\%}, stack plots=y, area style]']
    for e in dc.GRUPOS[grupo][0]:
        o.append(f'    \\addplot[draw=white, line width=0.4pt, fill={color[e]}] coordinates {{'
                 + coords((a, rm[a].get(e, 0.0)) for a in anios) + '} \\closedcycle;')
    o.append('  \\end{axis}')
    # leyenda común de (c) y (d)
    x = 1.1
    for e in dc.GRUPOS[grupo][0]:
        o.append(f'  \\fill[{color[e]}] ({x:.2f},-1.15) rectangle ({x + 0.4:.2f},-0.95);')
        o.append(f'  \\node[anchor=west, inner sep=1pt] at ({x + 0.45:.2f},-1.05) {{{NOMBRES[e]}}};')
        x += 0.75 + len(NOMBRES[e]) * 0.15
    o.append('\\end{tikzpicture}')
    return o


def main(grupo):
    it, comp, cm, cp, sd, rm = ib.main(grupo)
    for nombre, lineas in (('comercio_intrarregional', fig_integracion(grupo, it)), ('composicion', fig_composicion(grupo, comp, cm)),
                           ('complementariedad', fig_complementariedad(grupo, cp, sd, rm))):
        destino = dc.TEMA / 'Img' / f'{grupo}_{nombre}.tikz'
        destino.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
        print('Escrito', destino)


if __name__ == '__main__':
    main(sys.argv[1])
