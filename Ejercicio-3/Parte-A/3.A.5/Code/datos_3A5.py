# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3A5.xlsx) y figura b1_inflacion (cuerpo, bloque 1):
#   variación interanual del IPC en el Reino Unido (1861-1995) y Estados Unidos (1914-1995).
# Fuentes (FRED, Banco de la Reserva Federal de San Luis):
#   CPIUKA   IPC del Reino Unido, anual, 1209-2016 (2015=100); origen: Banco de Inglaterra,
#            A Millennium of Macroeconomic Data for the UK.
#   CPIAUCNS IPC de Estados Unidos (todos los consumidores urbanos), mensual desde 1913
#            (1982-84=100), sin desestacionalizar; origen: Bureau of Labor Statistics.
# Tratamiento: la serie mensual de EE. UU. se pasa a media anual; la inflación es la variación
# porcentual de la media anual respecto al año anterior.
# Uso, desde la carpeta del tema:  python3 -I Code/datos_3A5.py [carpeta con los CSV de FRED]
#   Sin carpeta, descarga los CSV en una carpeta temporal. Después:
#   compilar Code/b1_inflacion.tex como el resto de figuras (pdflatex) y copiar el PDF a Img/.

import csv, os, sys, tempfile, urllib.request

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(TEMA, "Code")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
FECHA_DESCARGA = "13/11/2026"

SERIES = {
    "CPIUKA": ("IPC del Reino Unido", "Reino Unido", "índice, 2015=100", "anual",
               "Banco de Inglaterra, A Millennium of Macroeconomic Data for the UK (vía FRED)"),
    "CPIAUCNS": ("IPC de Estados Unidos, todos los consumidores urbanos", "Estados Unidos",
                 "índice, 1982-84=100, sin desestacionalizar", "mensual",
                 "Bureau of Labor Statistics (vía FRED)"),
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


def main():
    if len(sys.argv) > 1:
        carpeta = sys.argv[1]
    else:
        carpeta = tempfile.mkdtemp()
        for sid in SERIES:
            destino = os.path.join(carpeta, sid + ".csv")
            print("descargando", sid)
            urllib.request.urlretrieve(FRED + sid, destino)

    # Reino Unido: anual directo (nos quedamos desde 1850)
    uk = [(int(f[:4]), v) for f, v in leer_csv(os.path.join(carpeta, "CPIUKA.csv"))]
    uk = [(a, v) for a, v in uk if a >= 1850]

    # Estados Unidos: media anual de la serie mensual (solo años completos)
    por_anio = {}
    for f, v in leer_csv(os.path.join(carpeta, "CPIAUCNS.csv")):
        por_anio.setdefault(int(f[:4]), []).append(v)
    us = [(a, sum(vs) / len(vs)) for a, vs in sorted(por_anio.items()) if len(vs) == 12]

    def inflacion(serie):
        return [(a1, 100.0 * (v1 / v0 - 1.0)) for (a0, v0), (a1, v1) in zip(serie, serie[1:]) if a1 == a0 + 1]

    infl_uk = inflacion(uk)
    infl_us = inflacion(us)

    # ---- Libro de datos ----
    hoja_ipc = [["serie", "pais", "anio", "valor"]]
    hoja_ipc += [["CPIUKA", "Reino Unido", a, v] for a, v in uk]
    hoja_ipc += [["CPIAUCNS (media anual)", "Estados Unidos", a, round(v, 3)] for a, v in us]
    hoja_infl = [["pais", "anio", "variacion_interanual_pct"]]
    hoja_infl += [["Reino Unido", a, round(v, 2)] for a, v in infl_uk]
    hoja_infl += [["Estados Unidos", a, round(v, 2)] for a, v in infl_us]
    hoja_fuentes = [["serie", "descripcion", "pais", "unidades", "frecuencia", "fuente", "tratamiento", "descarga"]]
    for sid, (desc, pais, uni, frec, fuente) in SERIES.items():
        trat = ("media anual de la serie mensual (años completos); variación interanual de la media"
                if sid == "CPIAUCNS" else "variación interanual; niveles conservados desde 1850")
        hoja_fuentes.append([sid, desc, pais, uni, frec, fuente, trat, FECHA_DESCARGA])
    escribir_xlsx(os.path.join(CODE, "datos_3A5.xlsx"),
                  [("ipc", hoja_ipc), ("inflacion", hoja_infl), ("fuentes", hoja_fuentes)])
    print("escrito Code/datos_3A5.xlsx")

    # ---- Figura b1_inflacion ----
    def coords(serie, desde, hasta):
        return " ".join(f"({a},{v:.2f})" for a, v in serie if desde <= a <= hasta)

    tex = r"""%% Figura cuerpo B1: inflación interanual en el Reino Unido y Estados Unidos (generada por Code/datos_3A5.py)
\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}[font=\footnotesize]
\begin{axis}[
  width=15.4cm, height=6.6cm,
  axis lines=left,
  xmin=1858, xmax=2000, ymin=-24, ymax=28,
  xtick={1860,1880,1900,1920,1940,1960,1980},
  xticklabel style={/pgf/number format/1000 sep=},
  ytick={-20,-10,0,10,20},
  ylabel={variación interanual del IPC (\%)},
  ylabel style={font=\footnotesize},
  tick label style={font=\scriptsize},
  legend style={at={(0.02,0.97)}, anchor=north west, draw=none, fill=none, font=\scriptsize},
  legend cell align=left,
  clip=false]
\fill[gray!14] (axis cs:1914,-24) rectangle (axis cs:1918,28);
\fill[gray!14] (axis cs:1939,-24) rectangle (axis cs:1945,28);
\node[gray!40!black, font=\tiny, anchor=south] at (axis cs:1916,24.5) {guerra};
\node[gray!40!black, font=\tiny, anchor=south] at (axis cs:1942,24.5) {guerra};
\addplot[gray!70, thin] coordinates {(1858,0) (2000,0)};
\draw[densely dashed, gray!55] (axis cs:1965,-24) -- (axis cs:1965,28);
\node[anchor=north west, align=left, font=\scriptsize, gray!25!black] at (axis cs:1966.5,27)
  {desde mediados de los 60\\la inflación deja de\\autocorregirse};
\addplot[black, line width=0.7pt] coordinates { %%UK%% };
\addlegendentry{Reino Unido}
\addplot[blue!55!black, line width=0.7pt] coordinates { %%US%% };
\addlegendentry{Estados Unidos}
\end{axis}
\end{tikzpicture}
\end{document}
"""
    tex = tex.replace("%%UK%%", coords(infl_uk, 1861, 1995)).replace("%%US%%", coords(infl_us, 1914, 1995))
    with open(os.path.join(CODE, "b1_inflacion.tex"), "w", encoding="utf-8") as f:
        f.write(tex)
    print("escrito Code/b1_inflacion.tex",
          f"(RU {infl_uk[0][0]}-1995, EE. UU. {infl_us[0][0]}-1995)")


if __name__ == "__main__":
    main()
