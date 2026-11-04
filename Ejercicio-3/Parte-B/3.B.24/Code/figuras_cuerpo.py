"""Figuras del cuerpo del 3.B.24 (b1_… del bloque «Instrumentos»). Escribe los .tikz en Img/.

Uso, desde la carpeta del tema:  python3 -B Code/figuras_cuerpo.py
y después, para cada figura:   bash Code/generar_figura.sh b1_flujos   (y lo mismo con las demás)

Son figuras abstractas: sin cifras en los ejes, con letras y condiciones. Las cifras con que se dibujan solo fijan la
forma y figuran en la cabecera de cada .tikz. Usa escribir(), coords(), precio() y tir() de figuras_anexo1.py.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_anexo1 import escribir, coords, precio, tir  # noqa: E402


def _cabecera(nombre, texto):
    return f"% Figura del cuerpo ({texto}).\n% Generar con: bash Code/generar_figura.sh {nombre}\n"


def _curva(f, a, b, X, Y, n=80):
    return coords([(X(a + j * (b - a) / n), Y(f(a + j * (b - a) / n))) for j in range(n + 1)])


# =====================  Tanda T10 (bloque 1, «Instrumentos»)  =====================
# b1_flujos: pagos prometidos (gris claro) y su valor actual (gris oscuro) de un bono con T = 8 cupones anuales;
#   c = 16 % y r = 9 % (solo fijan la forma); a la izquierda, el precio como suma de los valores actuales.
# b1_convergencia: precio ex cupón de tres bonos a T = 10 años con r = 5 % y cupones del 8 %, 5 % y 2 %; en
#   discontinua, el bono a la par si en k = 4 el tipo sube al 7 %.
# b1_precio_rendimiento: precio de un bono con c = 6 % y T = 10 frente a su rendimiento (0 % a 16 %); P0 = 80.
# b1_diferencial: descomposición esquemática del rendimiento de tres bonos del mismo plazo (sin escala).
# b1_balanza: valor actual de los pagos como pesos sobre el eje del tiempo; cupón cero y bono con cupón (c = 12 %,
#   y = 9 %, T = 8, los mismos de b1_flujos).
# b1_tangente: bonos a la par con y0 = c = 6 % a 20 años (A) y a 3 años (B), con sus tangentes en y0.
# b1_convexidad: bono a 10 años con c = 6 %, tangente en y0 = 6 % y cambios de 4 puntos.
# b1_pesas_bala: bala = cupón cero a 10 años; pesas = cupones cero a 2 y 18 años a partes iguales (duración 10 en
#   las dos y valor 100 con y0 = 6 %).
# b1_convexidad_negativa: bono a 10 años con c = 6 % sin opción y amortizable esquemático (precio de rescate K = 104,
#   mínimo suave con k = 0,12, como anx_convexidad_negativa).
# b1_inmunizacion: rentabilidad realizada en H frente al tipo que rige tras la compra, esquemática.
# b1_brecha: balance de un banco antes y después de una subida de los tipos, esquemático: el activo cae ΔA (en
#   discontinua) y el pasivo menos, de modo que el capital E se reduce a menos de la mitad.
CLARO, MEDIO, OSCURO = "black!16", "black!40", "black!62"


def flujos():
    T, c, r = 8, 0.16, 0.09
    dx, hN, w = 1.3, 2.4, 0.17
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (-1.0,0) -- ({T*dx+0.7:.2f},0) node[below] {{$t$}};")
    va = []
    for t in range(1, T + 1):
        x = t * dx
        pago = c + (1 if t == T else 0)
        actual = pago / (1 + r) ** t
        va.append(actual)
        out.append(rf"\fill[{CLARO}] ({x-w:.3f},0) rectangle ({x+w:.3f},{pago*hN:.3f});")
        out.append(rf"\fill[{OSCURO}] ({x-w:.3f},0) rectangle ({x+w:.3f},{actual*hN:.3f});")
    for t, et in ((1, "$1$"), (2, "$2$"), (3, "$3$"), (T, "$T$")):
        out.append(rf"\node[below] at ({t*dx:.2f},0) {{{et}}};")
    out.append(rf"\node[below] at ({5.5*dx:.2f},0) {{$\cdots$}};")
    out.append(rf"\node[above, inner sep=1.5pt] at ({dx:.2f},{c*hN:.3f}) {{$cN$}};")
    out.append(rf"\node[above, inner sep=1.5pt] at ({T*dx:.2f},{(1+c)*hN:.3f}) {{$cN+N$}};")
    # precio: valores actuales apilados en t = 0
    y = 0.0
    for k, v in enumerate(va):
        out.append(rf"\fill[{OSCURO}] (-0.28,{y:.3f}) rectangle (0.28,{y+v*hN:.3f});")
        if k:
            out.append(rf"\draw[white, line width=0.5pt] (-0.28,{y:.3f}) -- (0.28,{y:.3f});")
        y += v * hN
    out.append(r"\node[below] at (0,0) {$0$};")
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt}}] (-0.42,0) -- (-0.42,{y:.3f})"
               r" node[midway, left=5pt] {$P$};")
    # leyenda
    lx, ly = 1.9 * dx, 2.6
    out.append(rf"\fill[{CLARO}] ({lx:.2f},{ly:.2f}) rectangle ({lx+0.3:.2f},{ly+0.22:.2f});")
    out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{ly+0.11:.2f}) {{Pago prometido, $CF_t$}};")
    out.append(rf"\fill[{OSCURO}] ({lx:.2f},{ly-0.45:.2f}) rectangle ({lx+0.3:.2f},{ly-0.23:.2f});")
    out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{ly-0.34:.2f}) {{Valor actual, $CF_t/(1+r)^t$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_flujos", _cabecera("b1_flujos", "B1, «Valor actual»: pagos de un bono con c = 16 %, r = 9 % y T = 8, y su"
                                    f" valor actual; P = {y/hN*100:.1f} por cada 100 de nominal") + "\n".join(out) + "\n")


def convergencia():
    T, r, k, r2 = 10, 0.05, 4, 0.07
    sx, base, sy = 1.0, 70.0, 0.074
    X = lambda t: t * sx
    Y = lambda p: (p - base) * sy
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({X(T)+0.6:.2f},0) node[below] {{$t$}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(130):.2f}) node[above] {{Precio}};")
    estilos = {0.08: "very thick", 0.05: "very thick, black!45", 0.02: "very thick, black!70"}
    for c, est in estilos.items():
        pts = [(X(t), Y(precio(c, r, T - t))) for t in range(0, T + 1)]
        out.append(rf"\draw[{est}] {' -- '.join(f'({x:.3f},{y:.3f})' for x, y in pts)};")
    # el bono a la par cuando el tipo sube en k
    p_k = precio(0.05, r2, T - k)
    pts = [(X(t), Y(precio(0.05, r2, T - t))) for t in range(k, T + 1)]
    out.append(rf"\draw[thick, densely dashed] ({X(k):.3f},{Y(100):.3f}) -- ({X(k):.3f},{Y(p_k):.3f});")
    out.append(rf"\draw[thick, densely dashed] {' -- '.join(f'({x:.3f},{y:.3f})' for x, y in pts)};")
    out.append(rf"\node[anchor=south west, inner sep=2pt] at ({X(k+0.9):.3f},{Y(precio(0.05, r2, T-k-1)) + 0.03:.3f}) {{$r'>r$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.15):.3f},{Y(precio(0.08, r, T)):.3f}) {{$c>r$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.15):.3f},{Y(100):.3f}) {{$c=r$}};")
    out.append(rf"\node[anchor=north west] at ({X(0.15):.3f},{Y(precio(0.02, r, T)):.3f}) {{$c<r$}};")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$N$}};")
    out.append(r"\node[below] at (0,0) {$0$};")
    out.append(rf"\node[below] at ({X(k):.3f},0) {{$k$}};")
    out.append(rf"\node[below] at ({X(T):.3f},0) {{$T$}};")
    out.append(rf"\draw[densely dotted] ({X(T):.3f},0) -- ({X(T):.3f},{Y(100):.3f});")
    out.append(r"\end{tikzpicture}")
    escribir("b1_convergencia", _cabecera("b1_convergencia", "B1, «Par, prima y descuento»: precios de bonos a 10 años con"
                                          f" r = 5 % y c = 8, 5 y 2 %; en k = 4 el tipo del bono a la par pasa al 7 % y su"
                                          f" precio a {p_k:.2f}") + "\n".join(out) + "\n")


def precio_rendimiento():
    c, T = 0.06, 10
    ymax, sx, sy = 0.16, 56.0, 0.027
    X = lambda yy: yy * sx
    Y = lambda p: p * sy
    P0 = 80.0
    y0 = tir(P0, c, T)
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({X(ymax)+0.6:.2f},0) node[below left] {{Rendimiento, $y$}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(175):.2f}) node[above] {{Precio, $P$}};")
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{_curva(lambda v: precio(c, v, T), 0, ymax, X, Y)}}};")
    out.append(rf"\fill (0,{Y(precio(c, 0, T)):.3f}) circle (1.6pt);")
    out.append(rf"\node[left] at (0,{Y(precio(c, 0, T)):.3f}) {{$N\,(1+cT)$}};")
    out.append(rf"\draw[densely dotted] ({X(c):.3f},0) -- ({X(c):.3f},{Y(100):.3f}) -- (0,{Y(100):.3f});")
    out.append(rf"\fill ({X(c):.3f},{Y(100):.3f}) circle (1.6pt);")
    out.append(rf"\node[below] at ({X(c):.3f},0) {{$c$}};")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$N$}};")
    out.append(rf"\draw[densely dashed, ->] (0,{Y(P0):.3f}) -- ({X(y0)-0.04:.3f},{Y(P0):.3f});")
    out.append(rf"\draw[densely dashed, ->] ({X(y0):.3f},{Y(P0)-0.04:.3f}) -- ({X(y0):.3f},0.04);")
    out.append(rf"\fill ({X(y0):.3f},{Y(P0):.3f}) circle (1.6pt);")
    out.append(rf"\node[left] at (0,{Y(P0):.3f}) {{$P_0$}};")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.022):.3f},{Y(precio(c, 0.022, T)):.3f}) {{$P>N$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.125):.3f},{Y(precio(c, 0.125, T)):.3f}) {{$P<N$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_precio_rendimiento", _cabecera("b1_precio_rendimiento", f"B1, «TIR»: bono con c = 6 % y T = 10; P0 = 80"
                                                f" da y0 = {100*y0:.2f} %") + "\n".join(out) + "\n")


def diferencial():
    rf_h = 2.1
    bonos = [("Deuda pública", []), ("Grado de inversión", [0.22, 0.42, 0.28]), ("Alto rendimiento", [0.95, 1.05, 0.5])]
    tonos = [MEDIO, "black!26", CLARO]
    nombres = [r"Pérdida esperada, $p\,\ell$", "Prima por riesgo de impago", "Prima de liquidez"]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    ancho, paso = 1.25, 2.35
    out.append(rf"\draw (-0.5,0) -- ({2*paso+ancho+0.3:.2f},0);")
    for k, (nombre, piezas) in enumerate(bonos):
        x0 = k * paso
        out.append(rf"\fill[{OSCURO}] ({x0:.2f},0) rectangle ({x0+ancho:.2f},{rf_h:.2f});")
        y = rf_h
        for h, tono in zip(piezas, tonos):
            out.append(rf"\fill[{tono}] ({x0:.2f},{y:.3f}) rectangle ({x0+ancho:.2f},{y+h:.3f});")
            y += h
        if piezas:
            out.append(rf"\draw[decorate, decoration={{brace, amplitude=3.5pt}}] ({x0-0.1:.2f},{rf_h:.2f}) --"
                       rf" ({x0-0.1:.2f},{y:.3f}) node[midway, left=4pt] {{$s$}};")
        out.append(rf"\node[below, align=center, text width=2.2cm] at ({x0+ancho/2:.3f},0) {{{nombre}}};")
    out.append(rf"\draw[densely dotted] (-0.3,{rf_h:.2f}) -- ({2*paso+ancho+0.2:.2f},{rf_h:.2f});")
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt, mirror}}] (-0.15,0) -- (-0.15,{rf_h:.2f})"
               r" node[midway, left=5pt] {$r_f$};")
    lx, ly = 2 * paso + ancho + 0.7, 3.9
    for k, (nombre, tono) in enumerate(reversed(list(zip(nombres, tonos)))):
        yy = ly - 0.5 * k
        out.append(rf"\fill[{tono}] ({lx:.2f},{yy:.2f}) rectangle ({lx+0.3:.2f},{yy+0.22:.2f});")
        out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{yy+0.11:.2f}) {{{nombre}}};")
    yy = ly - 1.5
    out.append(rf"\fill[{OSCURO}] ({lx:.2f},{yy:.2f}) rectangle ({lx+0.3:.2f},{yy+0.22:.2f});")
    out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{yy+0.11:.2f}) {{Precio del tiempo, $r_f$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_diferencial", _cabecera("b1_diferencial", "B1, «Riesgos»: rendimiento de tres bonos del mismo plazo;"
                                         " esquemática, sin escala") + "\n".join(out) + "\n")


def balanza():
    T, c, y = 8, 0.12, 0.09
    dx, esc, w = 0.72, 2.3, 0.15
    pesos = [(t, (c + (1 if t == T else 0)) / (1 + y) ** t) for t in range(1, T + 1)]
    P = sum(v for _, v in pesos)
    D = sum(t * v for t, v in pesos) / P
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]

    def viga(x0, barras, fulcro, titulo, etiqueta):
        out.append(rf"\begin{{scope}}[xshift={x0}cm]")
        out.append(rf"\node[font=\footnotesize\bfseries, anchor=west] at (-0.1,2.75) {{{titulo}}};")
        for t, v in barras:
            out.append(rf"\fill[{OSCURO}] ({t*dx-w:.3f},0.03) rectangle ({t*dx+w:.3f},{0.03+v*esc:.3f});")
        out.append(rf"\draw[line width=1.6pt] (0,0) -- ({(T+0.45)*dx:.3f},0);")
        out.append(rf"\fill[black] ({fulcro*dx:.3f},-0.03) -- ({fulcro*dx-0.22:.3f},-0.45) -- ({fulcro*dx+0.22:.3f},-0.45) -- cycle;")
        out.append(rf"\node[below] at ({fulcro*dx:.3f},-0.45) {{{etiqueta}}};")
        out.append(r"\node[below] at (0,-0.05) {$0$};")
        if fulcro < T - 0.5:
            out.append(rf"\node[below] at ({T*dx:.3f},-0.05) {{$T$}};")
        out.append(r"\end{scope}")

    viga(0.0, [(T, 1 / (1 + y) ** T)], T, "Cupón cero", "$D=T$")
    viga(7.4, pesos, D, "Con cupón", "$D$")
    out.append(r"\end{tikzpicture}")
    escribir("b1_balanza", _cabecera("b1_balanza", f"B1, «Plazo medio»: valor actual de los pagos de un cupón cero y de"
                                     f" un bono con c = 12 %, y = 9 % y T = 8 (D = {D:.2f})") + "\n".join(out) + "\n")


def _ejes(out, ymin, ymax, base, sx, sy, top, etx="Rendimiento, $y$", ety="Precio, $P$"):
    X = lambda yy: (yy - ymin) * sx
    Y = lambda p: (p - base) * sy
    out.append(rf"\draw[->] (0,0) -- ({X(ymax)+0.5:.3f},0) node[below left] {{{etx}}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(top):.3f}) node[above] {{{ety}}};")
    return X, Y


def _dmod(c, y, T):
    P = precio(c, y, T)
    return sum(t * (c * 100 + (100 if t == T else 0)) / (1 + y) ** (t + 1) for t in range(1, T + 1)) / P


def tangente():
    y0, dy = 0.06, 0.02
    ymin, ymax, base, sx, sy = 0.03, 0.10, 55.0, 105.0, 0.045
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes(out, ymin, ymax, base, sx, sy, top=152)
    bonos = {"A": (20, "very thick"), "B": (3, "very thick, black!45")}
    for nombre, (T, est) in bonos.items():
        out.append(rf"\draw[{est}] plot[smooth] coordinates {{{_curva(lambda v: precio(0.06, v, T), ymin, ymax, X, Y)}}};")
        Ds = _dmod(0.06, y0, T)
        tg = lambda v: 100 * (1 - Ds * (v - y0))
        a, b = y0 - 0.022, y0 + 0.031
        out.append(rf"\draw[thick, densely dashed] ({X(a):.3f},{Y(tg(a)):.3f}) -- ({X(b):.3f},{Y(tg(b)):.3f});")
        out.append(rf"\draw[{{Stealth[length=2.5pt]}}-{{Stealth[length=2.5pt]}}, thin] ({X(y0+dy):.3f},{Y(100):.3f}) -- ({X(y0+dy):.3f},{Y(tg(y0+dy)):.3f});")
    out.append(rf"\node[anchor=south west] at ({X(0.031):.3f},{Y(precio(0.06, 0.031, 20)):.3f}) {{$A$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.031):.3f},{Y(precio(0.06, 0.031, 3)):.3f}) {{$B$}};")
    DsA, DsB = _dmod(0.06, y0, 20), _dmod(0.06, y0, 3)
    out.append(rf"\node[anchor=west] at ({X(y0+dy)+0.06:.3f},{Y(100-50*DsB*dy):.3f}) {{$\Delta P_B$}};")
    out.append(rf"\node[anchor=west] at ({X(y0+dy)+0.06:.3f},{Y(100-60*DsA*dy):.3f}) {{$\Delta P_A$}};")
    out.append(rf"\draw[densely dotted] ({X(y0):.3f},0) -- ({X(y0):.3f},{Y(100):.3f}) -- (0,{Y(100):.3f});")
    out.append(rf"\draw[densely dotted] ({X(y0):.3f},{Y(100):.3f}) -- ({X(y0+dy):.3f},{Y(100):.3f});")
    out.append(rf"\draw[densely dotted] ({X(y0+dy):.3f},0) -- ({X(y0+dy):.3f},{Y(100*(1-DsA*dy)):.3f});")
    out.append(rf"\fill ({X(y0):.3f},{Y(100):.3f}) circle (1.7pt);")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[below] at ({X(y0+dy):.3f},0) {{$y_0+\Delta y$}};")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$P_0$}};")
    out.append(rf"\node[anchor=south west, inner sep=1.5pt] at ({X(0.091):.3f},{Y(100*(1-DsB*0.031))+0.08:.3f}) {{pendiente $-D_B^*P_0$}};")
    out.append(rf"\node[anchor=north west, inner sep=1.5pt] at ({X(0.091):.3f},{Y(100*(1-DsA*0.031)):.3f}) {{pendiente $-D_A^*P_0$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_tangente", _cabecera("b1_tangente", f"B1, «Sensibilidad»: bonos a la par con c = y0 = 6 % a 20 años"
                                      f" (D* = {DsA:.2f}) y a 3 años (D* = {DsB:.2f}); tangentes en y0") + "\n".join(out) + "\n")


def convexidad():
    c, T, y0, dy = 0.06, 10, 0.06, 0.04
    ymin, ymax, base, sx, sy = 0.0, 0.13, 50.0, 70.0, 0.05
    P = lambda v: precio(c, v, T)
    Ds = _dmod(c, y0, T)
    tg = lambda v: 100 * (1 - Ds * (v - y0))
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes(out, ymin, ymax, base, sx, sy, top=158)
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{_curva(P, 0.012, ymax, X, Y)}}};")
    out.append(rf"\draw[thick, densely dashed] ({X(0.012):.3f},{Y(tg(0.012)):.3f}) -- ({X(0.112):.3f},{Y(tg(0.112)):.3f});")
    out.append(rf"\draw[densely dotted] (0,{Y(100):.3f}) -- ({X(y0+dy)+0.3:.3f},{Y(100):.3f});")
    for v in (y0 - dy, y0 + dy):
        out.append(rf"\draw[densely dotted] ({X(v):.3f},0) -- ({X(v):.3f},{Y(min(P(v), tg(v))):.3f});")
        out.append(rf"\draw[line width=2.2pt, black!35] ({X(v):.3f},{Y(tg(v)):.3f}) -- ({X(v):.3f},{Y(P(v)):.3f});")
    xa, xb = X(y0 - dy) - 0.22, X(y0 + dy) + 0.22
    out.append(rf"\draw[<->] ({xa:.3f},{Y(100):.3f}) -- ({xa:.3f},{Y(P(y0-dy)):.3f}) node[midway, left] {{$\Delta P^+$}};")
    out.append(rf"\draw[<->] ({xb:.3f},{Y(100):.3f}) -- ({xb:.3f},{Y(P(y0+dy)):.3f}) node[midway, right] {{$\Delta P^-$}};")
    out.append(rf"\fill ({X(y0):.3f},{Y(100):.3f}) circle (1.7pt);")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$P_0$}};")
    out.append(rf"\node[below] at ({X(y0-dy):.3f},0) {{$y_0-\Delta y$}};")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[below] at ({X(y0+dy):.3f},0) {{$y_0+\Delta y$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.112):.3f},{Y(P(0.112)):.3f}) {{$P(y)$}};")
    out.append(rf"\node[anchor=north west, inner sep=1.5pt] at ({X(0.112):.3f},{Y(tg(0.112)):.3f}) {{$P_0\,(1-D^*\Delta y)$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_convexidad", _cabecera("b1_convexidad", f"B1, «Segundo orden»: bono a 10 años con c = y0 = 6 %, cambios de"
                                        f" 4 puntos; ganancia {P(y0-dy)-100:.1f} y pérdida {100-P(y0+dy):.1f}; la tangente"
                                        f" da ±{100*Ds*dy:.1f}") + "\n".join(out) + "\n")


def pesas_bala():
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    # izquierda: dónde están los pagos (valor actual como peso), con la misma duración
    dx, esc, w, D = 0.27, 1.25, 0.16, 10
    out.append(r"\node[font=\footnotesize\bfseries, anchor=west] at (-0.1,4.6) {Pagos};")
    for nombre, y_base, barras in (("Bala", 2.2, [(D, 1.0)]), ("Pesas", 0.0, [(2, 0.5), (18, 0.5)])):
        for t, v in barras:
            out.append(rf"\fill[{OSCURO}] ({t*dx-w:.3f},{y_base+0.03:.3f}) rectangle ({t*dx+w:.3f},{y_base+0.03+v*esc:.3f});")
        out.append(rf"\draw[line width=1.6pt] (0,{y_base:.2f}) -- ({19.5*dx:.3f},{y_base:.2f});")
        out.append(rf"\fill[black] ({D*dx:.3f},{y_base-0.03:.2f}) -- ({D*dx-0.2:.3f},{y_base-0.4:.2f}) -- ({D*dx+0.2:.3f},{y_base-0.4:.2f}) -- cycle;")
        out.append(rf"\node[below] at ({D*dx:.3f},{y_base-0.4:.2f}) {{$D$}};")
        out.append(rf"\node[anchor=west, font=\footnotesize\itshape] at ({19.7*dx:.3f},{y_base+0.25:.2f}) {{{nombre}}};")
    # derecha: precio frente al rendimiento
    x0 = 7.3
    ymin, ymax, base, sx, sy = 0.0, 0.14, 40.0, 42.0, 0.0225
    X = lambda yy: x0 + (yy - ymin) * sx
    Y = lambda p: (p - base) * sy
    bala = lambda v: 100 * (1.06 / (1 + v)) ** 10
    pesas = lambda v: 50 * (1.06 / (1 + v)) ** 2 + 50 * (1.06 / (1 + v)) ** 18
    out.append(rf"\node[font=\footnotesize\bfseries, anchor=west] at ({x0-0.1:.2f},4.6) {{Precio}};")
    out.append(rf"\draw[->] ({x0:.2f},0) -- ({X(ymax)+0.4:.3f},0) node[below left] {{$y$}};")
    out.append(rf"\draw[->] ({x0:.2f},0) -- ({x0:.2f},{Y(210):.3f}) node[above] {{$P$}};")
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{_curva(pesas, ymin, ymax, X, Y)}}};")
    out.append(rf"\draw[very thick, black!45] plot[smooth] coordinates {{{_curva(bala, ymin, ymax, X, Y)}}};")
    out.append(rf"\fill ({X(0.06):.3f},{Y(100):.3f}) circle (1.7pt);")
    out.append(rf"\draw[densely dotted] ({X(0.06):.3f},0) -- ({X(0.06):.3f},{Y(100):.3f}) -- ({x0:.2f},{Y(100):.3f});")
    out.append(rf"\node[below] at ({X(0.06):.3f},0) {{$y_0$}};")
    out.append(rf"\node[left] at ({x0:.2f},{Y(100):.3f}) {{$P_0$}};")
    out.append(rf"\node[anchor=south west, font=\footnotesize\itshape] at ({X(0.012):.3f},{Y(pesas(0.012)):.3f}) {{Pesas}};")
    out.append(rf"\node[anchor=north east, font=\footnotesize\itshape] at ({X(0.02):.3f},{Y(bala(0.02))-0.06:.3f}) {{Bala}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_pesas_bala", _cabecera("b1_pesas_bala", "B1, «Valor»: bala = cupón cero a 10 años; pesas = cupones cero a 2"
                                        f" y 18 años a partes iguales; con y = 0 %: {pesas(0):.1f} y {bala(0):.1f}; con 14 %:"
                                        f" {pesas(0.14):.1f} y {bala(0.14):.1f}") + "\n".join(out) + "\n")


def convexidad_negativa():
    c, T, K, k = 0.06, 10, 104.0, 0.12
    ymin, ymax, base, sx, sy = 0.01, 0.13, 55.0, 75.0, 0.047
    P = lambda v: precio(c, v, T)
    amort = lambda v: -math.log(math.exp(-k * P(v)) + math.exp(-k * K)) / k
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes(out, ymin, ymax, base, sx, sy, top=150)
    out.append(rf"\draw[very thick, black!45] plot[smooth] coordinates {{{_curva(P, ymin, ymax, X, Y)}}};")
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{_curva(amort, ymin, ymax, X, Y)}}};")
    out.append(rf"\draw[dashed] (0,{Y(K):.3f}) -- ({X(ymax):.3f},{Y(K):.3f});")
    out.append(rf"\node[left] at (0,{Y(K):.3f}) {{$K$}};")
    v = 0.03
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt, mirror}}] ({X(v)+0.08:.3f},{Y(amort(v))+0.03:.3f}) --"
               rf" ({X(v)+0.08:.3f},{Y(P(v))-0.03:.3f}) node[midway, right=5pt] {{Opción}};")
    out.append(rf"\node[anchor=south west] at ({X(0.014):.3f},{Y(P(0.014)):.3f}) {{Sin opción}};")
    out.append(rf"\node[anchor=north] at ({X(0.022):.3f},{Y(amort(0.022))-0.1:.3f}) {{Amortizable}};")
    out.append(rf"\node[anchor=north] at ({X(0.05):.3f},{Y(amort(0.05))-0.12:.3f}) {{$C<0$}};")
    out.append(rf"\node[anchor=north east] at ({X(0.112):.3f},{Y(amort(0.112))-0.05:.3f}) {{$C>0$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_convexidad_negativa", _cabecera("b1_convexidad_negativa", "B1, «Convexidad negativa»: bono a 10 años"
                                                 " con c = 6 % sin opción y amortizable esquemático (K = 104)")
             + "\n".join(out) + "\n")


def inmunizacion():
    a = 1.0                      # medio intervalo del tipo, en unidades del dibujo
    sx, sy, y0p = 3.0, 1.4, 1.0   # cm por unidad y altura de la línea de y0
    X = lambda u: (u + a) * sx
    Y = lambda v: y0p + v * sy
    curvas = {r"$D<H$": (0.45, 0.12, "very thick, black!45"), r"$D=H$": (0.0, 0.3, "very thick"),
              r"$D>H$": (-0.6, 0.14, "very thick, densely dashed")}
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({X(a)+0.5:.2f},0) node[below left] {{Tipo tras la compra, $y$}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(0.95):.2f}) node[above] {{Rentabilidad realizada en $H$}};")
    for et, (m, q, est) in curvas.items():
        f = lambda u: m * u + q * u * u
        pts = [(X(-a + j * 2 * a / 60), Y(f(-a + j * 2 * a / 60))) for j in range(61)]
        out.append(rf"\draw[{est}] plot[smooth] coordinates {{{coords(pts)}}};")
        out.append(rf"\node[anchor=west] at ({X(a)+0.05:.3f},{Y(f(a)):.3f}) {{{et}}};")
    out.append(rf"\draw[densely dotted] (0,{Y(0):.3f}) -- ({X(a):.3f},{Y(0):.3f});")
    out.append(rf"\draw[densely dotted] ({X(0):.3f},0) -- ({X(0):.3f},{Y(0):.3f});")
    out.append(rf"\fill ({X(0):.3f},{Y(0):.3f}) circle (1.7pt);")
    out.append(rf"\node[left] at (0,{Y(0):.3f}) {{$y_0$}};")
    out.append(rf"\node[below] at ({X(0):.3f},0) {{$y_0$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_inmunizacion", _cabecera("b1_inmunizacion", "B1, «Inmunización»: rentabilidad realizada en H según el"
                                          " tipo que rige justo después de la compra; esquemática (curvatura exagerada)")
             + "\n".join(out) + "\n")


def brecha():
    A, L, dA, dL = 2.5, 2.14, 0.3, 0.1
    ancho = 1.35
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]

    def balance(x0, titulo, a, l, perdidas):
        out.append(rf"\node[font=\footnotesize\bfseries] at ({x0+ancho:.2f},{A+0.45:.2f}) {{{titulo}}};")
        out.append(rf"\fill[{MEDIO}] ({x0:.2f},0) rectangle ({x0+ancho:.2f},{a:.3f});")
        out.append(rf"\node at ({x0+ancho/2:.2f},{a/2:.3f}) {{$A$}};")
        out.append(rf"\fill[{CLARO}] ({x0+ancho:.2f},0) rectangle ({x0+2*ancho:.2f},{l:.3f});")
        out.append(rf"\node at ({x0+1.5*ancho:.2f},{l/2:.3f}) {{$L$}};")
        out.append(rf"\fill[{OSCURO}] ({x0+ancho:.2f},{l:.3f}) rectangle ({x0+2*ancho:.2f},{a:.3f});")
        out.append(rf"\draw ({x0:.2f},0) rectangle ({x0+2*ancho:.2f},{a:.3f});")
        out.append(rf"\draw ({x0+ancho:.2f},0) -- ({x0+ancho:.2f},{a:.3f});")
        out.append(rf"\draw ({x0+ancho:.2f},{l:.3f}) -- ({x0+2*ancho:.2f},{l:.3f});")
        if a - l > 0.35:
            out.append(rf"\node[text=white] at ({x0+1.5*ancho:.2f},{(a+l)/2:.3f}) {{$E$}};")
        else:
            out.append(rf"\draw[black!50] ({x0+2*ancho:.2f},{(a+l)/2:.3f}) -- ({x0+2*ancho+0.35:.2f},{(a+l)/2:.3f})"
                       r" node[right, text=black] {$E$};")
        if perdidas:
            out.append(rf"\draw[densely dashed] ({x0:.2f},{a:.3f}) rectangle ({x0+ancho:.2f},{A:.3f});")
            out.append(rf"\node at ({x0+ancho/2:.2f},{(a+A)/2:.3f}) {{$\Delta A$}};")

    balance(0.0, "Antes", A, L, False)
    balance(4.3, r"Tras una subida de los tipos", A - dA, L - dL, True)
    out.append(rf"\node[anchor=north] at ({ancho:.2f},-0.12) {{$D_A^*>D_L^*$}};")
    out.append(rf"\node[anchor=north] at ({4.3+ancho:.2f},-0.12) {{$\Delta A>\Delta L$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b1_brecha", _cabecera("b1_brecha", "B1, «Balances»: activo, pasivo y capital de un banco con activos más largos"
                                    " que sus pasivos antes y después de una subida de los tipos; esquemática")
             + "\n".join(out) + "\n")


# =====================  Tanda T11 (bloque 2, «Mercados»)  =====================
# b2_variantes: variantes del bono ordinario ordenadas, en cada riesgo, por el que dejan al inversor (izquierda, menos
#   riesgo y menor rendimiento; derecha, más riesgo y mayor rendimiento); esquemática.
# b2_liquidez: precios a los que vende (P_v) y compra (P_c) un intermediario según la cantidad, en un bono líquido
#   (horquilla 0,25 y pendiente 0,08) y en uno poco líquido (0,9 y 0,32); esquemática, sin escala.
# b2_referencia: rendimiento a un mismo plazo de la deuda alemana y de la de otro Estado del euro, con la prima de
#   riesgo descompuesta; esquemática, sin escala.
def variantes():
    filas = [("Tipo de interés", 2.2, ["Con opción de venta", "Tipo variable"], ["Amortizable anticipadamente"]),
             ("Inflación", 1.1, ["Indexado"], []),
             ("Crédito", 0.0, ["Cédula"], ["Subordinado", "Convertible contingente"])]
    xs_izq, xs_der = [-2.5, -4.85], [2.5, 4.85]
    caja = (r"rounded corners=2pt, fill=black!7, draw=black!45, text width=2.0cm, align=center, minimum height=0.62cm,"
            r" inner sep=2pt, font=\footnotesize")
    out = [r"\begin{tikzpicture}[>={Stealth[length=4pt]}]"]
    out.append(r"\fill[black!22, rounded corners=2pt] (-0.85,-0.42) rectangle (0.85,2.62);")
    out.append(r"\node[align=center, font=\footnotesize\bfseries] at (0,1.1) {Bono\\ordinario};")
    for nombre, y, izq, der in filas:
        out.append(rf"\node[anchor=west, font=\footnotesize\bfseries] at (-8.25,{y:.2f}) {{{nombre}}};")
        prev = -0.85
        for x, et in zip(xs_izq, izq):
            out.append(rf"\node[{caja}] (n) at ({x:.2f},{y:.2f}) {{{et}}};")
            out.append(rf"\draw[->, black!60] ({prev:.2f},{y:.2f}) -- (n.east);")
            prev = x - 1.06
        prev = 0.85
        for x, et in zip(xs_der, der):
            out.append(rf"\node[{caja}] (n) at ({x:.2f},{y:.2f}) {{{et}}};")
            out.append(rf"\draw[->, black!60] ({prev:.2f},{y:.2f}) -- (n.west);")
            prev = x + 1.06
    out.append(r"\draw[<->, thick] (-5.9,-0.95) -- (5.9,-0.95);")
    out.append(r"\node[anchor=east, font=\footnotesize] at (-5.95,-0.95) {$-$};")
    out.append(r"\node[anchor=west, font=\footnotesize] at (5.95,-0.95) {$+$};")
    out.append(r"\node[anchor=north, font=\footnotesize] at (0,-1.05) {Riesgo para el inversor y rendimiento exigido};")
    out.append(r"\end{tikzpicture}")
    escribir("b2_variantes", _cabecera("b2_variantes", "B2, «Variantes»: variantes del bono ordinario según el riesgo que"
                                       " reparten; esquemática") + "\n".join(out) + "\n")


def liquidez():
    Q, V, alto = 4.6, 1.9, 3.8
    paneles = [("Bono líquido", 0.0, 0.25, 0.08), ("Bono poco líquido", 6.6, 0.9, 0.32)]
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    for titulo, x0, h, k in paneles:
        out.append(rf"\begin{{scope}}[xshift={x0}cm]")
        out.append(rf"\node[font=\footnotesize\bfseries, anchor=west] at (-0.1,{alto+0.45:.2f}) {{{titulo}}};")
        out.append(rf"\draw[->] (0,0) -- ({Q+0.4:.2f},0) node[below left] {{Cantidad}};")
        out.append(rf"\draw[->] (0,0) -- (0,{alto:.2f}) node[above] {{Precio}};")
        out.append(rf"\draw[densely dotted] (0,{V:.2f}) -- ({Q:.2f},{V:.2f});")
        out.append(rf"\node[left] at (0,{V:.2f}) {{$V$}};")
        out.append(rf"\draw[very thick] (0,{V+h/2:.3f}) -- ({Q:.2f},{V+h/2+k*Q:.3f}) node[right] {{$P_v$}};")
        out.append(rf"\draw[very thick, black!45] (0,{V-h/2:.3f}) -- ({Q:.2f},{V-h/2-k*Q:.3f}) node[right] {{$P_c$}};")
        out.append(rf"\draw[decorate, decoration={{brace, amplitude=2.5pt, mirror}}] (0.12,{V-h/2:.3f}) -- (0.12,{V+h/2:.3f})"
                   r" node[midway, right=3pt] {$h$};")
        out.append(r"\end{scope}")
    out.append(r"\end{tikzpicture}")
    escribir("b2_liquidez", _cabecera("b2_liquidez", "B2, «Secundario»: precios de un intermediario según la cantidad en un"
                                      " bono líquido y en uno poco líquido; esquemática, sin escala") + "\n".join(out) + "\n")


def referencia():
    rf_h = 2.0
    piezas = [("Riesgo de crédito", 0.7, MEDIO), ("Liquidez", 0.35, "black!26"), ("Redenominación", 0.5, CLARO)]
    ancho, paso = 1.25, 2.5
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\draw (-0.5,0) -- ({paso+ancho+0.3:.2f},0);")
    for k, nombre in enumerate(("Alemania", "Otro Estado del euro")):
        x0 = k * paso
        out.append(rf"\fill[{OSCURO}] ({x0:.2f},0) rectangle ({x0+ancho:.2f},{rf_h:.2f});")
        out.append(rf"\node[below, align=center, text width=2.4cm] at ({x0+ancho/2:.3f},0) {{{nombre}}};")
    y = rf_h
    for _, h, tono in piezas:
        out.append(rf"\fill[{tono}] ({paso:.2f},{y:.3f}) rectangle ({paso+ancho:.2f},{y+h:.3f});")
        y += h
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=3.5pt}}] ({paso-0.1:.2f},{rf_h:.2f}) -- ({paso-0.1:.2f},{y:.3f})"
               r" node[midway, left=4pt] {$s$};")
    out.append(rf"\draw[densely dotted] (-0.3,{rf_h:.2f}) -- ({paso+ancho+0.2:.2f},{rf_h:.2f});")
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt, mirror}}] (-0.15,0) -- (-0.15,{rf_h:.2f})"
               r" node[midway, left=5pt] {$r_f$};")
    lx, ly = paso + ancho + 0.7, 2.95
    for k, (nombre, _, tono) in enumerate(reversed(piezas)):
        yy = ly - 0.5 * k
        out.append(rf"\fill[{tono}] ({lx:.2f},{yy:.2f}) rectangle ({lx+0.3:.2f},{yy+0.22:.2f});")
        out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{yy+0.11:.2f}) {{{nombre}}};")
    yy = ly - 1.5
    out.append(rf"\fill[{OSCURO}] ({lx:.2f},{yy:.2f}) rectangle ({lx+0.3:.2f},{yy+0.22:.2f});")
    out.append(rf"\node[anchor=west] at ({lx+0.38:.2f},{yy+0.11:.2f}) {{Precio del tiempo, $r_f$}};")
    out.append(r"\end{tikzpicture}")
    escribir("b2_referencia", _cabecera("b2_referencia", "B2, «Zona del euro»: rendimiento a un mismo plazo de la deuda"
                                        " alemana y de la de otro Estado del euro; esquemática, sin escala")
             + "\n".join(out) + "\n")


if __name__ == "__main__":
    for f in (flujos, convergencia, precio_rendimiento, diferencial, balanza, tangente, convexidad, pesas_bala,
              convexidad_negativa, inmunizacion, brecha, variantes, liquidez, referencia):
        f()
