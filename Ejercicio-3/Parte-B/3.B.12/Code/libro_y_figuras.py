# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3B12.xlsx) y figuras calculadas de los anexos (T7, 12/11/2026):
#   a3_desequilibrios (saldos por cuenta corriente en porcentaje del PIB mundial, 1990-2025: EE. UU., China, Alemania,
#     Japón, exportadores de combustibles del FMI y suma de los valores absolutos de todas las economías; FMI, WEO de
#     octubre de 2026), anexo III.4.4;
#   a4_espana (España: cuenta corriente, posición de inversión internacional neta y NENDI en porcentaje del PIB, 1995-2025;
#     FMI, WEO de octubre de 2026, y Eurostat, cuadro de indicadores del PDM), anexo IV.5.
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py CARPETA
#   CARPETA contiene las subcarpetas imf, eurostat y ecb con las descargas (ver DESCARGAS).
#   Después, para cada figura:  bash Code/generar_figura.sh <nombre>
# Convenciones: saldos con signo (superávit positivo); la posición exterior negativa es deudora.

import csv, json, os, sys

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FECHA_DESCARGA = "12/11/2026"
DESCARGAS = {
    "imf/BCA.json": "https://www.imf.org/external/datamapper/api/v1/BCA (WEO de octubre de 2026)",
    "imf/NGDPD.json": "https://www.imf.org/external/datamapper/api/v1/NGDPD (WEO de octubre de 2026)",
    "imf/BCA_NGDPD.json": "https://www.imf.org/external/datamapper/api/v1/BCA_NGDPD (WEO de octubre de 2026)",
    "imf/countries.json": "https://www.imf.org/external/datamapper/api/v1/countries",
    "imf/groups.json": "https://www.imf.org/external/datamapper/api/v1/groups",
    "imf/indicators.json": "https://www.imf.org/external/datamapper/api/v1/indicators",
    "eurostat/tipsii10.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tipsii10?geo=ES&format=JSON&lang=EN",
    "eurostat/tipsii20.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tipsii20?geo=ES&format=JSON&lang=EN",
    "eurostat/tipsii50.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tipsii50?geo=ES&format=JSON&lang=EN",
    "ecb/target_es.csv": "https://data-api.ecb.europa.eu/service/data/TGB/M.ES.N.A094T.U2.EUR.E?format=csvdata",
}
A0, A1 = 1990, 2025
# Exportadores de combustibles: el agregado OEXP del FMI no trae saldos en la API, así que se suman estas economías
# (las grandes exportadoras netas de petróleo y gas, con Noruega); un año sin dato de una economía cuenta como cero.
EXPORTADORES = ["SAU", "ARE", "KWT", "QAT", "OMN", "BHR", "IRN", "IRQ", "RUS", "KAZ", "AZE", "DZA", "NGA", "AGO", "LBY", "VEN", "NOR"]

EJES = r"""\footnotesize
\begin{axis}[
  width=14.6cm, height=6.6cm, scale only axis=false,
  axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={},
  /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  legend style={draw=none, fill=none, font=\footnotesize, legend columns=3, /tikz/every even column/.append style={column sep=0.5cm}},
"""


def coordenadas(puntos, d=2):
    return " ".join(("(%d,%." + str(d) + "f)") % p for p in puntos)


def coma(x, d=1):
    return (("%." + str(d) + "f") % x).replace(".", "{,}")


# ---------------------------------------------------------------- lectura
def leer_imf(carpeta, ind):
    return json.load(open(os.path.join(carpeta, "imf", ind + ".json"), encoding="utf-8"))["values"][ind]


def leer_estat(carpeta, codigo):
    d = json.load(open(os.path.join(carpeta, "eurostat", codigo + ".json"), encoding="utf-8"))
    dims, size = d["id"], d["size"]
    inv = {k: {v: kk for kk, v in d["dimension"][k]["category"]["index"].items()} for k in dims}
    out = {}
    for pos, val in d["value"].items():
        pos = int(pos)
        coords = {}
        for k, s in zip(reversed(dims), reversed(size)):
            coords[k] = inv[k][pos % s]
            pos //= s
        if coords.get("partner") != "WRL_REST":
            continue
        out.setdefault(coords.get("unit", "PC_GDP"), {})[int(coords["time"])] = val
    return out


def leer_target(carpeta):
    out = []
    with open(os.path.join(carpeta, "ecb", "target_es.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append((r["TIME_PERIOD"], float(r["OBS_VALUE"])))
    return out


# ---------------------------------------------------------------- A3: desequilibrios globales
def desequilibrios(bca, ngdpd, paises):
    mundo = ngdpd["WEOWORLD"]
    total, series = [], {"USA": [], "CHN": [], "DEU": [], "JPN": [], "OEXP": []}
    for a in range(A0, A1 + 1):
        y = str(a)
        suma = sum(abs(bca[c][y]) for c in paises if c in bca and y in bca[c])
        total.append((a, 100.0 * suma / mundo[y]))
        for k in series:
            if k == "OEXP":
                series[k].append((a, 100.0 * sum(bca[c].get(y, 0.0) for c in EXPORTADORES if c in bca) / mundo[y]))
            elif k in bca and y in bca[k]:
                series[k].append((a, 100.0 * bca[k][y] / mundo[y]))
    return total, series


def fig_desequilibrios(total, series):
    t = "% Saldos por cuenta corriente en porcentaje del PIB mundial, 1990-2025 (FMI, WEO de octubre de 2026: BCA y NGDPD).\n"
    t += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh a3_desequilibrios\n"
    t += "\\begin{tikzpicture}\n" + EJES
    t += r"""  xmin=1989.5, xmax=2025.5, xtick={1990,1995,2000,2005,2010,2015,2020,2025}, ymin=-2, ymax=6.5, ytick={-2,-1,0,1,2,3,4,5,6},
  ylabel={Porcentaje del PIB mundial},
  legend to name=leyendades,
]
"""
    t += "\\draw[black!50] (axis cs:1989.5,0) -- (axis cs:2025.5,0);\n"
    for a, txt in ((1997, "crisis asi\\'atica"), (2008, "crisis financiera global"), (2020, "pandemia")):
        t += "\\draw[black!30, densely dotted] (axis cs:%d,-2) -- (axis cs:%d,6.5);\n" % (a, a)
        t += "\\node[font=\\scriptsize, black!55, anchor=north west, inner sep=1.5pt] at (axis cs:%d,6.5) {%s};\n" % (a, txt)
    t += "\\addplot[black!45, line width=2.2pt] coordinates {%s};\n" % coordenadas(total)
    t += "\\addlegendentry{Suma de los saldos en valor absoluto}\n"
    estilos = [("USA", "black, line width=1.1pt", "EE. UU."), ("CHN", "black, dashed, line width=1pt", "China"),
               ("DEU", "black, dash dot, line width=0.9pt", "Alemania"), ("JPN", "black, densely dotted, line width=1pt", "Jap\\'on"),
               ("OEXP", "black!60, line width=0.9pt", "Exportadores de combustibles")]
    for k, est, nom in estilos:
        t += "\\addplot[%s] coordinates {%s};\n" % (est, coordenadas(series[k]))
        t += "\\addlegendentry{%s}\n" % nom
    t += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendades}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "a3_desequilibrios.tikz"), "w", encoding="utf-8").write(t)


# ---------------------------------------------------------------- A4: España
def fig_espana(cc, piin, nendi):
    t = "% España: cuenta corriente (FMI, WEO de octubre de 2026) y posición de inversión internacional neta y NENDI\n"
    t += "% (Eurostat, cuadro de indicadores del PDM: tipsii10 y tipsii50), en porcentaje del PIB, 1995-2025.\n"
    t += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh a4_espana\n"
    t += "\\begin{tikzpicture}\n\\footnotesize\n"
    comun = r"""  width=14.6cm, scale only axis=false, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  xmin=1994.5, xmax=2025.5,
"""
    t += "\\begin{axis}[name=flujo,\n" + comun
    t += r"""  height=4.4cm, ymin=-10.5, ymax=4.5, ytick={-10,-5,0,5}, xtick={1995,2000,2005,2010,2015,2020,2025}, xticklabels={},
  ylabel={Flujo: cuenta corriente},
  title={\footnotesize\textbf{Flujo}: saldo por cuenta corriente (\% del PIB)}, title style={yshift=-4pt},
]
"""
    t += "\\draw[black!50] (axis cs:1994.5,0) -- (axis cs:2025.5,0);\n"
    t += "\\addplot[ybar, bar width=6pt, fill=black!45, draw=none] coordinates {%s};\n" % coordenadas(cc, 1)
    t += "\\end{axis}\n"
    t += "\\begin{axis}[at={(flujo.below south west)}, anchor=north west, yshift=-0.55cm,\n" + comun
    t += r"""  height=6.2cm, ymin=-105, ymax=5, ytick={-100,-80,-60,-40,-20,0}, xtick={1995,2000,2005,2010,2015,2020,2025},
  ylabel={Stocks: posici\'on exterior},
  title={\footnotesize\textbf{Stocks}: posici\'on de inversi\'on internacional neta y NENDI (\% del PIB)}, title style={yshift=-4pt},
  legend style={draw=none, fill=none, font=\footnotesize, legend columns=-1, /tikz/every even column/.append style={column sep=0.5cm}, at={(0.5,-0.2)}, anchor=north},
]
"""
    t += "\\draw[black!50] (axis cs:1994.5,0) -- (axis cs:2025.5,0);\n"
    t += "\\draw[black!45, dashed] (axis cs:1994.5,-35) -- (axis cs:2025.5,-35);\n"
    t += "\\node[font=\\scriptsize, black!60, anchor=south east, inner sep=1.5pt] at (axis cs:2025.4,-35) {umbral del PDM: $-35$};\n"
    t += "\\addplot[black, line width=1.2pt, mark=*, mark size=0.8pt] coordinates {%s};\n" % coordenadas(piin, 1)
    t += "\\addlegendentry{Posici\\'on de inversi\\'on internacional neta}\n"
    t += "\\addplot[black, dashed, line width=1pt] coordinates {%s};\n" % coordenadas(nendi, 1)
    t += "\\addlegendentry{NENDI (sin instrumentos que no pueden impagarse)}\n"
    t += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "a4_espana.tikz"), "w", encoding="utf-8").write(t)


# ---------------------------------------------------------------- principal
def main():
    carpeta = sys.argv[1]
    bca, ngdpd, cagdp = leer_imf(carpeta, "BCA"), leer_imf(carpeta, "NGDPD"), leer_imf(carpeta, "BCA_NGDPD")
    paises = set(json.load(open(os.path.join(carpeta, "imf", "countries.json"), encoding="utf-8"))["countries"].keys())
    total, series = desequilibrios(bca, ngdpd, paises)
    fig_desequilibrios(total, series)

    cc = [(a, cagdp["ESP"][str(a)]) for a in range(1995, A1 + 1) if str(a) in cagdp["ESP"]]
    piin_all, nendi_all, ned_all = leer_estat(carpeta, "tipsii10"), leer_estat(carpeta, "tipsii50"), leer_estat(carpeta, "tipsii20")
    piin = sorted((a, v) for a, v in piin_all["PC_GDP"].items() if a <= A1)
    piin_mio = dict(piin_all["MIO_NAC"])
    nendi = sorted((a, v) for a, v in nendi_all["PC_GDP"].items() if a <= A1)
    ned = sorted((a, v) for a, v in ned_all["PC_GDP"].items() if a <= A1)
    fig_espana(cc, piin, nendi)
    target = leer_target(carpeta)

    # ---- cifras que cita el texto
    td = dict(total)
    pico = max(total, key=lambda p: p[1])
    us = dict(series["USA"]); cn = dict(series["CHN"])
    a_us = min(us, key=us.get); a_cn = max(cn, key=cn.get)
    ccd = dict(cc); pd_ = dict(piin); nd = dict(nendi)
    a_min = min(pd_, key=pd_.get)
    sup = [a for a in sorted(ccd) if a >= 2012]
    tmin = min(target, key=lambda p: p[1]); tdict = dict(target)
    cif = [
        ["Suma de los saldos por cuenta corriente en valor absoluto, máximo (% del PIB mundial)", "%.2f en %d" % (pico[1], pico[0]), "FMI WEO oct. 2026", "Anexo III.4.4"],
        ["Suma de los saldos en valor absoluto, 2008 / 2013 / 2019 / 2024 / 2025 (% del PIB mundial)", " / ".join("%.2f" % td[a] for a in (2008, 2013, 2019, 2024, 2025)), "FMI WEO oct. 2026", "Anexo III.4.4"],
        ["Cuenta corriente de EE. UU., mínimo (% del PIB mundial)", "%.2f en %d" % (us[a_us], a_us), "FMI WEO oct. 2026", "Anexo III.4.4"],
        ["Cuenta corriente de China, máximo (% del PIB mundial)", "%.2f en %d" % (cn[a_cn], a_cn), "FMI WEO oct. 2026", "Anexo III.4.4"],
        ["España: cuenta corriente, 2007 (mínimo) y 2012-2025 (% del PIB)", "%.1f en 2007; %s" % (ccd[2007], ", ".join("%d: %.1f" % (a, ccd[a]) for a in sup)), "FMI WEO oct. 2026", "Anexo IV.5"],
        ["España: PIIN, 1999 / mínimo / 2014 / 2019 / 2020 / 2024 / 2025 (% del PIB)", "%.1f / %.1f en %d / %.1f / %.1f / %.1f / %.1f / %.1f" % (pd_[1999], pd_[a_min], a_min, pd_[2014], pd_[2019], pd_[2020], pd_[2024], pd_[2025]), "Eurostat tipsii10", "Anexo IV.5"],
        ["España: PIIN 2024 y 2025 (millones de euros)", "%.0f / %.0f" % (piin_mio[2024], piin_mio[2025]), "Eurostat tipsii10", "Anexo IV.5"],
        ["España: NENDI, 2009 / 2012 / 2019 / 2024 / 2025 (% del PIB)", " / ".join("%.1f" % nd[a] for a in (2009, 2012, 2019, 2024, 2025)), "Eurostat tipsii50", "Anexo IV.3 y IV.5"],
        ["España: deuda externa neta, 2014 / 2025 (% del PIB)", "%.1f / %.1f" % (dict(ned)[2014], dict(ned)[2025]), "Eurostat tipsii20", "Anexo IV.5"],
        ["Banco de España: saldo TARGET, agosto 2012 / mínimo / diciembre 2025 (millones de euros)", "%.0f / %.0f en %s / %.0f" % (tdict["2012-08"], tmin[1], tmin[0], tdict["2025-12"]), "BCE, TGB", "Anexo IV.5"],
    ]
    for c in cif:
        print(" - ", c[0], ":", c[1])

    # ---- libro
    leeme = [["Libro de datos del Tema 3.B.12 (Balanza de pagos II)"],
             ["Generado por Code/libro_y_figuras.py el %s a partir de las descargas listadas en la hoja Fuentes." % FECHA_DESCARGA],
             ["Hojas: Fuentes (de dónde sale cada serie), Series (formato largo: indicador, área, periodo, valor, unidad, fuente, tratamiento, figura), Cifras_citadas (lo que el texto cita)."],
             ["Convenciones: saldos con signo (superávit positivo); posición exterior negativa = deudora; porcentajes del PIB nominal."],
             ["Para rehacer: descargar con las URL de Fuentes en una carpeta y ejecutar python3 -I Code/libro_y_figuras.py CARPETA; después bash Code/generar_figura.sh a3_desequilibrios y a4_espana."]]
    fuentes = [["Fichero", "URL y edición", "Fecha de descarga"]] + [[k, v, FECHA_DESCARGA] for k, v in DESCARGAS.items()]
    filas = [["Indicador", "Área", "Periodo", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]
    for a, v in total:
        filas.append(["Suma de los saldos por cuenta corriente en valor absoluto", "Mundo (%d economías del WEO)" % len(paises), a, v, "% del PIB mundial", "FMI WEO oct. 2026 (BCA, NGDPD)", "suma de |BCA| de todas las economías / NGDPD de WEOWORLD", "a3_desequilibrios"])
    nombres = {"USA": "Estados Unidos", "CHN": "China", "DEU": "Alemania", "JPN": "Japón", "OEXP": "Exportadores de combustibles (%s)" % ", ".join(EXPORTADORES)}
    for k, ser in series.items():
        for a, v in ser:
            filas.append(["Saldo por cuenta corriente", nombres[k], a, v, "% del PIB mundial", "FMI WEO oct. 2026 (BCA, NGDPD)", "BCA / NGDPD de WEOWORLD", "a3_desequilibrios"])
    for a, v in cc:
        filas.append(["Saldo por cuenta corriente", "España", a, v, "% del PIB", "FMI WEO oct. 2026 (BCA_NGDPD)", "ninguno", "a4_espana"])
    for a, v in piin:
        filas.append(["Posición de inversión internacional neta", "España", a, v, "% del PIB", "Eurostat tipsii10", "ninguno", "a4_espana"])
        if a in piin_mio:
            filas.append(["Posición de inversión internacional neta", "España", a, piin_mio[a], "millones de euros", "Eurostat tipsii10", "ninguno", ""])
    for a, v in nendi:
        filas.append(["PIIN sin instrumentos que no pueden impagarse (NENDI)", "España", a, v, "% del PIB", "Eurostat tipsii50", "ninguno", "a4_espana"])
    for a, v in ned:
        filas.append(["Deuda externa neta", "España", a, v, "% del PIB", "Eurostat tipsii20", "ninguno", ""])
    for p, v in target:
        filas.append(["Saldo TARGET del Banco de España", "España", p, v, "millones de euros", "BCE, TGB", "fin de mes", ""])
    cifras = [["Cifra", "Valor", "Fuente", "Dónde"]] + cif
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B12.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cifras_citadas", cifras)])
    print("Libro escrito:", os.path.join(TEMA, "Code", "datos_3B12.xlsx"))


if __name__ == "__main__":
    main()
