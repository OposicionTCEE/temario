# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3B14.xlsx) y figuras calculadas del anexo I (A1, 06/11/2026):
#   anx_efectivo_euro (tipo bilateral EUR/USD y tipos efectivos nominal y real del euro, BPI y FRED),
#   anx_competitividad_espana (tipos efectivos de España frente a la zona del euro, Eurostat),
#   anx_penn (nivel de precios y PIB por habitante, ICP 2021) y anx_bigmac (índice Big Mac de julio de 2026).
# Fuentes: Banco de Pagos Internacionales (WS_EER, índices efectivos mensuales, cesta amplia de 64 economías,
# 2020 = 100); FRED (EXUSEU, dólares por euro, media mensual); Eurostat (ert_eff_ic_q, índices efectivos de España
# frente a los socios de la zona del euro, composición de 2026, 2020 = 100); Banco Mundial (base de datos del ICP 2021,
# fuente 90: nivel de precios del PIB, mundo = 100, y PIB por habitante en PPA; Indicadores del Desarrollo Mundial:
# NY.GDP.PCAP.CD de 2025, PIB por habitante en dólares corrientes);
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
    "dl_icp/gdp_PX.WL.json": "https://api.worldbank.org/v2/sources/90/country/all/series/1000000/classification/PX.WL/time/YR2021?format=json&per_page=300",
    "dl_icp/gdp_PCAP.PP.json": "https://api.worldbank.org/v2/sources/90/country/all/series/1000000/classification/PCAP.PP/time/YR2021?format=json&per_page=300",
    "dl_wb/NY.GDP.PCAP.CD_2025.json": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?date=2025&format=json&per_page=400",
    "dl_wb/paises.json": "https://api.worldbank.org/v2/country?format=json&per_page=400",
    "dl_bigmac/big-mac-full-index.csv": "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv",
    "dl_bis_xru/WS_XRU_csv_flat.csv": "https://data.bis.org/static/bulk/WS_XRU_csv_flat.zip (descomprimido; descargado el 07/11/2026)",
    "dl_bis_cpi/WS_LONG_CPI_csv_flat.csv": "https://data.bis.org/static/bulk/WS_LONG_CPI_csv_flat.zip (descomprimido; descargado el 07/11/2026)",
    "dl_eurostat_ppp/pli.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_ppp_ind?na_item=PLI_EU27_2020&ppp_cat=P0101&ppp_cat=P0201&ppp_cat=GDP&sinceTimePeriod=2022&format=JSON&lang=EN",
    "dl_eurostat_ppp/vol_aic.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_ppp_ind?na_item=VI_PPS_EU27_2020_HAB&ppp_cat=A01&sinceTimePeriod=2022&format=JSON&lang=EN",
    "dl_wb_ca/ca_esp.json": "https://api.worldbank.org/v2/country/ESP;DEU;EMU/indicator/BN.CAB.XOKA.GD.ZS?date=1995:2025&format=json&per_page=200",
    "dl_bis_pol/WS_CBPOL_csv_flat.csv": "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip (descomprimido; descargado el 07/11/2026)",
    "dl_wb_us/ca_usa.json": "https://api.worldbank.org/v2/country/USA/indicator/BN.CAB.XOKA.GD.ZS?date=1980:2025&format=json&per_page=200",
    "dl_wb_us/exp_wld.json": "https://api.worldbank.org/v2/country/WLD/indicator/NE.EXP.GNFS.CD?date=2015:2025&format=json&per_page=200",
    "dl_wb_m/m2.json": "https://api.worldbank.org/v2/country/all/indicator/FM.LBL.BMNY.CN?date=1995:2025&format=json&per_page=20000",
    "dl_wb_m/pib.json": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KN?date=1995:2025&format=json&per_page=20000",
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
            if area not in ("XM", "ES", "US"):
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


def leer_icp(carpeta, fichero):  # base de datos ICP 2021 del Banco Mundial (fuente 90): PIB, año 2021
    d = json.load(open(os.path.join(carpeta, "dl_icp", fichero), encoding="utf-8"))
    out = {}
    for r in d["source"]["data"]:
        v = {x["concept"]: x["id"] for x in r["variable"]}
        if r["value"] is not None:
            out[v["Country"]] = r["value"]
    return out


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
    tikz += r"""  xmin=1998.5, xmax=2027, xtick={2000,2005,2010,2015,2020,2025}, ymin=65, ymax=145,
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
    tikz += r"""  xmin=1993.5, xmax=2027, xtick={1995,2000,2005,2010,2015,2020,2025}, ymin=88, ymax=115,
  ylabel={Índice, $2020=100$},
  legend to name=leyendaespana,
]
"""
    tikz += "\\draw[black!35, densely dotted] (axis cs:1999,88) -- (axis cs:1999,115);\n"
    tikz += "\\node[font=\\scriptsize, black!60, anchor=north west, inner sep=1.5pt] at (axis cs:1999,115) {Euro};\n"
    tikz += "\\addplot[black!45, line width=0.6pt] coordinates {%s};\n" % coordenadas(nom)
    tikz += "\\addlegendentry{Nominal}\n"
    tikz += "\\addplot[black, line width=1.1pt] coordinates {%s};\n" % coordenadas(ipc)
    tikz += "\\addlegendentry{Real con precios de consumo}\n"
    tikz += "\\addplot[black, dashed, line width=0.8pt] coordinates {%s};\n" % coordenadas(clu)
    tikz += "\\addlegendentry{Real con costes laborales unitarios}\n"
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendaespana}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_competitividad_espana.tikz"), "w", encoding="utf-8").write(tikz)
    return nom, ipc, clu


ETIQ_PENN = {"USA": ("EE. UU.", "east"), "CHE": ("Suiza", "south east"), "ESP": ("España", "east"), "DEU": ("Alemania", "north west"),
             "JPN": ("Japón", "east"), "CHN": ("China", "south east"), "IND": ("India", "south east"), "MEX": ("México", "north west"),
             "NOR": ("Noruega", "west"), "EGY": ("Egipto", "north west")}


def fig_penn(pxwl, pcpp, nombres):
    filas = []
    us = pxwl["USA"]
    for iso in sorted(nombres):
        if iso in pxwl and iso in pcpp:
            filas.append((iso, nombres[iso], pxwl[iso], None, 100.0 * pxwl[iso] / us, pcpp[iso]))
    xs = [math.log(f[5]) for f in filas]
    ys = [math.log(f[4]) for f in filas]
    a, b, r2 = ols(xs, ys)
    puntos = [(f[5], f[4]) for f in filas]
    x0, x1 = 900.0, 150000.0
    recta = [(x, math.exp(a + b * math.log(x))) for x in (x0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0, x1)]
    tikz = "% Nivel de precios del PIB (ICP 2021: mundo = 100, reescalado a EE. UU. = 100) y PIB por habitante en PPA, 2021\n"
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
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.8pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_PENN[f[0]][1], f[5], f[4], ETIQ_PENN[f[0]][0])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_penn.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, (a, b, r2)


ISO_BM = {"EUZ": "EMU"}
ETIQ_BM = {"USA": ("EE. UU.", "south east"), "CHE": ("Suiza", "south east"), "EUZ": ("Zona del euro", "south east"), "JPN": ("Japón", "east"),
           "CHN": ("China", "south east"), "IND": ("India", "south east"), "NOR": ("Noruega", "south east"), "MEX": ("México", "south east")}


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
    tikz += "%% (The Economist, big-mac-data; Banco Mundial, NY.GDP.PCAP.CD; %d economías). Línea discontinua: precio en EE. UU.;\n" % len(filas)
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
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.8pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_BM[f[0]][1], f[6], f[4], ETIQ_BM[f[0]][0])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_bigmac.tikz"), "w", encoding="utf-8").write(tikz)
    return fecha, filas, (a, b, r2), pus


# ---------------------------------------------------------------- A2 (I.3): paridad relativa, hecho de MUSSA y semividas
# Fuentes: BPI WS_XRU (tipos frente al dólar, medias anuales y mensuales; los de los países del euro, en euros también antes
# de 1999), BPI WS_LONG_CPI (índices de precios de consumo, anuales y mensuales) y BPI WS_EER (efectivos reales, cesta
# reducida de 27 economías, mensual desde 1964).
NOMBRES_ES = {"AR": "Argentina", "PE": "Perú", "TR": "Turquía", "CL": "Chile", "IL": "Israel", "MX": "México", "IS": "Islandia",
              "CO": "Colombia", "ZA": "Sudáfrica", "IN": "India", "KR": "Corea", "ES": "España", "GB": "Reino Unido", "DE": "Alemania",
              "JP": "Japón", "CH": "Suiza", "XM": "Zona del euro", "DK": "Dinamarca", "IT": "Italia", "GR": "Grecia", "NO": "Noruega",
              "NZ": "Nueva Zelanda", "NL": "Países Bajos", "IE": "Irlanda", "AU": "Australia", "TW": "Taiwán", "CA": "Canadá",
              "HK": "Hong Kong", "BE": "Bélgica", "US": "Estados Unidos", "SG": "Singapur", "FR": "Francia", "FI": "Finlandia",
              "PT": "Portugal", "SE": "Suecia", "AT": "Austria", "MY": "Malasia", "LU": "Luxemburgo", "PH": "Filipinas"}


def leer_xru(carpeta):
    xa, xm = {}, {}
    with open(os.path.join(carpeta, "dl_bis_xru", "WS_XRU_csv_flat.csv"), encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["COLLECTION:Collection"][:1] != "A" or d["OBS_VALUE:Observation Value"] in ("", "NaN"):
                continue
            fr = d["FREQ:Frequency"][:1]
            if fr not in ("A", "M"):
                continue
            a = d["REF_AREA:Reference area"][:2]
            (xa if fr == "A" else xm).setdefault(a, {})[d["TIME_PERIOD:Time period or range"]] = float(d["OBS_VALUE:Observation Value"])
    return xa, xm


def leer_ipc(carpeta):
    ca, cm = {}, {}
    with open(os.path.join(carpeta, "dl_bis_cpi", "WS_LONG_CPI_csv_flat.csv"), encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["UNIT_MEASURE:Unit of measure"][:3] != "628" or d["OBS_VALUE:Observation Value"] in ("", "NaN"):
                continue
            a = d["REF_AREA:Reference area"][:2]
            (ca if d["FREQ:Frequency"][:1] == "A" else cm).setdefault(a, {})[d["TIME_PERIOD:Time period or range"]] = float(d["OBS_VALUE:Observation Value"])
    return ca, cm


def leer_eer_estrecho_real(carpeta):
    out = {}
    with open(os.path.join(carpeta, "dl_bis", "WS_EER_csv_flat.csv"), encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if (d["FREQ:Frequency"][:1] == "M" and d["EER_TYPE:Type"][:1] == "R" and d["EER_BASKET:Basket"][:1] == "N"
                    and d["OBS_VALUE:Observation Value"] not in ("", "NaN")):
                out.setdefault(d["REF_AREA:Reference area"][:2], {})[d["TIME_PERIOD:Time period or range"]] = float(d["OBS_VALUE:Observation Value"])
    return out


ETIQ_PPA_A = {"AR": "north west", "PE": "north west", "TR": "north west", "CL": "south east", "IL": "north west", "MX": "south east"}
ETIQ_PPA_B = {"CH": "south east", "JP": "north west", "ES": "north west", "GB": "south east", "IN": "south east", "KR": "south east",
              "ZA": "south east", "CO": "north west", "IS": "south east"}


def fig_ppa_relativa(xa, ca, t0="1970", t1="2025"):
    n = int(t1) - int(t0)
    us = math.log(ca["US"][t1] / ca["US"][t0]) / n
    pts = []
    for a in sorted(ca):
        if a == "US" or a not in xa:
            continue
        if t0 in ca[a] and t1 in ca[a] and t0 in xa[a] and t1 in xa[a]:
            pts.append((a, NOMBRES_ES.get(a, a), 100 * (math.log(ca[a][t1] / ca[a][t0]) / n - us), 100 * math.log(xa[a][t1] / xa[a][t0]) / n))
    a1, b1, r21 = ols([p[2] for p in pts], [p[3] for p in pts])
    sub = [p for p in pts if p[2] < 10]
    a2, b2, r22 = ols([p[2] for p in sub], [p[3] for p in sub])
    eje = r"""  scale only axis, width=6.1cm, height=5.0cm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize}, title style={font=\footnotesize},
  xlabel={Inflación menos la de EE.\,UU. (puntos al año)}, clip=false,
"""
    tikz = "% Paridad del poder adquisitivo relativa a largo plazo: depreciación media anual frente al dólar y diferencia\n"
    tikz += "%% media anual de inflación con EE. UU., %s-%s, %d economías (BPI WS_XRU y WS_LONG_CPI; tasas logarítmicas en puntos).\n" % (t0, t1, len(pts))
    tikz += "% Panel (b): las que tienen una diferencia menor de 10 puntos. Línea discontinua: 45 grados.\n"
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_ppa_relativa\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[name=pa,\n" + eje
    tikz += "  xmin=-5, xmax=60, ymin=-5, ymax=60, ylabel={Depreciación frente al dólar (puntos al año)},\n  title={(a) Las $%d$ economías},\n]\n" % len(pts)
    tikz += "\\addplot[black!40, dashed] coordinates {(-5,-5) (60,60)};\n"
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(p[2], p[3]) for p in pts], 2)
    for p in pts:
        if p[0] in ETIQ_PPA_A:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_PPA_A[p[0]], p[2], p[3], p[1])
    tikz += "\\end{axis}\n\\begin{axis}[at={(pa.east)}, anchor=west, xshift=1.3cm,\n" + eje
    tikz += "  xmin=-3, xmax=10.5, ymin=-4, ymax=11,\n  title={(b) Diferencia de inflación menor de $10$ puntos},\n]\n"
    tikz += "\\addplot[black!40, dashed] coordinates {(-3,-3) (10.5,10.5)};\n"
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(p[2], p[3]) for p in sub], 2)
    for p in sub:
        if p[0] in ETIQ_PPA_B:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_PPA_B[p[0]], p[2], p[3], p[1])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_ppa_relativa.tikz"), "w", encoding="utf-8").write(tikz)
    return pts, (a1, b1, r21), (len(sub), a2, b2, r22)


def estad_mussa(meses, s, q, m0, m1):
    idx = [i for i, m in enumerate(meses) if m0 <= m <= m1]
    ds = [s[i] - s[i - 1] for i in idx[1:]]
    dq = [q[i] - q[i - 1] for i in idx[1:]]
    def dt(v):
        m = sum(v) / len(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    mds, mdq = sum(ds) / len(ds), sum(dq) / len(dq)
    cor = sum((a - mds) * (b - mdq) for a, b in zip(ds, dq)) / ((len(ds) - 1) * dt(ds) * dt(dq))
    return 100 * dt(ds), 100 * dt(dq), cor, len(ds)


def fig_mussa(xm, cm):
    gb, pu, pg = xm["GB"], cm["US"], cm["GB"]
    meses = sorted(m for m in gb if m >= "1950-01" and m in pu and m in pg)
    s = [math.log(gb[m]) for m in meses]
    q = [math.log(gb[m]) + math.log(pu[m]) - math.log(pg[m]) for m in meses]
    b20 = [i for i, m in enumerate(meses) if m.startswith("2020")]
    s0 = sum(s[i] for i in b20) / len(b20)
    q0 = sum(q[i] for i in b20) / len(b20)
    nom = [(decimal_mes(m), 100 * math.exp(s[i] - s0)) for i, m in enumerate(meses)]
    rea = [(decimal_mes(m), 100 * math.exp(q[i] - q0)) for i, m in enumerate(meses)]
    bw = estad_mussa(meses, s, q, "1950-01", "1971-07")
    fl = estad_mussa(meses, s, q, "1973-03", meses[-1])
    tikz = "% El hecho de MUSSA (1986): tipos de cambio nominal y real de la libra frente al dólar (libras por dólar; sube =\n"
    tikz += "%% depreciación de la libra), mensual, %s a %s, índices 2020 = 100 (BPI WS_XRU y WS_LONG_CPI).\n" % (meses[0], meses[-1])
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_mussa\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmin=1949, xmax=2027.5, xtick={1950,1960,1970,1980,1990,2000,2010,2020}, ymin=35, ymax=135, clip=false,
  ylabel={Índice, $2020=100$},
  legend to name=leyendamussa,
]
"""
    tikz += "\\fill[black!8] (axis cs:1971.6,35) rectangle (axis cs:1973.2,135);\n"
    tikz += "\\node[font=\\scriptsize, black!65, anchor=north] at (axis cs:1960.5,135) {Bretton Woods};\n"
    tikz += "\\node[font=\\scriptsize, black!65, anchor=north] at (axis cs:2000,135) {Flotación};\n"
    tikz += "\\addplot[black!45, line width=0.6pt] coordinates {%s};\n" % coordenadas(nom)
    tikz += "\\addlegendentry{Tipo nominal}\n"
    tikz += "\\addplot[black, line width=0.9pt] coordinates {%s};\n" % coordenadas(rea)
    tikz += "\\addlegendentry{Tipo real}\n"
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendamussa}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_mussa.tikz"), "w", encoding="utf-8").write(tikz)
    return meses, nom, rea, bw, fl


def fig_semividas(eer, desde="1975-01"):
    res = []
    for a, ser in eer.items():
        ms = sorted(m for m in ser if m >= desde)
        if len(ms) < 600 or a not in NOMBRES_ES:
            continue
        y = [math.log(ser[m]) for m in ms]
        c, rho, _ = ols(y[:-1], y[1:])
        semivida = math.log(0.5) / math.log(rho) / 12.0 if rho < 1 else float("inf")
        rk = rho + (1 + 3 * rho) / (len(ms) - 1)  # corrección del sesgo de KENDALL (1954)
        semik = math.log(0.5) / math.log(rk) / 12.0 if rk < 1 else float("inf")
        res.append((a, NOMBRES_ES[a], ms[0], ms[-1], len(ms), rho, semivida, rk, semik))
    res.sort(key=lambda r: r[6], reverse=True)
    med = sorted(r[6] for r in res)[len(res) // 2]
    medk = sorted(r[8] for r in res)[len(res) // 2]
    nk = sum(1 for r in res if r[7] >= 1)
    tope = 20.0
    tikz = "% Semividas del tipo de cambio efectivo real (BPI, cesta reducida, mensual) estimadas con un AR(1) por mínimos\n"
    tikz += "%% cuadrados sobre el logaritmo, %s a %s, %d economías; semivida = ln(0,5)/ln(rho)/12 años. Banda: 3 a 5 años.\n" % (res[0][2], res[0][3], len(res))
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_semividas\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[\n"
    tikz += r"""  scale only axis, width=11.5cm, height=%.2fcm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  xmin=0, xmax=%.0f, ymin=0.3, ymax=%.1f, clip=false, xtick={0,2,...,20},
  ytick={%s}, yticklabels={%s},
  xlabel={Semivida estimada (años)},
]
""" % (0.34 * len(res), tope, len(res) + 0.7, ",".join(str(i + 1) for i in range(len(res))), ",".join(r[1] for r in res))
    tikz += "\\fill[black!8] (axis cs:3,0.3) rectangle (axis cs:5,%.1f);\n" % (len(res) + 0.7)
    barras = [(min(r[6], tope), i + 1) for i, r in enumerate(res)]
    tikz += "\\addplot[xbar, bar width=5.5pt, fill=black!50, draw=none] coordinates {%s};\n" % coordenadas(barras, 2)
    tikz += "\\draw[black, densely dashed] (axis cs:%.2f,0.3) -- (axis cs:%.2f,%.1f);\n" % (med, med, len(res) + 0.7)
    for i, r in enumerate(res):
        if r[6] > tope:
            tikz += "\\node[font=\\scriptsize, anchor=west, inner sep=2pt] at (axis cs:%.1f,%d) {$%s$};\n" % (tope, i + 1, coma(r[6], 0))
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_semividas.tikz"), "w", encoding="utf-8").write(tikz)
    return res, med, medk, nk


# ---------------------------------------------------------------- A3 (I.5 y I.6): precios de bienes y servicios, cuenta corriente
# Fuentes: Eurostat prc_ppp_ind (programa de paridades de Eurostat y la OCDE): índices de nivel de precios (UE27 = 100) de
# los bienes de consumo (P0101) y de los servicios de consumo (P0201), y volumen del consumo individual efectivo por
# habitante en estándares de poder adquisitivo (A01, UE27 = 100), 2024; Banco Mundial BN.CAB.XOKA.GD.ZS (cuenta corriente,
# % del PIB).
NOMBRES_EU = {"CH": "Suiza", "IS": "Islandia", "NO": "Noruega", "DK": "Dinamarca", "DE": "Alemania", "ES": "España",
              "PL": "Polonia", "BG": "Bulgaria", "TR": "Turquía", "AL": "Albania", "PT": "Portugal", "LU": "Luxemburgo",
              "IE": "Irlanda", "MK": "Macedonia del Norte", "FR": "Francia", "IT": "Italia", "RO": "Rumanía"}
# Ancla de cada etiqueta (la etiqueta queda al lado opuesto del ancla); una terna (ancla, x, y) la aparta a (x, y)
# con una línea fina hasta el punto, para España, rodeada de otros puntos.
ETIQ_BS = {"CH": "south east", "IS": "north east", "NO": "south east", "DE": "south", "ES": ("west", 101, 74),
           "PL": "north west", "BG": "north east", "TR": "north west", "AL": "south west"}


def leer_eurostat_ppp(carpeta, fichero):
    d = json.load(open(os.path.join(carpeta, "dl_eurostat_ppp", fichero), encoding="utf-8"))
    ids, tam = d["id"], d["size"]
    inv = {dim: {pos: cod for cod, pos in d["dimension"][dim]["category"]["index"].items()} for dim in ids}
    out = {}
    for plano, valor in d["value"].items():
        resto, c = int(plano), {}
        for dim, n in reversed(list(zip(ids, tam))):
            c[dim] = inv[dim][resto % n]
            resto //= n
        out[(c["ppp_cat"], c["geo"], c["time"])] = float(valor)
    return out, d["dimension"]["geo"]["category"]["label"]


def fig_bienes_servicios(pli, aic, geo, anio="2024"):
    filas = []
    for g in sorted(geo):
        if g.startswith(("EA", "EU", "CPC")):
            continue
        if ("P0101", g, anio) in pli and ("P0201", g, anio) in pli and ("A01", g, anio) in aic:
            filas.append((g, NOMBRES_EU.get(g, geo[g]), aic[("A01", g, anio)], pli[("P0101", g, anio)], pli[("P0201", g, anio)]))
    lx = [math.log(f[2]) for f in filas]
    ab, bb, rb = ols(lx, [math.log(f[3]) for f in filas])
    as_, bs, rs = ols(lx, [math.log(f[4]) for f in filas])
    def dt(v):
        m = sum(v) / len(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    db, ds = dt([math.log(f[3]) for f in filas]), dt([math.log(f[4]) for f in filas])
    xs = [35, 50, 70, 90, 110, 130, 150]
    tikz = "% Niveles de precios de los bienes y de los servicios de consumo (UE27 = 100) y consumo individual efectivo por\n"
    tikz += "%% habitante en estándares de poder adquisitivo (UE27 = 100), %s, %d economías europeas (Eurostat, prc_ppp_ind).\n" % (anio, len(filas))
    tikz += "% Curvas: regresiones en logaritmos de cada serie. Generado por Code/libro_y_figuras.py;\n"
    tikz += "% compilar con: bash Code/generar_figura.sh anx_bienes_servicios\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmin=30, xmax=155, ymin=20, ymax=215, clip=false,
  xlabel={Consumo individual por habitante en poder adquisitivo (UE${}=100$)},
  ylabel={Nivel de precios (UE${}=100$)},
  legend to name=leyendabs,
]
"""
    tikz += "\\addplot[only marks, mark=o, mark size=1.5pt, black!60] coordinates {%s};\n" % coordenadas([(f[2], f[3]) for f in filas], 1)
    tikz += "\\addlegendentry{Bienes de consumo}\n"
    tikz += "\\addplot[only marks, mark=*, mark size=1.5pt, black] coordinates {%s};\n" % coordenadas([(f[2], f[4]) for f in filas], 1)
    tikz += "\\addlegendentry{Servicios de consumo}\n"
    tikz += "\\addplot[black!60, line width=0.7pt, dashed, smooth] coordinates {%s};\n" % coordenadas([(x, math.exp(ab + bb * math.log(x))) for x in xs], 2)
    tikz += "\\addplot[black, line width=0.8pt, smooth] coordinates {%s};\n" % coordenadas([(x, math.exp(as_ + bs * math.log(x))) for x in xs], 2)
    for f in filas:
        e = ETIQ_BS.get(f[0])
        if isinstance(e, tuple):
            tikz += "\\draw[black!50, line width=0.3pt] (axis cs:%.1f,%.1f) -- (axis cs:%.1f,%.1f);\n" % (f[2], f[4], e[1], e[2])
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.8pt] at (axis cs:%.1f,%.1f) {%s};\n" % (e[0], e[1], e[2], f[1])
        elif e:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.8pt] at (axis cs:%.1f,%.1f) {%s};\n" % (e, f[2], f[4], f[1])
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendabs}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_bienes_servicios.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, (bb, rb, db), (bs, rs, ds)


def leer_cuenta_corriente(carpeta):
    d = json.load(open(os.path.join(carpeta, "dl_wb_ca", "ca_esp.json"), encoding="utf-8"))
    out = {}
    for r in d[1]:
        if r["value"] is not None:
            out.setdefault(r["countryiso3code"], {})[r["date"]] = r["value"]
    return out


def fig_cuenta_corriente(ccor):
    # El Banco Mundial no da el agregado de la zona del euro (EMU sin valores): solo España y Alemania.
    serie = {p: sorted((int(a), v) for a, v in ccor[p].items()) for p in ("ESP", "DEU")}
    tikz = "% Saldo de la cuenta corriente en porcentaje del PIB de España y Alemania, anual, 1995-2025\n"
    tikz += "% (Banco Mundial, Indicadores del Desarrollo Mundial, BN.CAB.XOKA.GD.ZS).\n"
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_cuenta_corriente\n"
    tikz += "\\begin{tikzpicture}\n" + EJES
    tikz += r"""  xmin=1994.5, xmax=2025.5, xtick={1995,2000,2005,2010,2015,2020,2025}, ymin=-11, ymax=10, ytick={-10,-5,0,5,10},
  ylabel={Porcentaje del PIB},
  legend to name=leyendacc,
]
"""
    tikz += "\\draw[black!50] (axis cs:1994.5,0) -- (axis cs:2025.5,0);\n"
    tikz += "\\draw[black!35, densely dotted] (axis cs:1999,-11) -- (axis cs:1999,10);\n"
    tikz += "\\node[font=\\scriptsize, black!60, anchor=north west, inner sep=1.5pt] at (axis cs:1999,10) {Euro};\n"
    tikz += "\\addplot[black, line width=1.1pt, mark=*, mark size=0.9pt] coordinates {%s};\n" % coordenadas(serie["ESP"], 1)
    tikz += "\\addlegendentry{España}\n"
    tikz += "\\addplot[black, dashed, line width=0.8pt] coordinates {%s};\n" % coordenadas(serie["DEU"], 1)
    tikz += "\\addlegendentry{Alemania}\n"
    tikz += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendacc}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_cuenta_corriente.tikz"), "w", encoding="utf-8").write(tikz)
    return serie


# ---------------------------------------------------------------- A4 (anexo II): flujos y paridades
# BPI WS_CBPOL (tipos oficiales, mensuales, fin de periodo); Banco Mundial: cuenta corriente de EE. UU. y exportaciones
# mundiales de bienes y servicios.
def leer_cbpol(carpeta):
    out = {}
    with open(os.path.join(carpeta, "dl_bis_pol", "WS_CBPOL_csv_flat.csv"), encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if not d["FREQ:Frequency"].startswith("M") or d["OBS_VALUE:Observation Value"] in ("", "NaN"):
                continue
            out.setdefault(d["REF_AREA:Reference area"][:2], {})[d["TIME_PERIOD:Time period or range"]] = float(d["OBS_VALUE:Observation Value"])
    return out


def leer_wb_simple(carpeta, sub, fichero):
    d = json.load(open(os.path.join(carpeta, sub, fichero), encoding="utf-8"))
    return {int(r["date"]): r["value"] for r in d[1] if r["value"] is not None}


def meses_entre(t0, t1):
    y, m, out = int(t0[:4]), int(t0[5:]), []
    while (y, m) <= (int(t1[:4]), int(t1[5:])):
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def fig_dolar_cuenta_corriente(bis, ccus, a0=1980, a1=2025):
    meses = {}
    for f, v in bis[("US", "R", "N")]:
        meses.setdefault(int(f[:4]), []).append(v)
    reer = [(a, sum(meses[a]) / len(meses[a])) for a in range(a0, a1 + 1) if len(meses.get(a, [])) == 12]
    cc = [(a, ccus[a]) for a in range(a0, a1 + 1) if a in ccus]
    lo, hi = 10 * math.floor(min(v for _, v in reer) / 10), 10 * math.ceil(max(v for _, v in reer) / 10)
    eje = r"""  scale only axis, width=14.2cm, height=3.4cm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize}, title style={font=\footnotesize},
  xmin=1979.5, xmax=2025.5, xtick={1980,1985,1990,1995,2000,2005,2010,2015,2020,2025}, clip=false,
"""
    tikz = "% (a) Tipo de cambio efectivo real del dólar (BPI, cesta reducida, media anual, 2020 = 100; subida = apreciación) y\n"
    tikz += "%% (b) saldo de la cuenta corriente de Estados Unidos en porcentaje del PIB (Banco Mundial, BN.CAB.XOKA.GD.ZS), %d-%d.\n" % (a0, a1)
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_dolar_cuenta_corriente\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[name=pa,\n" + eje
    tikz += "  ymin=%d, ymax=%d, ylabel={Índice, $2020=100$}, xticklabels={}, title={(a) Tipo de cambio efectivo real del dólar},\n]\n" % (lo, hi)
    tikz += "\\addplot[black, line width=1.1pt] coordinates {%s};\n" % coordenadas(reer, 1)
    tikz += "\\end{axis}\n\\begin{axis}[at={(pa.south)}, anchor=north, yshift=-1.0cm,\n" + eje
    tikz += "  ymin=-7, ymax=1, ytick={-6,-4,-2,0}, ylabel={Porcentaje del PIB}, title={(b) Saldo de la cuenta corriente de Estados Unidos},\n]\n"
    tikz += "\\draw[black!50] (axis cs:1979.5,0) -- (axis cs:2025.5,0);\n"
    tikz += "\\addplot[black, line width=1.1pt, mark=*, mark size=0.8pt] coordinates {%s};\n" % coordenadas(cc, 2)
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_dolar_cuenta_corriente.tikz"), "w", encoding="utf-8").write(tikz)
    return dict(reer), dict(cc)


NOMBRES_PAR = dict(NOMBRES_ES, BR="Brasil", RU="Rusia", CN="China", CZ="Chequia", HU="Hungría", ID="Indonesia", KW="Kuwait",
                   MA="Marruecos", MK="Macedonia del Norte", PL="Polonia", RO="Rumanía", RS="Serbia", SA="Arabia Saudí",
                   TH="Tailandia")
# La zona del euro está rodeada de puntos: etiqueta apartada con una línea fina, como España en anx_bienes_servicios.
ETIQ_PAR_A = {"BR": "north east", "RU": "south east", "CN": "north", "CH": "south west", "XM": ("west", -2.3, 2.3)}
ETIQ_PAR_B = {"BR": "north east", "RU": "south east", "ZA": "south east", "CN": "north", "CH": "south west", "XM": ("west", -2.4, 1.7)}


def fig_paridades_largo(pol, xm, cm, t0="2006-01", t1="2025-06", tope=10.0):
    ms = meses_entre(t0, t1)
    n = len(ms) / 12.0
    filas = []
    for a in sorted(pol):
        if a == "US" or a not in xm or t0 not in xm[a] or t1 not in xm[a]:
            continue
        if not all(m in pol[a] and m in pol["US"] for m in ms):
            continue
        di = 100 * sum(math.log(1 + pol[a][m] / 100) - math.log(1 + pol["US"][m] / 100) for m in ms) / len(ms)
        dep = 100 * math.log(xm[a][t1] / xm[a][t0]) / n
        inf = None
        if a in cm and t0 in cm[a] and t1 in cm[a]:
            inf = 100 * (math.log(cm[a][t1] / cm[a][t0]) - math.log(cm["US"][t1] / cm["US"][t0])) / n
        filas.append((a, NOMBRES_PAR.get(a, a), di, inf, dep))
    sub = [f for f in filas if abs(f[2]) < tope]
    con_inf = [f for f in sub if f[3] is not None]
    est = {"uip_todas": ols([f[2] for f in filas], [f[4] for f in filas]),
           "uip_sub": ols([f[2] for f in sub], [f[4] for f in sub]),
           "fisher_sub": ols([f[2] for f in con_inf], [f[3] for f in con_inf]),
           "ppa_sub": ols([f[3] for f in con_inf], [f[4] for f in con_inf])}
    eje = r"""  scale only axis, width=6.1cm, height=5.0cm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize}, title style={font=\footnotesize},
  xlabel={Tipo oficial menos el de EE.\,UU. (puntos al año)}, clip=false, xmin=-2.5, xmax=9, ymin=-3, ymax=7,
"""
    def recta(ab):
        return coordenadas([(x, ab[0] + ab[1] * x) for x in (-2.5, 9)], 2)
    tikz = "%% Paridades a largo plazo, %s a %s: diferencia media del tipo oficial con el de EE. UU. frente a (a) la diferencia\n" % (t0, t1)
    tikz += "%% media de inflación y (b) la depreciación media frente al dólar; %d economías con diferencia menor de %d puntos\n" % (len(sub), tope)
    tikz += "% (BPI WS_CBPOL, WS_LONG_CPI y WS_XRU; tasas logarítmicas en puntos al año). Discontinua: 45 grados; continua: MCO.\n"
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_paridades_largo\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[name=pa,\n" + eje
    tikz += "  ylabel={Inflación menos la de EE.\\,UU. (puntos al año)}, title={(a) Tipos de interés e inflación},\n]\n"
    tikz += "\\addplot[black!40, dashed] coordinates {(-2.5,-2.5) (7,7)};\n"
    tikz += "\\addplot[black, line width=0.6pt] coordinates {%s};\n" % recta(est["fisher_sub"])
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(f[2], f[3]) for f in con_inf], 2)
    for f in con_inf:
        e = ETIQ_PAR_A.get(f[0])
        if isinstance(e, tuple):
            tikz += "\\draw[black!50, line width=0.3pt] (axis cs:%.2f,%.2f) -- (axis cs:%.2f,%.2f);\n" % (f[2], f[3], e[1] + 1.4, e[2] - 0.35)
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (e[0], e[1], e[2], f[1])
        elif e:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (e, f[2], f[3], f[1])
    tikz += "\\end{axis}\n\\begin{axis}[at={(pa.east)}, anchor=west, xshift=1.3cm,\n" + eje
    tikz += "  ylabel={Depreciación frente al dólar (puntos al año)}, title={(b) Tipos de interés y depreciación},\n]\n"
    tikz += "\\addplot[black!40, dashed] coordinates {(-2.5,-2.5) (7,7)};\n"
    tikz += "\\addplot[black, line width=0.6pt] coordinates {%s};\n" % recta(est["uip_sub"])
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(f[2], f[4]) for f in sub], 2)
    for f in sub:
        e = ETIQ_PAR_B.get(f[0])
        if isinstance(e, tuple):
            tikz += "\\draw[black!50, line width=0.3pt] (axis cs:%.2f,%.2f) -- (axis cs:%.2f,%.2f);\n" % (f[2], f[4], e[1] + 1.4, e[2] - 0.35)
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (e[0], e[1], e[2], f[1])
        elif e:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (e, f[2], f[4], f[1])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_paridades_largo.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, sub, est


# ---------------------------------------------------------------- A5 (anexo II): modelo monetario a largo plazo
# Banco Mundial: dinero en sentido amplio (FM.LBL.BMNY.CN, moneda nacional) y PIB real (NY.GDP.MKTP.KN); BPI: tipos de cambio
# medios anuales frente al dólar. Se excluyen las monedas con tipo fijo: desviación típica de la variación anual frente al
# dólar menor de un punto (ancladas al dólar) o correlación mayor de 0,95 con la del euro (ancladas al euro).
def leer_wb_panel(carpeta, sub, fichero):
    d = json.load(open(os.path.join(carpeta, sub, fichero), encoding="utf-8"))
    out, nombres = {}, {}
    for r in d[1]:
        if r["value"] is not None:
            out.setdefault(r["country"]["id"], {})[int(r["date"])] = r["value"]
            nombres[r["country"]["id"]] = r["country"]["value"]
    return out, nombres


NOMBRES_MON = dict(NOMBRES_PAR, AO="Angola", GH="Ghana", UA="Ucrania", NG="Nigeria", EG="Egipto", CD="R. D. del Congo")
ETIQ_MON_A = {"AR": "north west", "TR": "south east", "GH": "north west", "UA": "north west", "NG": "south east"}
ETIQ_MON_B = {"JP": "south east", "CN": "north", "BR": "north west", "EG": "south east"}


def fig_monetario_largo(m2, pib, nombres_wb, xa_txt, t0=2000, t1=2024, tope=10.0):
    xa = {c: {int(k): v for k, v in serie.items()} for c, serie in xa_txt.items()}  # años como enteros
    n = t1 - t0
    us_m = math.log(m2["US"][t1] / m2["US"][t0]) / n
    us_y = math.log(pib["US"][t1] / pib["US"][t0]) / n
    def cambios(c):
        return [math.log(xa[c][t + 1] / xa[c][t]) for t in range(t0, t1) if t in xa[c] and t + 1 in xa[c]]
    ce = cambios("XM")
    def corr(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den if den > 0 else 0.0
    filas, fijas = [], []
    for c in sorted(m2):
        if c == "US" or c not in pib or c not in xa:
            continue
        if not all(t in m2[c] and t in pib[c] and t in xa[c] for t in (t0, t1)):
            continue
        d = cambios(c)
        if len(d) != len(ce):
            continue
        sd = 100 * math.sqrt(sum((x - sum(d) / len(d)) ** 2 for x in d) / (len(d) - 1))
        nombre = NOMBRES_MON.get(c, nombres_wb.get(c, c))
        if sd < 1.0 or corr(d, ce) > 0.95:
            fijas.append((c, nombre))
            continue
        dm = 100 * (math.log(m2[c][t1] / m2[c][t0]) / n - us_m)
        dy = 100 * (math.log(pib[c][t1] / pib[c][t0]) / n - us_y)
        ds = 100 * math.log(xa[c][t1] / xa[c][t0]) / n
        filas.append((c, nombre, dm, dy, dm - dy, ds))
    sub = [f for f in filas if abs(f[4]) < tope]
    est = {"todas": ols([f[4] for f in filas], [f[5] for f in filas]), "todas_dinero": ols([f[2] for f in filas], [f[5] for f in filas]),
           "sub": ols([f[4] for f in sub], [f[5] for f in sub])}
    eje = r"""  scale only axis, width=6.1cm, height=5.0cm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize}, title style={font=\footnotesize},
  xlabel={Dinero menos producción, frente a EE.\,UU. (puntos al año)}, clip=false,
"""
    def recta(ab, x0, x1):
        return coordenadas([(x, ab[0] + ab[1] * x) for x in (x0, x1)], 2)
    tikz = "%% Modelo monetario a largo plazo, %d-%d: depreciación media anual frente al dólar y crecimiento medio anual del dinero\n" % (t0, t1)
    tikz += "%% en sentido amplio menos el del PIB real, en diferencia con EE. UU.; %d economías sin tipo fijo (Banco Mundial y BPI).\n" % len(filas)
    tikz += "%% Panel (b): las de diferencia menor de %d puntos. Discontinua: 45 grados; continua: MCO.\n" % tope
    tikz += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_monetario_largo\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[name=pa,\n" + eje
    tikz += "  xmin=-5, xmax=28, ymin=-5, ymax=30, ylabel={Depreciación frente al dólar (puntos al año)},\n  title={(a) Las $%d$ economías},\n]\n" % len(filas)
    tikz += "\\addplot[black!40, dashed] coordinates {(-5,-5) (28,28)};\n"
    tikz += "\\addplot[black, line width=0.6pt] coordinates {%s};\n" % recta(est["todas"], -5, 28)
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(f[4], f[5]) for f in filas], 2)
    for f in filas:
        if f[0] in ETIQ_MON_A:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_MON_A[f[0]], f[4], f[5], f[1])
    tikz += "\\end{axis}\n\\begin{axis}[at={(pa.east)}, anchor=west, xshift=1.3cm,\n" + eje
    tikz += "  xmin=-5, xmax=10.5, ymin=-4, ymax=12,\n  title={(b) Diferencia menor de $%d$ puntos},\n]\n" % tope
    tikz += "\\addplot[black!40, dashed] coordinates {(-4,-4) (10.5,10.5)};\n"
    tikz += "\\addplot[black, line width=0.6pt] coordinates {%s};\n" % recta(est["sub"], -5, 10.5)
    tikz += "\\addplot[only marks, mark=*, mark size=1.2pt, black!60] coordinates {%s};\n" % coordenadas([(f[4], f[5]) for f in sub], 2)
    for f in sub:
        if f[0] in ETIQ_MON_B:
            tikz += "\\node[font=\\scriptsize, anchor=%s, inner sep=1.6pt] at (axis cs:%.2f,%.2f) {%s};\n" % (ETIQ_MON_B[f[0]], f[4], f[5], f[1])
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_monetario_largo.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, sub, est, fijas, (100 * us_m, 100 * us_y)


# ---------------------------------------------------------------- A6 (anexo II): DORNBUSCH (1976)
# Simulación del modelo en tiempo continuo, en desviaciones respecto del equilibrio inicial (p* = 0, renta fija):
#   s' = (p - p_barra)/h (demanda de dinero m - p = k y - h i y paridad no cubierta i = i* + s'),
#   p' = kappa (s - p - q_barra) (los precios suben si el tipo real está por encima de su nivel de equilibrio).
# El aumento del dinero es delta; nu es la velocidad de convergencia de la senda de silla.
def dornbusch_sendas(h=2.0, kappa=0.6, delta=1.0, t1=2.0, tmin=-1.5, tmax=8.0, paso=0.05):
    raiz = math.sqrt(kappa ** 2 + 4 * kappa / h)
    nu = (kappa + raiz) / 2
    r1, r2 = (-kappa + raiz) / 2, -nu
    ts = [tmin + k * paso for k in range(int(round((tmax - tmin) / paso)) + 1)]
    sorpresa, anuncio = [], []
    for t in ts:
        if t < 0:
            sorpresa.append((t, 0.0, 0.0, 0.0, 0.0))
        else:
            e = math.exp(-nu * t)
            sorpresa.append((t, delta, delta + delta / (h * nu) * e, delta - delta * e, -delta / h * e))
    # anunciado en 0 para t1: con el dinero viejo, x = a e^{r1 t} + b e^{r2 t}, z = h (r1 a e^{r1 t} + r2 b e^{r2 t}),
    # z(0) = 0 obliga a b = -r1 a / r2; en t1 el punto tiene que estar en la nueva senda de silla.
    E1, E2 = math.exp(r1 * t1), math.exp(r2 * t1)
    a = delta * (1 + 1 / (h * nu)) / (E1 - (r1 / r2) * E2 + (r1 / nu) * (E1 - E2))
    b = -r1 * a / r2
    x1 = a * E1 + b * E2
    z1 = h * (r1 * a * E1 + r2 * b * E2)
    for t in ts:
        if t < 0:
            anuncio.append((t, 0.0, 0.0, 0.0, 0.0))
        elif t < t1:
            x = a * math.exp(r1 * t) + b * math.exp(r2 * t)
            z = h * (r1 * a * math.exp(r1 * t) + r2 * b * math.exp(r2 * t))
            anuncio.append((t, 0.0, x, z, z / h))
        else:
            e = math.exp(-nu * (t - t1))
            x = delta + (x1 - delta) * e
            z = delta + (z1 - delta) * e
            anuncio.append((t, delta, x, z, (z - delta) / h))
    datos = {"nu": nu, "salto_sorpresa": delta + delta / (h * nu), "salto_anuncio": a + b, "s_t1": x1, "p_t1": z1,
             "i_antes_t1": z1 / h, "i_despues_t1": (z1 - delta) / h, "h": h, "kappa": kappa, "t1": t1}
    return sorpresa, anuncio, datos


def tikz_dornbusch(sendas, nombre, titulos, t1=None, comentario=""):
    # tres paneles: (a) dinero, (b) tipo de cambio y precios, (c) tipo de interés; escalas fijas para comparar las dos figuras
    xs, ys, yi = 0.47, 1.5, 2.6
    def X(t):
        return (t + 1.5) * xs
    tikz = comentario
    tikz += "\\begin{tikzpicture}[font=\\footnotesize, x=1cm, y=1cm]\n"
    for k, (dx, tit) in enumerate(zip((0, 5.2, 10.4), titulos)):
        alto = 3.1
        base = 0.0 if k < 2 else 1.7
        tikz += "\\begin{scope}[xshift=%.2fcm]\n" % dx
        tikz += "  \\draw[-{Stealth[length=1.8mm]}] (0,%.2f) -- (4.6,%.2f) node[below left] {$t$};\n" % (base, base)
        tikz += "  \\draw[-{Stealth[length=1.8mm]}] (0,0) -- (0,%.2f);\n" % alto
        tikz += "  \\draw[black!35, densely dotted] (%.3f,0) -- (%.3f,%.2f);\n" % (X(0), X(0), alto - 0.2)
        tikz += "  \\node[below] at (%.3f,0) {$t_0$};\n" % X(0)
        if t1 is not None:
            tikz += "  \\draw[black!35, densely dotted] (%.3f,0) -- (%.3f,%.2f);\n" % (X(t1), X(t1), alto - 0.2)
            tikz += "  \\node[below] at (%.3f,0) {$t_1$};\n" % X(t1)
        tikz += "  \\node[anchor=south] at (2.3,%.2f) {%s};\n" % (alto + 0.1, tit)
        tikz += "\\end{scope}\n"
    def linea(pts, estilo, dx, fy, y0, etiqueta=None, ancla="west"):
        trozos, actual, previo = [], [], None
        for (t, v) in pts:
            if previo is not None and abs(v - previo) > 0.2:
                actual.append((t, previo))
                trozos.append(actual)
                actual = [(t, previo)]
            actual.append((t, v))
            previo = v
        trozos.append(actual)
        out = ""
        coords = [(X(t) + dx, y0 + fy * v) for tr in trozos for (t, v) in tr]
        out += "\\draw[%s] %s;\n" % (estilo, " -- ".join("(%.3f,%.3f)" % c for c in coords))
        if etiqueta:
            out += "\\node[anchor=%s, inner sep=2pt] at (%.3f,%.3f) {%s};\n" % (ancla, coords[-1][0], coords[-1][1], etiqueta)
        return out
    # (a) dinero
    tikz += linea([(f[0], f[1]) for f in sendas], "black!55, densely dashed, line width=0.9pt", 0.0, ys, 0.5, "$m$")
    # (b) tipo de cambio y precios (estos, desplazados hacia abajo para distinguirlos); punteada: nuevo nivel de s
    tikz += "\\draw[black!40, densely dotted] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (5.2 + X(0), 0.5 + ys, 5.2 + X(8.0), 0.5 + ys)
    tikz += linea([(f[0], f[2]) for f in sendas], "black, line width=1pt", 5.2, ys, 0.5, "$s$", "south west")
    tikz += linea([(f[0], f[3]) for f in sendas], "black!55, densely dashed, line width=0.9pt", 5.2, ys, 0.2, "$p$", "north west")
    # (c) tipo de interés, en diferencia con el extranjero
    tikz += "\\node[left] at (10.4,1.7) {$i^*$};\n"
    tikz += linea([(f[0], f[4]) for f in sendas], "black, line width=1pt", 10.4, yi, 1.7, "$i$")
    tikz += "\\end{tikzpicture}\n"
    open(os.path.join(IMG, nombre + ".tikz"), "w", encoding="utf-8").write(tikz)


def fig_dornbusch():
    sorpresa, anuncio, datos = dornbusch_sendas()
    c = "%% DORNBUSCH (1976), simulación con h = %.1f y kappa = %.1f (Code/libro_y_figuras.py, dornbusch_sendas): aumento\n" % (datos["h"], datos["kappa"])
    tikz_dornbusch(sorpresa, "anx_dornbusch_sorpresa", ("(a) Dinero", "(b) Tipo de cambio y precios", "(c) Tipo de interés"),
                   comentario=c + "% permanente y no anticipado del dinero en t_0. Compilar con: bash Code/generar_figura.sh anx_dornbusch_sorpresa\n")
    tikz_dornbusch(anuncio, "anx_dornbusch_anuncio", ("(a) Dinero", "(b) Tipo de cambio y precios", "(c) Tipo de interés"), t1=datos["t1"],
                   comentario=c + "% del dinero anunciado en t_0 para t_1. Compilar con: bash Code/generar_figura.sh anx_dornbusch_anuncio\n")
    return datos


# Dólar y diferencia de tipos de interés reales, 1975-1998: tipo efectivo real del dólar (BPI, cesta reducida, mensual) y
# tipo oficial real de EE. UU. (tipo oficial menos la inflación interanual) menos la media de los de Alemania, Japón y el
# Reino Unido.
def fig_dolar_tipos_reales(bis, pol, cm, t0="1975-01", t1="1998-12"):
    reer = dict(bis[("US", "R", "N")])
    def anterior(m, k):
        y, mm = int(m[:4]), int(m[5:]) - k
        while mm <= 0:
            y, mm = y - 1, mm + 12
        return "%04d-%02d" % (y, mm)
    def real(a, m):
        if m in pol.get(a, {}) and m in cm.get(a, {}) and anterior(m, 12) in cm[a]:
            return pol[a][m] - 100 * (cm[a][m] / cm[a][anterior(m, 12)] - 1)
        return None
    filas = []
    for m in sorted(x for x in reer if t0 <= x <= t1):
        ru, otros = real("US", m), [real(a, m) for a in ("DE", "JP", "GB")]
        if ru is None or any(r is None for r in otros):
            continue
        filas.append((m, reer[m], ru, sum(otros) / 3, ru - sum(otros) / 3))
    def corr(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    cors = {k: corr([f[1] for f in filas[k:]], [f[4] for f in filas[:len(filas) - k]]) for k in (0, 6, 12, 24)}
    eje = r"""  scale only axis, width=14.2cm, height=3.3cm, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize}, title style={font=\footnotesize},
  xmin=1974.8, xmax=1999.2, xtick={1975,1980,1985,1990,1995}, clip=false,
"""
    tikz = "%% (a) Tipo de cambio efectivo real del dólar (BPI, cesta reducida, mensual, 2020 = 100; subida = apreciación) y (b) tipo\n"
    tikz += "%% oficial real de EE. UU. menos la media de los de Alemania, Japón y el Reino Unido (tipo oficial menos inflación\n"
    tikz += "%% interanual; BPI WS_CBPOL y WS_LONG_CPI), %s a %s. Generado por Code/libro_y_figuras.py;\n" % (t0, t1)
    tikz += "% compilar con: bash Code/generar_figura.sh anx_dolar_tipos_reales\n"
    tikz += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[name=pa,\n" + eje
    tikz += "  ymin=70, ymax=120, ylabel={Índice, $2020=100$}, xticklabels={}, title={(a) Tipo de cambio efectivo real del dólar},\n]\n"
    tikz += "\\addplot[black, line width=1pt] coordinates {%s};\n" % coordenadas([(decimal_mes(f[0]), f[1]) for f in filas], 2)
    tikz += "\\end{axis}\n\\begin{axis}[at={(pa.south)}, anchor=north, yshift=-1.0cm,\n" + eje
    tikz += "  ymin=-6, ymax=9, ytick={-4,0,4,8}, ylabel={Puntos porcentuales}, title={(b) Diferencia de tipos de interés reales a corto plazo},\n]\n"
    tikz += "\\draw[black!50] (axis cs:1974.8,0) -- (axis cs:1999.2,0);\n"
    tikz += "\\addplot[black, line width=0.8pt] coordinates {%s};\n" % coordenadas([(decimal_mes(f[0]), f[4]) for f in filas], 2)
    tikz += "\\end{axis}\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_dolar_tipos_reales.tikz"), "w", encoding="utf-8").write(tikz)
    return filas, cors


# ---------------------------------------------------------------- principal
def main():
    carpeta = sys.argv[1]
    bis = leer_bis(carpeta)
    fred = leer_fred(carpeta, "EXUSEU")
    eu = leer_eurostat(carpeta)
    nombres = paises_bm(carpeta)
    pxwl = leer_icp(carpeta, "gdp_PX.WL.json")
    pcpp = leer_icp(carpeta, "gdp_PCAP.PP.json")
    pib25 = leer_bm(carpeta, "NY.GDP.PCAP.CD_2025.json")
    bm = leer_bigmac(carpeta)

    bil, nom, rea = fig_efectivo_euro(bis, fred)
    enom, eipc, eclu = fig_competitividad_espana(eu)
    penn, (pa, pb, pr2) = fig_penn(pxwl, pcpp, nombres)
    fecha_bm, bmf, (ba, bb, br2), pus = fig_bigmac(bm, pib25)
    xa, xm = leer_xru(carpeta)
    ca, cm = leer_ipc(carpeta)
    eer = leer_eer_estrecho_real(carpeta)
    ppa, (pa1, pb1, pr21), (nsub, pa2, pb2, pr22) = fig_ppa_relativa(xa, ca)
    mmeses, mnom, mrea, mbw, mfl = fig_mussa(xm, cm)
    semis, smed, smedk, snk = fig_semividas(eer)
    pliE, geoE = leer_eurostat_ppp(carpeta, "pli.json")
    aicE, _ = leer_eurostat_ppp(carpeta, "vol_aic.json")
    bsf, (bsb, bsrb, bsdb), (bss, bsrs, bsds) = fig_bienes_servicios(pliE, aicE, geoE)
    ccor = leer_cuenta_corriente(carpeta)
    ccs = fig_cuenta_corriente(ccor)
    pol = leer_cbpol(carpeta)
    ccus = leer_wb_simple(carpeta, "dl_wb_us", "ca_usa.json")
    expw = leer_wb_simple(carpeta, "dl_wb_us", "exp_wld.json")
    dreer, dcc = fig_dolar_cuenta_corriente(bis, ccus)
    parf, pars, pare = fig_paridades_largo(pol, xm, cm)
    m2w, nombres_m2 = leer_wb_panel(carpeta, "dl_wb_m", "m2.json")
    pibw, _ = leer_wb_panel(carpeta, "dl_wb_m", "pib.json")
    monf, mons, mone, monfijas, monus = fig_monetario_largo(m2w, pibw, nombres_m2, xa)
    dorn = fig_dornbusch()
    dtr, dtrc = fig_dolar_tipos_reales(bis, pol, cm)

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
    # ---- A2
    poner("PPA relativa 1970-2025: economías; pendiente y constante (todas)", "%d; %.3f y %.3f" % (len(ppa), pb1, pa1), "BPI WS_XRU, WS_LONG_CPI", "I.3.2")
    poner("PPA relativa 1970-2025: diferencia < 10 puntos: economías, pendiente, correlación", "%d; %.3f; %.3f" % (nsub, pb2, math.sqrt(pr22)), "BPI", "I.3.2")
    for p in ppa:
        if p[0] in ("AR", "TR", "MX", "ES", "CH", "JP", "IN", "KR", "GB", "DE"):
            poner("PPA relativa 1970-2025 %s: inflación menos la de EE. UU. y depreciación (puntos al año)" % p[1], "%.1f y %.1f" % (p[2], p[3]), "BPI", "I.3.2")
    poner("MUSSA, libra-dólar: periodo", "%s a %s" % (mmeses[0], mmeses[-1]), "BPI", "I.3.3")
    poner("MUSSA, Bretton Woods 1950-01 a 1971-07: desv. típica mensual nominal, real (%); correlación", "%.2f, %.2f; %.3f (n=%d)" % mbw, "BPI", "I.3.3")
    poner("MUSSA, flotación 1973-03 en adelante: desv. típica mensual nominal, real (%); correlación", "%.2f, %.2f; %.3f (n=%d)" % mfl, "BPI", "I.3.3")
    poner("Semividas del tipo efectivo real (MCO, mensual): economías y mediana (años)", "%d; %.1f" % (len(semis), smed), "BPI WS_EER", "I.3.4")
    poner("Semividas corregidas (KENDALL): mediana (años) y economías con rho corregido >= 1", "%.1f; %d" % (smedk, snk), "BPI WS_EER", "I.3.4")
    poner("Semividas MCO: economías entre 3 y 5 años, por encima de 5, por debajo de 3", "%d, %d, %d" % (sum(1 for r in semis if 3 <= r[6] <= 5), sum(1 for r in semis if r[6] > 5), sum(1 for r in semis if r[6] < 3)), "BPI WS_EER", "I.3.4")
    for r in semis:
        poner("  semivida %s (años), rho mensual" % r[1], "%.1f; %.4f" % (r[6], r[5]), "BPI WS_EER", "I.3.4")
    # ---- A3
    poner("Bienes y servicios 2024: economías", "%d" % len(bsf), "Eurostat prc_ppp_ind", "I.5.2")
    poner("Bienes: elasticidad al consumo por habitante, R2, desv. típica del log", "%.3f, %.3f, %.3f" % (bsb, bsrb, bsdb), "Eurostat", "I.5.2")
    poner("Servicios: elasticidad al consumo por habitante, R2, desv. típica del log", "%.3f, %.3f, %.3f" % (bss, bsrs, bsds), "Eurostat", "I.5.2")
    poner("Bienes y servicios: rangos de los niveles de precios", "bienes %.1f a %.1f; servicios %.1f a %.1f" % (min(f[3] for f in bsf), max(f[3] for f in bsf), min(f[4] for f in bsf), max(f[4] for f in bsf)), "Eurostat", "I.5.2")
    for f in bsf:
        if f[0] in ("CH", "BG", "ES", "DE", "NO", "TR", "PL", "PT", "IS", "DK", "AL"):
            poner("Bienes y servicios 2024 %s: consumo por habitante, bienes, servicios" % f[1], "%.0f; %.1f; %.1f" % (f[2], f[3], f[4]), "Eurostat", "I.5.2")
    for pais in ("ESP", "DEU"):
        c = ccor.get(pais, {})
        poner("Cuenta corriente (%% del PIB) de %s: 1999, 2004, 2007, 2008, 2012, 2013, 2024, 2025" % pais,
              ", ".join("%s %.1f" % (a, c[a]) for a in ("1999", "2004", "2007", "2008", "2012", "2013", "2024", "2025") if a in c), "Banco Mundial BN.CAB.XOKA.GD.ZS", "I.6.6")
    for pais in ("ESP", "DEU"):
        s = ccs[pais]
        poner("Cuenta corriente de %s: mínimo y máximo 1995-2025 (%% del PIB)" % pais,
              "%.1f en %d; %.1f en %d" % (min((v, a) for a, v in s)[0], min((v, a) for a, v in s)[1], max((v, a) for a, v in s)[0], max((v, a) for a, v in s)[1]), "Banco Mundial", "I.6.6")
    esp = dict(ccs["ESP"])
    poner("España: primer año con superávit corriente tras 1999 y años seguidos con superávit hasta 2025",
          "%s; %d" % (min(a for a, v in esp.items() if a > 1999 and v > 0), sum(1 for a, v in esp.items() if a >= 2013 and v > 0)), "Banco Mundial", "I.6.6")
    # ---- A4
    for a in (1980, 1981, 1985, 1987, 1991, 1995, 2001, 2002, 2006, 2008, 2011, 2014, 2022, 2024, 2025):
        poner("Dólar: tipo efectivo real (media anual, 2020 = 100) y cuenta corriente de EE. UU. (%% del PIB) en %d" % a,
              "%s; %s" % ("%.1f" % dreer[a] if a in dreer else "-", "%.2f" % dcc[a] if a in dcc else "-"), "BPI WS_EER; Banco Mundial", "II.1.2")
    for x0, x1 in ((1980, 1985), (1985, 1987), (1985, 1995), (1995, 2001), (2001, 2011), (2011, 2022), (2022, 2025)):
        poner("Dólar: variación del tipo efectivo real, medias anuales %d-%d (%%)" % (x0, x1), "%.1f" % (100 * (dreer[x1] / dreer[x0] - 1)), "BPI WS_EER", "II.1.2")
    poner("Cuenta corriente de EE. UU. 1980-2025: mínimo y máximo (% del PIB)", "%.2f en %d; %.2f en %d" % (min((v, a) for a, v in dcc.items()) + max((v, a) for a, v in dcc.items())), "Banco Mundial", "II.1.2")
    poner("Exportaciones mundiales de bienes y servicios 2024 y 2025 (billones de dólares)", "%.1f y %.1f" % (expw[2024] / 1e12, expw[2025] / 1e12), "Banco Mundial NE.EXP.GNFS.CD", "II.1.2")
    poner("Exportaciones mundiales 2025 por día hábil (250 días, billones de dólares) y veces que las supera un volumen de 9 billones diarios",
          "%.3f; %.0f" % (expw[2025] / 250 / 1e12, 9e12 / (expw[2025] / 250)), "Banco Mundial; BPI (2025)", "II.1.2")
    msp = meses_entre("2006-01", "2025-06")
    poner("Paridades 2006-01 a 2025-06: economías con datos completos; con diferencia de tipos menor de 10 puntos", "%d; %d" % (len(parf), len(pars)), "BPI WS_CBPOL, WS_XRU, WS_LONG_CPI", "II.2.5")
    poner("  tipo oficial medio de EE. UU. en el periodo (%)", "%.2f" % (sum(pol["US"][m] for m in msp) / len(msp)), "BPI WS_CBPOL", "II.2.5")
    for k, txt in (("uip_todas", "depreciación sobre diferencia de tipos, todas"), ("uip_sub", "depreciación sobre diferencia de tipos, < 10 puntos"),
                   ("fisher_sub", "inflación sobre diferencia de tipos, < 10 puntos"), ("ppa_sub", "depreciación sobre inflación, < 10 puntos")):
        poner("  MCO %s: constante, pendiente, R2" % txt, "%.2f, %.2f, %.2f" % pare[k], "BPI", "II.2.5")
    poner("  depreciación menos diferencia de tipos, media de las < 10 puntos (puntos al año)", "%.2f" % (sum(f[4] - f[2] for f in pars) / len(pars)), "BPI", "II.2.5")
    for f in parf:
        if f[0] in ("AR", "TR", "BR", "RU", "ZA", "IN", "MX", "CN", "CH", "XM", "GB", "CA", "AU", "HK", "SA"):
            poner("  %s: diferencia de tipos, de inflación y depreciación (puntos al año)" % f[1], "%.2f; %s; %.2f" % (f[2], "%.2f" % f[3] if f[3] is not None else "-", f[4]), "BPI", "II.2.5")
    sin = sorted(a for a in pol if a != "US" and a in xm and not all(m in pol[a] and m in pol["US"] for m in msp) and max(pol[a]) >= "2025-06")
    poner("  economías con tipo oficial pero sin la serie completa del periodo (excluidas)", ", ".join(sin), "BPI WS_CBPOL", "II.2.5")
    # ---- A5
    poner("Monetario 2000-2024: economías sin tipo fijo; con diferencia < 10 puntos; con tipo fijo (excluidas)", "%d; %d; %d" % (len(monf), len(mons), len(monfijas)), "Banco Mundial; BPI WS_XRU", "II.3.4")
    poner("  excluidas por tipo fijo", ", ".join("%s %s" % f for f in monfijas), "Banco Mundial; BPI", "II.3.4")
    poner("  EE. UU.: crecimiento medio anual del dinero amplio y del PIB real (%)", "%.2f y %.2f" % monus, "Banco Mundial", "II.3.4")
    for k, txt in (("todas", "depreciación sobre dinero menos producción, todas"), ("todas_dinero", "depreciación sobre dinero, todas"),
                   ("sub", "depreciación sobre dinero menos producción, < 10 puntos")):
        poner("  MCO %s: constante, pendiente, R2" % txt, "%.2f, %.2f, %.2f" % mone[k], "Banco Mundial; BPI", "II.3.4")
    for f in monf:
        if f[0] in ("AR", "TR", "GH", "UA", "NG", "AO", "EG", "BR", "MX", "ZA", "JP", "CN", "GB", "KR", "IN", "CA", "AU", "NO", "SE", "PL", "CL", "CO", "RU"):
            poner("  %s: dinero, producción, dinero menos producción y depreciación (puntos al año)" % f[1], "%.1f; %.1f; %.1f; %.1f" % f[2:], "Banco Mundial; BPI", "II.3.4")
    # ---- A6
    poner("DORNBUSCH simulado (h, kappa, t1): velocidad nu; salto por sorpresa; salto con anuncio; s y p en t1; i - i* antes y después de t1",
          "h %.1f, kappa %.1f, t1 %.1f: nu %.3f; %.3f; %.3f; %.3f y %.3f; %.3f y %.3f" % (dorn["h"], dorn["kappa"], dorn["t1"], dorn["nu"], dorn["salto_sorpresa"],
          dorn["salto_anuncio"], dorn["s_t1"], dorn["p_t1"], dorn["i_antes_t1"], dorn["i_despues_t1"]), "simulación propia", "II.4.2-II.4.3")
    poner("Dólar y diferencia de tipos reales 1975-1998: meses; correlación del tipo real con la diferencia de 0, 6, 12 y 24 meses antes",
          "%d; %.2f, %.2f, %.2f, %.2f" % (len(dtr), dtrc[0], dtrc[6], dtrc[12], dtrc[24]), "BPI WS_EER, WS_CBPOL, WS_LONG_CPI", "II.4.4")
    for a in range(1975, 1999):
        sel = [f for f in dtr if f[0].startswith(str(a))]
        if sel:
            poner("  %d: tipo real del dólar, tipo real de EE. UU., media de Alemania, Japón y Reino Unido, diferencia" % a,
                  "%.1f; %.2f; %.2f; %.2f" % tuple(sum(f[k] for f in sel) / len(sel) for k in (1, 2, 3, 4)), "BPI", "II.4.4")
    mx = max(dtr, key=lambda f: f[1])
    md = max(dtr, key=lambda f: f[4])
    poner("  máximo del tipo real del dólar y máximo de la diferencia", "%.1f en %s; %.2f en %s" % (mx[1], mx[0], md[4], md[0]), "BPI", "II.4.4")

    # ---- libro de datos
    leeme = [["Libro de datos del Tema 3.B.14 (Teorías de la determinación del tipo de cambio)"],
             ["Generado por Code/libro_y_figuras.py el %s. Hojas: Fuentes, Series (formato largo), ICP_2021, Big_Mac, PPA_1970_2025, Semividas, Bienes_servicios_2024, Paridades_2006_2025, Monetario_2000_2024, Cifras_citadas." % FECHA_DESCARGA],
             ["Convención del tema: S son euros por dólar (sube = depreciación del euro). Los índices efectivos siguen la de sus fuentes (sube = apreciación)."]]
    fuentes = [["Serie o fichero", "Organismo", "Dirección de descarga", "Fecha de descarga"]]
    for fichero, url in DESCARGAS.items():
        org = {"dl_bis": "Banco de Pagos Internacionales", "dl_fred": "Banco de la Reserva Federal de San Luis (FRED)",
               "dl_eurostat": "Eurostat", "dl_wb": "Banco Mundial", "dl_icp": "Banco Mundial (ICP 2021)",
               "dl_bigmac": "The Economist", "dl_bis_xru": "Banco de Pagos Internacionales",
               "dl_bis_cpi": "Banco de Pagos Internacionales", "dl_eurostat_ppp": "Eurostat (programa de paridades Eurostat-OCDE)",
               "dl_wb_ca": "Banco Mundial", "dl_bis_pol": "Banco de Pagos Internacionales", "dl_wb_us": "Banco Mundial", "dl_wb_m": "Banco Mundial"}[fichero.split("/")[0]]
        fuentes.append([fichero, org, url, FECHA_DESCARGA])
    filas = [["Serie", "Área", "Fecha", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]
    for f, v in fred:
        filas.append(["EXUSEU", "Zona del euro frente a EE. UU.", f, v, "dólares por euro, media mensual", "FRED", "ninguno", "anx_efectivo_euro (índice 2020 = 100)"])
    for (area, tipo, cesta), serie in sorted(bis.items()):
        if cesta != "B":
            continue
        for f, v in serie:
            filas.append(["BPI efectivo %s, cesta amplia" % ("nominal" if tipo == "N" else "real"), {"XM": "Zona del euro", "ES": "España", "US": "Estados Unidos"}[area],
                          f, v, "índice, 2020 = 100", "BPI WS_EER", "ninguno", "anx_efectivo_euro" if area == "XM" else ""])
    for f, v in bis.get(("US", "R", "N"), []):
        filas.append(["BPI efectivo real, cesta reducida", "Estados Unidos", f, v, "índice, 2020 = 100", "BPI WS_EER", "media anual en la figura", "anx_dolar_cuenta_corriente"])
    for s, serie in sorted(eu.items()):
        for f, v in serie:
            filas.append([s, "España", f, v, "índice, 2020 = 100", "Eurostat ert_eff_ic_q", "ninguno", "anx_competitividad_espana" if s != "REER_IC42_CPI" else ""])
    icp = [["ISO3", "Economía", "Nivel de precios del PIB (mundo = 100, ICP 2021)", "Nivel de precios del PIB (EE. UU. = 100, reescalado)",
            "PIB por habitante en PPA (dólares, ICP 2021)"]]
    for f in penn:
        icp.append([f[0], f[1], f[2], f[4], f[5]])
    big = [["ISO3", "Economía", "Precio local", "Tipo de cambio (moneda local por dólar)", "Precio en dólares", "Valoración bruta frente al dólar", "PIB por habitante 2025 (dólares)"]]
    for f in bmf:
        big.append(list(f))
    for (m, vn), (_, vr) in zip(zip(mmeses, [v for _, v in mnom]), zip(mmeses, [v for _, v in mrea])):
        filas.append(["Libra frente al dólar, nominal", "Reino Unido", m, vn, "índice, 2020 = 100 (libras por dólar)", "BPI WS_XRU", "índice", "anx_mussa"])
        filas.append(["Libra frente al dólar, real (IPC)", "Reino Unido", m, vr, "índice, 2020 = 100", "BPI WS_XRU y WS_LONG_CPI", "s + p_EEUU - p_RU", "anx_mussa"])
    ppah = [["Código BPI", "Economía", "Inflación menos la de EE. UU., media anual 1970-2025 (puntos)", "Depreciación media anual frente al dólar 1970-2025 (puntos)"]]
    for p in ppa:
        ppah.append(list(p))
    semh = [["Código BPI", "Economía", "Desde", "Hasta", "Meses", "Rho mensual (AR(1), MCO)", "Semivida (años)",
             "Rho corregido (KENDALL, 1954)", "Semivida corregida (años; inf = raíz unitaria o explosiva)"]]
    for r in semis:
        semh.append(list(r))
    bsh = [["Código Eurostat", "Economía", "Consumo individual efectivo por habitante en EPA (UE27 = 100), 2024",
            "Nivel de precios de los bienes de consumo (UE27 = 100), 2024", "Nivel de precios de los servicios de consumo (UE27 = 100), 2024"]]
    for f in bsf:
        bsh.append(list(f))
    for pais, serie in sorted(ccor.items()):
        for a, v in sorted(serie.items()):
            filas.append(["Cuenta corriente", pais, a, v, "% del PIB", "Banco Mundial BN.CAB.XOKA.GD.ZS", "ninguno", "anx_cuenta_corriente"])
    for a, v in sorted(ccus.items()):
        filas.append(["Cuenta corriente", "USA", a, v, "% del PIB", "Banco Mundial BN.CAB.XOKA.GD.ZS", "ninguno", "anx_dolar_cuenta_corriente"])
    for a, v in sorted(expw.items()):
        filas.append(["Exportaciones de bienes y servicios", "Mundo", a, v, "dólares corrientes", "Banco Mundial NE.EXP.GNFS.CD", "ninguno", ""])
    for f in parf:
        for m in msp:
            filas.append(["Tipo oficial (fin de mes)", f[1], m, pol[f[0]][m], "% anual", "BPI WS_CBPOL", "ln(1 + i/100) en la media", "anx_paridades_largo"])
    for m in msp:
        filas.append(["Tipo oficial (fin de mes)", "Estados Unidos", m, pol["US"][m], "% anual", "BPI WS_CBPOL", "ln(1 + i/100) en la media", "anx_paridades_largo"])
    for c in [f[0] for f in monf] + ["US"]:
        for a in range(2000, 2025):
            if a in m2w.get(c, {}):
                filas.append(["Dinero en sentido amplio", NOMBRES_MON.get(c, nombres_m2.get(c, c)), a, m2w[c][a], "moneda nacional corriente", "Banco Mundial FM.LBL.BMNY.CN", "logaritmo en la tasa media", "anx_monetario_largo"])
            if a in pibw.get(c, {}):
                filas.append(["PIB real", NOMBRES_MON.get(c, nombres_m2.get(c, c)), a, pibw[c][a], "moneda nacional constante", "Banco Mundial NY.GDP.MKTP.KN", "logaritmo en la tasa media", "anx_monetario_largo"])
    for f in dtr:
        filas.append(["Tipo oficial real de EE. UU. menos la media de Alemania, Japón y Reino Unido", "Estados Unidos", f[0], f[4], "puntos porcentuales",
                      "BPI WS_CBPOL y WS_LONG_CPI", "tipo oficial menos inflación interanual; media simple de los tres", "anx_dolar_tipos_reales"])
    monh = [["Código", "Economía", "Dinero amplio: crecimiento medio anual menos el de EE. UU., 2000-2024 (puntos)", "PIB real: crecimiento medio anual menos el de EE. UU. (puntos)",
             "Dinero menos producción (puntos)", "Depreciación media anual frente al dólar (puntos)", "En el panel (b) (diferencia menor de 10 puntos)"]]
    for f in monf:
        monh.append(list(f) + ["sí" if abs(f[4]) < 10 else "no"])
    for c, nombre in monfijas:
        monh.append([c, nombre, "", "", "", "", "excluida: tipo fijo"])
    parh = [["Código BPI", "Economía", "Tipo oficial menos el de EE. UU., media de ln(1 + i) 2006-01 a 2025-06 (puntos al año)",
             "Inflación menos la de EE. UU., IPC 2006-01 a 2025-06 (puntos al año)", "Depreciación frente al dólar, tipo medio mensual 2006-01 a 2025-06 (puntos al año)",
             "Tipo de cambio 2006-01 (moneda por dólar)", "Tipo de cambio 2025-06 (moneda por dólar)", "En la figura (diferencia menor de 10 puntos)"]]
    for f in parf:
        parh.append([f[0], f[1], f[2], f[3] if f[3] is not None else "", f[4], xm[f[0]]["2006-01"], xm[f[0]]["2025-06"], "sí" if abs(f[2]) < 10 else "no"])
    cifras = [["Cifra", "Valor", "Fuente", "Dónde"]] + cif
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B14.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("ICP_2021", icp), ("Big_Mac", big),
                   ("PPA_1970_2025", ppah), ("Semividas", semh), ("Bienes_servicios_2024", bsh), ("Paridades_2006_2025", parh),
                   ("Monetario_2000_2024", monh), ("Cifras_citadas", cifras)])
    print("Libro escrito:", os.path.join(TEMA, "Code", "datos_3B14.xlsx"))


if __name__ == "__main__":
    main()
