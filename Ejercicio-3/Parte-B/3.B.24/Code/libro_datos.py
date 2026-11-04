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
    baa = dict(serie_fred("BAA"))
    gs = dict(serie_fred("GS10"))
    dif = [(d, baa[d] - gs[d]) for d in sorted(gs) if d in baa]
    for d, v in dif:
        indicadores.append(("BAA-GS10", "Estados Unidos", "Diferencial Baa frente al Tesoro a 10 años", d, round(v, 4),
                            "puntos porcentuales", "F4, F5", "T3", "Figura anx_diferencial_credito (I.4.3)"))
    media = sum(v for _, v in dif) / len(dif)
    maximo = max(dif, key=lambda x: x[1])
    cifras.append((f"Diferencial Baa frente al Tesoro a 10 años: media desde {dif[0][0][:7]}", round(media, 2),
                   "puntos porcentuales", "F4, F5", "T3", "I.4.3"))
    cifras.append((f"Diferencial Baa frente al Tesoro a 10 años: máximo ({maximo[0][:7]})", round(maximo[1], 2),
                   "puntos porcentuales", "F4, F5", "T3", "I.4.3"))
    cifras.append(("Diferencial Baa frente al Tesoro a 10 años en 2020-03", round(dict(dif)["2020-03-01"], 2),
                   "puntos porcentuales", "F4, F5", "T3", "I.4.3"))
    cifras.append(("Deuda del ICO con garantía explícita, irrevocable, incondicional y directa del Estado", None, "", "F7", "T0", "I.5.1"))
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

    # A3: bono de referencia a 10 años, cupón anual del 6 %, rendimiento del 6 % (I.6 e I.7)
    def P(c, y, T):
        return sum(c * 100 / (1 + y) ** t for t in range(1, T + 1)) + 100 / (1 + y) ** T

    def dur(c, y, T):
        return sum(t * (c * 100 + (100 if t == T else 0)) / (1 + y) ** t for t in range(1, T + 1)) / P(c, y, T)

    def conv(c, y, T):
        return sum(t * (t + 1) * (c * 100 + (100 if t == T else 0)) / (1 + y) ** (t + 2) for t in range(1, T + 1)) / P(c, y, T)

    d, cv = dur(0.06, 0.06, 10), conv(0.06, 0.06, 10)
    ds = d / 1.06
    calculos += [("I.6-I.7", "Duración de MACAULAY del bono de referencia", round(d, 4), "años", "F0", "T2"),
                 ("I.6-I.7", "Duración modificada del bono de referencia", round(ds, 4), "años", "F0", "T2"),
                 ("I.6-I.7", "Convexidad del bono de referencia", round(cv, 4), "años al cuadrado", "F0", "T2"),
                 ("I.6", "Peso del último pago en el precio del bono de referencia", round(106 / 1.06 ** 10, 2), "%", "F0", "T2"),
                 ("I.6", "Duración de una perpetuidad con y = 5 %", 21.0, "años", "F0", "T2")]
    for dy in (-0.03, -0.01, 0.01, 0.03):
        ex = (P(0.06, 0.06 + dy, 10) - 100) / 100 * 100
        calculos.append(("cuadro I.7", f"Cambio de {100*dy:+.0f} puntos: exacto / duración / duración y convexidad",
                         f"{ex:+.2f} / {-ds*dy*100:+.2f} / {(-ds*dy+0.5*cv*dy*dy)*100:+.2f}", "%", "F0", "T2"))
    mx = max(((T, dur(0.02, 0.06, T)) for T in range(1, 201)), key=lambda x: x[1])
    calculos.append(("anx_duracion_vencimiento", "Máximo de la duración con c = 2 % e y = 6 % (años) y vencimiento en que se alcanza",
                     f"{mx[1]:.2f} en T = {mx[0]}", "años", "F0", "T2"))

    # A4: inmunización (I.8), con el bono de referencia y un cambio inmediato y permanente del tipo
    def rr(H, y1):
        W = sum((6 + (100 if t == 10 else 0)) * (1 + y1) ** (H - t) for t in range(1, 11))
        return (W / 100) ** (1 / H) - 1

    for y1 in (0.04, 0.08):
        calculos.append(("anx_inmunizacion", f"Rentabilidad realizada con H = D = {d:.2f} años si el tipo pasa al {100*y1:.0f} %",
                         round(100 * rr(d, y1), 3), "%", "F0", "T2"))
    f = lambda yy, t, y0=0.06: (1 + y0) ** t / (1 + yy) ** t
    for yy in (0.02, 0.10):
        calculos.append(("anx_redington", f"Excedente con y = {100*yy:.0f} %: inmunizada / desajustada",
                         f"{50*f(yy,5)+50*f(yy,15)-100*f(yy,10):.2f} / {100*f(yy,5)-100*f(yy,10):.2f}", "euros por 100", "F0", "T2"))
    g = lambda yy, t: 1.05 ** t / (1 + yy) ** t
    for yy in (0.01, 0.09):
        calculos.append(("anx_brecha", f"Capital con y = {100*yy:.0f} %: banco / fondo de pensiones",
                         f"{100*g(yy,6)-90*g(yy,1):.1f} / {100*g(yy,8)-90*g(yy,20):.1f}", "euros por 100 de activo", "F0", "T2"))

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
