# Libro de datos del tema (Code/datos_3B25.xlsx) y figuras del apartado de datos del anexo III (anx_tamano y
# anx_composicion). Fuente: estadísticas de derivados del Banco de Pagos Internacionales (BPI), descarga masiva de
# data.bis.org: derivados extrabursátiles (conjunto WS_OTC_DERIV2, semestral) y negociados en mercados organizados
# (WS_XTD_DERIV, trimestral).
# Uso, desde la carpeta del tema:  python3 Code/libro_y_figuras_A8.py [carpeta con los dos CSV ya descomprimidos]
#   Sin carpeta, descarga los dos ficheros del BPI en una carpeta temporal (unos 4 MB comprimidos y 180 MB sin comprimir).
#   Después:  bash Code/generar_figura.sh anx_tamano  y  bash Code/generar_figura.sh anx_composicion
# Descarga usada en el tema: 02/11/2026 (extrabursátiles hasta el segundo semestre de 2025; organizados, hasta el segundo
# trimestre de 2026). Unidades del BPI: millones de dólares; aquí se pasan a billones (millones de millones).

import collections, csv, glob, os, sys, tempfile, urllib.request, zipfile

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_OTC = "https://data.bis.org/static/bulk/WS_OTC_DERIV2_csv_flat.zip"
URL_XTD = "https://data.bis.org/static/bulk/WS_XTD_DERIV_csv_flat.zip"
FECHA_DESCARGA = "02/11/2026"


def descargar(carpeta):
    for url in (URL_OTC, URL_XTD):
        destino = os.path.join(carpeta, os.path.basename(url))
        urllib.request.urlretrieve(url, destino)
        with zipfile.ZipFile(destino) as z:
            z.extractall(carpeta)


def codigo(fila, columna):
    return fila[columna].split(":")[0].strip()


def leer_otc(ruta):
    """Series semestrales del BPI, todos los países, todas las monedas, plazos y calificaciones, base neta-neta."""
    series = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if codigo(r, "FREQ:Frequency") != "H" or codigo(r, "DER_BASIS:Basis") != "C":
                continue
            if codigo(r, "DER_REP_CTY:Reporting country") != "5J" or codigo(r, "DER_CPC:Counterparty country") != "5J":
                continue
            if codigo(r, "DER_SECTOR_UDL:Underlying risk sector") != "A":
                continue
            if codigo(r, "DER_CURR_LEG1:Currency leg 1") != "TO1" or codigo(r, "DER_CURR_LEG2:Currency leg 2") != "TO1":
                continue
            if codigo(r, "DER_ISSUE_MAT:Maturity") != "A":
                continue
            if codigo(r, "DER_RATING:Rating (outstanding) or settlement (FX turnover)") != "A":
                continue
            medida = codigo(r, "DER_TYPE:Measure")
            if medida not in ("A", "D", "H"):
                continue
            v = r["OBS_VALUE:Observation Value"]
            if v in ("", "NaN"):
                continue
            clave = (medida, codigo(r, "DER_INSTR:Instrument"), codigo(r, "DER_RISK:Risk category"),
                     codigo(r, "DER_SECTOR_CPY:Counterparty sector"))
            series[clave][r["TIME_PERIOD:Time period or range"]] = float(v) / 1e6
    return series


def leer_xtd(ruta):
    """Posición abierta nocional trimestral en todos los mercados organizados, todas las monedas e instrumentos."""
    series = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if codigo(r, "FREQ:Frequency") != "Q" or codigo(r, "OD_TYPE:Measure") != "A":
                continue
            if codigo(r, "XD_EXCHANGE:Location of trade (Exchange or country)") != "8A":
                continue
            if codigo(r, "ISSUE_CUR:Issue currency") != "TO1" or codigo(r, "OD_INSTR:Instrument") != "A":
                continue
            riesgo = codigo(r, "OD_RISK_CAT:Risk category")
            if riesgo not in ("B", "C"):
                continue
            v = r["OBS_VALUE:Observation Status"]  # así se llama la columna del valor en este fichero del BPI
            if v in ("", "NaN"):
                continue
            series[riesgo][r["TIME_PERIOD:Time period or range"]] = float(v) / 1e6
    return series


def fin_de_periodo(p):
    a, s = p.split("-")
    return f"{a}-06-30" if s in ("S1", "Q2") else f"{a}-12-31" if s in ("S2", "Q4") else None


def x_anio(p):
    a, s = p.split("-")
    return int(a) + (0.5 if s in ("S1", "Q2") else 1.0)


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    if len(sys.argv) == 1:
        descargar(carpeta)
    otc = leer_otc(glob.glob(os.path.join(carpeta, "**", "WS_OTC_DERIV2*.csv"), recursive=True)[0])
    xtd = leer_xtd(glob.glob(os.path.join(carpeta, "**", "WS_XTD_DERIV*.csv"), recursive=True)[0])

    MED = {"A": "Nocional vivo", "D": "Valor de mercado bruto", "H": "Exposición crediticia bruta"}
    RIESGO = {"A": "Todas", "D": "Tipos de interés", "B": "Divisas", "E": "Acciones", "J": "Materias primas",
              "T": "Crédito", "U": "Otros"}
    INSTR = {"A": "Todos", "N": "Swaps de tipos de interés", "M": "FRA", "R": "Opciones",
             "D": "Contratos a plazo y FX swaps", "I": "Swaps de divisas", "U": "CDS"}
    SECTOR = {"A": "Todas", "K": "Cámaras de contrapartida central", "U": "Clientes no financieros",
              "B": "Intermediarios declarantes", "C": "Otras instituciones financieras"}
    filas = [["Mercado", "Medida", "Categoría de riesgo", "Instrumento", "Contraparte", "Periodo", "Fecha",
              "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]

    def fila(mercado, medida, riesgo, instr, sector, periodo, valor, unidad, fuente, trat, figura):
        filas.append([mercado, medida, riesgo, instr, sector, periodo, fin_de_periodo(periodo), valor, unidad,
                      fuente, trat, figura])

    ultimo = max(otc[("A", "A", "A", "A")])
    # Totales extrabursátiles, todos los semestres.
    for m in ("A", "D", "H"):
        for p, v in sorted(otc[(m, "A", "A", "A")].items()):
            fila("Extrabursátil", MED[m], "Todas", "Todos", "Todas", p, round(v, 4), "billones de dólares",
                 "BPI-OTC", "T1", "anx_tamano")
    # Organizados: tipos de interés más divisas, trimestres 2 y 4.
    for p in sorted(set(xtd["C"]) & set(xtd["B"])):
        if p.endswith(("Q2", "Q4")) and p >= "1998":
            fila("Organizado", "Posición abierta nocional", "Tipos de interés y divisas", "Futuros y opciones",
                 "Todas", p, round(xtd["C"][p] + xtd["B"][p], 4), "billones de dólares", "BPI-XTD", "T3",
                 "anx_tamano")
    # Composición por categoría de riesgo en el último semestre.
    cats = ["D", "B", "E", "J", "T", "U"]
    for m in ("A", "D"):
        total = otc[(m, "A", "A", "A")][ultimo]
        for c in cats:
            v = otc[(m, "A", c, "A")][ultimo]
            fila("Extrabursátil", MED[m], RIESGO[c], "Todos", "Todas", ultimo, round(v, 4), "billones de dólares",
                 "BPI-OTC", "T1", "anx_composicion")
            fila("Extrabursátil", MED[m] + " (cuota)", RIESGO[c], "Todos", "Todas", ultimo,
                 round(100 * v / total, 2), "% del total", "BPI-OTC", "T4", "anx_composicion")
    # Instrumentos citados en el texto.
    for (ins, rk) in [("N", "D"), ("M", "D"), ("R", "D"), ("D", "B"), ("I", "B"), ("R", "B"), ("U", "T")]:
        v = otc[("A", ins, rk, "A")][ultimo]
        fila("Extrabursátil", MED["A"], RIESGO[rk], INSTR[ins], "Todas", ultimo, round(v, 4),
             "billones de dólares", "BPI-OTC", "T1", "texto")
    # Cuota de las cámaras de contrapartida central.
    cuota = {}
    for rk in ("D", "T"):
        cuota[rk] = {}
        for p, v in sorted(otc[("A", "A", rk, "K")].items()):
            tot = otc[("A", "A", rk, "A")][p]
            cuota[rk][p] = 100 * v / tot
            fila("Extrabursátil", "Nocional frente a cámaras (cuota)", RIESGO[rk], "Todos", SECTOR["K"], p,
                 round(cuota[rk][p], 2), "% del nocional", "BPI-OTC", "T2", "anx_composicion")
    # Clientes no financieros.
    # El BPI no publica el desglose por contraparte del total: se suman las categorías que lo tienen.
    nf_num = sum(otc[("A", "A", c, "U")][ultimo] for c in cats if ultimo in otc.get(("A", "A", c, "U"), {}))
    nf_den = sum(otc[("A", "A", c, "A")][ultimo] for c in cats if ultimo in otc.get(("A", "A", c, "U"), {}))
    nf = 100 * nf_num / nf_den
    fila("Extrabursátil", "Nocional frente a clientes no financieros (cuota)", "Todas", "Todos", SECTOR["U"],
         ultimo, round(nf, 2), "% del nocional", "BPI-OTC", "T2", "texto")

    # Cifras citadas en el texto.
    n = otc[("A", "A", "A", "A")]; g = otc[("D", "A", "A", "A")]; e = otc[("H", "A", "A", "A")]
    pico_n = max(n, key=n.get); pico_g = max(g, key=g.get)
    cifras = [["Cifra", "Valor", "Unidad", "Periodo", "Fuente", "Tratamiento", "Apartado"],
              ["Nocional extrabursátil total", round(n[ultimo], 1), "billones de dólares", ultimo, "BPI-OTC", "T1", "III.1"],
              ["Valor de mercado bruto total", round(g[ultimo], 1), "billones de dólares", ultimo, "BPI-OTC", "T1", "III.1"],
              ["Exposición crediticia bruta total", round(e[ultimo], 2), "billones de dólares", ultimo, "BPI-OTC", "T1", "III.1"],
              ["Valor de mercado bruto / nocional", round(100 * g[ultimo] / n[ultimo], 1), "%", ultimo, "BPI-OTC", "T4", "III.1"],
              ["Exposición crediticia / valor de mercado bruto", round(100 * e[ultimo] / g[ultimo], 1), "%", ultimo, "BPI-OTC", "T4", "III.1"],
              ["Nocional extrabursátil en 1998-S1", round(n["1998-S1"], 1), "billones de dólares", "1998-S1", "BPI-OTC", "T1", "III.1"],
              ["Máximo del nocional", round(n[pico_n], 1), "billones de dólares", pico_n, "BPI-OTC", "T1", "III.1"],
              ["Nocional en 2013-S2", round(n["2013-S2"], 1), "billones de dólares", "2013-S2", "BPI-OTC", "T1", "III.1"],
              ["Nocional en 2016-S2", round(n["2016-S2"], 1), "billones de dólares", "2016-S2", "BPI-OTC", "T1", "III.1"],
              ["Máximo del valor de mercado bruto", round(g[pico_g], 1), "billones de dólares", pico_g, "BPI-OTC", "T1", "III.1"],
              ["Nocional de CDS en 2007-S2", round(otc[("A", "U", "T", "A")]["2007-S2"], 1), "billones de dólares", "2007-S2", "BPI-OTC", "T1", "III.1"],
              ["Cuota de las cámaras en tipos de interés", round(cuota["D"][ultimo], 1), "%", ultimo, "BPI-OTC", "T2", "III.1"],
              ["Cuota de las cámaras en tipos de interés en 2016-S1", round(cuota["D"]["2016-S1"], 1), "%", "2016-S1", "BPI-OTC", "T2", "III.1"],
              ["Cuota de las cámaras en CDS", round(cuota["T"][ultimo], 1), "%", ultimo, "BPI-OTC", "T2", "III.1"],
              ["Cuota de las cámaras en CDS en 2010-S1", round(cuota["T"]["2010-S1"], 1), "%", "2010-S1", "BPI-OTC", "T2", "III.1"],
              ["Cuota de los clientes no financieros en el nocional", round(nf, 1), "%", ultimo, "BPI-OTC", "T2", "III.1"],
              ["FRA a mediados de 2017", round(otc[("A", "M", "D", "A")]["2017-S1"], 1), "billones de dólares", "2017-S1", "BPI-OTC", "T1", "corrección del texto viejo"],
              ["FRA a finales de 2017", round(otc[("A", "M", "D", "A")]["2017-S2"], 1), "billones de dólares", "2017-S2", "BPI-OTC", "T1", "corrección del texto viejo"],
              ["Organizados, tipos de interés y divisas", round(xtd["C"]["2025-Q4"] + xtd["B"]["2025-Q4"], 1), "billones de dólares", "2025-Q4", "BPI-XTD", "T3", "III.1"],
              ["Organizados, divisas", round(xtd["B"]["2025-Q4"], 2), "billones de dólares", "2025-Q4", "BPI-XTD", "T1", "III.1"]]
    for c in cats:
        cifras.append([f"Cuota en el nocional: {RIESGO[c]}", round(100 * otc[("A", "A", c, "A")][ultimo] / n[ultimo], 1), "%", ultimo, "BPI-OTC", "T4", "III.1"])
        cifras.append([f"Cuota en el valor de mercado bruto: {RIESGO[c]}", round(100 * otc[("D", "A", c, "A")][ultimo] / g[ultimo], 1), "%", ultimo, "BPI-OTC", "T4", "III.1"])
    for (ins, rk) in [("N", "D"), ("M", "D"), ("R", "D"), ("D", "B"), ("I", "B"), ("R", "B"), ("U", "T")]:
        cifras.append([f"Nocional: {INSTR[ins]} ({RIESGO[rk]})", round(otc[("A", ins, rk, "A")][ultimo], 1), "billones de dólares", ultimo, "BPI-OTC", "T1", "III.1"])

    leeme = [["Léeme"],
             ["Libro de datos del tema 3.B.25 (derivados). Una fila por dato, en formato largo; filtrar por mercado, medida, categoría, instrumento, contraparte y periodo."],
             ["Hojas: Fuentes (códigos de fuente), Tratamientos (códigos de tratamiento), Indicadores (todas las series usadas en figuras y texto) y Cifras_citadas (las cifras que aparecen en el texto)."],
             [f"Datos descargados del Banco de Pagos Internacionales el {FECHA_DESCARGA}. Script: Code/libro_y_figuras_A8.py, que vuelve a descargar los datos y rehace el libro y las figuras anx_tamano y anx_composicion."],
             ["Periodos: S1 y S2 son el final de junio y de diciembre; Q2 y Q4, el final del segundo y del cuarto trimestre."]]
    fuentes = [["Código", "Fuente", "Dirección", "Descarga"],
               ["BPI-OTC", "Banco de Pagos Internacionales, estadísticas de derivados extrabursátiles (conjunto WS_OTC_DERIV2, semestral), base neta-neta, todos los países declarantes", URL_OTC, FECHA_DESCARGA],
               ["BPI-XTD", "Banco de Pagos Internacionales, estadísticas de derivados negociados en mercados organizados (conjunto WS_XTD_DERIV, trimestral), todos los mercados", URL_XTD, FECHA_DESCARGA]]
    trat = [["Código", "Tratamiento"],
            ["T1", "Valor publicado en millones de dólares, dividido por un millón: billones de dólares (millones de millones). Base neta-neta: ajustado por la doble contabilización de las operaciones entre intermediarios declarantes."],
            ["T2", "Cuota: nocional frente a la contraparte indicada dividido por el nocional total de la misma categoría, en porcentaje."],
            ["T3", "Mercados organizados: suma de los futuros y opciones sobre tipos de interés y sobre divisas (el BPI ya no publica otras categorías); trimestres 2 y 4, para compararlos con los semestres extrabursátiles; billones de dólares."],
            ["T4", "Porcentaje sobre el total extrabursátil de la misma medida."]]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B25.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Tratamientos", trat), ("Indicadores", filas),
                   ("Cifras_citadas", cifras)])

    # ---------- anx_tamano ----------
    X = lambda p: (x_anio(p) - 1998) * 0.2
    def linea(serie, escala):
        return " ".join(f"({X(p):.3f},{v * escala:.3f})" for p, v in sorted(serie.items()))
    org = {p: xtd["C"][p] + xtd["B"][p] for p in xtd["C"] if p.endswith(("Q2", "Q4")) and p >= "1998" and p in xtd["B"]}
    ejes = lambda ymax, paso, esc, etiqueta: (
        f"    \\draw[->] (0,0) -- (5.9,0);\n    \\draw[->] (0,0) -- (0,{ymax * esc + 0.25:.2f}) node[left] {{{etiqueta}}};\n"
        + "".join(f"    \\draw (0,{y * esc:.3f}) -- (-0.06,{y * esc:.3f}) node[left] {{{y}}};\n" for y in range(paso, ymax + 1, paso))
        + "".join(f"    \\draw ({(a - 1998) * 0.2:.2f},0) -- ({(a - 1998) * 0.2:.2f},-0.06) node[below] {{{a}}};\n" for a in (2000, 2010, 2020)))
    tam = (r"""% Figura (Anexo III, «Datos»): (a) nocional vivo de los derivados extrabursátiles (continua) y posición abierta nocional de los
% futuros y opciones sobre tipos de interés y divisas negociados en mercados organizados (discontinua), en billones de dólares
% (millones de millones), 1998-2025. (b) Valor de mercado bruto (continua) y exposición crediticia bruta, tras la compensación
% bilateral (discontinua), de los extrabursátiles. Fuente: BPI, conjuntos WS_OTC_DERIV2 y WS_XTD_DERIV, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B25.xlsx; generada con Code/libro_y_figuras_A8.py.
% Generar con: bash Code/generar_figura.sh anx_tamano
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Nocional ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries] at (2.9,3.75) {(a) Nocional};
""" + ejes(900, 300, 1 / 300, r"$\$\,\text{bn}$") + r"""    \draw[very thick] plot coordinates {""" + linea(otc[("A", "A", "A", "A")], 1 / 300) + r"""};
    \draw[very thick, dashed] plot coordinates {""" + linea(org, 1 / 300) + r"""};
    \node[anchor=south east] at (5.6,2.85) {extrabursátiles};
    \node[anchor=south east] at (5.7,0.42) {organizados};
  \end{scope}
  % ---------------- (b) Valor de mercado y exposición ----------------
  \begin{scope}[xshift=7.6cm]
    \node[font=\footnotesize\bfseries] at (2.9,3.75) {(b) Valor de mercado y exposición};
""" + ejes(36, 12, 1 / 12, r"$\$\,\text{bn}$") + r"""    \draw[very thick] plot coordinates {""" + linea(otc[("D", "A", "A", "A")], 1 / 12) + r"""};
    \draw[very thick, dashed] plot coordinates {""" + linea(otc[("H", "A", "A", "A")], 1 / 12) + r"""};
    \node[anchor=south] at (2.3,2.95) {valor de mercado bruto};
    \node[anchor=south] at (3.6,0.32) {exposición crediticia};
  \end{scope}
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_tamano.tikz"), "w", encoding="utf-8").write(tam)

    # ---------- anx_composicion ----------
    etiquetas = {"D": "Tipos de interés", "B": "Divisas", "E": "Acciones", "J": "Materias primas", "T": "Crédito"}
    barras = ""
    for i, c in enumerate(["D", "B", "E", "J", "T"]):
        y = 2.8 - i * 0.62
        sn = 100 * otc[("A", "A", c, "A")][ultimo] / n[ultimo]
        sg = 100 * otc[("D", "A", c, "A")][ultimo] / g[ultimo]
        barras += (f"    \\fill[black!70] (0,{y:.2f}) rectangle ({sn * 0.042:.3f},{y + 0.22:.2f});\n"
                   f"    \\fill[black!25] (0,{y - 0.24:.2f}) rectangle ({sg * 0.042:.3f},{y - 0.02:.2f});\n"
                   f"    \\node[anchor=east] at (-0.05,{y - 0.01:.2f}) {{{etiquetas[c]}}};\n"
                   f"    \\node[anchor=west, font=\\scriptsize] at ({sn * 0.042:.3f},{y + 0.11:.2f}) {{{sn:.0f}\\,\\%}};\n"
                   f"    \\node[anchor=west, font=\\scriptsize] at ({sg * 0.042:.3f},{y - 0.13:.2f}) {{{sg:.0f}\\,\\%}};\n")
    def cuota_linea(rk):
        return " ".join(f"({X(p):.3f},{v * 0.03:.3f})" for p, v in sorted(cuota[rk].items()))
    comp = (r"""% Figura (Anexo III, «Datos»): (a) peso de cada categoría de riesgo en el nocional (oscuro) y en el valor de mercado bruto
% (claro) de los derivados extrabursátiles, segundo semestre de """ + ultimo[:4] + r""". (b) Proporción del nocional cuya contraparte es una
% cámara de contrapartida central: derivados sobre tipos de interés (continua, desde 2016) y CDS (discontinua, desde 2010).
% Fuente: BPI, conjunto WS_OTC_DERIV2, descarga del """ + FECHA_DESCARGA + r""". Datos y tratamientos en Code/datos_3B25.xlsx; generada con
% Code/libro_y_figuras_A8.py.
% Generar con: bash Code/generar_figura.sh anx_composicion
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Composición ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries] at (1.6,3.55) {(a) Categorías de riesgo};
    \draw (0,0.1) -- (0,3.15);
""" + barras + r"""    \fill[black!70] (0.2,-0.35) rectangle (0.45,-0.2); \node[anchor=west] at (0.5,-0.275) {nocional};
    \fill[black!25] (2.0,-0.35) rectangle (2.25,-0.2); \node[anchor=west] at (2.3,-0.275) {valor de mercado};
  \end{scope}
  % ---------------- (b) Cámaras ----------------
  \begin{scope}[xshift=8.6cm, yshift=-0.2cm]
    \node[font=\footnotesize\bfseries] at (2.9,3.75) {(b) Proporción compensada en cámaras};
    \draw[->] (0,0) -- (5.9,0);
    \draw[->] (0,0) -- (0,3.25) node[left] {$\%$};
""" + "".join(f"    \\draw (0,{y * 0.03:.2f}) -- (-0.06,{y * 0.03:.2f}) node[left] {{{y}}};\n" for y in (25, 50, 75, 100))
        + "".join(f"    \\draw ({(a - 1998) * 0.2:.2f},0) -- ({(a - 1998) * 0.2:.2f},-0.06) node[below] {{{a}}};\n" for a in (2000, 2010, 2020))
        + r"""    \draw[very thick] plot coordinates {""" + cuota_linea("D") + r"""};
    \draw[very thick, dashed] plot coordinates {""" + cuota_linea("T") + r"""};
    \node[anchor=east] at (3.5,2.55) {tipos de interés};
    \node[anchor=north] at (3.4,0.75) {CDS};
  \end{scope}
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_composicion.tikz"), "w", encoding="utf-8").write(comp)
    print("último semestre:", ultimo, "| nocional", round(n[ultimo], 1), "| valor", round(g[ultimo], 1), "| exposición", round(e[ultimo], 2))
    print("cuotas cámaras:", round(cuota["D"][ultimo], 1), round(cuota["T"][ultimo], 1), "| no financieros", round(nf, 1))


if __name__ == "__main__":
    main()
