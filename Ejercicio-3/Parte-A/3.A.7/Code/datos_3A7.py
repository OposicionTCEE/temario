# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3A7.xlsx) y figura b3_moderacion (cuerpo, bloque 3):
#   la Gran Moderación y su final, en Estados Unidos entre 1960 y 2015.
# Fuentes (FRED, Banco de la Reserva Federal de San Luis):
#   GDPC1     PIB real de Estados Unidos, trimestral desde 1947, desestacionalizado y
#             en tasa anual (miles de millones de dólares encadenados); origen: BEA.
#   CPIAUCSL  IPC de Estados Unidos (todos los consumidores urbanos), mensual desde 1947,
#             desestacionalizado (1982-84=100); origen: Bureau of Labor Statistics.
# Tratamiento: del PIB real se calcula el crecimiento trimestral anualizado,
#   g_t = 400*ln(Y_t/Y_{t-1}); del IPC, la media trimestral y la inflación interanual,
#   pi_t = 100*(P_t/P_{t-4}-1). De cada serie se toma después la desviación típica móvil
#   de veinte trimestres (cinco años), fechada en el último trimestre de la ventana: es la
#   medida habitual de volatilidad con la que se documenta la Gran Moderación.
# Uso, desde la carpeta del tema:  python3 -I Code/datos_3A7.py [carpeta con los CSV de FRED]
#   Sin carpeta, descarga los CSV en una carpeta temporal. Después:
#   compilar Code/b3_moderacion.tex con pdflatex y copiar el PDF a Img/.

import csv, math, os, statistics, sys, tempfile, urllib.request

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(TEMA, "Code")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
FECHA_DESCARGA = "16/11/2026"
DESDE, HASTA = 1960, 2015
VENTANA = 20          # trimestres de la ventana móvil

SERIES = {
    "GDPC1":    ("PIB real de Estados Unidos", "miles de millones de dólares encadenados, tasa anual, desestacionalizado", "trimestral"),
    "CPIAUCSL": ("IPC de Estados Unidos, todos los consumidores urbanos", "índice 1982-84=100, desestacionalizado", "mensual"),
}


def descargar(serie, carpeta):
    destino = os.path.join(carpeta, serie + ".csv")
    if not os.path.exists(destino):
        urllib.request.urlretrieve(FRED + serie, destino)
    return destino


def leer(ruta):
    """Devuelve [(aaaa, mm, valor)] saltando los huecos que FRED marca con un punto."""
    out = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            claves = list(fila)
            fecha = fila[claves[0]]
            bruto = fila[claves[1]]
            if bruto in (".", "", None):
                continue
            a, m, _ = fecha.split("-")
            out.append((int(a), int(m), float(bruto)))
    return out


def a_trimestres(mensual):
    """Media trimestral de una serie mensual: {(año, trimestre): valor}."""
    cubos = {}
    for a, m, v in mensual:
        cubos.setdefault((a, (m - 1) // 3 + 1), []).append(v)
    return {k: sum(v) / len(v) for k, v in cubos.items() if len(v) == 3}


def movil(pares):
    """Desviación típica móvil de VENTANA trimestres, fechada en el último."""
    out = []
    for i in range(VENTANA - 1, len(pares)):
        trozo = [v for _, v in pares[i - VENTANA + 1:i + 1]]
        out.append((pares[i][0], statistics.stdev(trozo)))
    return out


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="fred_3A7_")
    os.makedirs(carpeta, exist_ok=True)
    pib = leer(descargar("GDPC1", carpeta))
    ipc = leer(descargar("CPIAUCSL", carpeta))

    # crecimiento trimestral anualizado del PIB real
    pib_t = sorted({(a, (m - 1) // 3 + 1): v for a, m, v in pib}.items())
    crec = [(pib_t[i][0], 400.0 * math.log(pib_t[i][1] / pib_t[i - 1][1])) for i in range(1, len(pib_t))]
    # inflación interanual del IPC trimestral
    ipc_t = sorted(a_trimestres(ipc).items())
    infl = [(ipc_t[i][0], 100.0 * (ipc_t[i][1] / ipc_t[i - 4][1] - 1.0)) for i in range(4, len(ipc_t))]

    vol_pib, vol_ipc = movil(crec), movil(infl)

    def decimal(clave):
        a, q = clave
        return a + (q - 1) / 4.0

    def recorta(serie):
        return [(decimal(k), v) for k, v in serie if DESDE <= k[0] <= HASTA]

    vpib, vipc = recorta(vol_pib), recorta(vol_ipc)
    assert len(vpib) > 200 and len(vipc) > 200, (len(vpib), len(vipc))

    # ---- libro de datos ----
    filas_series = [("fecha", "serie", "valor", "unidad")]
    for k, v in crec:
        if DESDE - 5 <= k[0] <= HASTA:
            filas_series.append((("%d-T%d" % k), "crecimiento del PIB real", round(v, 4), "% anual"))
    for k, v in infl:
        if DESDE - 5 <= k[0] <= HASTA:
            filas_series.append((("%d-T%d" % k), "inflación interanual del IPC", round(v, 4), "%"))
    filas_vol = [("fecha", "serie", "desviación típica móvil", "ventana")]
    for k, v in vol_pib:
        if DESDE <= k[0] <= HASTA:
            filas_vol.append((("%d-T%d" % k), "crecimiento del PIB real", round(v, 4), "20 trimestres"))
    for k, v in vol_ipc:
        if DESDE <= k[0] <= HASTA:
            filas_vol.append((("%d-T%d" % k), "inflación interanual del IPC", round(v, 4), "20 trimestres"))
    fuentes = [("serie", "descripción", "unidad", "frecuencia", "origen", "descarga")]
    for cod, (desc, uni, frec) in SERIES.items():
        fuentes.append((cod, desc, uni, frec, FRED + cod, FECHA_DESCARGA))
    escribir_xlsx(os.path.join(CODE, "datos_3A7.xlsx"),
                  {"series": filas_series, "volatilidad": filas_vol, "fuentes": fuentes})

    # ---- figura ----
    def coords(serie):
        return " ".join("(%.2f,%.3f)" % (x, y) for x, y in serie)

    tex = r"""%% Figura cuerpo B3: la Gran Moderación y su final (generada por Code/datos_3A7.py)
\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\begin{document}
\begin{tikzpicture}
\begin{axis}[width=14cm, height=6.2cm, font=\footnotesize,
  xmin=%(x0).2f, xmax=%(x1).2f, ymin=0, ymax=%(ymax).1f,
  xtick={1960,1970,1980,1990,2000,2010}, xticklabel style={/pgf/number format/1000 sep=},
  xlabel={}, ylabel={desviación típica móvil (5 años)},
  ylabel style={font=\scriptsize}, tick label style={font=\scriptsize},
  axis lines=left, legend style={font=\scriptsize, draw=none, fill=none, at={(0.02,0.97)}, anchor=north west},
  clip mode=individual]
  \fill[black!8] (axis cs:1984,0) rectangle (axis cs:2007,%(ymax).1f);
  \node[anchor=south, font=\scriptsize, text=black!60!white] at (axis cs:1995.5,%(yband).2f) {la Gran Moderación};
  \addplot[black, very thick] coordinates {%(pib)s};
  \addlegendentry{crecimiento del PIB real}
  \addplot[black, very thick, densely dashed] coordinates {%(ipc)s};
  \addlegendentry{inflación interanual}
\end{axis}
\end{tikzpicture}
\end{document}
""" % {"x0": DESDE, "x1": HASTA + 1,
       "ymax": math.ceil(max(max(v for _, v in vpib), max(v for _, v in vipc))) + 1,
       "yband": (math.ceil(max(max(v for _, v in vpib), max(v for _, v in vipc))) + 1) * 0.86,
       "pib": coords(vpib), "ipc": coords(vipc)}
    with open(os.path.join(CODE, "b3_moderacion.tex"), "w", encoding="utf-8") as f:
        f.write(tex)
    print("libro y figura escritos; puntos:", len(vpib), len(vipc))


if __name__ == "__main__":
    main()
