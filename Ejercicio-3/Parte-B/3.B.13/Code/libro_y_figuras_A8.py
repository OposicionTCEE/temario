# Libro de datos del tema (Code/datos_3B13.xlsx) y figuras con datos del anexo III, A8 (anx_contrapartes y
# anx_lineas_swap_uso). Fuentes: encuesta trienal del Banco de Pagos Internacionales (BPI), volumen de los derivados
# extrabursátiles y del contado (conjunto WS_DER_OTC_TOV, descarga masiva de data.bis.org), y saldo semanal de las líneas
# swap de la Reserva Federal (serie SWPT de FRED, Banco de la Reserva Federal de San Luis).
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras_A8.py [carpeta con el CSV del BPI y swpt.csv]
#   Sin carpeta, descarga los dos ficheros en una carpeta temporal (unos 14 MB comprimidos y 730 MB sin comprimir).
#   Después:  bash Code/generar_figura.sh anx_contrapartes  y  bash Code/generar_figura.sh anx_lineas_swap_uso
# Descarga usada en el tema: 04/11/2026 (encuesta trienal hasta abril de 2025; SWPT hasta el 28/10/2026). Unidades:
# el BPI publica millones de dólares de media diaria en abril y FRED, millones de dólares al cierre del miércoles; aquí,
# miles de millones de dólares.

import collections, csv, glob, os, sys, tempfile, urllib.request, zipfile

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_TOV = "https://data.bis.org/static/bulk/WS_DER_OTC_TOV_csv_flat.zip"
URL_SWPT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SWPT"
FECHA_DESCARGA = "04/11/2026"
ANIOS = [str(a) for a in range(1989, 2026, 3)]


def descargar(carpeta):
    destino = os.path.join(carpeta, "tov.zip")
    urllib.request.urlretrieve(URL_TOV, destino)
    with zipfile.ZipFile(destino) as z:
        z.extractall(carpeta)
    urllib.request.urlretrieve(URL_SWPT, os.path.join(carpeta, "swpt.csv"))


def codigo(fila, columna):
    return fila[columna].split(":")[0].strip()


def leer_tov(ruta):
    """Volumen mundial de divisas (todos los países declarantes), base neta-neta, años de encuesta, por instrumento y
    contraparte; todas las monedas, plazos, métodos de ejecución y de liquidación."""
    series = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if codigo(r, "DER_REP_CTY:Reporting country") != "5J" or codigo(r, "DER_RISK:Risk category") != "B":
                continue
            if codigo(r, "DER_CPC:Counterparty country") != "5J" or codigo(r, "DER_BASIS:Basis") != "C":
                continue
            if codigo(r, "DER_CURR_LEG1:Currency leg 1") != "TO1" or codigo(r, "DER_CURR_LEG2:Currency leg 2") != "TO1":
                continue
            if codigo(r, "DER_ISSUE_MAT:Maturity") != "A" or codigo(r, "DER_EX_METHOD:Execution method") != "3":
                continue
            if codigo(r, "DER_RATING:Rating (outstanding) or settlement (FX turnover)") != "A":
                continue
            p = r["TIME_PERIOD:Time period or range"]
            v = r["OBS_VALUE:Observation Value"]
            if p not in ANIOS or v in ("", "NaN"):
                continue
            clave = (codigo(r, "DER_INSTR:Instrument"), codigo(r, "DER_SECTOR_CPY:Counterparty sector"))
            series[clave][p] = float(v) / 1e3
    return series


def leer_swpt(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return [(r["observation_date"], float(r["SWPT"]) / 1e3) for r in csv.DictReader(f) if r["SWPT"] not in ("", ".")]


def coma(v, dec=1):
    return f"{v:.{dec}f}".replace(".", "{,}")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    if len(sys.argv) == 1:
        descargar(carpeta)
    tov = leer_tov(glob.glob(os.path.join(carpeta, "**", "WS_DER_OTC_TOV*.csv"), recursive=True)[0])
    swpt = leer_swpt(os.path.join(carpeta, "swpt.csv"))

    INSTR = {"A": "Todos", "B": "Contado", "E": "Plazo simple", "H": "FX swaps", "I": "Swaps de divisas",
             "R": "Opciones y otros"}
    SECTOR = {"A": "Todas", "B": "Intermediarios declarantes", "C": "Otras instituciones financieras",
              "D": "Bancos no declarantes", "E": "Inversores institucionales",
              "F": "Fondos de cobertura y empresas de negociación por cuenta propia", "G": "Sector oficial",
              "P": "Otras instituciones financieras residuales", "H": "Sin distribuir", "U": "Clientes no financieros",
              "V": "Pro memoria: con corretaje principal", "W": "Pro memoria: de origen minorista"}
    filas = [["Conjunto", "Medida", "Instrumento", "Contraparte", "Periodo", "Fecha", "Valor", "Unidad", "Fuente",
              "Tratamiento", "Figura"]]
    tot = tov[("A", "A")]
    for (ins, sec), serie in sorted(tov.items()):
        if ins not in INSTR or sec not in SECTOR or (ins != "A" and sec != "A"):
            continue
        for p, v in sorted(serie.items()):
            fig = "anx_contrapartes" if ins == "A" and sec in ("B", "C", "U", "D", "E", "F", "G", "P", "H") else "texto"
            filas.append(["Volumen de divisas", "Media diaria en abril", INSTR[ins], SECTOR[sec], p, f"{p}-04",
                          round(v, 1), "miles de millones de dólares", "BPI-TOV", "T1", fig])
            filas.append(["Volumen de divisas", "Cuota en el volumen total", INSTR[ins], SECTOR[sec], p, f"{p}-04",
                          round(100 * v / tot[p], 2), "% del total", "BPI-TOV", "T2", fig])
    for d, v in swpt:
        if d >= "2007-01-01":
            filas.append(["Líneas swap de la Reserva Federal", "Saldo vivo del miércoles", "Swaps de liquidez entre bancos centrales",
                          "Bancos centrales extranjeros", d[:7], d, round(v, 3), "miles de millones de dólares", "FRED-SWPT", "T3",
                          "anx_lineas_swap_uso"])

    cuota = lambda sec, p: 100 * tov[("A", sec)][p] / tot[p]
    pico = lambda desde, hasta: max(((d, v) for d, v in swpt if desde <= d <= hasta), key=lambda x: x[1])
    p08, p12, p20 = pico("2008-01-01", "2009-12-31"), pico("2011-01-01", "2012-12-31"), pico("2020-01-01", "2020-12-31")
    otras = lambda p: tov[("A", "P")][p] + tov[("A", "H")][p]
    cifras = [["Cifra", "Valor", "Unidad", "Periodo", "Fuente", "Tratamiento", "Apartado"]]
    for p in ("1998", "2019", "2022", "2025"):
        for sec in ("B", "C", "U"):
            cifras.append([f"Cuota: {SECTOR[sec]}", round(cuota(sec, p), 1), "%", p, "BPI-TOV", "T2", "III.1"])
    for sec in ("D", "E", "F", "G", "V", "W"):
        cifras.append([f"Volumen: {SECTOR[sec]}", round(tov[("A", sec)]["2025"], 0), "miles de millones de dólares", "2025", "BPI-TOV", "T1", "III.1-III.4"])
        cifras.append([f"Cuota: {SECTOR[sec]}", round(cuota(sec, "2025"), 1), "%", "2025", "BPI-TOV", "T2", "III.1-III.4"])
    cifras += [["Volumen total", round(tot["2025"], 0), "miles de millones de dólares", "2025", "BPI-TOV", "T1", "III.1"],
               ["Cuota: otras financieras residuales y sin distribuir", round(100 * otras("2025") / tot["2025"], 1), "%", "2025", "BPI-TOV", "T2", "III.1"],
               ["Volumen: clientes no financieros", round(tov[("A", "U")]["2025"], 0), "miles de millones de dólares", "2025", "BPI-TOV", "T1", "III.3"],
               ["Máximo de las líneas swap, 2008-2009", round(p08[1], 0), "miles de millones de dólares", p08[0], "FRED-SWPT", "T3", "III.4"],
               ["Máximo de las líneas swap, 2011-2012", round(p12[1], 0), "miles de millones de dólares", p12[0], "FRED-SWPT", "T3", "III.4"],
               ["Máximo de las líneas swap, 2020", round(p20[1], 0), "miles de millones de dólares", p20[0], "FRED-SWPT", "T3", "III.4"]]

    leeme = [["Léeme"],
             ["Libro de datos del tema 3.B.13 (mercado de divisas). Una fila por dato, en formato largo; filtrar por conjunto, medida, instrumento, contraparte y periodo."],
             ["Hojas: Fuentes (códigos de fuente), Tratamientos (códigos de tratamiento), Indicadores (todas las series usadas en figuras y texto) y Cifras_citadas (las cifras que aparecen en el texto)."],
             [f"Datos descargados el {FECHA_DESCARGA}. Script: Code/libro_y_figuras_A8.py, que vuelve a descargarlos y rehace el libro y las figuras anx_contrapartes y anx_lineas_swap_uso."],
             ["Encuesta trienal: abril de cada año de encuesta (1989-2025), media diaria. Líneas swap: saldo vivo de cada miércoles."]]
    fuentes = [["Código", "Fuente", "Dirección", "Descarga"],
               ["BPI-TOV", "Banco de Pagos Internacionales, encuesta trienal de bancos centrales, volumen de divisas y derivados extrabursátiles (conjunto WS_DER_OTC_TOV); todos los países declarantes, base neta-neta", URL_TOV, FECHA_DESCARGA],
               ["FRED-SWPT", "Junta de Gobernadores de la Reserva Federal, balance de la Reserva Federal (H.4.1): Assets: Other: Central Bank Liquidity Swaps, Wednesday Level (SWPT), a través de FRED", URL_SWPT, FECHA_DESCARGA]]
    trat = [["Código", "Tratamiento"],
            ["T1", "Valor publicado en millones de dólares de media diaria en abril, dividido por mil: miles de millones de dólares. Base neta-neta: sin la doble contabilización de las operaciones entre intermediarios declarantes del mismo país y de países distintos."],
            ["T2", "Cuota: volumen de la contraparte o del instrumento dividido por el volumen total del mismo año, en porcentaje."],
            ["T3", "Saldo publicado en millones de dólares, dividido por mil: miles de millones de dólares."]]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B13.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Tratamientos", trat), ("Indicadores", filas),
                   ("Cifras_citadas", cifras)])

    # ---------- anx_contrapartes ----------
    anios = [p for p in ANIOS if p >= "1998"]
    X = lambda p: (int(p) - 1998) * 0.22
    Y = lambda v: v * 0.05
    linea = lambda sec: " ".join(f"({X(p):.3f},{Y(cuota(sec, p)):.3f})" for p in anios)
    ejes = ("    \\draw[->] (0,0) -- (6.4,0);\n    \\draw[->] (0,0) -- (0,3.55) node[left] {$\\%$};\n"
            + "".join(f"    \\draw (0,{Y(y):.2f}) -- (-0.06,{Y(y):.2f}) node[left] {{${y}$}};\n" for y in (20, 40, 60))
            + "".join(f"    \\draw ({X(str(a)):.2f},0) -- ({X(str(a)):.2f},-0.06) node[below] {{${a}$}};\n" for a in (1998, 2007, 2016, 2025)))
    barras = ""
    comp = [("B", "intermediarios declarantes"), ("D", "bancos no declarantes"), ("E", "inversores institucionales"),
            ("F", "fondos de cobertura y\\\\negociación por cuenta propia"), ("G", "sector oficial"),
            ("PH", "otras financieras"), ("U", "clientes no financieros")]
    for i, (sec, nombre) in enumerate(comp):
        y = 3.0 - i * 0.46
        v = 100 * otras("2025") / tot["2025"] if sec == "PH" else cuota(sec, "2025")
        tono = "black!70" if sec == "B" else "black!25" if sec == "U" else "black!45"
        barras += (f"    \\fill[{tono}] (0,{y - 0.15:.2f}) rectangle ({v * 0.05:.3f},{y + 0.15:.2f});\n"
                   f"    \\node[anchor=east, align=right, font=\\scriptsize] at (-0.06,{y:.2f}) {{{nombre}}};\n"
                   f"    \\node[anchor=west, font=\\scriptsize] at ({v * 0.05:.3f},{y:.2f}) {{${coma(v)}$}};\n")
    fig = (r"""% Figura (Anexo III, «Participantes»): (a) cuota en el volumen de divisas de las operaciones entre intermediarios
% declarantes, con otras instituciones financieras y con clientes no financieros, en abril de cada año de encuesta,
% 1998-2025. (b) Desglose del volumen de abril de 2025 por contraparte, en porcentaje del total; las otras instituciones
% financieras se dividen en bancos no declarantes, inversores institucionales, fondos de cobertura y empresas de
% negociación por cuenta propia, sector oficial y otras (residuales y sin distribuir).
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras_A8.py.
% Generar con: bash Code/generar_figura.sh anx_contrapartes
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Evolución ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries] at (3.0,4.0) {(a) Cuota en el volumen, 1998-2025};
""" + ejes + r"""    \draw[very thick] plot coordinates {""" + linea("B") + r"""};
    \draw[very thick, dashed] plot coordinates {""" + linea("C") + r"""};
    \draw[very thick, dotted] plot coordinates {""" + linea("U") + r"""};
    \node[anchor=west] at (0.15,3.42) {intermediarios declarantes};
    \node[anchor=west, align=left] at (3.55,3.05) {otras instituciones\\financieras};
    \node[anchor=west] at (3.3,0.62) {clientes no financieros};
  \end{scope}
  % ---------------- (b) Desglose de 2025 ----------------
  \begin{scope}[xshift=10.6cm, yshift=0.1cm]
    \node[font=\footnotesize\bfseries] at (0.3,3.9) {(b) Desglose de 2025 ($\%$ del volumen)};
    \draw (0,0.05) -- (0,3.3);
""" + barras + r"""  \end{scope}
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_contrapartes.tikz"), "w", encoding="utf-8").write(fig)

    # ---------- anx_lineas_swap_uso ----------
    XS = lambda d: (int(d[:4]) + (int(d[5:7]) - 1) / 12 + (int(d[8:10]) - 1) / 365 - 2007) * 0.72
    YS = lambda v: v / 150
    serie = " ".join(f"({XS(d):.3f},{YS(v):.3f})" for d, v in swpt if d >= "2007-01-01")
    mes = {"01": "enero", "02": "febrero", "03": "marzo", "04": "abril", "05": "mayo", "06": "junio", "07": "julio",
           "08": "agosto", "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"}
    rot = lambda d, v: f"{mes[d[5:7]]} de {d[:4]}: ${v:.0f}$"
    ejes_s = ("  \\draw[->] (0,0) -- (14.3,0);\n  \\draw[->] (0,0) -- (0,4.35);\n"
              + "".join(f"  \\draw (0,{YS(y):.2f}) -- (-0.06,{YS(y):.2f}) node[left] {{${y}$}};\n" for y in (200, 400, 600))
              + "".join(f"  \\draw ({XS(f'{a}-01-01'):.2f},0) -- ({XS(f'{a}-01-01'):.2f},-0.06) node[below] {{${a}$}};\n"
                        for a in (2008, 2012, 2016, 2020, 2024)))
    fig2 = (r"""% Figura (Anexo III, «Bancos centrales»): saldo vivo de las líneas swap de la Reserva Federal con otros bancos centrales,
% cada miércoles, en miles de millones de dólares, de 2007 a 2026, con los máximos de 2008, 2012 y 2020.
% Fuente: Junta de Gobernadores de la Reserva Federal (balance H.4.1), serie SWPT de FRED, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras_A8.py.
% Generar con: bash Code/generar_figura.sh anx_lineas_swap_uso
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
""" + ejes_s + r"""  \node[anchor=south west] at (0.05,4.0) {miles de millones de dólares};
  \draw[thick] plot coordinates {""" + serie + r"""};
  \node[anchor=west] at (""" + f"{XS(p08[0]) + 0.15:.2f},{YS(p08[1]) - 0.1:.2f}" + r""") {""" + rot(*p08) + r"""};
  \node[anchor=south] at (""" + f"{XS(p12[0]):.2f},{YS(p12[1]) + 0.08:.2f}" + r""") {""" + rot(*p12) + r"""};
  \node[anchor=west] at (""" + f"{XS(p20[0]) + 0.15:.2f},{YS(p20[1]) - 0.1:.2f}" + r""") {""" + rot(*p20) + r"""};
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_lineas_swap_uso.tikz"), "w", encoding="utf-8").write(fig2)

    for p in ("1998", "2007", "2019", "2022", "2025"):
        print(p, "total", round(tot[p]), "| declarantes", round(cuota("B", p), 1), "| otras", round(cuota("C", p), 1),
              "| no financieros", round(cuota("U", p), 1))
    print("2025:", {SECTOR[s]: round(cuota(s, "2025"), 1) for s in ("D", "E", "F", "G", "V", "W")},
          "otras residuales", round(100 * otras("2025") / tot["2025"], 1))
    print("picos:", p08, p12, p20)


if __name__ == "__main__":
    main()
