"""Libro único de datos del 3.B.24: Code/datos_3B24.xlsx (regla del usuario: todos los datos del tema en un libro).

Uso, desde la carpeta del tema:  python3 -I -B Code/libro_datos.py
Descarga de FRED las series que faltan en Code/datos/ (copia local en CSV, que se reutiliza) y monta el libro con las
hojas Léeme, Fuentes, Tratamientos, Indicadores (formato largo), Cifras_citadas y Calculos (valores de las figuras
calculadas, sin datos). Al añadir una serie o una cifra: darla de alta en SERIES o CIFRAS, y la fuente y el
tratamiento en FUENTES y TRATAMIENTOS.
"""
import csv
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx  # noqa: E402

CODE = Path(__file__).resolve().parent
DATOS = CODE / "datos"

FUENTES = [
    ("Código", "Fuente", "Enlace"),
    ("F1", "OCDE, Main Economic Indicators, vía FRED (Banco de la Reserva Federal de San Luis)",
     "https://fred.stlouisfed.org/series/IRLTLT01DEM156N"),
    ("F2", "Orden ECM/2/2026, de 9 de enero (BOE núm. 11, de 13 de enero de 2026)",
     "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-678"),
    ("F3", "HM Treasury (27 de marzo de 2015), Repayment of £2.6 billion historical debt to be completed by government",
     "https://www.gov.uk/government/news/repayment-of-26-billion-historical-debt-to-be-completed-by-government"),
    ("F4", "Moody's, Seasoned Baa y Aaa Corporate Bond Yield, vía FRED", "https://fred.stlouisfed.org/series/BAA"),
    ("F5", "Junta de Gobernadores de la Reserva Federal, rendimiento del Tesoro a 10 años (GS10), vía FRED",
     "https://fred.stlouisfed.org/series/GS10"),
    ("F6", "NBER, indicador de recesión de Estados Unidos (USREC), vía FRED", "https://fred.stlouisfed.org/series/USREC"),
    ("F7", "Instituto de Crédito Oficial, página de financiación (garantía del Estado)",
     "https://www.ico.es/web/ico_en/ico/investor_relations/funding"),
    ("F0", "Cálculo propio (sin datos)", ""),
]
TRATAMIENTOS = [
    ("Código", "Tratamiento"),
    ("T0", "Sin tratamiento: dato tal como lo publica la fuente."),
    ("T1", "Medias mensuales de datos diarios (las calcula la OCDE); se buscan los tramos de meses consecutivos con valor negativo."),
    ("T2", "Cálculo con las fórmulas del anexo I (valor actual con tipo único y reinversión al mismo tipo)."),
    ("T3", "Diferencia mensual entre el rendimiento Baa de Moody's y el del Tesoro a 10 años (puntos porcentuales)."),
    ("T4", "Meses de recesión según el NBER (valor 1), agrupados en tramos para sombrearlos en la figura."),
]
SERIES = [  # (código FRED, país, indicador, unidad, fuente, tratamiento, uso)
    ("IRLTLT01DEM156N", "Alemania", "Rendimiento de la deuda pública a 10 años (media mensual)", "% anual", "F1", "T1",
     "Cifra citada en I.3.1 (rendimientos negativos)"),
    ("BAA", "Estados Unidos", "Rendimiento de los bonos de empresa Baa de Moody's (media mensual)", "% anual", "F4", "T0",
     "Figura anx_diferencial_credito (I.4.3)"),
    ("AAA", "Estados Unidos", "Rendimiento de los bonos de empresa Aaa de Moody's (media mensual)", "% anual", "F4", "T0",
     "Referencia (diferencial Baa-Aaa desde 1919)"),
    ("GS10", "Estados Unidos", "Rendimiento del Tesoro a 10 años, vencimiento constante (media mensual)", "% anual", "F5", "T0",
     "Figura anx_diferencial_credito (I.4.3)"),
    ("USREC", "Estados Unidos", "Indicador de recesión del NBER (1 = recesión)", "0/1", "F6", "T4",
     "Bandas de la figura anx_diferencial_credito"),
]


def serie_fred(codigo):
    """Lee la copia local o, si no existe, la descarga de FRED."""
    DATOS.mkdir(exist_ok=True)
    local = DATOS / f"fred_{codigo}.csv"
    if not local.exists():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={codigo}"
        with urllib.request.urlopen(url, timeout=60) as r:
            local.write_bytes(r.read())
    filas = list(csv.reader(local.open(encoding="utf-8")))[1:]
    return [(d, float(v)) for d, v in filas if v not in ("", ".")]


def tramos_negativos(obs):
    tramos, previo = [], None
    for d, v in obs:
        if v >= 0:
            continue
        a, m = map(int, d[:7].split("-"))
        k = a * 12 + m
        if previo is not None and k == previo + 1:
            tramos[-1][1] = d[:7]
        else:
            tramos.append([d[:7], d[:7]])
        previo = k
    return tramos


def main():
    indicadores = [("Serie", "País", "Indicador", "Fecha", "Valor", "Unidad", "Fuente", "Tratamiento", "Uso")]
    cifras = [("Cifra", "Valor", "Unidad", "Fuente", "Tratamiento", "Apartado")]
    for codigo, pais, ind, unidad, fte, trt, uso in SERIES:
        obs = serie_fred(codigo)
        for d, v in obs:
            indicadores.append((codigo, pais, ind, d, v, unidad, fte, trt, uso))
        neg = [(d, v) for d, v in obs if v < 0]
        if codigo == "IRLTLT01DEM156N":
            tr = tramos_negativos(obs)
            minimo = min(neg, key=lambda x: x[1])
            cifras.append(("Tramos con rendimiento medio mensual negativo, bono alemán a 10 años",
                           "; ".join(f"{a} a {b}" for a, b in tr), "meses", fte, trt, "I.3.1"))
            cifras.append(("Mínimo del rendimiento medio mensual, bono alemán a 10 años (" + minimo[0][:7] + ")",
                           round(minimo[1], 2), "% anual", fte, trt, "I.3.1"))
    cifras.append(("Últimos bonos británicos sin vencimiento (consols y demás) amortizados", 2015, "año", "F3", "T0", "I.1.1"))
    cifras.append(("Fórmula del precio de las Letras a un año o menos: P = 100 / (1 + d i / 360)", None, "", "F2", "T0", "I.3.4"))
    cifras.append(("Fórmula del precio de las Letras a más de un año: P = 100 / (1 + i)^(d/360)", None, "", "F2", "T0", "I.3.4"))
    cifras.append(("Cupón corrido de Bonos y Obligaciones: C = I dc / dt", None, "", "F2", "T0", "I.1.3"))

    calculos = [("Figura", "Variable", "Valor", "Unidad", "Fuente", "Tratamiento")]
    for anos in (5, 10, 20, 30):
        vf = 1.04 ** (2 * anos)
        g = vf - 1
        cup = 0.08 * anos
        calculos.append(("anx_fuentes", f"Valor final por euro de nominal, {anos} años", round(vf, 4), "euros", "F0", "T2"))
        calculos.append(("anx_fuentes", f"Cupones sobre la ganancia, {anos} años", round(100 * cup / g, 1), "%", "F0", "T2"))
        calculos.append(("anx_fuentes", f"Intereses de los intereses sobre la ganancia, {anos} años",
                         round(100 * (g - cup) / g, 1), "%", "F0", "T2"))

    leeme = [("Libro de datos del Tema 3.B.24 (renta fija)",),
             ("Cada dato cita su fuente (hoja Fuentes) y su tratamiento (hoja Tratamientos).",),
             ("Indicadores: series en formato largo, filtrables por serie, país e indicador.",),
             ("Cifras_citadas: cifras y reglas que el tema cita sin figura.",),
             ("Calculos: valores de las figuras calculadas con las fórmulas del anexo, sin datos.",),
             ("Se genera con Code/libro_datos.py; las descargas se guardan en Code/datos/.",)]
    escribir_xlsx(str(CODE / "datos_3B24.xlsx"),
                  [("Léeme", leeme), ("Fuentes", FUENTES), ("Tratamientos", TRATAMIENTOS),
                   ("Indicadores", indicadores), ("Cifras_citadas", cifras), ("Calculos", calculos)])
    print(f"Escrito Code/datos_3B24.xlsx: {len(indicadores)-1} observaciones, {len(cifras)-1} cifras, {len(calculos)-1} cálculos")
    for fila in cifras[1:3]:
        print(fila)


if __name__ == "__main__":
    main()
