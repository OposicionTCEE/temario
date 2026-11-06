# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3B14.xlsx) y figuras calculadas del anexo I (A1, 06/11/2026):
#   anx_efectivo_euro (tipo bilateral EUR/USD y tipos efectivos nominal y real del euro, BPI y FRED),
#   anx_competitividad_espana (tipos efectivos de España frente a la zona del euro, Eurostat),
#   anx_penn (nivel de precios y PIB por habitante, ICP 2021) y anx_bigmac (índice Big Mac de julio de 2026).
# Fuentes: Banco de Pagos Internacionales (WS_EER, índices efectivos mensuales, cesta amplia de 64 economías,
# 2020 = 100); FRED (EXUSEU, dólares por euro, media mensual); Eurostat (ert_eff_ic_q, índices efectivos de España
# frente a los socios de la zona del euro, composición de 2026, 2020 = 100); Banco Mundial (Indicadores del
# Desarrollo Mundial: PA.NUS.PPP, PA.NUS.FCRF y NY.GDP.PCAP.PP.CD de 2021, del ICP 2021, y NY.GDP.PCAP.CD de 2025);
# The Economist (big-mac-data, output-data/big-mac-full-index.csv, edición de julio de 2026).
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py CARPETA
#   CARPETA contiene las subcarpetas dl_bis, dl_fred, dl_eurostat, dl_wb y dl_bigmac con las descargas (ver DESCARGAS).
#   Después, para cada figura:  bash Code/generar_figura.sh <nombre>
# Convenciones: en el tema, S son euros por dólar (sube = depreciación del euro). Las figuras de índices efectivos
# usan la convención de las fuentes (sube = apreciación), y por eso el tipo bilateral se dibuja como dólares por euro.

import csv, json, math, os, sys

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FECHA_DESCARGA = "06/11/2026"
DESCARGAS = {
    "dl_bis/WS_EER_csv_flat.csv": "https://data.bis.org/static/bulk/WS_EER_csv_flat.zip (descomprimido)",
    "dl_fred/EXUSEU.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EXUSEU",
    "dl_eurostat/ert_es_q_sel.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ert_eff_ic_q?geo=ES&unit=I20&exch_rt=NEER_EA21&exch_rt=REER_EA21_CPI&exch_rt=REER_EA21_ULCT&exch_rt=REER_IC42_CPI&format=JSON&lang=EN",
    "dl_wb/PA.NUS.PPP.json": "https://api.worldbank.org/v2/country/all/indicator/PA.NUS.PPP?date=2021&format=json&per_page=400",
    "dl_wb/PA.NUS.FCRF.json": "https://api.worldbank.org/v2/country/all/indicator/PA.NUS.FCRF?date=2021&format=json&per_page=400",
    "dl_wb/NY.GDP.PCAP.PP.CD.json": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.CD?date=2021&format=json&per_page=400",
    "dl_wb/NY.GDP.PCAP.CD_2025.json": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?date=2025&format=json&per_page=400",
    "dl_wb/paises.json": "https://api.worldbank.org/v2/country?format=json&per_page=400",
    "dl_bigmac/big-mac-full-index.csv": "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv",
}


# ---------------------------------------------------------------- utilidades
def decimal_mes(fecha):  # "1999-01" -> 1999.0
    a, m = fecha[:7].split("-")
    return int(a) + (int(m) - 1) / 12.0


def decimal_trim(fecha):  # "1999-Q1" -> 1999.0
    a, q = fecha.split("-Q")
    return int(a) + (int(q) - 1) / 4.0


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    syy = sum((y - my) ** 2 for y in ys)
    r2 = sxy * sxy / (sxx * syy)
    return a, b, r2


def coma(x, d=1):  # 12.34 -> "12{,}3" para escribir en modo matemático
    s = ("%." + str(d) + "f") % x
    return s.replace(".", "{,}")


def coordenadas(puntos, d=3):
    return " ".join(("(%." + str(d) + "f,%." + str(d) + "f)") % p for p in puntos)


# ---------------------------------------------------------------- lectura
def leer_bis(carpeta):
    series = {}
    with open(os.path.join(carpeta, "dl_bis", "WS_EER_csv_flat.csv"), encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if not d["FREQ:Frequency"].startswith("M"):
                continue
            area = d["REF_AREA:Reference area"][:2]
            if area not in ("XM", "ES"):
                continue
            tipo = d["EER_TYPE:Type"][:1]
            cesta = d["EER_BASKET:Basket"][:1]
            if d["OBS_VALUE:Observation Value"] in ("", "NaN"):
                continue
            series.setdefault((area, tipo, cesta), []).append((d["TIME_PERIOD:Time period or range"], float(d["OBS_VALUE:Observation Value"])))
    for k in series:
        series[k].sort()
    return series


def leer_fred(carpeta, serie):
    filas = []
    with open(os.path.join(carpeta, "dl_fred", serie + ".csv"), encoding="utf-8") as f:
        lector = csv.reader(f)
        next(lector)
        for fecha, valor in lector:
            if valor not in (".", ""):
                filas.append((fecha[:7], float(valor)))
    return filas


def leer_eurostat(carpeta):
    d = json.load(open(os.path.join(carpeta, "dl_eurostat", "ert_es_q_sel.json"), encoding="utf-8"))
    ids, tam = d["id"], d["size"]
    inv = {dim: {pos: cod for cod, pos in d["dimension"][dim]["category"]["index"].items()} for dim in ids}
    series = {}
    for plano, valor in d["value"].items():
        resto, coords = int(plano), {}
        for dim, n in reversed(list(zip(ids, tam))):
            coords[dim] = inv[dim][resto % n]
            resto //= n
        series.setdefault(coords["exch_rt"], []).append((coords["time"], float(valor)))
    for k in series:
        series[k].sort()
    return series


def leer_bm(carpeta, fichero):
    d = json.load(open(os.path.join(carpeta, "dl_wb", fichero), encoding="utf-8"))
    return {r["countryiso3code"]: r["value"] for r in d[1] if r["value"] is not None and r["countryiso3code"]}


def paises_bm(carpeta):
    d = json.load(open(os.path.join(carpeta, "dl_wb", "paises.json"), encoding="utf-8"))
    return {r["id"]: r["name"] for r in d[1] if r["region"]["value"] != "Aggregates"}


def leer_bigmac(carpeta):
    with open(os.path.join(carpeta, "dl_bigmac", "big-mac-full-index.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- figuras
EJES = r"""\footnotesize
\begin{axis}[
  width=14.6cm, height=6.6cm, scale only axis=false,
  axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={},
  /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  legend style={draw=none, fill=none, font=\footnotesize, legend columns=-1, /tikz/every even column/.append style={column sep=0.6cm}},
"""


def fig_efectivo_euro(bis, fred):
    usd = dict(fred)
    base = sum(v for f, v in fred if f.startswith("2020")) / 12.0
    bil = [(decimal_mes(f), 100.0 * v / base) for f, v in fred if f >= "1999-01" and f <= "2026-09"]
    nom = [(decimal_mes(f), v) for f, v in bis[("XM", "N", "B")] if f >= "1999-01"]
    rea = [(decimal_mes(f), v) for f, v in bis[("XM", "R", "B")] if f >= "1999-01"]
    tikz = "% Tipo bilateral EUR/USD (dólares por euro, índice 2020 = 100) y tipos efectivos nominal y real del euro\n"
    tikz += "% (BPI, cesta amplia de 64 economías, 2020 = 100), mensual, 1999-2026. Subida = apreciación del euro.\n"
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_efectivo_euro\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmin=1998.5, xmax=2027, xtick={2000,2005,2010,2015,2020,2025},
  ylabel={Índice, $2020=100$},
  legend to name=leyendaefectivo,
]
"""
    tikz += "\\addplot[black!45, line width=0.6pt] coordinates {%s};\n" % coordenadas(bil)
    tikz += "\\addlegendentry{Bilateral frente al dólar}\n"
    tikz += "\\addplot[black, line width=1.1pt] coordinates {%s};\n" % coordenadas(nom)
    tikz += "\\addlegendentry{Efectivo nominal}\n"
    tikz += "\\addplot[black, dashed, line width=0.8pt] coordinates {%s};\n" % coordenadas(rea)
    tikz += "\\addlegendentry{Efectivo real}\n"
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendaefectivo}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_efectivo_euro.tikz"), "w", encoding="utf-8").write(tikz)
    return bil, nom, rea


def fig_competitividad_espana(eu):
    nom = [(decimal_trim(f), v) for f, v in eu["NEER_EA21"]]
    ipc = [(decimal_trim(f), v) for f, v in eu["REER_EA21_CPI"]]
    clu = [(decimal_trim(f), v) for f, v in eu["REER_EA21_ULCT"]]
    tikz = "% Tipos efectivos de España frente a los socios de la zona del euro (composición de 2026), trimestral,\n"
    tikz += "% 1994-2026, 2020 = 100 (Eurostat, ert_eff_ic_q): nominal, real con IPC y real con costes laborales unitarios.\n"
    tikz += "% Subida = apreciación. Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_competitividad_espana\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmin=1993.5, xmax=2027, xtick={1995,2000,2005,2010,2015,2020,2025},
  ylabel={Índice, $2020=100$},
  legend to name=leyendaespana,
]
"""
    tikz += "\\draw[black!35, densely dotted] (axis cs:1999,\\pgfkeysvalueof{/pgfplots/ymin}) -- (axis cs:1999,\\pgfkeysvalueof{/pgfplots/ymax});\n"
    tikz += "\\addplot[black!45, line width=0.6pt] coordinates {%s};\n" % coordenadas(nom)
    tikz += "\\addlegendentry{Nominal}\n"
    tikz += "\\addplot[black, line width=1.1pt] coordinates {%s};\n" % coordenadas(ipc)
    tikz += "\\addlegendentry{Real con precios de consumo}\n"
    tikz += "\\addplot[black, dashed, line width=0.8pt] coordinates {%s};\n" % coordenadas(clu)
    tikz += "\\addlegendentry{Real con costes laborales unitarios}\n"
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendaespana}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_competitividad_espana.tikz"), "w", encoding="utf-8").write(tikz)
    return nom, ipc, clu


ETIQ_PENN = {"USA": "EE. UU.", "CHE": "Suiza", "ESP": "España", "DEU": "Alemania", "JPN": "Japón", "CHN": "China",
             "IND": "India", "MEX": "México", "NOR": "Noruega", "EGY": "Egipto"}


def fig_penn(ppp, xr, pibppa, nombres):
    filas = []
    for iso in sorted(nombres):
        if iso in ppp and iso in xr and iso in pibppa and xr[iso] > 0:
            filas.append((iso, nombres[iso], ppp[iso], xr[iso], 100.0 * ppp[iso] / xr[iso], pibppa[iso]))
    xs = [math.log(f[5]) for f in filas]
    ys = [math.log(f[4]) for f in filas]
    a, b, r2 = ols(xs, ys)
    puntos = [(f[5], f[4]) for f in filas]
    x0, x1 = 900.0, 150000.0
    recta = [(x, math.exp(a + b * math.log(x))) for x in (x0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0, x1)]
    tikz = "% Nivel de precios del PIB (EE. UU. = 100: PPA / tipo de cambio de mercado) y PIB por habitante en PPA, 2021\n"
    tikz += "%% (Banco Mundial, ICP 2021; %d economías), con la recta de regresión en logaritmos.\n" % len(filas)
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_penn\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmode=log, xmin=800, xmax=160000, ymin=0, ymax=170,
  xtick={1000,10000,100000}, xticklabels={$1$ mil, $10$ mil, $100$ mil},
  xlabel={PIB por habitante en dólares internacionales (PPA), escala logarítmica},
  ylabel={Nivel de precios, EE. UU.$\,=100$},
]
"""
    tikz += "\\addplot[only marks, mark=*, mark size=1.1pt, black!55] coordinates {%s};\n" % coordenadas(puntos, 2)
    tikz += "\\addplot[black, line width=0.8pt, smooth] coordinates {%s};\n" % coordenadas(recta, 2)
    for f in filas:
        if f[0] in ETIQ_PENN:
            tikz += "\\node[font=\\scriptsize, anchor=south east, inner sep=1.5pt] at (axis cs:%.2f,%.2f) {%s};\n" % (f[5], f[4], ETIQ_PENN[f[0]])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_penn.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, (a, b, r2)


ISO_BM = {"EUZ": "EMU"}
ETIQ_BM = {"USA": "EE. UU.", "CHE": "Suiza", "EUZ": "Zona del euro", "JPN": "Japón", "CHN": "China", "IND": "India",
           "NOR": "Noruega", "MEX": "México", "GBR": "Reino Unido", "ARG": "Argentina"}


def fig_bigmac(bm, pib25):
    fecha = max(r["date"] for r in bm)
    ult = [r for r in bm if r["date"] == fecha]
    us = [r for r in ult if r["iso_a3"] == "USA"][0]
    filas = []
    for r in ult:
        iso_bm = ISO_BM.get(r["iso_a3"], r["iso_a3"])
        if iso_bm in pib25:
            filas.append((r["iso_a3"], r["name"], float(r["local_price"]), float(r["dollar_ex"]), float(r["dollar_price"]),
                          float(r["USD_raw"]), pib25[iso_bm]))
    xs = [math.log(f[6]) for f in filas]
    ys = [math.log(f[4]) for f in filas]
    a, b, r2 = ols(xs, ys)
    puntos = [(f[6], f[4]) for f in filas]
    recta = [(x, math.exp(a + b * math.log(x))) for x in (900.0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0, 140000.0)]
    pus = float(us["dollar_price"])
    tikz = "% Precio de un Big Mac en dólares (edición de julio de 2026) y PIB por habitante de 2025 en dólares\n"
    tikz += "% (The Economist, big-mac-data; Banco Mundial, NY.GDP.PCAP.CD; %d economías). Línea discontinua: precio en EE. UU.;\n" % len(filas)
    tikz += "% recta: regresión en logaritmos. Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_bigmac\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmode=log, xmin=800, xmax=150000, ymin=0, ymax=10.5,
  xtick={1000,10000,100000}, xticklabels={$1$ mil, $10$ mil, $100$ mil},
  xlabel={PIB por habitante en dólares, escala logarítmica},
  ylabel={Precio del Big Mac en dólares},
]
"""
    tikz += "\\draw[black!45, dashed] (axis cs:800,%.2f) -- (axis cs:150000,%.2f);\n" % (pus, pus)
    tikz += "\\addplot[only marks, mark=*, mark size=1.3pt, black!55] coordinates {%s};\n" % coordenadas(puntos, 2)
    tikz += "\\addplot[black, line width=0.8pt, smooth] coordinates {%s};\n" % coordenadas(recta, 2)
    for f in filas:
        if f[0] in ETIQ_BM:
            tikz += "\\node[font=\\scriptsize, anchor=south east, inner sep=1.5pt] at (axis cs:%.2f,%.2f) {%s};\n" % (f[6], f[4], ETIQ_BM[f[0]])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_bigmac.tikz"), "w", encoding="utf-8").write(tikz)
    return fecha, filas, (a, b, r2), pus


# ---------------------------------------------------------------- principal
def main():
    carpeta = sys.argv[1]
    bis = leer_bis(carpeta)
    fred = leer_fred(carpeta, "EXUSEU")
    eu = leer_eurostat(carpeta)
    nombres = paises_bm(carpeta)
    ppp = leer_bm(carpeta, "PA.NUS.PPP.json")
    xr = leer_bm(carpeta, "PA.NUS.FCRF.json")
    pibppa = leer_bm(carpeta, "NY.GDP.PCAP.PP.CD.json")
    pib25 = leer_bm(carpeta, "NY.GDP.PCAP.CD_2025.json")
    bm = leer_bigmac(carpeta)

    bil, nom, rea = fig_efectivo_euro(bis, fred)
    enom, eipc, eclu = fig_competitividad_espana(eu)
    penn, (pa, pb, pr2) = fig_penn(ppp, xr, pibppa, nombres)
    fecha_bm, bmf, (ba, bb, br2), pus = fig_bigmac(bm, pib25)

    # ---- cifras citadas en el texto
    cif = []
    def poner(clave, valor, fuente, donde):
        cif.append([clave, valor, fuente, donde])
        print("%-70s %s" % (clave, valor))
    fr = dict(fred)
    mn = min((v, f) for f, v in fred if "1999-01" <= f <= "2026-10")
    mx = max((v, f) for f, v in fred if "1999-01" <= f <= "2026-10")
    poner("EUR/USD mínimo mensual 1999-2026 (dólares por euro)", "%.4f en %s" % mn, "FRED EXUSEU", "I.1.2")
    poner("EUR/USD máximo mensual 1999-2026 (dólares por euro)", "%.4f en %s" % mx, "FRED EXUSEU", "I.1.2")
    poner("EUR/USD septiembre de 2022", "%.4f" % fr["2022-09"], "FRED EXUSEU", "I.1.2")
    poner("EUR/USD octubre de 2026", "%.4f" % fr["2026-10"], "FRED EXUSEU", "I.1.2")
    bn = dict(bis[("XM", "N", "B")]); br = dict(bis[("XM", "R", "B")])
    for a1, a2 in ((mn[1], mx[1]), (mx[1], "2022-09"), ("1999-01", "2026-09")):
        poner("Euro, variación %s a %s: bilateral / efectivo nominal / efectivo real (%%)" % (a1, a2),
              "%.1f / %.1f / %.1f" % (100 * (fr[a2] / fr[a1] - 1), 100 * (bn[a2] / bn[a1] - 1), 100 * (br[a2] / br[a1] - 1)),
              "FRED EXUSEU; BPI WS_EER", "I.1.2")
    # correlación de variaciones mensuales entre efectivo nominal y real
    meses = sorted(set(bn) & set(br))
    dn = [math.log(bn[m2] / bn[m1]) for m1, m2 in zip(meses, meses[1:]) if m1 >= "1999-01"]
    dr = [math.log(br[m2] / br[m1]) for m1, m2 in zip(meses, meses[1:]) if m1 >= "1999-01"]
    mdn, mdr = sum(dn) / len(dn), sum(dr) / len(dr)
    cor = sum((x - mdn) * (y - mdr) for x, y in zip(dn, dr)) / math.sqrt(sum((x - mdn) ** 2 for x in dn) * sum((y - mdr) ** 2 for y in dr))
    poner("Euro, correlación de las variaciones mensuales efectivo nominal y real 1999-2026", "%.3f" % cor, "BPI WS_EER", "I.1.2")
    e = {k: dict(v) for k, v in eu.items()}
    for s in ("NEER_EA21", "REER_EA21_CPI", "REER_EA21_ULCT"):
        v = e[s]
        poner("España frente a la zona del euro, %s: 1999T1, 2008T4, 2013T4, 2026T2" % s,
              "%.1f, %.1f, %.1f, %.1f" % (v["1999-Q1"], v["2008-Q4"], v["2013-Q4"], v[max(v)]), "Eurostat ert_eff_ic_q", "I.1.3")
        pico = max((val, t) for t, val in v.items() if "1999-Q1" <= t <= "2012-Q4")
        poner("  máximo 1999-2012 de %s" % s, "%.1f en %s" % pico, "Eurostat", "I.1.3")
        poner("  variación 1999T1-2008T4 y 2008T4-2013T4 de %s (%%)" % s,
              "%.1f y %.1f" % (100 * (v["2008-Q4"] / v["1999-Q1"] - 1), 100 * (v["2013-Q4"] / v["2008-Q4"] - 1)), "Eurostat", "I.1.3")
    poner("ICP 2021: economías en la figura", len(penn), "Banco Mundial", "I.1.4")
    poner("ICP 2021: elasticidad del nivel de precios al PIB por habitante (log-log), R2", "%.3f, %.3f" % (pb, pr2), "Banco Mundial", "I.1.4")
    dp = {f[0]: f for f in penn}
    for iso in ("CHE", "NOR", "DEU", "ESP", "JPN", "CHN", "MEX", "IND", "EGY"):
        if iso in dp:
            poner("ICP 2021 nivel de precios (EE. UU. = 100) y PIB pc PPA de %s" % iso, "%.1f; %.0f" % (dp[iso][4], dp[iso][5]), "Banco Mundial", "I.1.4")
    poner("Big Mac: edición y economías con PIB", "%s; %d" % (fecha_bm, len(bmf)), "The Economist; Banco Mundial", "I.2.2")
    poner("Big Mac: precio en EE. UU. (dólares)", "%.2f" % pus, "The Economist", "I.2.2")
    poner("Big Mac: elasticidad del precio en dólares al PIB por habitante (log-log), R2", "%.3f, %.3f" % (bb, br2), "The Economist; Banco Mundial", "I.2.2")
    dbm = {f[0]: f for f in bmf}
    for iso in ("CHE", "NOR", "EUZ", "GBR", "JPN", "CHN", "IND", "MEX"):
        if iso in dbm:
            f = dbm[iso]
            poner("Big Mac %s: precio local, tipo de cambio, precio en dólares, valoración bruta" % iso,
                  "%.2f; %.4f; %.2f; %.1f %%" % (f[2], f[3], f[4], 100 * f[5]), "The Economist", "I.2.2")
    extremos = sorted(bmf, key=lambda f: f[5])
    poner("Big Mac: más infravalorada y más sobrevalorada", "%s %.1f %%; %s %.1f %%" % (extremos[0][1], 100 * extremos[0][5], extremos[-1][1], 100 * extremos[-1][5]), "The Economist", "I.2.2")

    # ---- libro de datos
    leeme = [["Libro de datos del Tema 3.B.14 (Teorías de la determinación del tipo de cambio)"],
             ["Generado por Code/libro_y_figuras.py el %s. Hojas: Fuentes, Series (formato largo), ICP_2021, Big_Mac, Cifras_citadas." % FECHA_DESCARGA],
             ["Convención del tema: S son euros por dólar (sube = depreciación del euro). Los índices efectivos siguen la de sus fuentes (sube = apreciación)."]]
    fuentes = [["Serie o fichero", "Organismo", "Dirección de descarga", "Fecha de descarga"]]
    for fichero, url in DESCARGAS.items():
        org = {"dl_bis": "Banco de Pagos Internacionales", "dl_fred": "Banco de la Reserva Federal de San Luis (FRED)",
               "dl_eurostat": "Eurostat", "dl_wb": "Banco Mundial", "dl_bigmac": "The Economist"}[fichero.split("/")[0]]
        fuentes.append([fichero, org, url, FECHA_DESCARGA])
    filas = [["Serie", "Área", "Fecha", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]
    for f, v in fred:
        filas.append(["EXUSEU", "Zona del euro frente a EE. UU.", f, v, "dólares por euro, media mensual", "FRED", "ninguno", "anx_efectivo_euro (índice 2020 = 100)"])
    for (area, tipo, cesta), serie in sorted(bis.items()):
        if cesta != "B":
            continue
        for f, v in serie:
            filas.append(["BPI efectivo %s, cesta amplia" % ("nominal" if tipo == "N" else "real"), {"XM": "Zona del euro", "ES": "España"}[area],
                          f, v, "índice, 2020 = 100", "BPI WS_EER", "ninguno", "anx_efectivo_euro" if area == "XM" else ""])
    for s, serie in sorted(eu.items()):
        for f, v in serie:
            filas.append([s, "España", f, v, "índice, 2020 = 100", "Eurostat ert_eff_ic_q", "ninguno", "anx_competitividad_espana" if s != "REER_IC42_CPI" else ""])
    icp = [["ISO3", "Economía", "PPA del PIB (moneda nacional por dólar internacional)", "Tipo de cambio oficial (moneda nacional por dólar)",
            "Nivel de precios (EE. UU. = 100)", "PIB por habitante en PPA (dólares internacionales)"]]
    for f in penn:
        icp.append(list(f))
    big = [["ISO3", "Economía", "Precio local", "Tipo de cambio (moneda local por dólar)", "Precio en dólares", "Valoración bruta frente al dólar", "PIB por habitante 2025 (dólares)"]]
    for f in bmf:
        big.append(list(f))
    cifras = [["Cifra", "Valor", "Fuente", "Dónde"]] + cif
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B14.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("ICP_2021", icp), ("Big_Mac", big), ("Cifras_citadas", cifras)])
    print("Libro escrito:", os.path.join(TEMA, "Code", "datos_3B14.xlsx"))


if __name__ == "__main__":
    main()
