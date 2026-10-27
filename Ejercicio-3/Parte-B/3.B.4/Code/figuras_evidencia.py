#!/usr/bin/env python3
"""Escribe las figuras con datos del anexo de olas y evidencia del tema 3.B.4 (27/10/2026).

Lee los CSV que prepara Code/datos_evidencia.py y escribe:
  Img/anx_olas_datos.tikz  (a) fusiones en la industria y la minería de EE. UU., 1895-1970 (NELSON y FTC);
                           (b) valor mundial de las fusiones transfronterizas, 1990-2025;
                           (c) número de fusiones transfronterizas con empresa comprada o comprador españoles.
  Img/anx_ciclo.tikz       (a) valor mundial de las fusiones transfronterizas en % de la capitalización bursátil
                           mundial, 1990-2024; (b) endurecimiento del crédito bancario en EE. UU. (media anual de la
                           SLOOS) frente a la variación anual del número mundial de operaciones, 1991-2025.
  Code/datos/tablas_figuras.csv  las series de cada panel, con su tratamiento, para el libro de datos.
Después: bash Code/generar_figura.sh anx_olas_datos y bash Code/generar_figura.sh anx_ciclo.
Uso, desde la carpeta del tema:  python3 -I Code/figuras_evidencia.py
"""
import csv
import statistics as st
from pathlib import Path

TEMA = Path(__file__).resolve().parent.parent
DATOS = TEMA / 'Code' / 'datos'
IMG = TEMA / 'Img'


def leer(nombre):
    with open(DATOS / nombre, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def coords(pares, dec=1):
    return ' '.join(f'({x},{round(y, dec)})' for x, y in pares)


hsus = leer('hsus_fusiones_1895_1970.csv')
nelson = [(int(r['año']), int(r['número'])) for r in hsus if r['serie'] == 'NELSON']
ftc = [(int(r['año']), int(r['número'])) for r in hsus if r['serie'] == 'FTC']

unc = leer('unctad_fusiones.csv')


def serie(economia, lado, indicador):
    return {int(r['año']): float(r['valor']) for r in unc
            if r['economía'] == economia and r['lado'] == lado and r['indicador'] == indicador}


valor_mundo = serie('Mundo', 'vendedor', 'valor')            # millones de dólares
numero_mundo = serie('Mundo', 'vendedor', 'número')
esp_vendedor = serie('España', 'vendedor', 'número')
esp_comprador = serie('España', 'comprador', 'número')

cap = {int(r['año']): float(r['valor_usd']) for r in leer('wdi_capitalizacion.csv') if r['economía'] == 'Mundo'}
ratio = [(a, 100 * valor_mundo[a] * 1e6 / cap[a]) for a in sorted(valor_mundo) if a in cap]

trimestres = {}
for r in leer('sloos_ci_grandes.csv'):
    trimestres.setdefault(int(r['fecha'][:4]), []).append(float(r['porcentaje_neto']))
sloos = {a: st.mean(v) for a, v in trimestres.items() if len(v) == 4}   # solo años completos
variacion = {a: 100 * (numero_mundo[a] / numero_mundo[a - 1] - 1) for a in numero_mundo if a - 1 in numero_mundo}
años_b = [a for a in sorted(variacion) if a in sloos]
xs, ys = [sloos[a] for a in años_b], [variacion[a] for a in años_b]
mx, my = st.mean(xs), st.mean(ys)
pendiente = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
ordenada = my - pendiente * mx
correlacion = st.correlation(xs, ys)
print(f'Panel (b) de anx_ciclo: {años_b[0]}-{años_b[-1]}, n = {len(años_b)}, correlación = {correlacion:.2f}, '
      f'pendiente = {pendiente:.2f}')

ETIQUETADOS = {2001: 'above right', 2002: 'below right', 2005: 'above', 2008: 'right', 2009: 'below left',
               2020: 'below', 2021: 'above', 2023: 'below left'}

olas = rf"""% Figura del anexo de olas y evidencia: las olas en los datos. Generada por Code/figuras_evidencia.py (no editar a mano).
% (a) Fusiones registradas en la industria y la minería de EE. UU., 1895-1970: NELSON (1895-1918) y FTC (1919-1970),
% Historical Statistics of the United States (1975), series V 38-39. (b) Valor de las fusiones transfronterizas netas en
% el mundo, 1990-2025, en miles de millones de dólares (UNCTAD, tabla anexa 5). (c) Número de fusiones transfronterizas
% netas con empresa comprada española y con comprador español (UNCTAD, tablas anexas 7 y 8).
% Generar con: bash Code/generar_figura.sh anx_olas_datos
\begin{{tikzpicture}}[font=\footnotesize]
  \begin{{axis}}[name=a, width=16cm, height=5.4cm, scale only axis=false, axis lines=left, ybar, bar width=2.5pt,
      xmin=1893, xmax=1972, ymin=0, ymax=2700, xtick={{1900,1910,...,1970}}, ytick={{0,500,...,2500}},
      xticklabel style={{/pgf/number format/1000 sep=}}, yticklabel style={{/pgf/number format/1000 sep=}},
      tick label style={{font=\scriptsize}}, ylabel={{operaciones}}, ylabel style={{font=\scriptsize}},
      legend style={{at={{(0.03,0.97)}}, anchor=north west, draw=none, font=\scriptsize, fill=none}},
      legend image code/.code={{\draw[#1, draw=none] (0cm,-0.1cm) rectangle (0.25cm,0.12cm);}},
      title={{\textbf{{(a) Estados Unidos: fusiones en la industria y la minería, 1895-1970}}}},
      title style={{font=\footnotesize, yshift=-2pt}}]
    \addplot[fill=black!40, draw=none, bar shift=0pt] coordinates {{{coords(nelson, 0)}}};
    \addlegendentry{{NELSON (1959)}}
    \addplot[fill=teal!60!black, draw=none, bar shift=0pt] coordinates {{{coords(ftc, 0)}}};
    \addlegendentry{{Comisión Federal de Comercio (FTC)}}
  \end{{axis}}
  \begin{{axis}}[at={{(a.south west)}}, anchor=north west, yshift=-1.5cm, width=7.6cm, height=4.6cm, axis lines=left,
      ybar, bar width=3pt, xmin=1988.5, xmax=2026.5, ymin=0, ymax=1150, xtick={{1990,2000,2010,2020}},
      ytick={{0,250,500,750,1000}}, xticklabel style={{/pgf/number format/1000 sep=}},
      yticklabel style={{/pgf/number format/1000 sep=}}, tick label style={{font=\scriptsize}},
      ylabel={{miles de millones de dólares}}, ylabel style={{font=\scriptsize}},
      title={{\textbf{{(b) Mundo: valor de las fusiones transfronterizas}}}}, title style={{font=\footnotesize}}]
    \addplot[fill=teal!60!black, draw=none, bar shift=0pt] coordinates {{{coords(sorted((a, v / 1000) for a, v in valor_mundo.items()))}}};
  \end{{axis}}
  \begin{{axis}}[at={{(a.south east)}}, anchor=north east, yshift=-1.5cm, width=7.6cm, height=4.6cm, axis lines=left,
      xmin=1988.5, xmax=2026.5, ymin=0, ymax=560, xtick={{1990,2000,2010,2020}}, ytick={{0,100,...,500}},
      xticklabel style={{/pgf/number format/1000 sep=}}, tick label style={{font=\scriptsize}},
      ylabel={{operaciones}}, ylabel style={{font=\scriptsize}},
      legend style={{at={{(0.03,0.97)}}, anchor=north west, draw=none, font=\scriptsize, fill=none}},
      title={{\textbf{{(c) España: número de fusiones transfronterizas}}}}, title style={{font=\footnotesize}}]
    \addplot[thick, teal!60!black, mark=*, mark size=1pt] coordinates {{{coords(sorted(esp_vendedor.items()), 0)}}};
    \addlegendentry{{empresa comprada española}}
    \addplot[thick, black!55, mark=square*, mark size=1pt] coordinates {{{coords(sorted(esp_comprador.items()), 0)}}};
    \addlegendentry{{comprador español}}
  \end{{axis}}
\end{{tikzpicture}}
"""

etiquetas = '\n'.join(
    f'    \\node[font=\\scriptsize, {pos}, inner sep=1.5pt] at (axis cs:{round(sloos[a], 1)},{round(variacion[a], 1)}) {{{a}}};'
    for a, pos in ETIQUETADOS.items() if a in años_b)
ciclo = rf"""% Figura del anexo de olas y evidencia: dos indicadores del ciclo. Generada por Code/figuras_evidencia.py (no editar a mano).
% (a) Valor de las fusiones transfronterizas netas en el mundo (UNCTAD, tabla anexa 5) en % de la capitalización bursátil
% mundial (Banco Mundial, CM.MKT.LCAP.CD), 1990-2024. (b) Media anual del porcentaje neto de bancos de EE. UU. que
% endurecen los criterios de los préstamos comerciales e industriales a empresas grandes y medianas (SLOOS) frente a la
% variación anual del número mundial de fusiones transfronterizas netas (UNCTAD, tabla anexa 7), {años_b[0]}-{años_b[-1]};
% recta de mínimos cuadrados. Correlación: {correlacion:.2f}.
% Generar con: bash Code/generar_figura.sh anx_ciclo
\begin{{tikzpicture}}[font=\footnotesize]
  \begin{{axis}}[name=a, width=7.6cm, height=5.2cm, axis lines=left, xmin=1988.5, xmax=2025.5, ymin=0, ymax=3.5,
      xtick={{1990,2000,2010,2020}}, ytick={{0,1,2,3}}, xticklabel style={{/pgf/number format/1000 sep=}},
      tick label style={{font=\scriptsize}}, ylabel={{\% de la capitalización bursátil}}, ylabel style={{font=\scriptsize}},
      title={{\textbf{{(a) Valor de las operaciones y capitalización}}}}, title style={{font=\footnotesize}}]
    \addplot[thick, teal!60!black, mark=*, mark size=1pt] coordinates {{{coords(ratio, 2)}}};
  \end{{axis}}
  \begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.6cm, width=7.6cm, height=5.2cm, axis lines=left,
      xmin=-30, xmax=65, ymin=-45, ymax=50, xtick={{-20,0,20,40,60}}, ytick={{-40,-20,0,20,40}},
      tick label style={{font=\scriptsize}}, xlabel={{bancos que endurecen el crédito (\% neto)}},
      ylabel={{variación del número de operaciones (\%)}}, label style={{font=\scriptsize}},
      title={{\textbf{{(b) Crédito bancario y actividad}}}}, title style={{font=\footnotesize}}]
    \addplot[only marks, mark=*, mark size=1.4pt, teal!60!black] coordinates {{{coords(list(zip(xs, ys)), 1)}}};
    \addplot[thick, black!55, domain=-28:62] {{{ordenada:.3f}+({pendiente:.4f})*x}};
    \draw[black!30] (axis cs:-30,0) -- (axis cs:65,0);
{etiquetas}
  \end{{axis}}
\end{{tikzpicture}}
"""

(IMG / 'anx_olas_datos.tikz').write_text(olas, encoding='utf-8')
(IMG / 'anx_ciclo.tikz').write_text(ciclo, encoding='utf-8')

filas = []
filas += [('anx_olas_datos (a)', 'NELSON: fusiones registradas, industria y minería', 'Estados Unidos', a, v, 'operaciones', 'T01')
          for a, v in nelson]
filas += [('anx_olas_datos (a)', 'FTC: fusiones registradas, industria y minería', 'Estados Unidos', a, v, 'operaciones', 'T01')
          for a, v in ftc]
filas += [('anx_olas_datos (b)', 'Valor de las fusiones transfronterizas netas (vendedor)', 'Mundo', a, round(v / 1000, 3),
           'miles de millones USD', 'T02') for a, v in sorted(valor_mundo.items())]
filas += [('anx_olas_datos (c)', 'Número de fusiones transfronterizas netas, empresa comprada española', 'España', a, v,
           'operaciones', 'T02') for a, v in sorted(esp_vendedor.items())]
filas += [('anx_olas_datos (c)', 'Número de fusiones transfronterizas netas, comprador español', 'España', a, v,
           'operaciones', 'T02') for a, v in sorted(esp_comprador.items())]
filas += [('anx_ciclo (a)', 'Valor de las fusiones transfronterizas / capitalización bursátil', 'Mundo', a, round(v, 3), '%', 'T03')
          for a, v in ratio]
filas += [('anx_ciclo (b)', 'SLOOS: porcentaje neto que endurece (media anual)', 'Estados Unidos', a, round(sloos[a], 2),
           '% neto', 'T04') for a in años_b]
filas += [('anx_ciclo (b)', 'Variación anual del número de fusiones transfronterizas netas', 'Mundo', a, round(variacion[a], 2),
           '%', 'T05') for a in años_b]
with open(DATOS / 'tablas_figuras.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['figura', 'serie', 'economía', 'año', 'valor', 'unidad', 'tratamiento'])
    w.writerows(filas)
print('Escritos Img/anx_olas_datos.tikz, Img/anx_ciclo.tikz y Code/datos/tablas_figuras.csv')
