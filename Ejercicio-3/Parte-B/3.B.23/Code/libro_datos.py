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
from datos_french import BETA, BM, CINCO, FACTORES, IMPULSO, SECTORES, TAMANO_VALOR, URL, seccion  # noqa: E402
from datos_fred import CONSUMO, trimestres  # noqa: E402
from datos_fred import URL as URL_FRED  # noqa: E402
from figuras_anexo2 import (DECILES_BETA, DECILES_BM, PERIODO, SECTORES_ES, componentes, contraste_deciles,  # noqa: E402
                            cota_hj, factores_acumulados, tres_factores)
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
    ("T0", "Sin tratamiento: dato mensual tal como lo publica la fuente (en %)."),
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
    return filas


def series_brutas():
    filas = [("Fichero", "Serie", "Mes", "Valor", "Unidad", "Fuente", "Tratamiento")]
    for fichero, marca, columnas, fuente in ((FACTORES, ",Mkt-RF", ["Mkt-RF", "RF"], "F1"),
                                             (BETA, "Value Weighted Returns -- Monthly", DECILES_BETA, "F2"),
                                             (BM, "Value Weight Returns -- Monthly", DECILES_BM, "F3")):
        meses, cab, matriz = seccion(fichero, marca)
        dentro = (meses >= PERIODO[0]) & (meses <= PERIODO[1])
        for col in columnas:
            j = cab.index(col)
            for mes, valor in zip(meses[dentro], matriz[dentro, j]):
                filas.append((fichero, col, int(mes), float(valor), "% mensual", fuente, "T0"))
    return filas


def main():
    leeme = [
        ("Libro de datos del tema 3.B.23 (renta variable)",),
        ("Contiene los datos reales que usan las figuras y las cifras del tema; cada fila cita su fuente y su tratamiento.",),
        ("Hojas: Fuentes y Tratamientos (códigos); Indicadores (formato largo: figura, panel, cartera, indicador, valor,"
         " unidad, periodo, fuente y tratamiento); Series_brutas (datos mensuales usados, sin tratar).",),
        ("Figuras: anx_sml_empirica (anexo II, contraste del CAPM): deciles por beta (a) y por valor contable sobre valor"
         " de mercado (b), julio de 1963 a diciembre de 2025.",),
        ("Se regenera con  python3 Code/libro_datos.py  desde la carpeta del tema.",),
        (f"Biblioteca de datos de FRENCH: {LIBRERIA}",),
    ]
    destino = CODE / "datos_3B23.xlsx"
    escribir_xlsx(destino, [("Léeme", leeme), ("Fuentes", FUENTES), ("Tratamientos", TRATAMIENTOS),
                            ("Indicadores", indicadores()), ("Series_brutas", series_brutas())])
    print("escrito", destino)


if __name__ == "__main__":
    main()
