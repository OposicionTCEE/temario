# -*- coding: utf-8 -*-
# Libro de datos del tema 3.B.16 (Code/datos_3B16.xlsx) y figuras calculadas del anexo de evidencia.
# A7 (07/11/2026): II.1 simetría (ciclos, amplitud, perturbaciones a la manera de BAYOUMI y EICHENGREEN, estructuras
# productivas) y II.2 ajuste (réplica de BLANCHARD y KATZ con los estados de EE. UU.; dispersión y persistencia del paro).
# Fuentes: Banco Mundial (Indicadores del Desarrollo Mundial): NY.GDP.MKTP.KN (PIB a precios constantes, moneda nacional),
# NY.GDP.MKTP.CN (PIB a precios corrientes, moneda nacional), NY.GDP.MKTP.KD (PIB a precios constantes, dólares de 2015);
# Eurostat: nama_10_a10 (valor añadido bruto por ramas, millones de euros corrientes), une_rt_a (tasa de paro, 15-74 años);
# FRED (Banco de la Reserva Federal de San Luis, con datos del BLS): {ST}NAN (empleo asalariado no agrario por estado, sin
# desestacionalizar), {ST}UR (tasa de paro por estado), LBSSA{FIPS} (tasa de actividad por estado), UNRATE y CIVPART.
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py [carpeta con las descargas]
#   Sin carpeta, descarga en una carpeta temporal. Después, para cada figura:  bash Code/generar_figura.sh <nombre>

import csv, json, math, os, sys, tempfile, time, urllib.request

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
WB = "https://api.worldbank.org/v2/country/%s/indicator/%s?format=json&per_page=20000&date=1960:2024"
EST = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
FECHA_DESCARGA = "07/11/2026"

# Países: once miembros fundadores de la zona del euro con datos largos (sin Luxemburgo) y tres de la Unión que no la adoptaron.
EURO = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN", "PRT", "IRL", "GRC"]
FUERA = ["GBR", "SWE", "DNK"]
NOMBRE = {"DEU": "Alemania", "FRA": "Francia", "ITA": "Italia", "ESP": "España", "NLD": "Países Bajos", "BEL": "Bélgica",
          "AUT": "Austria", "FIN": "Finlandia", "PRT": "Portugal", "IRL": "Irlanda", "GRC": "Grecia", "GBR": "Reino Unido",
          "SWE": "Suecia", "DNK": "Dinamarca"}
ISO2 = {"DEU": "DE", "FRA": "FR", "ITA": "IT", "ESP": "ES", "NLD": "NL", "BEL": "BE", "AUT": "AT", "FIN": "FI", "PRT": "PT",
        "IRL": "IE", "GRC": "EL", "GBR": "UK", "SWE": "SE", "DNK": "DK"}
WB_SERIES = {"NY.GDP.MKTP.KN": "PIB a precios constantes, moneda nacional",
             "NY.GDP.MKTP.CN": "PIB a precios corrientes, moneda nacional",
             "NY.GDP.MKTP.KD": "PIB a precios constantes, dólares de 2015"}
ESTADOS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
           "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
           "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
           "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
           "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
           "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"}
WB_PARO = "SL.UEM.TOTL.ZS"  # tasa de paro, estimación armonizada de la OIT, desde 1991
EUROSTAT = {"a10.json": "nama_10_a10?unit=CP_MEUR&na_item=B1G&" + "&".join("geo=" + ISO2[p] for p in EURO)}
SECTORES = ["A", "BDE", "C", "F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]
LAMBDA_ANUAL = 6.25  # RAVN y UHLIG (2002)
RETARDOS_BE, RETARDOS_BK, HORIZONTE = 2, 2, 10


# ---------------------------------------------------------------- descargas y lectura
def bajar(url, destino, pausa=0.25):
    if not os.path.exists(destino):
        urllib.request.urlretrieve(url, destino)
        time.sleep(pausa)


def descargar(carpeta):
    for s in list(WB_SERIES) + [WB_PARO]:
        bajar(WB % (";".join(EURO + FUERA), s), os.path.join(carpeta, "wb_" + s + ".json"))
    for st, fips in ESTADOS.items():
        for s in (st + "NAN", st + "UR", "LBSSA" + fips):
            bajar(FRED + s, os.path.join(carpeta, s + ".csv"))
    for s in ("UNRATE", "CIVPART"):
        bajar(FRED + s, os.path.join(carpeta, s + ".csv"))
    for nombre, consulta in EUROSTAT.items():
        bajar(EST + consulta + "&format=JSON&lang=EN", os.path.join(carpeta, nombre))


def leer_wb(carpeta, serie):
    d = json.load(open(os.path.join(carpeta, "wb_" + serie + ".json"), encoding="utf-8"))
    salida = {}
    for x in d[1]:
        if x["value"] is not None:
            salida.setdefault(x["countryiso3code"], {})[int(x["date"])] = float(x["value"])
    return salida


def leer_fred_anual(carpeta, serie, desde, hasta):  # media anual de los meses; solo años completos
    acum = {}
    with open(os.path.join(carpeta, serie + ".csv"), encoding="utf-8") as f:
        lector = csv.reader(f)
        next(lector)
        for fecha, valor in lector:
            if valor not in (".", ""):
                acum.setdefault(int(fecha[:4]), []).append(float(valor))
    return {a: sum(v) / len(v) for a, v in acum.items() if len(v) == 12 and desde <= a <= hasta}


def leer_eurostat_anual(ruta, **sel):
    d = json.load(open(ruta, encoding="utf-8"))
    ids, tam = d["id"], d["size"]
    pos = {k: d["dimension"][k]["category"]["index"] for k in ids}
    salida = {}
    for t, it in pos["time"].items():
        indice = 0
        for k, n in zip(ids, tam):
            i = it if k == "time" else (pos[k][sel[k]] if k in sel else 0)
            indice = indice * n + i
        v = d["value"].get(str(indice))
        if v is not None:
            salida[int(t)] = float(v)
    return salida


# ---------------------------------------------------------------- herramientas
def hp(y, lam=LAMBDA_ANUAL):
    n = len(y)
    d = sparse.diags([np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)], [0, 1, 2], shape=(n - 2, n))
    tendencia = spsolve((sparse.eye(n) + lam * d.T @ d).tocsc(), y)
    return y - tendencia


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def svar_bq(X, p=RETARDOS_BE):
    """VAR(p) con constante y tendencia lineal en (crecimiento, inflación) e identificación de BLANCHARD y QUAH: la segunda
    perturbación (demanda) no afecta a la producción a largo plazo. La tendencia recoge la desinflación de 1970-2019: sin
    ella, la perturbación de oferta sube los precios a largo plazo en 12 de los 14 países y la de demanda baja la producción
    en el impacto en 9, contra lo que predice el modelo de oferta y demanda agregadas. Devuelve las perturbaciones
    estructurales normalizadas (T-p x 2), las respuestas acumuladas [h, variable, perturbación] y la matriz de impacto G."""
    Y = X[p:]
    Z = np.hstack([np.ones((len(Y), 1)), np.arange(len(Y)).reshape(-1, 1) / 10.0] + [X[p - j:len(X) - j] for j in range(1, p + 1)])
    B = np.linalg.lstsq(Z, Y, rcond=None)[0]
    E = Y - Z @ B
    S = E.T @ E / (len(Y) - Z.shape[1])
    Phi = [B[2 + 2 * (j - 1):2 + 2 * j].T for j in range(1, p + 1)]
    C1 = np.linalg.inv(np.eye(2) - sum(Phi))
    G = np.linalg.inv(C1) @ np.linalg.cholesky(C1 @ S @ C1.T)  # efecto a largo plazo triangular inferior con diagonal positiva
    eps = E @ np.linalg.inv(G).T
    Psi = [np.eye(2)]
    for h in range(1, HORIZONTE + 1):
        Psi.append(sum(Phi[j] @ Psi[h - 1 - j] for j in range(min(p, h))))
    R = np.cumsum(np.array([P @ G for P in Psi]), axis=0)  # niveles (logaritmo de la producción y de los precios)
    return eps, R, G


# ---------------------------------------------------------------- II.1 simetría
def simetria(carpeta, series, cifras):
    kn, cn, kd = (leer_wb(carpeta, s) for s in WB_SERIES)
    anios = list(range(1970, 2020))
    for p in EURO + FUERA:
        for a in anios:
            series.append(("PIB real (moneda nacional constante)", NOMBRE[p], a, kn[p][a], "moneda nacional constante", "Banco Mundial NY.GDP.MKTP.KN", "nivel", "anx2_correlaciones; anx2_amplitud; anx2_bayoumi"))
            series.append(("PIB nominal (moneda nacional corriente)", NOMBRE[p], a, cn[p][a], "moneda nacional corriente", "Banco Mundial NY.GDP.MKTP.CN", "nivel; el deflactor es el cociente con el PIB real", "anx2_bayoumi"))
            series.append(("PIB real (dólares de 2015)", NOMBRE[p], a, kd[p][a], "dólares constantes de 2015", "Banco Mundial NY.GDP.MKTP.KD", "nivel; pondera los agregados", "anx2_correlaciones; anx2_amplitud"))
    ciclo = {p: hp(100 * np.log([kn[p][a] for a in anios])) for p in EURO + FUERA}
    total = np.array([sum(kd[p][a] for p in EURO) for a in anios])
    ciclo["EA11"] = hp(100 * np.log(total))
    resto = {p: hp(100 * np.log(total - np.array([kd[p][a] for a in anios]))) for p in EURO}
    i1, i2 = anios.index(1971), anios.index(1998) + 1
    j1, j2 = anios.index(1999), anios.index(2019) + 1
    res = {}
    for p in EURO + FUERA:
        ref = resto[p] if p in EURO else ciclo["EA11"]
        r1 = corr(ciclo[p][i1:i2], ref[i1:i2])
        r2 = corr(ciclo[p][j1:j2], ref[j1:j2])
        amp = float(np.std(ciclo[p][j1:j2]) / np.std(ciclo["EA11"][j1:j2]))
        res[p] = (r1, r2, amp)
        cifras.append(("Correlación del ciclo con el resto de la zona, 1971-1998, " + NOMBRE[p], round(r1, 2), "coeficiente", "II.1.1"))
        cifras.append(("Correlación del ciclo con el resto de la zona, 1999-2019, " + NOMBRE[p], round(r2, 2), "coeficiente", "II.1.1"))
        cifras.append(("Amplitud del ciclo respecto a la zona, 1999-2019, " + NOMBRE[p], round(amp, 2), "cociente de desviaciones típicas", "II.1.2"))
    for nombre, grupo in (("zona del euro", EURO), ("fuera de la zona", FUERA)):
        m1 = float(np.mean([res[p][0] for p in grupo])); m2 = float(np.mean([res[p][1] for p in grupo]))
        cifras.append(("Correlación media, 1971-1998, " + nombre, round(m1, 2), "coeficiente", "II.1.1"))
        cifras.append(("Correlación media, 1999-2019, " + nombre, round(m2, 2), "coeficiente", "II.1.1"))
    # BAYOUMI y EICHENGREEN: VAR(2) en crecimiento e inflación del deflactor, 1971-2019 (estimación 1973-2019).
    be, shocks = {}, {}
    for p in EURO + FUERA:
        y = 100 * np.diff(np.log([kn[p][a] for a in anios]))
        pr = 100 * np.diff(np.log([cn[p][a] / kn[p][a] for a in anios]))
        eps, R, G = svar_bq(np.column_stack([y, pr]))
        shocks[p] = eps  # años 1973-2019
        be[p] = R
    t = list(range(1973, 2020))
    k1, k2, k3 = t.index(1998) + 1, t.index(1999), t.index(2019) + 1
    corr_be = {}
    for p in EURO + FUERA:
        if p == "DEU":
            continue
        o1 = corr(shocks[p][:k1, 0], shocks["DEU"][:k1, 0]); d1 = corr(shocks[p][:k1, 1], shocks["DEU"][:k1, 1])
        o2 = corr(shocks[p][k2:k3, 0], shocks["DEU"][k2:k3, 0]); d2 = corr(shocks[p][k2:k3, 1], shocks["DEU"][k2:k3, 1])
        corr_be[p] = (o1, d1, o2, d2)
        for nom, v, per in (("oferta", o1, "1973-1998"), ("demanda", d1, "1973-1998"), ("oferta", o2, "1999-2019"), ("demanda", d2, "1999-2019")):
            cifras.append(("Correlación con Alemania de las perturbaciones de %s, %s, %s" % (nom, per, NOMBRE[p]), round(v, 2), "coeficiente", "II.1.3"))
    for nombre, grupo in (("zona del euro", [p for p in EURO if p != "DEU"]), ("fuera de la zona", FUERA)):
        for k, nom in ((0, "oferta 1973-1998"), (1, "demanda 1973-1998"), (2, "oferta 1999-2019"), (3, "demanda 1999-2019")):
            cifras.append(("Correlación media con Alemania, %s, %s" % (nom, nombre), round(float(np.mean([corr_be[p][k] for p in grupo])), 2), "coeficiente", "II.1.3"))
    return res, corr_be, be


def estructuras(carpeta, series, cifras):
    ruta = os.path.join(carpeta, "a10.json")
    datos = {}
    for p in EURO:
        g = ISO2[p]
        for n in ["TOTAL", "A", "B-E", "C", "F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]:
            datos[(p, n)] = leer_eurostat_anual(ruta, geo=g, nace_r2=n, unit="CP_MEUR", na_item="B1G", freq="A")
    def cuotas(p, a):
        v = {"A": datos[(p, "A")][a], "BDE": datos[(p, "B-E")][a] - datos[(p, "C")][a], "C": datos[(p, "C")][a]}
        for n in ["F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]:
            v[n] = datos[(p, n)][a]
        return v
    res = {}
    for a in (1995, 2023):
        niveles = {p: cuotas(p, a) for p in EURO}
        for p in EURO:
            for n in SECTORES:
                series.append(("Valor añadido bruto por ramas (NACE " + n + ")", NOMBRE[p], a, niveles[p][n], "millones de euros corrientes", "Eurostat nama_10_a10", "nivel; BDE = B-E menos C", "anx2_krugman"))
        for p in EURO:
            propio = niveles[p]; tot = sum(propio.values())
            otros = {n: sum(niveles[q][n] for q in EURO if q != p) for n in SECTORES}; tot_o = sum(otros.values())
            k = sum(abs(propio[n] / tot - otros[n] / tot_o) for n in SECTORES)
            res.setdefault(p, {})[a] = k
            cifras.append(("Índice de especialización de KRUGMAN frente al resto de la zona, %d, %s" % (a, NOMBRE[p]), round(k, 3), "índice (0 a 2)", "II.1.4"))
    for a in (1995, 2023):
        cifras.append(("Índice de KRUGMAN medio, %d" % a, round(float(np.mean([res[p][a] for p in EURO])), 3), "índice (0 a 2)", "II.1.4"))
    for p in EURO:
        cifras.append(("Peso de la industria manufacturera en el valor añadido, 1995 y 2023, " + NOMBRE[p],
                       "%.1f y %.1f" % tuple(100 * datos[(p, "C")][a] / sum(cuotas(p, a).values()) for a in (1995, 2023)), "porcentaje", "II.1.4"))
    return res


# ---------------------------------------------------------------- II.2 ajuste
def blanchard_katz(carpeta, series, cifras):
    desde, hasta = 1976, 2019
    emp = {st: leer_fred_anual(carpeta, st + "NAN", desde, hasta) for st in ESTADOS}
    par = {st: leer_fred_anual(carpeta, st + "UR", desde, hasta) for st in ESTADOS}
    act = {st: leer_fred_anual(carpeta, "LBSSA" + f, desde, hasta) for st, f in ESTADOS.items()}
    u_us = leer_fred_anual(carpeta, "UNRATE", desde, hasta)
    p_us = leer_fred_anual(carpeta, "CIVPART", desde, hasta)
    anios = list(range(desde, hasta + 1))
    e_us = np.array([sum(emp[st][a] for st in ESTADOS) for a in anios])
    for st in ESTADOS:
        for a in anios:
            series.append(("Empleo asalariado no agrario (media anual)", st, a, emp[st][a], "miles de personas", "FRED " + st + "NAN (BLS)", "media de los doce meses", "anx2_bk"))
            series.append(("Tasa de paro (media anual)", st, a, par[st][a], "porcentaje", "FRED " + st + "UR (BLS)", "media de los doce meses", "anx2_bk; anx2_dispersion"))
            series.append(("Tasa de actividad (media anual)", st, a, act[st][a], "porcentaje", "FRED LBSSA" + ESTADOS[st] + " (BLS)", "media de los doce meses", "anx2_bk"))
    # variables relativas a la nación, en 100 x logaritmos
    Xe, Xl, Xp, ids = [], [], [], []
    for st in ESTADOS:
        e = 100 * (np.log([emp[st][a] for a in anios]) - np.log(e_us))
        le = 100 * (np.log([1 - par[st][a] / 100 for a in anios]) - np.log([1 - u_us[a] / 100 for a in anios]))
        lp = 100 * (np.log([act[st][a] / 100 for a in anios]) - np.log([p_us[a] / 100 for a in anios]))
        Xe.append(np.diff(e)); Xl.append(le[1:]); Xp.append(lp[1:])  # años 1977-2019
    # regresiones agrupadas con efectos fijos por estado (desviaciones respecto a la media de cada estado)
    def apilar(dep, regs):
        Y, Z = [], []
        for i in range(len(ESTADOS)):
            y = dep[i]; cols = [r[i] for r in regs]
            y = y - y.mean(); cols = [c - c.mean() for c in cols]
            Y.append(y); Z.append(np.column_stack(cols))
        return np.concatenate(Y), np.vstack(Z)
    p = RETARDOS_BK
    T = len(Xe[0])  # 43 años, 1977-2019
    def r(serie, k):  # retardo k sobre la muestra t = p..T-1
        return [s[p - k:T - k] for s in serie]
    regs_e = [r(Xe, 1), r(Xe, 2), r(Xl, 1), r(Xl, 2), r(Xp, 1), r(Xp, 2)]
    regs_lp = [r(Xe, 0), r(Xe, 1), r(Xe, 2), r(Xl, 1), r(Xl, 2), r(Xp, 1), r(Xp, 2)]
    ye, Ze = apilar(r(Xe, 0), regs_e)
    yl, Zl = apilar(r(Xl, 0), regs_lp)
    yp, Zp = apilar(r(Xp, 0), regs_lp)
    be = np.linalg.lstsq(Ze, ye, rcond=None)[0]
    bl = np.linalg.lstsq(Zl, yl, rcond=None)[0]
    bp = np.linalg.lstsq(Zp, yp, rcond=None)[0]
    # respuestas a una caída del 1 % del empleo relativo
    H = HORIZONTE
    de, le, lp = np.zeros(H + 1 + p), np.zeros(H + 1 + p), np.zeros(H + 1 + p)
    for h in range(H + 1):
        t = h + p
        de[t] = (-1.0 if h == 0 else 0.0) + be @ [de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
        le[t] = bl @ [de[t], de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
        lp[t] = bp @ [de[t], de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
    de, le, lp = de[p:], le[p:], lp[p:]
    empleo = np.cumsum(de)
    paro = -le          # puntos de la tasa de paro (aproximación de 100 x log(1 - u))
    actividad = lp      # 100 x log de la tasa de actividad
    poblacion = empleo - le - lp  # 100 x log de la población en edad de trabajar: migración
    for h in range(H + 1):
        for nombre, v in (("empleo", empleo[h]), ("tasa de paro", paro[h]), ("tasa de actividad", actividad[h]), ("población en edad de trabajar", poblacion[h])):
            series.append(("Respuesta de " + nombre + " a una caída del 1 % del empleo relativo", "Estados de EE. UU. (agrupados)", h, float(v),
                           "100 x log o puntos", "estimación propia", "VAR agrupado de BLANCHARD y KATZ, 2 retardos, 1979-2019", "anx2_bk"))
    pico = int(np.argmax(paro))
    vida = next((h for h in range(pico, H + 1) if paro[h] <= paro[pico] / 2), None)
    for nombre, v in (("Empleo relativo a largo plazo (10 años)", empleo[H]), ("Tasa de paro en el impacto", paro[0]), ("Tasa de paro máxima", paro[pico]),
                      ("Año del máximo de la tasa de paro", pico), ("Años hasta que el paro cae a la mitad de su máximo", vida),
                      ("Tasa de paro a los 5 años", paro[5]), ("Tasa de actividad en el impacto", actividad[0]), ("Tasa de actividad a los 5 años", actividad[5]),
                      ("Población en edad de trabajar a los 5 años", poblacion[5]), ("Población en edad de trabajar a los 10 años", poblacion[H]),
                      ("Parte del ajuste del empleo hecha por migración a los 10 años", poblacion[H] / empleo[H])):
        cifras.append(("BLANCHARD y KATZ, réplica propia: " + nombre, None if v is None else round(float(v), 3), "puntos o 100 x log", "II.2.1"))
    return empleo, paro, actividad, poblacion


def dispersion(carpeta, series, cifras):
    desde, hasta = 1991, 2024
    wb = leer_wb(carpeta, WB_PARO)
    ue = {p: wb[p] for p in EURO}
    us = {st: leer_fred_anual(carpeta, st + "UR", desde, hasta) for st in ESTADOS}
    anios = list(range(desde, hasta + 1))
    for p in EURO:
        for a in anios:
            series.append(("Tasa de paro (estimación armonizada de la OIT)", NOMBRE[p], a, ue[p][a], "porcentaje de la población activa", "Banco Mundial " + WB_PARO, "nivel", "anx2_dispersion"))
    disp_ea = [float(np.std([ue[p][a] for p in EURO])) for a in anios]
    disp_us = [float(np.std([us[st][a] for st in ESTADOS])) for a in anios]
    for a, x, y in zip(anios, disp_ea, disp_us):
        series.append(("Desviación típica de la tasa de paro entre países", "Zona del euro (11)", a, x, "puntos", "Banco Mundial " + WB_PARO, "desviación típica sin ponderar", "anx2_dispersion"))
        series.append(("Desviación típica de la tasa de paro entre estados", "EE. UU. (51)", a, y, "puntos", "FRED {ST}UR", "desviación típica sin ponderar", "anx2_dispersion"))
    def persistencia(datos, unidades):
        X, Y = [], []
        for u in unidades:
            dev = np.array([datos[u][a] - np.mean([datos[v][a] for v in unidades]) for a in anios])
            x, y = dev[:-1] - dev[:-1].mean(), dev[1:] - dev[1:].mean()
            X.append(x); Y.append(y)
        X, Y = np.concatenate(X), np.concatenate(Y)
        rho = float(X @ Y / (X @ X))
        return rho, math.log(0.5) / math.log(rho)
    r_ea, v_ea = persistencia(ue, EURO)
    r_us, v_us = persistencia(us, list(ESTADOS))
    for nombre, v in (("Desviación típica entre países de la zona, 2007", disp_ea[anios.index(2007)]), ("Desviación típica entre países de la zona, 2013", disp_ea[anios.index(2013)]),
                      ("Desviación típica entre países de la zona, 2024", disp_ea[-1]), ("Desviación típica entre estados de EE. UU., 2007", disp_us[anios.index(2007)]),
                      ("Desviación típica entre estados de EE. UU., 2010", disp_us[anios.index(2010)]), ("Desviación típica entre estados de EE. UU., 2024", disp_us[-1]),
                      ("Persistencia anual del paro relativo, zona del euro", r_ea), ("Vida media del paro relativo, zona del euro (años)", v_ea),
                      ("Persistencia anual del paro relativo, EE. UU.", r_us), ("Vida media del paro relativo, EE. UU. (años)", v_us)):
        cifras.append((nombre + ", 1991-2024", round(v, 2), "puntos, coeficiente o años", "II.2.2"))
    return anios, disp_ea, disp_us


# ---------------------------------------------------------------- figuras (TikZ simple, escala de grises, \footnotesize)
def num(x, dec=1):  # cifra con coma decimal en modo matemático
    s = ("%." + str(dec) + "f") % x
    return "$" + s.replace("-", "-").replace(".", "{,}") + "$"


def escribir(nombre, cuerpo, comentario):
    texto = ("% " + nombre + ": " + comentario + "\n% Generada por Code/libro_y_figuras.py; PDF con: bash Code/generar_figura.sh "
             + nombre + "\n\\begin{tikzpicture}[font=\\footnotesize, >={Stealth[length=2mm]}]\n" + cuerpo + "\\end{tikzpicture}\n")
    with open(os.path.join(IMG, nombre + ".tikz"), "w", encoding="utf-8") as f:
        f.write(texto)


def eje_x(x0, x1, ticks, esc, etiqueta, y=0.0, dec=1, desde=0.0):
    c = "  \\draw[->] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (x0, y, x1, y)
    for t in ticks:
        x = (t - desde) * esc
        c += "  \\draw (%.3f,%.3f) -- (%.3f,%.3f) node[below] {%s};\n" % (x, y + 0.06, x, y - 0.06, num(t, dec) if dec >= 0 else "$%d$" % t)
    c += "  \\node[below=12pt] at (%.3f,%.3f) {%s};\n" % ((x0 + x1) / 2, y, etiqueta)
    return c


def fig_correlaciones(res):
    orden = sorted(EURO, key=lambda p: -res[p][1]) + sorted(FUERA, key=lambda p: -res[p][1])
    esc, dy, c = 9.0, 0.42, ""
    ys = {}
    for i, p in enumerate(orden):
        ys[p] = -(i * dy + (0.35 if p in FUERA else 0.0))
    fondo = min(ys.values()) - 0.45
    for t in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        c += "  \\draw[black!12] (%.3f,0.3) -- (%.3f,%.3f);\n" % (t * esc, t * esc, fondo)
    for p in orden:
        y = ys[p]; a, b = res[p][0] * esc, res[p][1] * esc
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, NOMBRE[p])
        c += "  \\draw[black!45, thick] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (a, y, b, y)
        c += "  \\draw[black!80, fill=white] (%.3f,%.3f) circle (2.1pt);\n" % (a, y)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (2.1pt);\n" % (b, y)
    ye = ys[orden[len(EURO) - 1]]; yf = ys[orden[len(EURO)]]
    c += "  \\draw[black!40, densely dashed] (-2.6,%.3f) -- (%.3f,%.3f);\n" % ((ye + yf) / 2, esc, (ye + yf) / 2)
    c += "  \\node[anchor=west, black!60] at (%.3f,%.3f) {zona del euro};\n" % (esc + 0.1, ys[orden[0]])
    c += "  \\node[anchor=west, black!60] at (%.3f,%.3f) {fuera de la zona};\n" % (esc + 0.1, yf)
    c += eje_x(0, esc + 0.3, [0, 0.2, 0.4, 0.6, 0.8, 1.0], esc, "correlación del ciclo con el resto de la zona del euro", y=fondo)
    c += "  \\draw[black!80, fill=white] (1.2,0.75) circle (2.1pt) node[right=3pt, black] {$1971$-$1998$};\n"
    c += "  \\fill[black!85] (4.2,0.75) circle (2.1pt) node[right=3pt, black] {$1999$-$2019$};\n"
    escribir("anx2_correlaciones", c, "correlación del ciclo (HP, lambda 6,25) de cada país con el resto de la zona del euro, 1971-1998 y 1999-2019 (anexo II.1.1)")


def dispersion_puntos(puntos, desp, esc_x, esc_y, x0, y0):
    c = ""
    for p, (x, y) in puntos.items():
        X, Y = (x - x0) * esc_x, (y - y0) * esc_y
        c += "  \\fill[black!85] (%.3f,%.3f) circle (1.9pt);\n" % (X, Y)
        pos = desp.get(p, "above right")
        c += "  \\node[%s=1pt, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % (pos, X, Y, ISO2[p])
    return c


DESP_BE1 = {"AUT": "above left", "ITA": "above right", "PRT": "below"}
DESP_BE2 = {"BEL": "above left", "SWE": "above", "ESP": "below right", "GBR": "left", "NLD": "above right"}


def fig_amplitud(res):
    x0, x1, y0, y1 = 0.0, 1.0, 0.0, 3.2
    ex, ey = 10.0, 1.9
    c = "  \\draw[black!40, densely dashed] (0,%.3f) -- (%.3f,%.3f);\n" % ((1 - y0) * ey, (x1 - x0) * ex, (1 - y0) * ey)
    c += "  \\node[above right, black!60, font=\\scriptsize] at (0.05,%.3f) {amplitud igual a la de la zona};\n" % ((1 - y0) * ey)
    fuera = {p: (res[p][1], res[p][2]) for p in EURO + FUERA if res[p][1] < 0.85}
    c += dispersion_puntos(fuera, {}, ex, ey, x0, y0)
    # los países con correlación alta forman un grupo apretado: sus etiquetas van en una columna a la derecha, con guías
    grupo = sorted([p for p in EURO + FUERA if res[p][1] >= 0.85], key=lambda p: -res[p][2])
    centro = np.mean([res[p][2] * ey for p in grupo]); paso = 0.36
    for i, p in enumerate(grupo):
        X, Y = res[p][1] * ex, res[p][2] * ey
        yl = centro + paso * (len(grupo) - 1) / 2 - i * paso
        c += "  \\draw[black!35] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (X, Y, 10.45, yl)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (1.9pt);\n" % (X, Y)
        c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % (10.45, yl, ISO2[p])
    c += eje_x(0, (x1 - x0) * ex + 0.3, [0, 0.2, 0.4, 0.6, 0.8, 1.0], ex, "correlación del ciclo con el resto de la zona, $1999$-$2019$")
    c += "  \\draw[->] (0,0) -- (0,%.3f) node[above] {amplitud relativa del ciclo};\n" % ((y1 - y0) * ey + 0.2)
    for t in [0, 1, 2, 3]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % ((t - y0) * ey, (t - y0) * ey, t)
    escribir("anx2_amplitud", c, "correlación del ciclo con el resto de la zona y amplitud relativa (desviación típica del ciclo del país entre la de la zona), 1999-2019 (anexo II.1.2)")


def fig_bayoumi(corr_be):
    x0, x1, y0, y1 = -0.2, 0.9, -0.1, 0.7
    ex, ey = 6.0, 6.0
    c = ""
    for k, (titulo, desp, dx) in enumerate(((r"(a) $1973$-$1998$", DESP_BE1, 0.0), (r"(b) $1999$-$2019$", DESP_BE2, 7.8))):
        c += "  \\begin{scope}[xshift=%.2fcm]\n" % dx
        c += "  \\node[anchor=base] at (%.3f,%.3f) {%s};\n" % ((x1 - x0) * ex / 2, (y1 - y0) * ey + 0.55, titulo)
        c += "  \\draw[black!25] (%.3f,0) -- (%.3f,%.3f);\n" % ((0 - x0) * ex, (0 - x0) * ex, (y1 - y0) * ey)
        c += "  \\draw[black!25] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex, (0 - y0) * ey)
        pts = {p: (v[0], v[1]) if k == 0 else (v[2], v[3]) for p, v in corr_be.items()}
        c += dispersion_puntos(pts, desp, ex, ey, x0, y0)
        c += "  \\draw[->] (0,0) -- (%.3f,0);\n" % ((x1 - x0) * ex + 0.2)
        for t in [-0.2, 0, 0.2, 0.4, 0.6, 0.8]:
            c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {%s};\n" % ((t - x0) * ex, (t - x0) * ex, num(t))
        c += "  \\node[below=12pt] at (%.3f,0) {perturbaciones de oferta};\n" % ((x1 - x0) * ex / 2)
        c += "  \\draw[->] (0,0) -- (0,%.3f);\n" % ((y1 - y0) * ey + 0.2)
        for t in [0, 0.2, 0.4, 0.6]:
            c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - y0) * ey, (t - y0) * ey, num(t))
        c += "  \\node[rotate=90, above=16pt] at (0,%.3f) {perturbaciones de demanda};\n" % ((y1 - y0) * ey / 2)
        c += "  \\end{scope}\n"
    escribir("anx2_bayoumi", c, "correlación con Alemania de las perturbaciones de oferta y de demanda identificadas a la manera de BAYOUMI y EICHENGREEN (1993), 1973-1998 y 1999-2019 (anexo II.1.3)")


def fig_krugman(krug):
    orden = sorted(EURO, key=lambda p: -krug[p][2023])
    esc, dy, c = 13.0, 0.42, ""
    ys = {p: -i * dy for i, p in enumerate(orden)}
    fondo = min(ys.values()) - 0.45
    for t in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        c += "  \\draw[black!12] (%.3f,0.3) -- (%.3f,%.3f);\n" % (t * esc, t * esc, fondo)
    for p in orden:
        y = ys[p]; a, b = krug[p][1995] * esc, krug[p][2023] * esc
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, NOMBRE[p])
        c += "  \\draw[black!45, thick] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (a, y, b, y)
        c += "  \\draw[black!80, fill=white] (%.3f,%.3f) circle (2.1pt);\n" % (a, y)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (2.1pt);\n" % (b, y)
    c += eje_x(0, 0.6 * esc + 0.3, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], esc, "índice de especialización de KRUGMAN frente al resto de la zona", y=fondo)
    c += "  \\draw[black!80, fill=white] (1.2,0.75) circle (2.1pt) node[right=3pt, black] {$1995$};\n"
    c += "  \\fill[black!85] (3.4,0.75) circle (2.1pt) node[right=3pt, black] {$2023$};\n"
    escribir("anx2_krugman", c, "índice de especialización de KRUGMAN (suma de las diferencias absolutas de cuotas de valor añadido en once ramas) de cada país frente al resto de la zona, 1995 y 2023 (anexo II.1.4)")


def linea(xs, ys, ex, ey, x0, y0, estilo):
    return "  \\draw[%s] %s;\n" % (estilo, " -- ".join("(%.3f,%.3f)" % ((x - x0) * ex, (y - y0) * ey) for x, y in zip(xs, ys)))


def fig_bk(bk):
    empleo, paro, actividad, poblacion = bk
    h = list(range(HORIZONTE + 1))
    c = ""
    # (a) niveles: empleo y población en edad de trabajar
    ex, ey, y0 = 0.6, 2.2, -2.2
    c += "  \\node[anchor=base] at (3,%.3f) {(a) Empleo y población};\n" % ((0.2 - y0) * ey + 0.45)
    c += "  \\draw[black!30] (0,%.3f) -- (6.2,%.3f);\n" % ((0 - y0) * ey, (0 - y0) * ey)
    c += linea(h, empleo, ex, ey, 0, y0, "black!85, thick")
    c += linea(h, poblacion, ex, ey, 0, y0, "black!55, thick, dashed")
    c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {empleo};\n" % (10 * ex + 0.1, (empleo[-1] - y0) * ey - 0.12)
    c += "  \\node[anchor=west, font=\\scriptsize, black!70] at (%.3f,%.3f) {población};\n" % (10 * ex + 0.1, (poblacion[-1] - y0) * ey + 0.12)
    c += "  \\draw[->] (0,0) -- (6.3,0);\n  \\draw[->] (0,0) -- (0,%.3f);\n" % ((0.2 - y0) * ey + 0.2)
    for t in [0, 2, 4, 6, 8, 10]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % (t * ex, t * ex, t)
    c += "  \\node[below=12pt] at (3,0) {años};\n"
    for t in [-2, -1.5, -1, -0.5, 0]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - y0) * ey, (t - y0) * ey, num(t))
    c += "  \\node[rotate=90, above=18pt] at (0,%.3f) {desviación, en porcentaje};\n" % ((0.2 - y0) * ey / 2)
    # (b) tasas: paro y actividad
    dx, ey2, yb = 8.6, 8.0, -0.4
    c += "  \\begin{scope}[xshift=%.2fcm]\n" % dx
    c += "  \\node[anchor=base] at (3,%.3f) {(b) Tasas de paro y de actividad};\n" % ((0.4 - yb) * ey2 + 0.45)
    c += "  \\draw[black!30] (0,%.3f) -- (6.2,%.3f);\n" % ((0 - yb) * ey2, (0 - yb) * ey2)
    c += linea(h, paro, ex, ey2, 0, yb, "black!85, thick")
    c += linea(h, actividad, ex, ey2, 0, yb, "black!55, thick, dashed")
    c += "  \\node[anchor=south west, font=\\scriptsize] at (%.3f,%.3f) {tasa de paro};\n" % (1 * ex + 0.05, (paro[1] - yb) * ey2 + 0.02)
    c += "  \\node[anchor=north west, font=\\scriptsize, black!70] at (%.3f,%.3f) {tasa de actividad};\n" % (4 * ex, (actividad[4] - yb) * ey2 - 0.05)
    c += "  \\draw[->] (0,0) -- (6.3,0);\n  \\draw[->] (0,0) -- (0,%.3f);\n" % ((0.4 - yb) * ey2 + 0.2)
    for t in [0, 2, 4, 6, 8, 10]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % (t * ex, t * ex, t)
    c += "  \\node[below=12pt] at (3,0) {años};\n"
    for t in [-0.4, -0.2, 0, 0.2, 0.4]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - yb) * ey2, (t - yb) * ey2, num(t))
    c += "  \\node[rotate=90, above=18pt] at (0,%.3f) {desviación, en puntos};\n" % ((0.4 - yb) * ey2 / 2)
    c += "  \\end{scope}\n"
    escribir("anx2_bk", c, "respuesta de un estado de EE. UU. a una caída del 1 % de su empleo relativo, VAR agrupado de BLANCHARD y KATZ (1992), réplica propia con 51 estados, 1979-2019 (anexo II.2.1)")


def fig_dispersion(disp):
    anios, ea, us = disp
    ex, ey, x0 = 0.33, 0.62, 1991
    c = linea(anios, ea, ex, ey, x0, 0, "black!85, thick")
    c += linea(anios, us, ex, ey, x0, 0, "black!55, thick, dashed")
    i13 = anios.index(2013)
    c += "  \\node[anchor=south, font=\\scriptsize] at (%.3f,%.3f) {zona del euro (once países)};\n" % ((2013 - x0) * ex, ea[i13] * ey + 0.05)
    i10 = anios.index(2010)
    c += "  \\node[anchor=south, font=\\scriptsize, black!70] at (%.3f,%.3f) {EE. UU. ($51$ estados)};\n" % ((2003 - x0) * ex, us[anios.index(2003)] * ey + 0.35)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f) node[above] {desviación típica de la tasa de paro, en puntos};\n" % ((2024 - x0) * ex + 0.4, 8 * ey + 0.3)
    for t in [1991, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in [0, 2, 4, 6, 8]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % (t * ey, t * ey, t)
    escribir("anx2_dispersion", c, "desviación típica sin ponderar de la tasa de paro entre los once países de la zona del euro y entre los 51 estados de EE. UU., 1991-2024 (anexo II.2.2)")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    descargar(carpeta)
    series, cifras = [], []
    res, corr_be, be = simetria(carpeta, series, cifras)
    krug = estructuras(carpeta, series, cifras)
    bk = blanchard_katz(carpeta, series, cifras)
    disp = dispersion(carpeta, series, cifras)
    fig_correlaciones(res)
    fig_amplitud(res)
    fig_bayoumi(corr_be)
    fig_krugman(krug)
    fig_bk(bk)
    fig_dispersion(disp)
    leeme = [["Libro de datos del tema 3.B.16 (Teoría de la integración monetaria)"],
             ["Generado por Code/libro_y_figuras.py el %s con los datos descargados ese día del Banco Mundial, de Eurostat y de FRED." % FECHA_DESCARGA],
             ["Hojas: Fuentes (series y su origen), Series (formato largo: serie, país o estado, año u horizonte, valor, unidad, fuente, tratamiento, figura)"],
             ["y Cifras_citadas (las que da el texto del anexo de evidencia, con su apartado)."],
             ["II.1.1-II.1.2: ciclo = componente cíclico del filtro de HODRICK y PRESCOTT con lambda 6,25 (RAVN y UHLIG, 2002) sobre 100 x log del PIB real, 1970-2019;"],
             ["el agregado de la zona suma el PIB en dólares de 2015 de once países (sin Luxemburgo); para cada miembro, el resto de la zona excluye al propio país."],
             ["II.1.3: VAR(2) por país en crecimiento del PIB real e inflación del deflactor (100 x diferencias logarítmicas), con constante y tendencia lineal, 1973-2019;"],
             ["identificación de BLANCHARD y QUAH: la perturbación de demanda no afecta a la producción a largo plazo; correlaciones con las de Alemania."],
             ["II.1.4: índice de KRUGMAN = suma de las diferencias absolutas entre las cuotas del país y del resto de la zona en once ramas (NACE A, BDE, C, F, G-I, J, K, L, M_N, O-Q, R-U)."],
             ["II.2.1: VAR agrupado con efectos fijos por estado, 2 retardos, 1979-2019, en el crecimiento del empleo relativo, el log de la tasa de empleo relativa y el log"],
             ["de la tasa de actividad relativa (estado menos nación), como BLANCHARD y KATZ (1992); el empleo entra el primero y afecta en el mismo año a las otras dos."],
             ["II.2.2: desviación típica sin ponderar de las tasas de paro; persistencia = coeficiente de un AR(1) agrupado de la desviación respecto a la media"],
             ["sin ponderar de cada año, con efectos fijos, 1991-2024; vida media = log 0,5 / log del coeficiente."]]
    fuentes = [["Código", "Serie", "Ámbito", "Unidad", "Frecuencia", "Institución", "Enlace", "Descarga"]]
    for s, nombre in list(WB_SERIES.items()) + [(WB_PARO, "Tasa de paro, estimación armonizada de la OIT")]:
        fuentes.append([s, nombre, ", ".join(NOMBRE[p] for p in EURO + FUERA), "ver serie", "anual", "Banco Mundial, Indicadores del Desarrollo Mundial",
                        WB % (";".join(EURO + FUERA), s), FECHA_DESCARGA])
    for nombre, consulta in EUROSTAT.items():
        fuentes.append(["Eurostat nama_10_a10", "Valor añadido bruto por ramas", ", ".join(NOMBRE[p] for p in EURO), "millones de euros corrientes", "anual",
                        "Eurostat", EST + consulta, FECHA_DESCARGA])
    for st, fips in ESTADOS.items():
        for s, nombre, unidad in ((st + "NAN", "Empleo asalariado no agrario, sin desestacionalizar", "miles de personas"),
                                  (st + "UR", "Tasa de paro, desestacionalizada", "porcentaje"),
                                  ("LBSSA" + fips, "Tasa de actividad, desestacionalizada", "porcentaje")):
            fuentes.append([s, nombre, st, unidad, "mensual (media anual)", "FRED, Banco de la Reserva Federal de San Luis (BLS)", FRED + s, FECHA_DESCARGA])
    for s, nombre in (("UNRATE", "Tasa de paro de EE. UU."), ("CIVPART", "Tasa de actividad de EE. UU.")):
        fuentes.append([s, nombre, "Estados Unidos", "porcentaje", "mensual (media anual)", "FRED, Banco de la Reserva Federal de San Luis (BLS)", FRED + s, FECHA_DESCARGA])
    filas = [["Serie", "Ámbito", "Año u horizonte", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]] + [list(f) for f in series]
    cif = [["Cifra", "Valor", "Unidad", "Apartado"]] + [list(c) for c in cifras]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B16.xlsx"), [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cifras_citadas", cif)])
    for c in cifras:
        print("%-100s %s %s" % (c[0], c[1], c[2]))


if __name__ == "__main__":
    main()
