"""Monta Code/datos_3B23.xlsx, el libro único con los datos reales del tema (figuras y cifras citadas).

Uso, desde la carpeta del tema:  python3 Code/libro_datos.py
Hay que volver a ejecutarlo después de cambiar o añadir una figura con datos. Al añadir una fuente o un tratamiento,
darlos de alta en FUENTES y TRATAMIENTOS. Las figuras con ejemplos inventados o simulados no tienen datos aquí: sus
parámetros y semillas están en figuras_anexo1.py y figuras_anexo2.py.
"""
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from datos_french import (BETA, BM, CINCO, FACTORES, FACTORES_DIARIOS, IMPULSO, SECTORES, TAMANO_VALOR, URL,  # noqa: E402
                          anual, diaria, seccion)
from datos_fred import CONSUMO, trimestres  # noqa: E402
from datos_fred import URL as URL_FRED  # noqa: E402
from figuras_anexo2 import (DECILES_BETA, DECILES_BM, PERIODO, SECTORES_ES, componentes, contraste_deciles,  # noqa: E402
                            cota_hj, factores_acumulados, tres_factores)
from figuras_anexo3 import razon_varianzas  # noqa: E402
from xlsx_simple import escribir_xlsx  # noqa: E402

LIBRERIA = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
FUENTES = [
    ("Código", "Fuente", "Fichero", "Dirección", "Descarga", "Notas"),
    ("F1", "Kenneth R. French Data Library: Fama/French 3 Factors (mensual)", f"Code/datos/{FACTORES}.csv",
     URL.format(FACTORES), "02/11/2026", "Base de CRSP de 202609. Mkt-RF: rentabilidad en exceso del mercado (todas las"
     " acciones de CRSP de NYSE, AMEX y NASDAQ, ponderadas por valor); RF: letra del Tesoro a un mes (Ibbotson hasta"
     " 202405; ICE BofA desde 202406)."),
    ("F2", "Kenneth R. French Data Library: Portfolios Formed on Market Beta (mensual, ponderadas por valor)",
     f"Code/datos/{BETA}.csv", URL.format(BETA), "02/11/2026", "Carteras formadas a finales de junio; beta estimada"
     " con los 60 meses anteriores (24 como mínimo) por el método de SCHOLES y WILLIAMS. Deciles Lo 10 a Hi 10."),
    ("F3", "Kenneth R. French Data Library: Portfolios Formed on Book-to-Market (mensual, ponderadas por valor)",
     f"Code/datos/{BM}.csv", URL.format(BM), "02/11/2026", "Carteras formadas a finales de junio; valor contable del"
     " último ejercicio del año anterior dividido por el valor de mercado de diciembre. Deciles Lo 10 (crecimiento)"
     " a Hi 10 (valor)."),
    ("F4", "Kenneth R. French Data Library: Fama/French 5 Factors (2x3) (mensual)", f"Code/datos/{CINCO}.csv",
     URL.format(CINCO), "02/11/2026", "Base de CRSP de 202609. Mkt-RF, SMB, HML, RMW (rentabilidad operativa alta"
     " menos baja), CMA (inversión baja menos alta) y RF, desde julio de 1963. Su SMB es la media de los de las tres"
     " clasificaciones (valor, rentabilidad e inversión) y difiere algo del de F1."),
    ("F5", "Kenneth R. French Data Library: Momentum Factor (Mom) (mensual)", f"Code/datos/{IMPULSO}.csv",
     URL.format(IMPULSO), "02/11/2026", "Media de las dos carteras (grandes y pequeñas) de rentabilidad pasada alta"
     " menos la de las dos de rentabilidad pasada baja; rentabilidad pasada de los meses -12 a -2, percentiles 30 y 70"
     " de NYSE; carteras mensuales ponderadas por valor."),
    ("F6", "Kenneth R. French Data Library: 25 Portfolios Formed on Size and Book-to-Market (5 x 5) (mensual,"
     " ponderadas por valor)", f"Code/datos/{TAMANO_VALOR}.csv", URL.format(TAMANO_VALOR), "02/11/2026",
     "Carteras formadas a finales de junio por quintiles de capitalización (NYSE) y de valor contable sobre valor de"
     " mercado (NYSE). Columnas SMALL LoBM (pequeñas de crecimiento) a BIG HiBM (grandes de valor)."),
    ("F7", "Kenneth R. French Data Library: 30 Industry Portfolios (mensual, ponderadas por valor)",
     f"Code/datos/{SECTORES}.csv", URL.format(SECTORES), "02/11/2026", "Carteras sectoriales formadas a finales de"
     " junio por el código SIC de CRSP; sección Average Value Weighted Returns -- Monthly."),
    ("F8", "FRED (Banco de la Reserva Federal de San Luis), serie A794RX0Q048SBEA del Bureau of Economic Analysis:"
     " gasto real en consumo personal por habitante de Estados Unidos", f"Code/datos/FRED_{CONSUMO}.csv",
     URL_FRED.format(CONSUMO), "02/11/2026", "Trimestral, dólares encadenados de 2017, desestacionalizado, en tasa"
     " anual. Incluye los bienes duraderos."),
    ("F9", "Kenneth R. French Data Library: Fama/French 3 Factors [Daily]", f"Code/datos/{FACTORES_DIARIOS}.csv",
     URL.format(FACTORES_DIARIOS), "02/11/2026", "Base de CRSP de 202609. Rentabilidades diarias en % de Mkt-RF y RF desde el 1 de"
     " julio de 1926; se usan hasta el 31 de diciembre de 2025."),
]
TRATAMIENTOS = [
    ("Código", "Tratamiento"),
    ("T1", "Rentabilidad en exceso: rentabilidad mensual de la cartera menos RF del mismo mes (F1), en %."),
    ("T2", "Beta: pendiente de la regresión por MCO de la rentabilidad mensual en exceso de la cartera sobre Mkt-RF,"
           " julio de 1963 a diciembre de 2025 (750 meses)."),
    ("T3", "Rentabilidad media en exceso anualizada: media de las rentabilidades mensuales en exceso por 12."),
    ("T4", "Predicción del CAPM: beta (T2) por la prima media del mercado (media de Mkt-RF por 12); alfa = T3 − T4."),
    ("T5", "Volatilidad anualizada: desviación típica muestral de las rentabilidades mensuales en exceso por raíz de 12."),
    ("T6", "Recta ajustada: regresión por MCO de la rentabilidad media en exceso (T3) sobre la beta (T2) de los diez"
           " deciles."),
    ("T7", "Regresión de series temporales por MCO, con constante, de la rentabilidad mensual en exceso de cada cartera"
           " sobre los factores (CAPM: Mkt-RF de F1; FF3: Mkt-RF, SMB y HML de F1; FF5: los cinco de F4; FF5+Mom:"
           " además Mom de F5), julio de 1963 a diciembre de 2025. Alfa = constante por 12; predicción = suma de las"
           " cargas por la media mensual de cada factor, por 12; R² = 1 − varianza residual / varianza total."),
    ("T8", "Contraste de GIBBONS, ROSS y SHANKEN (1989): J = (T − N − L)/N · α'Σ⁻¹α / (1 + μ'Ω⁻¹μ), con Σ la matriz de"
           " covarianzas residual (dividida por T − L − 1), μ y Ω la media y la covarianza muestrales de los factores;"
           " se distribuye como una F(N, T − N − L)."),
    ("T9", "Componentes principales de la matriz de correlaciones de las rentabilidades mensuales en exceso de los 30"
           " sectores (rentabilidades tipificadas). Cuota = valor propio / suma de los valores propios. Signos: cargas"
           " positivas en el primero, la de Food negativa en el segundo y la de Oil positiva en el tercero."),
    ("T10", "Rentabilidad acumulada: producto de (1 + rentabilidad mensual/100) desde julio de 1963 (valor 1 a finales"
            " de junio de 1963), sin sumar el tipo sin riesgo. Media de un tramo = media mensual por 12; t = media /"
            " (desviación típica / raíz del número de meses)."),
    ("T11", "Ratio de SHARPE máximo (cartera tangente de los factores, en la muestra): raíz de μ'Ω⁻¹μ, con μ y Ω la"
            " media y la covarianza de las rentabilidades mensuales en exceso de los factores, por raíz de 12."),
    ("T12", "Crecimiento del consumo: logaritmo del cociente entre la media de los cuatro trimestres de un año y la del"
            " anterior (1964 a 2025, 62 años), en %; versión del cuarto trimestre: cociente entre el cuarto trimestre de"
            " cada año y el del anterior."),
    ("T13", "CAPM de consumo con utilidad CRRA y crecimiento lognormal: σ(m)/E[m] = raíz de (exp(γ²σc²) − 1). Aversión"
            " mínima para cada cota: γ = raíz de ln(1 + SR²) / σc. Tipo sin riesgo implícito con δ = 1:"
            " exp(γg − γ²σc²/2) − 1, con g y σc la media y la desviación típica de T12."),
    ("T14", "Correlación entre el crecimiento del consumo (T12) y la rentabilidad anual en exceso del mercado (Mkt-RF de"
            " la sección anual de F1, enero a diciembre), 1964 a 2025."),
    ("T15", "Razón de varianzas de LO y MacKINLAY (1988): rentabilidad total mensual del mercado (Mkt-RF + RF de F1) en"
            " logaritmos, ln(1 + r/100); varianza de las sumas solapadas de q meses con corrección del sesgo, dividida por q veces"
            " la varianza mensual; error típico con rentabilidades i.i.d., raíz de 2(2q-1)(q-1)/(3qT); z = (VR - 1)/error."),
    ("T16", "Autocorrelación de primer orden de la rentabilidad total diaria del mercado (Mkt-RF + RF de F9) en cada decenio"
            " (1926-1935 a 2016-2025); banda de ±2/raíz(n), con n la media de días por decenio."),
    ("T0", "Sin tratamiento: dato mensual (o trimestral, en F8, o diario, en F9) tal como lo publica la fuente."),
]


def indicadores():
    filas = [("Figura", "Panel", "Cartera", "Indicador", "Valor", "Unidad", "Periodo", "Fuente", "Tratamiento")]
    periodo = "1963-07 a 2025-12"
    datos = contraste_deciles()
    for panel, fuente, figura_panel in (("beta", "F1, F2", "(a)"), ("bm", "F1, F3", "(b)")):
        fs = [f for f in datos if f["panel"] == panel]
        for f in fs:
            cartera = f"Decil {f['decil']} ({f['columna']})"
            for ind, clave, unidad, trat in (("Beta", "beta", "", "T1, T2"),
                                              ("Rentabilidad media en exceso", "media", "% anual", "T1, T3"),
                                              ("Predicción del CAPM", "capm", "% anual", "T4"),
                                              ("Alfa", "alfa", "% anual", "T4"),
                                              ("Volatilidad", "vol", "% anual", "T5")):
                filas.append(("anx_sml_empirica", figura_panel, cartera, ind, round(f[clave], 4), unidad, periodo,
                              fuente, trat))
        pend, orden = np.polyfit([f["beta"] for f in fs], [f["media"] for f in fs], 1)
        for ind, valor, unidad, trat in (("Prima media del mercado (Mkt-RF)", fs[0]["prima"], "% anual", "T3"),
                                         ("Tipo sin riesgo medio (RF)", fs[0]["rf"], "% anual", "T3"),
                                         ("Recta ajustada: ordenada", orden, "% anual", "T6"),
                                         ("Recta ajustada: pendiente", pend, "% anual por unidad de beta", "T6")):
            filas.append(("anx_sml_empirica", figura_panel, "Mercado y recta ajustada", ind, round(valor, 4), unidad,
                          periodo, "F1" if "Recta" not in ind else fuente, trat))
    return filas + indicadores_a7(periodo) + indicadores_a8()


def indicadores_a7(periodo):
    """Filas de las figuras de la A7: anx_componentes, anx_tres_factores, anx_factores y anx_hj."""
    filas = []
    c = componentes()
    for k in range(10):
        filas.append(("anx_componentes", "(a)", f"Componente {k + 1}", "Varianza explicada", round(c["cuota"][k], 4),
                      "% del total", periodo, "F1, F7", "T1, T9"))
        filas.append(("anx_componentes", "(a)", f"Componente {k + 1}", "Varianza explicada acumulada",
                      round(c["acum"][k], 4), "% del total", periodo, "F1, F7", "T1, T9"))
    for j, sector in enumerate(c["sectores"]):
        for comp in (2, 3):
            filas.append(("anx_componentes", "(b)", f"{sector} ({SECTORES_ES[sector]})", f"Carga en el componente {comp}",
                          round(float(c["cargas"][j, comp - 1]), 4), "", periodo, "F1, F7", "T1, T9"))
        filas.append(("anx_componentes", "texto", f"{sector} ({SECTORES_ES[sector]})", "R² del mercado (CAPM)",
                      round(float(c["r2_mercado"][j]), 4), "", periodo, "F1, F7", "T1, T7"))
    for comp, corr in c["corr_componentes"].items():
        for factor, valor in corr.items():
            filas.append(("anx_componentes", "texto", f"Componente {comp}", f"Correlación con {factor}",
                          round(float(valor), 4), "", periodo, "F1, F4, F5, F7", "T9"))
    tf = tres_factores()
    for modelo, r in tf["res"].items():
        fuente = {"CAPM": "F1, F6", "FF3": "F1, F6", "FF5": "F4, F6", "FF5+Mom": "F4, F5, F6"}[modelo]
        for ind, valor, unidad, trat in (("Estadístico GRS", r["grs"], f"F({r['gl'][0]}, {r['gl'][1]})", "T7, T8"),
                                         ("Alfa medio en valor absoluto", np.abs(r["alfa"]).mean(), "% anual", "T7"),
                                         ("R² medio", r["r2"].mean(), "", "T7"),
                                         ("Correlación entre predicción y observación",
                                          np.corrcoef(r["prediccion"], r["media"])[0, 1], "", "T7")):
            filas.append(("anx_tres_factores", "(a)" if modelo == "CAPM" else "(b)" if modelo == "FF3" else "texto",
                          f"25 carteras, modelo {modelo}", ind, round(float(valor), 4), unidad, periodo, fuente, trat))
        for i, cartera in enumerate(tf["carteras"]):
            for ind, valor in (("Rentabilidad media en exceso", r["media"][i]), ("Predicción", r["prediccion"][i]),
                               ("Alfa", r["alfa"][i])):
                if ind == "Rentabilidad media en exceso" and modelo != "CAPM":
                    continue
                filas.append(("anx_tres_factores", "(a)" if modelo == "CAPM" else "(b)" if modelo == "FF3" else "texto",
                              f"{cartera}, modelo {modelo}" if ind != "Rentabilidad media en exceso" else cartera, ind,
                              round(float(valor), 4), "% anual", periodo, fuente, "T1, T3" if "media" in ind else "T7"))
    for factor, prima in tf["primas"].items():
        filas.append(("anx_tres_factores", "texto", factor, "Prima media", round(float(prima), 4), "% anual", periodo,
                      "F1", "T3"))
    fa = factores_acumulados()
    fuentes_factor = {"Mkt-RF": "F1", "SMB": "F1", "HML": "F1", "RMW": "F4", "CMA": "F4", "Mom": "F5"}
    for factor, r in fa["resumen"].items():
        for ind, clave, unidad in (("Media", "media", "% anual"), ("Volatilidad", "vol", "% anual"),
                                   ("Ratio de SHARPE", "sharpe", ""), ("Estadístico t de la media", "t", ""),
                                   ("Valor acumulado de un dólar", "acumulado", "dólares")):
            filas.append(("anx_factores", "(a)" if factor in ("Mkt-RF", "SMB", "HML") else "(b)", factor, ind,
                          round(float(r[clave]), 4), unidad, periodo, fuentes_factor[factor], "T10"))
    for (factor, a, b), r in fa["tramos"].items():
        tramo = f"{str(a)[:4]}-{str(a)[4:]} a {str(b)[:4]}-{str(b)[4:]}"
        for ind, clave, unidad in (("Media", "media", "% anual"), ("Estadístico t de la media", "t", ""),
                                   ("Valor acumulado de un dólar", "acumulado", "dólares")):
            filas.append(("anx_factores", "texto", factor, ind, round(float(r[clave]), 4), unidad, tramo,
                          fuentes_factor[factor], "T10"))
    for i, f1 in enumerate(fa["nombres"]):
        for j, f2 in enumerate(fa["nombres"]):
            if j > i:
                filas.append(("anx_factores", "texto", f"{f1} y {f2}", "Correlación", round(float(fa["corr"][i, j]), 4),
                              "", periodo, f"{fuentes_factor[f1]}, {fuentes_factor[f2]}", "T0"))
    hj = cota_hj()
    fuentes_hj = {"Mercado": "F1", "Tres factores": "F1", "Cinco factores": "F4", "Cinco factores e impulso": "F4, F5"}
    for conjunto, sr in hj["sr"].items():
        filas.append(("anx_hj", "", conjunto, "Ratio de SHARPE máximo", round(sr, 4), "anual", periodo,
                      fuentes_hj[conjunto], "T11"))
        filas.append(("anx_hj", "", conjunto, "Aversión mínima del CAPM de consumo", round(hj["gamma_min"][conjunto], 4),
                      "", "1964 a 2025", f"{fuentes_hj[conjunto]}, F8", "T11, T12, T13"))
        filas.append(("anx_hj", "texto", conjunto, "Tipo sin riesgo implícito con esa aversión (δ = 1)",
                      round(hj["rf_implicito"][conjunto] * 100, 4), "% anual", "1964 a 2025",
                      f"{fuentes_hj[conjunto]}, F8", "T12, T13"))
    for ind, valor, unidad in (("Crecimiento medio del consumo real por habitante", hj["media_c"] * 100, "% anual"),
                               ("Volatilidad del crecimiento del consumo", hj["sigma_c"] * 100, "% anual"),
                               ("Correlación con Mkt-RF (consumo del cuarto trimestre)", hj["corr_q4"], ""),
                               ("Correlación con Mkt-RF (consumo medio del año)", hj["corr_media"], "")):
        filas.append(("anx_hj", "texto", "Consumo", ind, round(float(valor), 4), unidad, "1964 a 2025",
                      "F8" if "Correlación" not in ind else "F1, F8", "T12" if "Correlación" not in ind else "T12, T14"))
    for año, g in sorted(hj["crecimiento"].items()):
        filas.append(("anx_hj", "", "Consumo", "Crecimiento anual del consumo real por habitante", round(g, 4), "%",
                      str(año), "F8", "T12"))
    return filas


def indicadores_a8():
    """Filas de la figura de la A8 con datos: anx_razon_varianzas."""
    filas = []
    r = razon_varianzas()
    for nombre, clave, tramo in (("1926-2025", "vr_largo", "1926-07 a 2025-12"), ("1963-2025", "vr_corto", "1963-07 a 2025-12")):
        for q, (vr, error) in zip(r["qs"], r[clave]):
            filas.append(("anx_razon_varianzas", "(a)", f"Mercado, {nombre}", f"Razón de varianzas a {q} meses", round(float(vr), 4),
                          "", tramo, "F1", "T15"))
            if q > 1:
                filas.append(("anx_razon_varianzas", "(a)", f"Mercado, {nombre}", f"Estadístico z a {q} meses",
                              round(float((vr - 1) / error), 4), "", tramo, "F1", "T15"))
    for a, b, c, n in r["autoc"]:
        filas.append(("anx_razon_varianzas", "(b)", "Mercado, rentabilidad diaria", "Autocorrelación de primer orden", round(float(c), 4),
                      f"{n} días", f"{a} a {b}", "F9", "T16"))
    filas.append(("anx_razon_varianzas", "(b)", "Mercado, rentabilidad diaria", "Banda de ±2/raíz(n)", round(float(r["banda"]), 4), "",
                  "1926 a 2025", "F9", "T16"))
    return filas


def series_brutas():
    filas = [("Fichero", "Serie", "Periodo", "Valor", "Unidad", "Fuente", "Tratamiento")]
    for fichero, marca, columnas, fuente in ((FACTORES, ",Mkt-RF", ["Mkt-RF", "SMB", "HML", "RF"], "F1"),
                                             (BETA, "Value Weighted Returns -- Monthly", DECILES_BETA, "F2"),
                                             (BM, "Value Weight Returns -- Monthly", DECILES_BM, "F3"),
                                             (CINCO, ",Mkt-RF", ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"], "F4"),
                                             (IMPULSO, ",Mom", ["Mom"], "F5"),
                                             (TAMANO_VALOR, "Average Value Weighted Returns -- Monthly", None, "F6"),
                                             (SECTORES, "Average Value Weighted Returns -- Monthly", None, "F7")):
        meses, cab, matriz = seccion(fichero, marca)
        dentro = (meses >= PERIODO[0]) & (meses <= PERIODO[1])
        for col in columnas or cab:
            j = cab.index(col)
            for mes, valor in zip(meses[dentro], matriz[dentro, j]):
                filas.append((fichero, col, int(mes), float(valor), "% mensual", fuente, "T0"))
    meses, cab, matriz = seccion(FACTORES, ",Mkt-RF")
    antes = (meses >= 192607) & (meses < PERIODO[0])
    for col in ("Mkt-RF", "RF"):
        j = cab.index(col)
        for mes, valor in zip(meses[antes], matriz[antes, j]):
            filas.append((FACTORES, col, int(mes), float(valor), "% mensual", "F1", "T0"))
    fechas, cd, d = diaria()
    dentro = fechas <= 20251231
    for col in ("Mkt-RF", "RF"):
        j = cd.index(col)
        for fecha, valor in zip(fechas[dentro], d[dentro, j]):
            filas.append((FACTORES_DIARIOS, col, int(fecha), float(valor), "% diario", "F9", "T0"))
    for año, valor in sorted(anual(FACTORES, "Mkt-RF").items()):
        if 1964 <= año <= 2025:
            filas.append((f"{FACTORES} (sección anual)", "Mkt-RF", año, valor, "% anual", "F1", "T0"))
    for fecha, valor in trimestres(CONSUMO):
        if "1963" <= fecha[:4] <= "2025":
            filas.append((f"FRED_{CONSUMO}", CONSUMO, fecha, valor,
                          "dólares encadenados de 2017 por habitante, tasa anual", "F8", "T0"))
    return filas


def main():
    leeme = [
        ("Libro de datos del tema 3.B.23 (renta variable)",),
        ("Contiene los datos reales que usan las figuras y las cifras del tema; cada fila cita su fuente y su tratamiento.",),
        ("Hojas: Fuentes y Tratamientos (códigos); Indicadores (formato largo: figura, panel, cartera, indicador, valor,"
         " unidad, periodo, fuente y tratamiento; el panel «texto» son cifras citadas en el texto que no salen en la"
         " figura); Series_brutas (datos usados, sin tratar: mensuales, la sección anual de Mkt-RF y el consumo"
         " trimestral).",),
        ("Figuras del anexo II, todas de julio de 1963 a diciembre de 2025:",),
        ("· anx_sml_empirica (contraste del CAPM): deciles por beta (a) y por valor contable sobre valor de mercado (b).",),
        ("· anx_componentes (contraste de la APT): componentes principales de los 30 sectores.",),
        ("· anx_tres_factores (modelo de tres factores): rentabilidad observada y predicha de las 25 carteras por tamaño y"
         " valor con el CAPM (a) y con tres factores (b); también los modelos de cinco y de cinco con impulso.",),
        ("· anx_factores (riesgo o error): rentabilidad acumulada de los seis factores y sus medias por tramos.",),
        ("· anx_hj (factor de descuento estocástico): cota de HANSEN y JAGANNATHAN y CAPM de consumo, con el consumo de"
         " FRED de 1964 a 2025.",),
        ("· anx_razon_varianzas (anexo III, eficiencia): razón de varianzas mensual del mercado, 1926-2025 y 1963-2025, y autocorrelación diaria por decenios, 1926-2025.",),
        ("Las figuras anx_apt_replica, anx_conjuntos_informacion, anx_reaccion_noticias y anx_grossman_stiglitz son esquemas o ejemplos inventados y no tienen datos aquí.",),
        ("Se regenera con  python3 Code/libro_datos.py  desde la carpeta del tema.",),
        (f"Biblioteca de datos de FRENCH: {LIBRERIA}",),
    ]
    destino = CODE / "datos_3B23.xlsx"
    escribir_xlsx(destino, [("Léeme", leeme), ("Fuentes", FUENTES), ("Tratamientos", TRATAMIENTOS),
                            ("Indicadores", indicadores()), ("Series_brutas", series_brutas())])
    print("escrito", destino)


if __name__ == "__main__":
    main()
