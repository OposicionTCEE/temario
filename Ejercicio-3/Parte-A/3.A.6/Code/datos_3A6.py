# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3A6.xlsx) y figura b1_estanflacion (cuerpo, bloque 1):
#   recorrido de la inflación y el paro en Estados Unidos entre 1960 y 1985.
# Fuentes (FRED, Banco de la Reserva Federal de San Luis):
#   CPIAUCNS  IPC de Estados Unidos (todos los consumidores urbanos), mensual desde 1913
#             (1982-84=100), sin desestacionalizar; origen: Bureau of Labor Statistics.
#   UNRATE    Tasa de paro civil de Estados Unidos, mensual desde 1948, desestacionalizada;
#             origen: Bureau of Labor Statistics.
# Tratamiento: las dos series mensuales se pasan a media anual (solo años completos); la
#   inflación es la variación porcentual de la media anual del IPC respecto al año anterior.
#   La curva de trazos de la figura es un ajuste por mínimos cuadrados de pi = a/U + b a los
#   puntos de 1961 a 1969, es decir, a la disyuntiva tal como se veía en los años sesenta.
# Uso, desde la carpeta del tema:  python3 -I Code/datos_3A6.py [carpeta con los CSV de FRED]
#   Sin carpeta, descarga los CSV en una carpeta temporal. Después:
#   compilar Code/b1_estanflacion.tex como el resto de figuras (pdflatex) y copiar el PDF a Img/.

import csv, os, sys, tempfile, urllib.request

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(TEMA, "Code")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
FECHA_DESCARGA = "13/11/2026"
DESDE, HASTA = 1960, 1985

SERIES = {
    "CPIAUCNS": ("IPC de Estados Unidos, todos los consumidores urbanos",
                 "índice, 1982-84=100, sin desestacionalizar", "mensual",
                 "Bureau of Labor Statistics (vía FRED)",
                 "media anual de la serie mensual (años completos); variación interanual de la media"),
    "UNRATE": ("Tasa de paro civil de Estados Unidos",
               "porcentaje de la población activa, desestacionalizada", "mensual",
               "Bureau of Labor Statistics (vía FRED)",
               "media anual de la serie mensual (años completos)"),
}


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    datos = []
    for fecha, valor in filas[1:]:
        if valor in ("", "."):
            continue
        datos.append((fecha, float(valor)))
    return datos


def media_anual(ruta):
    por_anio = {}
    for f, v in leer_csv(ruta):
        por_anio.setdefault(int(f[:4]), []).append(v)
    return {a: sum(vs) / len(vs) for a, vs in sorted(por_anio.items()) if len(vs) == 12}


def ajuste(puntos):
    """Mínimos cuadrados de pi = a*(1/U) + b."""
    xs = [1.0 / u for u, _ in puntos]
    ys = [p for _, p in puntos]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    a = sxy / sxx
    b = my - a * mx
    sct = sum((y - my) ** 2 for y in ys)
    scr = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
    return a, b, 1.0 - scr / sct


def main():
    if len(sys.argv) > 1:
        carpeta = sys.argv[1]
    else:
        carpeta = tempfile.mkdtemp()
        for sid in SERIES:
            destino = os.path.join(carpeta, sid + ".csv")
            print("descargando", sid)
            urllib.request.urlretrieve(FRED + sid, destino)

    ipc = media_anual(os.path.join(carpeta, "CPIAUCNS.csv"))
    paro = media_anual(os.path.join(carpeta, "UNRATE.csv"))

    anios = [a for a in range(DESDE, HASTA + 1) if a in ipc and (a - 1) in ipc and a in paro]
    datos = [(a, 100.0 * (ipc[a] / ipc[a - 1] - 1.0), paro[a]) for a in anios]

    # ---- Libro de datos ----
    hoja_series = [["serie", "anio", "valor", "unidades"]]
    hoja_series += [["CPIAUCNS (media anual)", a, round(v, 3), "índice 1982-84=100"]
                    for a, v in sorted(ipc.items()) if DESDE - 1 <= a <= HASTA]
    hoja_series += [["UNRATE (media anual)", a, round(v, 2), "% de la población activa"]
                    for a, v in sorted(paro.items()) if DESDE - 1 <= a <= HASTA]
    hoja_ph = [["anio", "inflacion_pct", "paro_pct"]]
    hoja_ph += [[a, round(pi, 2), round(u, 2)] for a, pi, u in datos]
    a60, b60, r2 = ajuste([(u, pi) for an, pi, u in datos if 1961 <= an <= 1969])
    hoja_ajuste = [["parametro", "valor", "nota"],
                   ["a", round(a60, 4), "pendiente de pi = a/U + b, ajuste 1961-1969"],
                   ["b", round(b60, 4), "constante"],
                   ["R2", round(r2, 4), "bondad del ajuste a los nueve años"]]
    hoja_fuentes = [["serie", "descripcion", "unidades", "frecuencia", "fuente", "tratamiento", "descarga"]]
    for sid, (desc, uni, frec, fuente, trat) in SERIES.items():
        hoja_fuentes.append([sid, desc, uni, frec, fuente, trat, FECHA_DESCARGA])
    escribir_xlsx(os.path.join(CODE, "datos_3A6.xlsx"),
                  [("series", hoja_series), ("phillips", hoja_ph),
                   ("ajuste_60", hoja_ajuste), ("fuentes", hoja_fuentes)])
    print("escrito Code/datos_3A6.xlsx")

    # ---- Figura b1_estanflacion ----
    def coords(desde, hasta):
        return " ".join(f"({u:.2f},{pi:.2f})" for a, pi, u in datos if desde <= a <= hasta)

    etiquetas = {1961: "above left", 1965: "below left", 1969: "left",
                 1971: "above left", 1975: "above right", 1979: "left",
                 1980: "above right", 1983: "below right", 1985: "below"}
    nodos = []
    for a, pi, u in datos:
        if a in etiquetas:
            nodos.append(f"\\node[font=\\tiny, gray!25!black, anchor={etiquetas[a]}] "
                         f"at (axis cs:{u:.2f},{pi:.2f}) {{{a}}};")

    tex = r"""%% Figura cuerpo B1: inflación y paro en Estados Unidos, 1960-1985 (generada por Code/datos_3A6.py)
\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}[font=\footnotesize]
\begin{axis}[
  width=13.6cm, height=8.2cm,
  axis lines=left,
  xmin=3, xmax=10.4, ymin=0, ymax=14.5,
  xlabel={tasa de paro (\%)}, ylabel={inflación interanual (\%)},
  xlabel style={font=\footnotesize}, ylabel style={font=\footnotesize},
  tick label style={font=\scriptsize},
  legend style={at={(0.98,0.97)}, anchor=north east, draw=none, fill=none, font=\scriptsize},
  legend cell align=left,
  clip=false]
\addplot[gray!55, densely dashed, line width=0.7pt, domain=3.3:7.2, samples=60]
  {%%A60%%/x + (%%B60%%)};
\addlegendentry{ajuste a 1961-1969}
\addplot[black, line width=0.7pt, mark=*, mark size=1.1pt] coordinates { %%S60%% };
\addlegendentry{1960-1969}
\addplot[blue!55!black, line width=0.7pt, mark=*, mark size=1.1pt] coordinates { %%S70%% };
\addlegendentry{1970-1985}
%%NODOS%%
\node[anchor=west, align=left, font=\scriptsize, gray!25!black] at (axis cs:3.15,12.4)
  {en los sesenta, menos paro se pagaba\\con algo más de inflación};
\node[anchor=east, align=left, font=\scriptsize, blue!45!black] at (axis cs:10.3,2.2)
  {en los setenta, la inflación y el paro\\suben a la vez: el menú desaparece};
\end{axis}
\end{tikzpicture}
\end{document}
"""
    tex = (tex.replace("%%A60%%", f"{a60:.3f}").replace("%%B60%%", f"{b60:.3f}")
              .replace("%%S60%%", coords(1960, 1969)).replace("%%S70%%", coords(1969, 1985))
              .replace("%%NODOS%%", "\n".join(nodos)))
    with open(os.path.join(CODE, "b1_estanflacion.tex"), "w", encoding="utf-8") as f:
        f.write(tex)
    print("escrito Code/b1_estanflacion.tex",
          f"({datos[0][0]}-{datos[-1][0]}; ajuste 60: a={a60:.3f}, b={b60:.3f}, R2={r2:.3f})")


if __name__ == "__main__":
    main()
