# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3B11.xlsx) y figuras con datos del anexo III.9 (A9, 13/11/2026):
#   anx_flujos_brutos: España, flujos financieros brutos y saldo de la cuenta financiera, 1999-2025, en % del PIB
#     (Eurostat, bop_c6_a; los pasivos del Banco de España se aproximan por la variación de su posición pasiva de
#     otra inversión, sobre todo TARGET2, de bop_iip6_q);
#   anx_pii_instrumentos: España, PII neta por instrumentos en 2007, 2012 y 2025, en % del PIB (Eurostat, bop_iip6_q);
#   anx_reservas_monedas: reservas mundiales de divisas por monedas y su total, 1999-2026 (FMI, COFER).
# Además, las cifras de España en 2025 que citan el anexo III.2.1 y el Tema 3.A.30 (hoja Cifras_citadas).
# Uso, desde la carpeta del tema:  python3 -I -B Code/libro_y_figuras.py CARPETA
#   CARPETA contiene las subcarpetas eurostat e imf con las descargas (ver DESCARGAS).
#   Después, para cada figura:  bash Code/generar_figura.sh <nombre>
# Convenciones: saldos con signo (superávit o salida neta de capital, positivos); posición negativa = deudora.

import csv, itertools, json, os, sys

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FECHA_DESCARGA = "13/11/2026"
E = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
DESCARGAS = {
    "eurostat/bop_2024_2025.json": E + "bop_c6_a?geo=ES&currency=MIO_EUR&stk_flow=BAL&partner=WRL_REST&sector10=S1&sectpart=S1&time=2024&time=2025&format=JSON&lang=EN (actualización del 2/10/2026)",
    "eurostat/flujos.json": E + "bop_c6_a?geo=ES&currency=MIO_EUR&partner=WRL_REST&bop_item=FA&sector10=S1&sector10=S121&sectpart=S1&stk_flow=ASS&stk_flow=LIAB&stk_flow=NET&format=JSON&lang=EN (2/10/2026)",
    "eurostat/pib.json": E + "nama_10_gdp?geo=ES&na_item=B1GQ&unit=CP_MEUR&format=JSON&lang=EN (11/11/2026)",
    "eurostat/pii.json": E + "bop_iip6_q?geo=ES&freq=A&currency=MIO_EUR&partner=WRL_REST&sector10=S1&sectpart=S1&stk_flow=N_LE&bop_item=FA&bop_item=FA__D__F&bop_item=FA__P__F5&bop_item=FA__P__F3&bop_item=FA__F__F7&bop_item=FA__O__F&bop_item=FA__R__F&format=JSON&lang=EN (29/10/2026)",
    "eurostat/pii_bde.json": E + "bop_iip6_q?geo=ES&freq=A&currency=MIO_EUR&partner=WRL_REST&sector10=S121&bop_item=FA__O__F&format=JSON&lang=EN (29/10/2026)",
    "eurostat/reservas.json": E + "bop_iip6_q?geo=ES&freq=A&currency=MIO_EUR&partner=WRL_REST&stk_flow=A_LE&bop_item=FA__R__F&format=JSON&lang=EN (29/10/2026)",
    "eurostat/pii_2025.json": E + "bop_iip6_q?geo=ES&freq=A&currency=MIO_EUR&partner=WRL_REST&sector10=S1&sectpart=S1&bop_item=FA&bop_item=FA__D__F&bop_item=FA__D__F5&bop_item=FA__D__FL&bop_item=FA__P__F5&bop_item=FA__P__F3&bop_item=FA__F__F7&bop_item=FA__O__F&bop_item=FA__R__F&bop_item=FA__NENDI&time=2025&format=JSON&lang=EN (29/10/2026)",
    "eurostat/sectores.json": E + "nasq_10_nf_tr?geo=ES&unit=CP_MEUR&s_adj=NSA&na_item=B9&sector=S1&sector=S11&sector=S12&sector=S13&sector=S14_S15&sinceTimePeriod=2024-Q1&format=JSON&lang=EN (29/10/2026)",
    "imf/cofer.csv": "https://api.imf.org/external/sdmx/2.1/data/IMF.STA,COFER/all?startPeriod=1999-Q1&dimensionAtObservation=AllDimensions (cabecera Accept: application/vnd.sdmx.data+csv;version=1.0.0; publicación del 30/09/2026)",
}
A0, A1 = 1999, 2025
AÑOS_PII = (2007, 2012, 2025)


def coma(x, d=1):
    return (("%." + str(d) + "f") % x).replace(".", "{,}")


def coordenadas(puntos, d=2):
    return " ".join(("(%s,%." + str(d) + "f)") % (("%g" % a), v) for a, v in puntos)


# ---------------------------------------------------------------- lectura
def leer_estat(carpeta, nombre):
    """Lista de (coordenadas, valor) de un JSON-stat 2.0 de Eurostat."""
    d = json.load(open(os.path.join(carpeta, "eurostat", nombre), encoding="utf-8"))
    ids, cats = d["id"], []
    for k in ids:
        idx = d["dimension"][k]["category"]["index"]
        cats.append(sorted(idx, key=idx.get))
    out = []
    for pos, combo in enumerate(itertools.product(*cats)):
        v = d["value"].get(str(pos))
        if v is not None:
            out.append((dict(zip(ids, combo)), v))
    return out


def filtra(datos, **cond):
    return {c["time"]: v for c, v in datos if all(c.get(k) == val for k, val in cond.items())}


def leer_cofer(carpeta):
    filas = csv.DictReader(open(os.path.join(carpeta, "imf", "cofer.csv"), encoding="utf-8"))
    out = {}
    for r in filas:
        if r["COUNTRY"] != "G001" or r["FREQUENCY"] != "Q" or not r["OBS_VALUE"]:
            continue
        a, q = r["TIME_PERIOD"].split("-Q")
        t = int(a) + (int(q) - 1) / 4.0
        out.setdefault((r["INDICATOR"], r["FXR_CURRENCY"], r["TYPE_OF_TRANSFORMATION"]), {})[t] = float(r["OBS_VALUE"])
    return out


# ---------------------------------------------------------------- figura 1: flujos brutos de España
def fig_flujos(pas_priv, pas_bde, act, neto):
    t = "% España: flujos financieros brutos y saldo de la cuenta financiera, 1999-2025, en porcentaje del PIB (Eurostat).\n"
    t += "% Pasivos del Banco de España = variación de su posición pasiva de otra inversión (sobre todo TARGET2); el resto de\n"
    t += "% las entradas, por diferencia con la emisión neta de pasivos de toda la economía. Anexo III.9.1.\n"
    t += "% Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_flujos_brutos\n"
    todos = [v for s in (pas_priv, pas_bde, act, neto) for _, v in s]
    ymin, ymax = 5 * int(min(todos) // 5), 5 * (int(max(todos) // 5) + 1)
    t += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[\n"
    t += r"""  width=14.6cm, height=7.0cm, scale only axis=false, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  xmin=1998.5, xmax=2025.5, xtick={2000,2005,2010,2015,2020,2025},
"""
    t += "  ymin=%d, ymax=%d, ytick distance=5, ylabel={Porcentaje del PIB},\n" % (ymin, ymax)
    t += r"""  legend style={draw=none, fill=none, font=\footnotesize, legend columns=2, /tikz/every even column/.append style={column sep=0.5cm}},
  legend cell align=left, legend to name=leyendaflujos,
]
"""
    t += "\\fill[black!7] (axis cs:2010.5,%d) rectangle (axis cs:2012.5,%d);\n" % (ymin, ymax)
    t += "\\node[font=\\scriptsize, black!60, anchor=north, align=center, inner sep=1.5pt] at (axis cs:2011.5,%d) {crisis de\\\\ la deuda};\n" % ymax
    t += "\\draw[black!50] (axis cs:1998.5,0) -- (axis cs:2025.5,0);\n"
    t += "\\addplot[ybar, bar width=5pt, fill=black!25, draw=none] coordinates {%s};\n" % coordenadas(neto, 1)
    t += "\\addlegendentry{Saldo de la cuenta financiera ($FA$)}\n"
    t += "\\addplot[black, line width=1.2pt] coordinates {%s};\n" % coordenadas(pas_priv, 1)
    t += "\\addlegendentry{Entradas: pasivos frente a no residentes, sin el Banco de Espa\\~na}\n"
    t += "\\addplot[black, dashed, line width=1.1pt] coordinates {%s};\n" % coordenadas(pas_bde, 1)
    t += "\\addlegendentry{Pasivos del Banco de Espa\\~na (sobre todo TARGET2)}\n"
    t += "\\addplot[black!55, line width=1.1pt] coordinates {%s};\n" % coordenadas(act, 1)
    t += "\\addlegendentry{Salidas: adquisici\\'on neta de activos exteriores ($\\Delta AF$)}\n"
    t += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendaflujos}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_flujos_brutos.tikz"), "w", encoding="utf-8").write(t)


# ---------------------------------------------------------------- figura 2: PII de España por instrumentos
CATEG = [("id", "Inversi\\'on directa"), ("acc", "Cartera: acciones y fondos"), ("deu", "Cartera: deuda"),
         ("bde", "Otra inversi\\'on: Banco de Espa\\~na"), ("res", "Otra inversi\\'on: resto"), ("rd", "Reservas y derivados")]


def fig_pii(comp, total):
    t = "% España: posición de inversión internacional neta por instrumentos en 2007, 2012 y 2025, en porcentaje del PIB\n"
    t += "% (Eurostat, bop_iip6_q). Otra inversión del Banco de España: sobre todo su pasivo frente al Eurosistema (TARGET2).\n"
    t += "% Anexo III.9.2. Generado por Code/libro_y_figuras.py; compilar con: bash Code/generar_figura.sh anx_pii_instrumentos\n"
    vals = [comp[a][k] for a in AÑOS_PII for k, _ in CATEG]
    ymin, ymax = 10 * int(min(vals) // 10), max(10, 10 * (int(max(vals) // 10) + 1))
    t += "\\begin{tikzpicture}\n\\footnotesize\n\\begin{axis}[\n"
    t += r"""  width=14.6cm, height=6.6cm, scale only axis=false, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  ybar=1pt, bar width=9pt, enlarge x limits=0.09,
"""
    t += "  symbolic x coords={%s}, xtick=data,\n" % ",".join(k for k, _ in CATEG)
    t += "  xticklabels={%s},\n" % ",".join("{%s}" % n for _, n in CATEG)
    t += "  x tick label style={align=center, text width=2.2cm, font=\\scriptsize},\n"
    t += "  ymin=%d, ymax=%d, ytick distance=10, ylabel={Porcentaje del PIB},\n" % (ymin, ymax)
    t += r"""  extra y ticks={0}, extra y tick labels={}, extra y tick style={grid=major, major grid style={black!60}},
  legend style={draw=none, fill=none, font=\footnotesize, legend columns=-1, /tikz/every even column/.append style={column sep=0.5cm}},
  legend cell align=left, legend to name=leyendapii, legend image code/.code={\draw[#1] (0cm,-0.1cm) rectangle (0.3cm,0.12cm);},
]
"""
    rellenos = {2007: "black!15", 2012: "black!45", 2025: "black!85"}
    for a in AÑOS_PII:
        pts = " ".join("(%s,%.1f)" % (k, comp[a][k]) for k, _ in CATEG)
        t += "\\addplot[fill=%s, draw=black!70, line width=0.3pt] coordinates {%s};\n" % (rellenos[a], pts)
        t += "\\addlegendentry{%d (PII total: $%s\\%%$)}\n" % (a, coma(total[a]))
    t += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendapii}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_pii_instrumentos.tikz"), "w", encoding="utf-8").write(t)


# ---------------------------------------------------------------- figura 3: reservas mundiales por monedas
MONEDAS = [("CI_USD", "D\\'olar", "black, line width=1.3pt"), ("CI_EUR", "Euro", "black, dashed, line width=1.1pt"),
           ("CI_JPY", "Yen", "black!55, line width=1pt"), ("CI_GBP", "Libra", "black!55, dashed, line width=1pt"),
           ("CI_CNY", "Renminbi", "black, densely dotted, line width=1.2pt"), ("OTRAS", "Otras", "black!40, densely dotted, line width=1.1pt")]


def fig_reservas(cuotas, total, asignadas):
    t = "% Reservas mundiales de divisas: (a) composición por monedas de las reservas asignadas, en %; (b) total y asignadas, en\n"
    t += "% billones de dólares. Trimestral, 1999-2026 (FMI, COFER, publicación del 30/09/2026). Otras: dólar australiano y\n"
    t += "% canadiense, franco suizo y resto. Anexo III.9.3. Generado por Code/libro_y_figuras.py;\n"
    t += "% compilar con: bash Code/generar_figura.sh anx_reservas_monedas\n"
    comun = r"""  scale only axis=false, axis lines=left, tick align=outside, tick style={black!60},
  /pgf/number format/.cd, use comma, 1000 sep={}, /pgfplots/.cd,
  every axis label/.style={font=\footnotesize}, tick label style={font=\footnotesize},
  xmin=1998.75, xmax=2026.75, xtick={2000,2005,2010,2015,2020,2025},
"""
    t += "\\begin{tikzpicture}\n\\footnotesize\n"
    t += "\\begin{axis}[name=cuotas, width=8.6cm, height=6.4cm,\n" + comun
    t += r"""  ymin=0, ymax=80, ytick distance=10, title={\footnotesize\textbf{(a) Composici\'on por monedas (\% de las asignadas)}},
  legend style={draw=none, fill=none, font=\footnotesize, legend columns=3, /tikz/every even column/.append style={column sep=0.4cm}},
  legend cell align=left, legend to name=leyendares,
]
"""
    for k, nombre, estilo in MONEDAS:
        pts = sorted(cuotas[k].items())
        t += "\\addplot[%s] coordinates {%s};\n" % (estilo, coordenadas(pts, 2))
        t += "\\addlegendentry{%s}\n" % nombre
    t += "\\end{axis}\n"
    t += "\\begin{axis}[at={(cuotas.east)}, anchor=west, xshift=1.3cm, width=6.4cm, height=6.4cm,\n" + comun
    ymax = 2 * (int(max(total.values()) / 1e12 // 2) + 1)
    t += "  ymin=0, ymax=%d, ytick distance=2, title={\\footnotesize\\textbf{(b) Reservas de divisas (billones de d\\'olares)}},\n]\n" % ymax
    t += "\\addplot[black, line width=1.3pt] coordinates {%s};\n" % coordenadas([(a, v / 1e12) for a, v in sorted(total.items())], 2)
    t += "\\addplot[black!55, dashed, line width=1.1pt] coordinates {%s};\n" % coordenadas([(a, v / 1e12) for a, v in sorted(asignadas.items())], 2)
    ultimo = max(total)
    t += "\\node[font=\\scriptsize, anchor=east] at (axis cs:2025,%.2f) {total};\n" % (total[ultimo] / 1e12 + 1.2)
    t += "\\node[font=\\scriptsize, black!60, anchor=west] at (axis cs:2006.5,%.2f) {asignadas};\n" % (asignadas[2007.0] / 1e12 - 0.9 if 2007.0 in asignadas else 2)
    t += "\\end{axis}\n\\node[anchor=north] at (current bounding box.south) {\\pgfplotslegendfromname{leyendares}};\n\\end{tikzpicture}\n"
    open(os.path.join(IMG, "anx_reservas_monedas.tikz"), "w", encoding="utf-8").write(t)


# ---------------------------------------------------------------- principal
def main():
    carpeta = sys.argv[1]
    pib = {int(a): v for a, v in filtra(leer_estat(carpeta, "pib.json")).items()}

    # --- Figura 1
    flujos = leer_estat(carpeta, "flujos.json")
    asf = {int(a): v for a, v in filtra(flujos, sector10="S1", stk_flow="ASS").items()}
    lia = {int(a): v for a, v in filtra(flujos, sector10="S1", stk_flow="LIAB").items()}
    net = {int(a): v for a, v in filtra(flujos, sector10="S1", stk_flow="NET").items()}
    bde = leer_estat(carpeta, "pii_bde.json")
    bde_pas = {int(a): v for a, v in filtra(bde, sectpart="S1", stk_flow="L_LE").items()}
    bde_net = {int(a): v for a, v in filtra(bde, sectpart="S1", stk_flow="N_LE").items()}
    años = [a for a in range(A0, A1 + 1) if a in asf and a in lia and a in net and a in pib and a in bde_pas and a - 1 in bde_pas]
    d_bde = {a: bde_pas[a] - bde_pas[a - 1] for a in años}
    pas_priv = [(a, 100 * (lia[a] - d_bde[a]) / pib[a]) for a in años]
    pas_bde = [(a, 100 * d_bde[a] / pib[a]) for a in años]
    act = [(a, 100 * asf[a] / pib[a]) for a in años]
    neto = [(a, 100 * net[a] / pib[a]) for a in años]
    fig_flujos(pas_priv, pas_bde, act, neto)

    # --- Figura 2
    pii = leer_estat(carpeta, "pii.json")
    reservas = {int(a): v for a, v in filtra(leer_estat(carpeta, "reservas.json"), sector10="S121").items()}
    item = lambda it: {int(a): v for a, v in filtra(pii, bop_item=it).items()}
    tot, idir, acc, deu, der, oin = item("FA"), item("FA__D__F"), item("FA__P__F5"), item("FA__P__F3"), item("FA__F__F7"), item("FA__O__F")
    comp, total = {}, {}
    for a in AÑOS_PII:
        p = pib[a] / 100.0
        c = {"id": idir[a] / p, "acc": acc[a] / p, "deu": deu[a] / p, "bde": bde_net[a] / p,
             "res": (oin[a] - bde_net[a]) / p, "rd": (reservas[a] + der.get(a, 0.0)) / p}
        assert abs(sum(c.values()) - tot[a] / p) < 0.2, (a, sum(c.values()), tot[a] / p)
        comp[a], total[a] = c, tot[a] / p
    fig_pii(comp, total)

    # --- Figura 3
    cofer = leer_cofer(carpeta)
    cuotas = {k: cofer[("AFXRA", k, "SHRO_PT")] for k in ("CI_USD", "CI_EUR", "CI_JPY", "CI_GBP", "CI_CNY")}
    otras = {}
    for k in ("CI_AUD", "CI_CAD", "CI_CHF", "CI_OTHC"):
        for tt, v in cofer.get(("AFXRA", k, "SHRO_PT"), {}).items():
            otras[tt] = otras.get(tt, 0.0) + v
    cuotas["OTRAS"] = otras
    total_res = cofer[("TFXRA", "CI_T", "NV_USD")]
    asignadas = cofer[("AFXRA", "CI_T", "NV_USD")]
    fig_reservas(cuotas, total_res, asignadas)

    # --- Cifras de España 2025 (anexo III.2.1 y Tema 3.A.30)
    bp = leer_estat(carpeta, "bop_2024_2025.json")
    b = lambda it, a="2025": filtra(bp, bop_item=it)[a]
    p25 = pib[2025] / 100.0
    sect = leer_estat(carpeta, "sectores.json")
    b9 = {}
    for s in ("S1", "S11", "S12", "S13", "S14_S15"):
        serie = filtra(sect, sector=s, direct="PAID")
        for a in ("2024", "2025"):
            b9[(s, a)] = sum(v for t_, v in serie.items() if t_.startswith(a))
    p2025 = leer_estat(carpeta, "pii_2025.json")
    dfa = lambda it, sf: filtra(p2025, bop_item=it, stk_flow=sf)["2025"]
    k7a = dfa("FA", "A_K7A") - dfa("FA", "L_K7A")
    k7b = dfa("FA", "A_K7B") - dfa("FA", "L_K7B")
    ka = dfa("FA", "A_KA") - dfa("FA", "L_KA")

    # --- Cifras de las figuras
    pp, pb, ac, ne = dict(pas_priv), dict(pas_bde), dict(act), dict(neto)
    boom = max((a for a in años if a <= 2007), key=lambda a: pp[a])
    cof = lambda k, tt: cuotas[k][tt]
    usd_max = max(cuotas["CI_USD"], key=cuotas["CI_USD"].get)
    eur_max = max(cuotas["CI_EUR"], key=cuotas["CI_EUR"].get)
    ult = max(cuotas["CI_USD"])
    cny0 = min(cuotas["CI_CNY"])
    q = lambda tt: "%d-T%d" % (int(tt), int(round((tt - int(tt)) * 4)) + 1)
    cif = [
        ["España 2025: cuenta corriente / bienes / turismo / otros servicios (% del PIB)", "%.2f / %.2f / %.2f / %.2f" % (b("CA") / p25, b("G") / p25, b("SD") / p25, (b("S") - b("SD")) / p25), "Eurostat bop_c6_a y nama_10_gdp", "Anexo III.2.1; Tema 3.A.30"],
        ["España 2025: rentas primarias / secundarias / ambas (% del PIB)", "%.2f / %.2f / %.2f" % (b("IN1") / p25, b("IN2") / p25, (b("IN1") + b("IN2")) / p25), "Eurostat bop_c6_a y nama_10_gdp", "Anexo III.2.1"],
        ["España 2025: rentas de la inversión, total / directa / cartera / otra inversión (millones de euros)", "%.0f / %.0f / %.0f / %.0f (total: %.2f %% del PIB)" % (b("D4P__F"), b("D4P__D__F"), b("D4P__P__F"), b("D4P__O__F"), b("D4P__F") / p25), "Eurostat bop_c6_a", "Anexo III.2.1"],
        ["España 2025: cuenta de capital y capacidad de financiación de la balanza (millones de euros y % del PIB)", "%.0f; %.0f (%.2f %%)" % (b("KA"), b("CA") + b("KA"), (b("CA") + b("KA")) / p25), "Eurostat bop_c6_a", "Tema 3.A.30"],
        ["España: capacidad de financiación de la contabilidad nacional (B9), 2024 / 2025 (millones de euros y % del PIB)", "%.0f (%.2f %%) / %.0f (%.2f %%)" % (b9[("S1", "2024")], 100 * b9[("S1", "2024")] / pib[2024], b9[("S1", "2025")], 100 * b9[("S1", "2025")] / pib[2025]), "Eurostat nasq_10_nf_tr", "Tema 3.A.30"],
        ["España: B9 por sectores 2024 / 2025, hogares e ISFLSH, sociedades no financieras, instituciones financieras, AAPP (millones de euros)", "; ".join("%s: %.0f / %.0f" % (s, b9[(s, "2024")], b9[(s, "2025")]) for s in ("S14_S15", "S11", "S12", "S13")), "Eurostat nasq_10_nf_tr", "Tema 3.A.30"],
        ["España: PII neta 2024 / 2025 (% del PIB) y variación en 2025 (millones de euros)", "%.2f / %.2f; %.0f" % (100 * tot[2024] / pib[2024], 100 * tot[2025] / pib[2025], tot[2025] - tot[2024]), "Eurostat bop_iip6_q y nama_10_gdp", "Tema 3.A.30"],
        ["España 2025: variación de la PII por transacciones / tipo de cambio / otros precios / otros cambios de volumen (millones de euros)", "%.0f / %.0f / %.0f / %.0f" % (net[2025], k7a, k7b, ka), "Eurostat bop_c6_a y bop_iip6_q", "Tema 3.A.30"],
        ["España: entradas sin el Banco de España, máximo hasta 2007 (% del PIB)", "%.1f en %d" % (pp[boom], boom), "Eurostat", "Anexo III.9.1"],
        ["España 2011 / 2012: entradas sin el Banco de España / pasivos del Banco de España / salidas / saldo (% del PIB)", " ; ".join("%d: %.1f / %.1f / %.1f / %.1f" % (a, pp[a], pb[a], ac[a], ne[a]) for a in (2011, 2012)), "Eurostat", "Anexo III.9.1"],
        ["España 2025: entradas sin el Banco de España / pasivos del Banco de España / salidas / saldo (% del PIB)", "%.1f / %.1f / %.1f / %.1f" % (pp[2025], pb[2025], ac[2025], ne[2025]), "Eurostat", "Anexo III.9.1"],
        ["España: PII por instrumentos en 2007 / 2012 / 2025 (% del PIB)", " ; ".join("%d: " % a + ", ".join("%s %.1f" % (k, comp[a][k]) for k, _ in CATEG) + ", total %.1f" % total[a] for a in AÑOS_PII), "Eurostat bop_iip6_q", "Anexo III.9.2"],
        ["Reservas: cuota del dólar, máximo y último dato (%)", "%.1f en %s / %.1f en %s" % (cof("CI_USD", usd_max), q(usd_max), cof("CI_USD", ult), q(ult)), "FMI COFER", "Anexo III.9.3"],
        ["Reservas: cuota del euro, máximo y último dato (%)", "%.1f en %s / %.1f" % (cof("CI_EUR", eur_max), q(eur_max), cof("CI_EUR", ult)), "FMI COFER", "Anexo III.9.3"],
        ["Reservas: renminbi, primer dato y último; yen, libra y otras en el último dato (%)", "%.2f en %s / %.2f; %.1f, %.1f, %.1f" % (cof("CI_CNY", cny0), q(cny0), cof("CI_CNY", ult), cof("CI_JPY", ult), cof("CI_GBP", ult), otras[ult]), "FMI COFER", "Anexo III.9.3"],
        ["Reservas de divisas totales, 1999-T1 / 2008-T4 / 2014-T2 / último (billones de dólares); asignadas / total en 2005-T4 y último (%)", "%.2f / %.2f / %.2f / %.2f; %.0f %% / %.0f %%" % (total_res[1999.0] / 1e12, total_res[2008.75] / 1e12, total_res[2014.25] / 1e12, total_res[ult] / 1e12, 100 * asignadas[2005.75] / total_res[2005.75], 100 * asignadas[ult] / total_res[ult]), "FMI COFER", "Anexo III.9.3"],
    ]
    for c in cif:
        print(" - ", c[0], ":", c[1])

    # --- Libro
    leeme = [["Libro de datos del Tema 3.B.11 (Balanza de pagos: concepto, medición e interpretación)"],
             ["Generado por Code/libro_y_figuras.py el %s a partir de las descargas listadas en la hoja Fuentes." % FECHA_DESCARGA],
             ["Hojas: Fuentes (de dónde sale cada serie), Series (formato largo: indicador, área, periodo, valor, unidad, fuente, tratamiento, figura), Cifras_citadas (lo que citan el anexo III y el Tema 3.A.30)."],
             ["Convenciones: saldos con signo (superávit o salida neta de capital, positivos); posición negativa = deudora; porcentajes del PIB nominal de Eurostat."],
             ["Para rehacer: descargar con las URL de Fuentes en una carpeta (subcarpetas eurostat e imf) y ejecutar python3 -I -B Code/libro_y_figuras.py CARPETA; después bash Code/generar_figura.sh anx_flujos_brutos, anx_pii_instrumentos y anx_reservas_monedas."]]
    fuentes = [["Fichero", "URL y edición", "Fecha de descarga"]] + [[k, v, FECHA_DESCARGA] for k, v in DESCARGAS.items()]
    filas = [["Indicador", "Área", "Periodo", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]
    for nom, serie, trat in (("Pasivos frente a no residentes, sin el Banco de España (entradas)", pas_priv, "emisión neta de pasivos de la economía menos la variación de la posición pasiva de otra inversión del Banco de España"),
                             ("Pasivos del Banco de España (otra inversión, sobre todo TARGET2)", pas_bde, "variación anual de la posición pasiva de otra inversión del Banco de España (bop_iip6_q)"),
                             ("Adquisición neta de activos exteriores (salidas)", act, "ninguno"),
                             ("Saldo de la cuenta financiera", neto, "ninguno")):
        for a, v in serie:
            filas.append([nom, "España", a, v, "% del PIB", "Eurostat bop_c6_a, bop_iip6_q y nama_10_gdp", trat, "anx_flujos_brutos"])
    for a in AÑOS_PII:
        for k, n in CATEG:
            filas.append(["PII neta: " + n.replace("\\'o", "ó").replace("\\~n", "ñ"), "España", a, comp[a][k], "% del PIB", "Eurostat bop_iip6_q y nama_10_gdp", "otra inversión del resto = total menos Banco de España; reservas y derivados sumados", "anx_pii_instrumentos"])
        filas.append(["PII neta total", "España", a, total[a], "% del PIB", "Eurostat bop_iip6_q y nama_10_gdp", "ninguno", "anx_pii_instrumentos"])
    for k, n, _ in MONEDAS:
        for tt, v in sorted(cuotas[k].items()):
            filas.append(["Cuota en las reservas de divisas asignadas: " + n.replace("\\'o", "ó"), "Mundo", q(tt), v, "%", "FMI COFER", "otras = dólar australiano + dólar canadiense + franco suizo + otras" if k == "OTRAS" else "ninguno", "anx_reservas_monedas"])
    for tt, v in sorted(total_res.items()):
        filas.append(["Reservas de divisas, total", "Mundo", q(tt), v / 1e12, "billones de dólares", "FMI COFER", "ninguno", "anx_reservas_monedas"])
    for tt, v in sorted(asignadas.items()):
        filas.append(["Reservas de divisas asignadas por monedas", "Mundo", q(tt), v / 1e12, "billones de dólares", "FMI COFER", "ninguno", "anx_reservas_monedas"])
    for a in sorted(pib):
        filas.append(["PIB a precios corrientes", "España", a, pib[a], "millones de euros", "Eurostat nama_10_gdp", "ninguno", ""])
    cifras = [["Cifra", "Valor", "Fuente", "Dónde"]] + cif
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B11.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cifras_citadas", cifras)])
    print("Libro escrito:", os.path.join(TEMA, "Code", "datos_3B11.xlsx"))


if __name__ == "__main__":
    main()
