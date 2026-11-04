"""Libro único de datos del 3.B.24: Code/datos_3B24.xlsx (regla del usuario: todos los datos del tema en un libro).

Uso, desde la carpeta del tema:  python3 -I -B Code/libro_datos.py
Descarga de FRED las series que faltan en Code/datos/ (copia local en CSV, que se reutiliza) y monta el libro con las
hojas Léeme, Fuentes, Tratamientos, Indicadores (formato largo), Cifras_citadas y Calculos (valores de las figuras
calculadas, sin datos). Al añadir una serie o una cifra: darla de alta en SERIES o CIFRAS, y la fuente y el
tratamiento en FUENTES y TRATAMIENTOS.
"""
import csv
import math
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
    ("F5", "Junta de Gobernadores de la Reserva Federal, rendimientos del Tesoro de EE. UU. a vencimiento constante "
     "(GS1M a GS30 y DGS10 diario) y Letras a tres meses en el mercado secundario (TB3MS), vía FRED",
     "https://fred.stlouisfed.org/categories/115"),
    ("F6", "NBER, indicador de recesión de Estados Unidos (USREC), vía FRED", "https://fred.stlouisfed.org/series/USREC"),
    ("F7", "Instituto de Crédito Oficial, página de financiación (garantía del Estado)",
     "https://www.ico.es/web/ico_en/ico/investor_relations/funding"),
    ("F8", "Banco Central Europeo (10 de julio de 2007), First release of daily euro area government bond yield curves",
     "https://www.ecb.europa.eu/press/pr/date/2007/html/pr070710.en.html"),
    ("F9", "Junta de Gobernadores de la Reserva Federal, modelo de KIM y WRIGHT: tipos cupón cero ajustados y prima por "
     "plazo (THREEFY1, THREEFY2, THREEFY10, THREEFYTP10), vía FRED", "https://fred.stlouisfed.org/series/THREEFYTP10"),
    ("F10", "Banco de la Reserva Federal de Atlanta, Wu-Xia shadow federal funds rate (WU y XIA, 2016)",
     "https://www.atlantafed.org/research-and-data/data/wu-xia-shadow-federal-funds-rate"),
    ("F11", "Banco de la Reserva Federal de San Luis, inflación implícita a 10 años (T10YIE) y a 5 años dentro de 5 "
     "(T5YIFR), vía FRED", "https://fred.stlouisfed.org/series/T5YIFR"),
    ("F0", "Cálculo propio (sin datos)", ""),
]
TRATAMIENTOS = [
    ("Código", "Tratamiento"),
    ("T0", "Sin tratamiento: dato tal como lo publica la fuente."),
    ("T1", "Medias mensuales de datos diarios (las calcula la OCDE); se buscan los tramos de meses consecutivos con valor negativo."),
    ("T2", "Cálculo con las fórmulas del anexo I (valor actual con tipo único y reinversión al mismo tipo)."),
    ("T3", "Diferencia mensual entre el rendimiento Baa de Moody's y el del Tesoro a 10 años (puntos porcentuales)."),
    ("T4", "Meses de recesión según el NBER (valor 1), agrupados en tramos para sombrearlos en la figura."),
    ("T5", "Pendiente de la curva de EE. UU.: GS10 menos GS3M (puntos porcentuales), mensual desde 1982-01; media y "
           "porcentaje de meses con pendiente negativa."),
    ("T6", "Variaciones mensuales (primeras diferencias) de los rendimientos de GS3M a GS10 desde 1982-01: correlaciones "
           "entre plazos y componentes principales de su matriz de covarianzas (signos de la figura: nivel positivo, "
           "pendiente creciente con el plazo, curvatura positiva en el extremo corto)."),
    ("T7", "España: tipo interbancario a tres meses menos rendimiento de la deuda pública a largo plazo (OCDE), mensual; "
           "tramos de meses con diferencia positiva (curva invertida)."),
    ("T8", "Cálculo con las fórmulas de la segunda parte del anexo I: factores de descuento despejados bono a bono y "
           "tipos al contado, a plazo y par con capitalización anual."),
    ("T9", "Medias mensuales de datos diarios de KIM y WRIGHT (capitalización continua); tipo a plazo a un año dentro de "
           "un año = 2 y(2) - y(1), comparado con y(1) doce meses después: error medio, porcentaje de meses con error "
           "positivo y pendiente de la regresión del cambio de y(1) sobre el diferencial entre el tipo a plazo y y(1)."),
    ("T10", "Media de los tipos cortos esperados = tipo a 10 años menos prima por plazo (KIM y WRIGHT); medias por periodos."),
    ("T11", "Datos de fin de mes del Banco de la Reserva Federal de Atlanta (fechas de Excel convertidas a meses); mínimo "
            "del tipo sombra en cada episodio de tipos en el límite."),
]
SERIES = [  # (código FRED, país, indicador, unidad, fuente, tratamiento, uso)
    ("IRLTLT01DEM156N", "Alemania", "Rendimiento de la deuda pública a 10 años (media mensual)", "% anual", "F1", "T1",
     "Cifra citada en I.3.1 (rendimientos negativos)"),
    ("BAA", "Estados Unidos", "Rendimiento de los bonos de empresa Baa de Moody's (media mensual)", "% anual", "F4", "T0",
     "Figura anx_diferencial_credito (I.4.3)"),
    ("AAA", "Estados Unidos", "Rendimiento de los bonos de empresa Aaa de Moody's (media mensual)", "% anual", "F4", "T0",
     "Referencia (diferencial Baa-Aaa desde 1919)"),
    ("GS10", "Estados Unidos", "Rendimiento del Tesoro a 10 años, vencimiento constante (media mensual)", "% anual", "F5", "T0",
     "Figuras anx_diferencial_credito (I.4.3), anx_curvas_eeuu y anx_componentes (I.11)"),
    ("USREC", "Estados Unidos", "Indicador de recesión del NBER (1 = recesión)", "0/1", "F6", "T4",
     "Bandas de la figura anx_diferencial_credito"),
    ("IR3TIB01ESM156N", "España", "Tipo interbancario a tres meses (media mensual)", "% anual", "F1", "T7",
     "Cifra citada en I.11.1 (curva invertida en España)"),
    ("IRLTLT01ESM156N", "España", "Rendimiento de la deuda pública a largo plazo, 10 años (media mensual)", "% anual", "F1",
     "T7", "Cifra citada en I.11.1 (curva invertida en España)"),
]
# Tesoro de EE. UU. a vencimiento constante para la segunda parte del anexo I (GS10 ya figura arriba)
for _c, _p, _uso in [("GS1M", "1 mes", "Figura anx_curvas_eeuu (I.11.1)"),
                     ("GS3M", "3 meses", "Figuras anx_curvas_eeuu y anx_componentes (I.11); pendiente (I.11.1)"),
                     ("GS6M", "6 meses", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS1", "1 año", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS2", "2 años", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS3", "3 años", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS5", "5 años", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS7", "7 años", "Figuras anx_curvas_eeuu y anx_componentes (I.11)"),
                     ("GS20", "20 años", "Figura anx_curvas_eeuu (I.11.1)"),
                     ("GS30", "30 años", "Figura anx_curvas_eeuu (I.11.1)")]:
    SERIES.append((_c, "Estados Unidos", f"Rendimiento del Tesoro a {_p}, vencimiento constante (media mensual)",
                   "% anual", "F5", "T0", _uso))


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

    # A5: curvas (I.9), estimación (I.10) y movimientos (I.11)
    def tir(flujos, precio):
        a, b = -0.5, 1.0
        for _ in range(200):
            m = (a + b) / 2
            if sum(cf / (1 + m) ** t for t, cf in flujos) > precio:
                a = m
            else:
                b = m
        return m

    Bd = {1: 1 / 1.03, 2: 1 / 1.036 ** 2, 3: 1 / 1.04 ** 3}
    bonos = [("A", 1, 0.0), ("B", 2, 0.04), ("C", 3, 0.05)]
    for nombre, T, c in bonos:
        flujos = [(t, 100 * c + (100 if t == T else 0)) for t in range(1, T + 1)]
        precio = sum(cf * Bd[t] for t, cf in flujos)
        fwd = 1 / Bd[1] - 1 if T == 1 else Bd[T - 1] / Bd[T] - 1
        calculos.append(("cuadro I.10 (bootstrapping)", f"Bono {nombre} ({T} años, cupón {100*c:.0f} %): precio / B(0,{T}) / "
                         "contado / a plazo del año / rendimiento al vencimiento",
                         f"{precio:.3f} / {Bd[T]:.5f} / {100*(Bd[T]**(-1/T)-1):.2f} / {100*fwd:.2f} / {100*tir(flujos, precio):.3f}",
                         "por 100 de nominal; %", "F0", "T8"))
    for T in (1, 2, 3):
        par = (1 - Bd[T]) / sum(Bd[t] for t in range(1, T + 1))
        calculos.append(("I.9.3", f"Tipo par a {T} años con la curva del cuadro", round(100 * par, 3), "%", "F0", "T8"))
    for c in (0.05, 0.10):
        flujos = [(t, 100 * c + (100 if t == 3 else 0)) for t in range(1, 4)]
        calculos.append(("I.9.4 (efecto cupón)", f"Rendimiento al vencimiento de un bono a 3 años con cupón del {100*c:.0f} %",
                         round(100 * tir(flujos, sum(cf * Bd[t] for t, cf in flujos)), 3), "%", "F0", "T8"))

    import numpy as np
    mens = {c: {d[:7]: v for d, v in serie_fred(c)} for c in
            ("GS1M", "GS3M", "GS6M", "GS1", "GS2", "GS3", "GS5", "GS7", "GS10", "GS20", "GS30")}
    desde = sorted(f for f in set(mens["GS3M"]) & set(mens["GS10"]) if f >= "1982-01")
    pend = [mens["GS10"][f] - mens["GS3M"][f] for f in desde]
    cifras.append((f"Pendiente media GS10 menos GS3M, {desde[0]} a {desde[-1]}", round(sum(pend) / len(pend), 2),
                   "puntos porcentuales", "F5", "T5", "I.11.1"))
    cifras.append((f"Meses con GS10 por debajo de GS3M, {desde[0]} a {desde[-1]}",
                   round(100 * sum(p < 0 for p in pend) / len(pend), 1), "% de los meses", "F5", "T5", "I.11.1"))
    for f, corto, largo in (("2006-12", "GS6M", "GS10"), ("2023-06", "GS1", "GS10"), ("2026-10", "GS10", "GS3M")):
        cifras.append((f"{corto} menos {largo} en {f}", round(mens[corto][f] - mens[largo][f], 2), "puntos porcentuales",
                       "F5", "T0", "I.11.1"))
    pcs = ["GS3M", "GS6M", "GS1", "GS2", "GS3", "GS5", "GS7", "GS10"]
    comun = sorted(f for f in set.intersection(*[set(mens[c]) for c in pcs]) if f >= "1982-01")
    dX = np.diff(np.array([[mens[c][f] for c in pcs] for f in comun]), axis=0)
    cor = np.corrcoef(dX, rowvar=False)
    for a, b in (("GS2", "GS10"), ("GS3M", "GS10")):
        cifras.append((f"Correlación de las variaciones mensuales de {a} y {b}, {comun[0]} a {comun[-1]}",
                       round(float(cor[pcs.index(a), pcs.index(b)]), 2), "", "F5", "T6", "I.11.1"))
    w, v = np.linalg.eigh(np.cov(dX, rowvar=False))
    orden = np.argsort(w)[::-1]
    w, v = w[orden], v[:, orden]
    if v[:, 0].sum() < 0: v[:, 0] *= -1
    if v[-1, 1] < v[0, 1]: v[:, 1] *= -1
    if v[0, 2] < 0: v[:, 2] *= -1
    cuota = 100 * w / w.sum()
    cifras.append((f"Varianza explicada por nivel / pendiente / curvatura, {comun[0]} a {comun[-1]}",
                   f"{cuota[0]:.1f} / {cuota[1]:.1f} / {cuota[2]:.1f}", "%", "F5", "T6", "I.11.2"))
    for i, c in enumerate(pcs):
        calculos.append(("anx_componentes", f"Cargas de {c}: nivel / pendiente / curvatura",
                         f"{v[i,0]:.3f} / {v[i,1]:.3f} / {v[i,2]:.3f}", "", "F5", "T6"))
    es3 = {d[:7]: x for d, x in serie_fred("IR3TIB01ESM156N")}
    es10 = {d[:7]: x for d, x in serie_fred("IRLTLT01ESM156N")}
    inv = [(f + "-01", es10[f] - es3[f]) for f in sorted(set(es3) & set(es10))]
    cifras.append(("España: tramos de meses con el interbancario a 3 meses por encima de la deuda a largo plazo",
                   "; ".join(f"{a} a {b}" for a, b in tramos_negativos(inv)), "meses", "F1", "T7", "I.11.1"))
    cifras.append(("BCE: curvas diarias del área del euro desde el 10 de julio de 2007 (SVENSSON; bonos AAA y de todos "
                   "los Estados)", None, "", "F8", "T0", "I.10.2"))

    # A6: expectativas (I.12), primas (I.13) y modelos (I.14)
    def media_mensual(codigo):
        acc = {}
        for d, x in serie_fred(codigo):
            acc.setdefault(d[:7], []).append(x)
        return {m: sum(x) / len(x) for m, x in acc.items()}

    def mas12(m):
        t = int(m[:4]) * 12 + int(m[5:7]) + 11
        return f"{t // 12}-{t % 12 + 1:02d}"

    kw = {c: media_mensual(c) for c in ("THREEFY1", "THREEFY2", "THREEFY10", "THREEFYTP10")}
    nombres_kw = {"THREEFY1": "Tipo cupón cero a 1 año ajustado (KIM y WRIGHT)", "THREEFY2": "Tipo cupón cero a 2 años "
                  "ajustado (KIM y WRIGHT)", "THREEFY10": "Tipo cupón cero a 10 años ajustado (KIM y WRIGHT)",
                  "THREEFYTP10": "Prima por plazo a 10 años (KIM y WRIGHT)"}
    usos_kw = {"THREEFY1": "Figura anx_plazo_realizado (I.12.2)", "THREEFY2": "Figura anx_plazo_realizado (I.12.2)",
               "THREEFY10": "Figura anx_prima_kw (I.13.3)", "THREEFYTP10": "Figura anx_prima_kw (I.13.3)"}
    for c, obs in kw.items():
        for m in sorted(obs):
            indicadores.append((c, "Estados Unidos", nombres_kw[c] + ", media mensual", m + "-01", round(obs[m], 4),
                                "% anual, continuo", "F9", "T9", usos_kw[c]))
    y1, y2 = kw["THREEFY1"], kw["THREEFY2"]
    pares = [(2 * y2[m] - y1[m], y1[mas12(m)], y1[m]) for m in sorted(y1) if mas12(m) in y1 and m in y2]
    err = [f - r for f, r, _ in pares]
    xs = [f - s for f, _, s in pares]
    ys = [r - s for _, r, s in pares]
    mx_, my_ = sum(xs) / len(xs), sum(ys) / len(ys)
    pend = sum((a - mx_) * (b - my_) for a, b in zip(xs, ys)) / sum((a - mx_) ** 2 for a in xs)
    meses_prev = [m for m in sorted(y1) if mas12(m) in y1 and m in y2]
    cifras.append((f"Tipo a plazo a un año menos realizado: media, previsiones de {meses_prev[0]} a {meses_prev[-1]}",
                   round(sum(err) / len(err), 2), "puntos porcentuales", "F9", "T9", "I.12.2"))
    cifras.append(("Meses en que el tipo a plazo superó al realizado", round(100 * sum(e > 0 for e in err) / len(err), 1),
                   "% de los meses", "F9", "T9", "I.12.2"))
    cifras.append(("Pendiente del cambio del tipo a un año sobre el diferencial entre el tipo a plazo y el de contado",
                   round(pend, 2), "", "F9", "T9", "I.12.2"))
    tp, y10 = kw["THREEFYTP10"], kw["THREEFY10"]
    for a, b in (("1990-01", "1999-12"), ("2000-01", "2007-12"), ("2008-01", "2015-12"), ("2016-01", "2021-12"),
                 ("2022-01", "2026-12")):
        v = [x for m, x in tp.items() if a <= m <= b]
        cifras.append((f"Prima por plazo a 10 años, media de {a} a {b}", round(sum(v) / len(v), 2), "puntos porcentuales",
                       "F9", "T10", "I.13.3"))
    mn = min(tp.items(), key=lambda t: t[1])
    cifras.append((f"Prima por plazo a 10 años, mínimo ({mn[0]})", round(mn[1], 2), "puntos porcentuales", "F9", "T10", "I.13.3"))
    ult = max(m for m in tp if m in y10)
    cifras.append((f"Tipo a 10 años = media de tipos cortos esperados + prima ({ult})",
                   f"{y10[ult]:.2f} = {y10[ult]-tp[ult]:.2f} + {tp[ult]:.2f}", "puntos porcentuales", "F9", "T10", "I.13.3"))
    filas_wx = list(csv.reader((DATOS / "wuxia_sombra.csv").open(encoding="utf-8")))[1:]
    sombra = []
    for d, ff, sh in filas_wx:
        if ff:
            indicadores.append(("FF_efectivo", "Estados Unidos", "Tipo efectivo de los fondos federales, fin de mes", d,
                                float(ff), "% anual", "F10", "T11", "Figura anx_sombra (I.14.4)"))
        if sh:
            indicadores.append(("sombra_WuXia", "Estados Unidos", "Tipo sombra de WU y XIA, fin de mes", d, float(sh),
                                "% anual", "F10", "T11", "Figura anx_sombra (I.14.4)"))
            sombra.append((d[:7], float(sh)))
    for a, b in (("2009-01", "2015-12"), ("2020-03", "2022-02")):
        m, x = min(((m, x) for m, x in sombra if a <= m <= b), key=lambda t: t[1])
        cifras.append((f"Tipo sombra de WU y XIA, mínimo entre {a} y {b} ({m})", round(x, 2), "% anual", "F10", "T11", "I.14.4"))
    f13 = (Bd[1] / Bd[3]) ** 0.5 - 1
    calculos += [("I.12.3 (paso del tiempo)", "Cupón cero a 3 años con la curva quieta: precio hoy / dentro de un año / "
                  "rentabilidad", f"{Bd[3]:.5f} / {Bd[2]:.5f} / {100*(Bd[2]/Bd[3]-1):.2f}", "por euro; %", "F0", "T8"),
                 ("I.12.3 (paso del tiempo)", "Con la curva esperada: tipo a plazo entre el año 1 y el 3 / precio dentro de "
                  "un año / rentabilidad", f"{100*f13:.2f} / {Bd[3]/Bd[1]:.5f} / {100*(1/Bd[1]-1):.2f}", "%; por euro; %",
                  "F0", "T8")]
    ib, kap, sig = 4.5, 0.25, 0.02
    rinf = ib - 100 * sig ** 2 / (2 * kap ** 2)
    bn = lambda n: (1 - math.exp(-kap * n)) / (kap * n)
    for i0 in (1.5, 4.5, 7.5):
        r30 = rinf + (i0 - rinf) * bn(30) + 100 * sig ** 2 * 30 * bn(30) ** 2 / (4 * kap)
        calculos.append(("anx_vasicek", f"Tipo a 30 años con i = {i0} % (r_inf = {rinf:.2f} %)", round(r30, 2), "%", "F0", "T8"))

    leeme =[("Libro de datos del Tema 3.B.24 (renta fija)",),
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
