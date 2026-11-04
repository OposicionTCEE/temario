"""Figuras de la primera parte del anexo I del 3.B.24 (tanda A1: apartados I.1 a I.3). Escribe los .tikz en Img/.

Uso, desde la carpeta del tema:  python3 -B Code/figuras_anexo1.py
y después, para cada figura:   bash Code/generar_figura.sh anx_perfiles   (y lo mismo con las demás)

anx_perfiles: perfiles de pagos esquemáticos (con cupón, cupón cero, amortizable y perpetuo) en ocho periodos; las
  barras no están a escala (el cupón se dibuja más alto de lo que sería, para que se vea).
anx_convergencia: precio ex cupón en cada fecha de cupón de tres bonos a 10 años con N = 100 y r = 5 % constante,
  con cupones anuales del 8 %, 5 % y 2 %: valen hoy 123,17, 100 y 76,83, y 100 al vencimiento.
anx_precio_sucio: bono con prima (N = 100, c = 8 %, y = 5 %, 10 años, cupón anual) en sus tres primeros años:
  precio sucio P_k (1 + y)^tau y precio limpio P_k (1 + y)^tau - cN tau, con P_k el precio ex cupón en la fecha k.
anx_precio_rendimiento: precio de un bono a 10 años con c = 6 % y N = 100 para rendimientos entre -2 % y 16 %;
  P(0) = 160 (suma de los pagos), P(c) = 100 y un precio de mercado P_0 = 85, cuyo rendimiento y_0 se calcula.
anx_fuentes: reparto de la ganancia de un bono comprado a la par con cupón del 8 % pagadero por semestres y
  reinversión al 8 % (4 % por semestre), entre cupones e intereses de los intereses, a 5, 10, 20 y 30 años.
"""
import math
from pathlib import Path

IMG = Path(__file__).resolve().parent.parent / "Img"
MARGEN = r"\path ([yshift=1.5pt]current bounding box.north east) ([yshift=-1.5pt]current bounding box.south west);"


def escribir(nombre, tikz):
    """Escribe Img/<nombre>.tikz con 1,5 pt de margen arriba y abajo (como en el 3.B.23)."""
    (IMG / f"{nombre}.tikz").write_text(tikz.replace("\\end{tikzpicture}", MARGEN + "\n\\end{tikzpicture}"),
                                        encoding="utf-8")


def coords(pts):
    return " ".join(f"({x:.3f},{y:.3f})" for x, y in pts)


def precio(c, y, n, N=100.0):
    """Precio ex cupón de un bono con n cupones anuales pendientes, tasa del cupón c y rendimiento y."""
    return sum(c * N / (1 + y) ** t for t in range(1, n + 1)) + N / (1 + y) ** n


def tir(P, c, n, N=100.0):
    """Rendimiento al vencimiento por bisección (el precio decrece con el rendimiento)."""
    lo, hi = -0.5, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if precio(c, mid, n, N) > P:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- anx_perfiles ----------
def perfiles():
    # Los cuatro perfiles en una sola fila (15,5 x 3,8 cm), para que la figura quepa tras el párrafo que la comenta.
    dx, hN, hC, w = 0.38, 1.5, 0.28, 0.1   # cm por periodo, altura del nominal y del cupón, media anchura de barra
    claro, oscuro = "black!22", "black!62"
    paneles = [("Con cupón", 0.0), ("Cupón cero", 3.95), ("Amortizable", 7.9), ("Perpetuo", 11.85)]
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    for titulo, x0 in paneles:
        out.append(rf"\begin{{scope}}[xshift={x0}cm]")
        out.append(rf"\node[font=\footnotesize\bfseries, anchor=west] at (-0.15,2.15) {{{titulo}}};")
        fin = 3.6 if titulo == "Perpetuo" else 3.4
        out.append(rf"\draw[->] (-0.15,0) -- ({fin},0) node[below] {{$t$}};")
        out.append(r"\draw[->, thick] (0,0) -- (0,-0.6) node[below] {$P$};")
        out.append(r"\node[above left, inner sep=1pt] at (0,0) {$0$};")
        if titulo != "Perpetuo":
            out.append(rf"\draw ({8*dx:.2f},0.06) -- ({8*dx:.2f},-0.06) node[below] {{$T$}};")
        for t in range(1, 9):
            x = t * dx
            if titulo == "Con cupón":
                out.append(rf"\fill[{claro}] ({x-w:.3f},0) rectangle ({x+w:.3f},{hC});")
                if t == 8:
                    out.append(rf"\fill[{oscuro}] ({x-w:.3f},{hC}) rectangle ({x+w:.3f},{hC+hN});")
            elif titulo == "Cupón cero" and t == 8:
                out.append(rf"\fill[{oscuro}] ({x-w:.3f},0) rectangle ({x+w:.3f},{hN});")
            elif titulo == "Amortizable":
                amort = hN / 8
                interes = hC * (9 - t) / 8
                out.append(rf"\fill[{oscuro}] ({x-w:.3f},0) rectangle ({x+w:.3f},{amort:.3f});")
                out.append(rf"\fill[{claro}] ({x-w:.3f},{amort:.3f}) rectangle ({x+w:.3f},{amort+interes:.3f});")
            elif titulo == "Perpetuo":
                out.append(rf"\fill[{claro}] ({x-w:.3f},0) rectangle ({x+w:.3f},{hC});")
        if titulo == "Con cupón":
            out.append(rf"\node[above] at ({dx},{hC}) {{$cN$}};")
            out.append(rf"\node[left] at ({8*dx-w:.3f},{hC+hN/2}) {{$N$}};")
        elif titulo == "Cupón cero":
            out.append(rf"\node[left] at ({8*dx-w:.3f},{hN/2}) {{$N$}};")
        elif titulo == "Perpetuo":
            out.append(rf"\node[above] at ({dx},{hC}) {{$cN$}};")
            out.append(rf"\node at ({8*dx+0.32:.2f},{hC/2}) {{$\cdots$}};")
        out.append(r"\end{scope}")
    # leyenda común
    out.append(rf"\fill[{claro}] (4.6,-1.45) rectangle (4.9,-1.2); \node[anchor=west] at (4.95,-1.32) {{Intereses}};")
    out.append(rf"\fill[{oscuro}] (8.0,-1.45) rectangle (8.3,-1.2); \node[anchor=west] at (8.35,-1.32) {{Nominal}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_perfiles", "% Figura (Anexo I, I.1, «Promesa»): perfiles de pagos de cuatro bonos. Esquemática, sin escala.\n"
             "% Generar con: bash Code/generar_figura.sh anx_perfiles\n" + "\n".join(out) + "\n")


# ---------- anx_convergencia ----------
def convergencia():
    T, r = 10, 0.05
    sx, sy, base = 1.2, 0.075, 70.0        # cm por año, cm por unidad de precio, precio en el eje
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({T*sx+1.4},0);")
    out.append(rf"\node[anchor=north east] at ({T*sx+1.4},-0.05) {{Tiempo}};")
    out.append(r"\draw[->] (0,0) -- (0,4.9) node[above] {Precio};")
    yN = (100 - base) * sy
    out.append(rf"\draw[dashed, black!45] (0,{yN}) -- ({T*sx},{yN});")
    out.append(rf"\node[left] at (0,{yN}) {{$N$}};")
    out.append(r"\node[below] at (0,0) {$0$};")
    out.append(rf"\draw ({T*sx},0.06) -- ({T*sx},-0.06) node[below] {{$T$}};")
    estilos = {0.08: "very thick", 0.05: "very thick, black!55", 0.02: "very thick, densely dashed"}
    etiquetas = {0.08: r"$c>r$", 0.05: r"$c=r$", 0.02: r"$c<r$"}
    for c in (0.08, 0.05, 0.02):
        pts = [(t * sx, (precio(c, r, T - t) - base) * sy) for t in range(0, T + 1)]
        out.append(rf"\draw[{estilos[c]}] plot[smooth] coordinates {{{coords(pts)}}};")
        x1, y1 = pts[1]
        desplaz = {0.08: "above right", 0.05: "above", 0.02: "below right"}[c]
        out.append(rf"\node[{desplaz}] at ({x1:.3f},{y1:.3f}) {{{etiquetas[c]}}};")
    out.append(r"\end{tikzpicture}")
    cab = ("% Figura (Anexo I, I.2, «Par, prima y descuento»): convergencia a la par de tres bonos a 10 años con N = 100 y\n"
           "% r = 5 % constante; cupones anuales del 8 %, 5 % y 2 % (precios de hoy: "
           f"{precio(0.08, r, T):.2f}, {precio(0.05, r, T):.2f} y {precio(0.02, r, T):.2f}).\n"
           "% Generar con: bash Code/generar_figura.sh anx_convergencia\n")
    escribir("anx_convergencia", cab + "\n".join(out) + "\n")


# ---------- anx_precio_sucio ----------
def precio_sucio():
    N, c, y, T = 100.0, 0.08, 0.05, 10
    sx, sy, base = 4.0, 0.4, 116.0
    Pk = [precio(c, y, T - k) for k in range(0, 4)]
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(r"\draw[->] (0,0) -- (13.4,0);")
    out.append(r"\node[anchor=north east] at (13.4,-0.05) {Tiempo};")
    out.append(r"\draw[->] (0,0) -- (0,6.3) node[above] {Precio};")
    for k in range(0, 4):
        out.append(rf"\draw ({k*sx},0.06) -- ({k*sx},-0.06) node[below] {{${k}$}};")
    for k in range(0, 3):
        sucio = [((k + j / 40) * sx, (Pk[k] * (1 + y) ** (j / 40) - base) * sy) for j in range(0, 41)]
        limpio = [((k + j / 40) * sx, (Pk[k] * (1 + y) ** (j / 40) - c * N * j / 40 - base) * sy) for j in range(0, 41)]
        out.append(rf"\draw[very thick] plot coordinates {{{coords(sucio)}}};")
        out.append(rf"\draw[very thick, black!50] plot coordinates {{{coords(limpio)}}};")
        xa, ya = sucio[-1]
        yb = (Pk[k + 1] - base) * sy
        out.append(rf"\draw[densely dotted, thick] ({xa:.3f},{ya:.3f}) -- ({xa:.3f},{yb:.3f});")
        if k == 0:
            out.append(rf"\node[right] at ({xa:.3f},{(ya+yb)/2:.3f}) {{$cN$}};")
    # cupón corrido en tau = 0,75 del tercer periodo
    tau = 0.75
    xs = (2 + tau) * sx
    ys = (Pk[2] * (1 + y) ** tau - base) * sy
    yl = (Pk[2] * (1 + y) ** tau - c * N * tau - base) * sy
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=3pt, mirror}}] ({xs+0.12:.3f},{yl:.3f}) -- ({xs+0.12:.3f},{ys:.3f})"
               rf" node[midway, right=3pt] {{$cN\tau$}};")
    xt, yt = 0.55 * sx, (Pk[0] * (1 + y) ** 0.55 - base) * sy
    out.append(rf"\node[above left] at ({xt:.3f},{yt:.3f}) {{$P^{{\text{{sucio}}}}$}};")
    xt2, yt2 = 1.5 * sx, (Pk[1] * (1 + y) ** 0.5 - c * N * 0.5 - base) * sy
    out.append(rf"\node[below] at ({xt2:.3f},{yt2:.3f}) {{$P^{{\text{{limpio}}}}$}};")
    out.append(r"\end{tikzpicture}")
    cab = ("% Figura (Anexo I, I.2, «Entre cupones»): precio sucio y limpio de un bono con prima (N = 100, c = 8 %, y = 5 %,\n"
           f"% 10 años, cupón anual) en sus tres primeros años; precios ex cupón {', '.join(f'{p:.2f}' for p in Pk)}.\n"
           "% Generar con: bash Code/generar_figura.sh anx_precio_sucio\n")
    escribir("anx_precio_sucio", cab + "\n".join(out) + "\n")


# ---------- anx_precio_rendimiento ----------
def precio_rendimiento():
    c, T = 0.06, 10
    ymin, ymax = -0.02, 0.16
    sx, sy, base = 70.0, 0.035, 40.0       # cm por unidad de rendimiento (0,7 cm por punto), cm por unidad de precio
    X = lambda yy: (yy - ymin) * sx
    Y = lambda p: (p - base) * sy
    pts = [(X(ymin + j * (ymax - ymin) / 90), Y(precio(c, ymin + j * (ymax - ymin) / 90, T))) for j in range(0, 91)]
    P0 = 85.0
    y0 = tir(P0, c, T)
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({X(ymax)+0.5:.3f},0) node[below left] {{Rendimiento, $y$}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(205):.3f}) node[above] {{Precio, $P$}};")
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{coords(pts)}}};")
    # y = 0 y suma de los pagos
    out.append(rf"\draw[densely dotted] ({X(0):.3f},0) -- ({X(0):.3f},{Y(160):.3f}) -- (0,{Y(160):.3f});")
    out.append(rf"\node[below] at ({X(0):.3f},0) {{$0$}};")
    out.append(rf"\node[left] at (0,{Y(160):.3f}) {{$\textstyle\sum_t CF_t$}};")
    # par
    out.append(rf"\draw[densely dotted] ({X(c):.3f},0) -- ({X(c):.3f},{Y(100):.3f}) -- (0,{Y(100):.3f});")
    out.append(rf"\fill ({X(c):.3f},{Y(100):.3f}) circle (1.6pt);")
    out.append(rf"\node[below] at ({X(c):.3f},0) {{$c$}};")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$N$}};")
    # precio de mercado
    out.append(rf"\draw[dashed] (0,{Y(P0):.3f}) -- ({X(y0):.3f},{Y(P0):.3f}) -- ({X(y0):.3f},0);")
    out.append(rf"\fill ({X(y0):.3f},{Y(P0):.3f}) circle (1.6pt);")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[left] at (0,{Y(P0):.3f}) {{$P_0$}};")
    out.append(r"\end{tikzpicture}")
    cab = ("% Figura (Anexo I, I.3, «Rendimiento al vencimiento»): precio de un bono a 10 años con c = 6 % y N = 100 frente a su\n"
           f"% rendimiento (de -2 % a 16 %); P(-2 %) = {precio(c, -0.02, T):.1f}, P(0) = 160, P(c) = 100, P(16 %) = {precio(c, 0.16, T):.1f};\n"
           f"% con P_0 = 85, y_0 = {100*y0:.2f} %.\n"
           "% Generar con: bash Code/generar_figura.sh anx_precio_rendimiento\n")
    escribir("anx_precio_rendimiento", cab + "\n".join(out) + "\n")


# ---------- anx_fuentes ----------
def fuentes():
    filas = []
    for anos in (5, 10, 20, 30):
        vf = 1.04 ** (2 * anos)
        ganancia = vf - 1
        cupones = 0.04 * 2 * anos
        ii = ganancia - cupones
        filas.append((anos, cupones / ganancia, ii / ganancia))
    alto = 5.0
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\draw (0,0) -- (8.6,0);")
    out.append(rf"\draw (0,0) -- (0,{alto});")
    for v in (0, 50, 100):
        yv = alto * v / 100
        out.append(rf"\draw (0,{yv}) -- (-0.08,{yv}) node[left] {{${v}\,\%$}};")
    for i, (anos, sc, si) in enumerate(filas):
        x = 1.3 + 2.0 * i
        hc = alto * sc
        out.append(rf"\fill[black!18] ({x-0.6},0) rectangle ({x+0.6},{hc:.3f});")
        out.append(rf"\fill[black!62] ({x-0.6},{hc:.3f}) rectangle ({x+0.6},{alto});")
        pc = f"{100*sc:.1f}".replace(".", "{,}")
        pi = f"{100*si:.1f}".replace(".", "{,}")
        out.append(rf"\node at ({x},{hc/2:.3f}) {{${pc}\,\%$}};")
        out.append(rf"\node[text=white] at ({x},{(hc+alto)/2:.3f}) {{${pi}\,\%$}};")
        out.append(rf"\node[below] at ({x},0) {{${anos}$}};")
    out.append(r"\node[below] at (4.3,-0.45) {Vencimiento (años)};")
    out.append(rf"\fill[black!62] (9.0,3.6) rectangle (9.3,3.9); \node[anchor=west] at (9.35,3.75) {{Intereses de los intereses}};")
    out.append(rf"\fill[black!18] (9.0,3.0) rectangle (9.3,3.3); \node[anchor=west] at (9.35,3.15) {{Cupones}};")
    out.append(r"\end{tikzpicture}")
    cab = ("% Figura (Anexo I, I.3, «Condiciones»): reparto de la ganancia de un bono comprado a la par, cupón del 8 % semestral y\n"
           "% reinversión al 4 % por semestre: " + "; ".join(f"{a} años: cupones {100*sc:.1f} %, intereses de los intereses {100*si:.1f} %" for a, sc, si in filas) + ".\n"
           "% Generar con: bash Code/generar_figura.sh anx_fuentes\n")
    escribir("anx_fuentes", cab + "\n".join(out) + "\n")


# =====================  Tanda A2 (I.4 Crédito e I.5 Liquidez y otros diferenciales)  =====================
# anx_arbol_impago: bono que promete CF en un periodo; paga con probabilidad 1 - p y recupera (1 - l) CF si impaga.
# anx_diferencial_credito: rendimiento medio mensual de los bonos Baa de Moody's menos el del Tesoro de EE. UU. a 10 años
#   (FRED: BAA y GS10, abril de 1953 a la última observación), con las recesiones del NBER (FRED: USREC) sombreadas.
# anx_clientelas: rendimiento exigido frente a la horquilla con tres clientelas de horizontes H1 < H2 < H3 (AMIHUD y
#   MENDELSON, 1986): tramos de pendiente 1/H decreciente; esquemática.
# anx_descomposicion: rendimiento de un bono de empresa frente al soberano del mismo plazo; esquemática.
DATOS = Path(__file__).resolve().parent / "datos"


def serie(codigo):
    import csv
    filas = list(csv.reader((DATOS / f"fred_{codigo}.csv").open(encoding="utf-8")))[1:]
    return {d: float(v) for d, v in filas if v not in ("", ".")}


def arbol_impago():
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(r"\node (P) at (0,0) {$P$};")
    out.append(r"\node[anchor=west] (A) at (4.2,1.1) {$CF$};")
    out.append(r"\node[anchor=west] (B) at (4.2,-1.1) {$(1-\ell)\,CF$};")
    out.append(r"\draw[->, thick] (P.east) -- (A.west) node[midway, above, sloped] {$1-p$};")
    out.append(r"\draw[->, thick] (P.east) -- (B.west) node[midway, below, sloped] {$p$};")
    out.append(r"\node[anchor=west, text=black!60] at ($(A.east)+(0.15,0)$) {paga};")
    out.append(r"\node[anchor=west, text=black!60] at ($(B.east)+(0.15,0)$) {impaga};")
    out.append(r"\draw[black!40] (-0.3,-1.9) -- (6.6,-1.9);")
    out.append(r"\node[below] at (0,-1.9) {$t=0$};")
    out.append(r"\node[below] at (4.6,-1.9) {$t=1$};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_arbol_impago", "% Figura (Anexo I, I.4, «Pérdida esperada»): árbol de un periodo de un bono con riesgo de impago.\n"
             "% Generar con: bash Code/generar_figura.sh anx_arbol_impago\n" + "\n".join(out) + "\n")


def diferencial_credito():
    baa, gs, rec = serie("BAA"), serie("GS10"), serie("USREC")
    fechas = sorted(d for d in gs if d in baa)
    año = lambda d: int(d[:4]) + (int(d[5:7]) - 1) / 12
    pts = [(año(d), baa[d] - gs[d]) for d in fechas]
    # tramos de recesión dentro del periodo de la serie
    tramos, ini = [], None
    for d in sorted(rec):
        if d < fechas[0]:
            continue
        if rec[d] == 1 and ini is None:
            ini = año(d)
        if rec[d] == 0 and ini is not None:
            tramos.append((ini, año(d)))
            ini = None
    ymax = 6.6
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=15.2cm, height=5.6cm, axis lines=left, xmin=1953, xmax=2027, ymin=0, ymax=" + str(ymax) + ","
               r" xtick={1960,1970,1980,1990,2000,2010,2020}, ytick={0,1,2,3,4,5,6},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={},"
               r" tick label style={font=\scriptsize}, label style={font=\footnotesize},"
               r" ylabel={Puntos porcentuales}, enlarge x limits=false, clip=true]")
    for a, b in tramos:
        out.append(rf"\addplot[fill=black!12, draw=none] coordinates {{({a:.3f},0) ({a:.3f},{ymax}) ({b:.3f},{ymax}) ({b:.3f},0) ({a:.3f},0)}};")
    out.append(r"\addplot[line width=0.6pt, black, mark=none] coordinates {" + coords(pts) + "};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    media = sum(v for _, v in pts) / len(pts)
    mx = max(pts, key=lambda x: x[1])
    cab = ("% Figura (Anexo I, I.4, «Diferencial de crédito»): rendimiento medio mensual de los bonos Baa de Moody's menos el del\n"
           f"% Tesoro de EE. UU. a 10 años, {fechas[0][:7]} a {fechas[-1][:7]} (FRED: BAA, GS10); recesiones del NBER (USREC)\n"
           f"% sombreadas. Media {media:.2f} puntos; máximo {mx[1]:.2f} en {mx[0]:.2f}.\n"
           "% Generar con: bash Code/generar_figura.sh anx_diferencial_credito\n")
    escribir("anx_diferencial_credito", cab + "\n".join(out) + "\n")


def clientelas():
    y0 = 1.0
    tramos = [(0.0, 2.6, 0.62, r"$H_1$"), (2.6, 5.6, 0.30, r"$H_2$"), (5.6, 8.6, 0.12, r"$H_3$")]
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(r"\draw[->] (0,0) -- (9.4,0) node[below left] {Horquilla, $h$};")
    out.append(r"\draw[->] (0,0) -- (0,4.9) node[above] {Rendimiento exigido};")
    out.append(rf"\node[left] at (0,{y0}) {{$y^*$}};")
    y = y0
    for i, (a, b, m, et) in enumerate(tramos):
        yb = y + m * (b - a)
        out.append(rf"\draw[very thick] ({a},{y:.3f}) -- ({b},{yb:.3f});")
        if i < 2:   # prolongación: lo que exigiría esa clientela por bonos aún menos líquidos
            out.append(rf"\draw[dashed, black!45] ({b},{yb:.3f}) -- ({b+1.9},{yb + m*1.9:.3f});")
            out.append(rf"\draw[densely dotted, black!45] ({b},0) -- ({b},{yb:.3f});")
        xm, ym = (a + b) / 2, (y + yb) / 2
        out.append(rf"\node[below right, inner sep=2pt] at ({xm:.2f},{ym:.3f}) {{{et}}};")
        y = yb
    out.append(r"\end{tikzpicture}")
    escribir("anx_clientelas", "% Figura (Anexo I, I.5, «Liquidez»): rendimiento exigido frente a la horquilla con tres clientelas\n"
             "% (AMIHUD y MENDELSON, 1986): pendientes 1/H decrecientes; discontinuas, lo que exigiría cada clientela fuera de su tramo.\n"
             "% Generar con: bash Code/generar_figura.sh anx_clientelas\n" + "\n".join(out) + "\n")


def descomposicion():
    piezas = [("Precio del tiempo", 3.0, "black!62"), ("Pérdida esperada", 0.55, "black!40"),
              ("Prima por riesgo de impago", 0.8, "black!28"), ("Prima de liquidez", 0.5, "black!16"),
              ("Impuestos y opciones", 0.3, "black!7")]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\draw (-0.4,0) -- (6.2,0);")
    # soberano
    out.append(r"\fill[black!62] (0,0) rectangle (1.3,3.0);")
    out.append(r"\node[below] at (0.65,0) {Soberano};")
    # empresa
    y = 0.0
    for nombre, h, color in piezas:
        out.append(rf"\fill[{color}] (2.6,{y:.2f}) rectangle (3.9,{y+h:.2f});")
        out.append(rf"\draw[black!30, very thin] (3.9,{y+h/2:.3f}) -- (4.25,{y+h/2:.3f});")
        out.append(rf"\node[anchor=west, inner sep=1pt] at (4.3,{y+h/2:.3f}) {{{nombre}}};")
        y += h
    out.append(r"\node[below] at (3.25,0) {Empresa};")
    out.append(r"\draw[densely dotted] (1.3,3.0) -- (2.6,3.0);")
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt}}] (2.45,3.0) -- (2.45,{y:.2f}) node[midway, left=5pt] {{$s$}};")
    out.append(rf"\draw[decorate, decoration={{brace, amplitude=4pt, mirror}}] (-0.15,0) -- (-0.15,3.0) node[midway, left=5pt] {{$r_f$}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_descomposicion", "% Figura (Anexo I, I.5, «Descomposición»): rendimiento de un bono de empresa frente al soberano del\n"
             "% mismo plazo; esquemática, sin escala.\n% Generar con: bash Code/generar_figura.sh anx_descomposicion\n"
             + "\n".join(out) + "\n")


# =====================  Tanda A3 (I.6 Duración e I.7 Convexidad)  =====================
# Bono de referencia: 10 años, cupón anual del 6 %, rendimiento del 6 % (precio 100): D = 7,80, D* = 7,36, C = 69,7.
# anx_balanza: valor actual de cada pago (barras) y duración como punto de equilibrio.
# anx_tangente: precio frente a rendimiento (0 % a 14 %) y tangente en y0 = 6 % (pendiente -D* P).
# anx_duracion_vencimiento: duración de MACAULAY frente al vencimiento (1 a 100 años) con y = 6 % para cupones del 0 %,
#   2 %, 6 % y 10 %; asíntota (1 + y)/y = 17,67.
# anx_convexidad: curva, tangente y errores de la duración con cambios de +-3 puntos.
# anx_pesas_bala: bala = cupón cero a 10 años; pesas = cupones cero a 2 y 20 años con pesos 10/18 y 8/18 (misma duración
#   de MACAULAY, 10 años, y mismo valor, 100, con y0 = 6 %).
# anx_convexidad_negativa: bono sin opción (el de referencia) y amortizable esquemático, mínimo suave del precio sin opción
#   y del precio de rescate K = 104 (P_am = -ln(e^{-kP} + e^{-kK})/k, k = 0,12).
def _precio_ref(y, c=0.06, T=10):
    return precio(c, y, T)


def balanza():
    c, y, T = 0.06, 0.06, 10
    vals = [(t, (c * 100 + (100 if t == T else 0)) / (1 + y) ** t) for t in range(1, T + 1)]
    P0 = sum(v for _, v in vals)
    D = sum(t * v for t, v in vals) / P0
    esc = 4.4 / max(v for _, v in vals)
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    for t, v in vals:
        out.append(rf"\fill[black!45] ({t-0.22:.2f},0) rectangle ({t+0.22:.2f},{v*esc:.3f});")
    out.append(r"\draw[line width=1.6pt] (0.4,0) -- (10.6,0);")
    out.append(rf"\fill[black] ({D:.3f},-0.04) -- ({D-0.28:.3f},-0.55) -- ({D+0.28:.3f},-0.55) -- cycle;")
    out.append(rf"\node[below] at ({D:.3f},-0.55) {{$D$}};")
    out.append(r"\node[below] at (1,-0.05) {$1$};")
    out.append(r"\node[below] at (10,-0.05) {$T$};")
    out.append(r"\draw[->] (10.6,0) -- (11.2,0) node[right] {$t$};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_balanza", f"% Figura (Anexo I, I.6, «Duración de MACAULAY»): valor actual de los pagos del bono a 10 años al 6 % con y = 6 %;\n"
             f"% D = {D:.2f} años. Generar con: bash Code/generar_figura.sh anx_balanza\n" + "\n".join(out) + "\n")


def _ejes_precio(out, ymin, ymax, base, sx, sy, etx="Rendimiento, $y$", ety="Precio, $P$", top=180):
    X = lambda yy: (yy - ymin) * sx
    Y = lambda p: (p - base) * sy
    out.append(rf"\draw[->] (0,0) -- ({X(ymax)+0.5:.3f},0) node[below left] {{{etx}}};")
    out.append(rf"\draw[->] (0,0) -- (0,{Y(top):.3f}) node[above] {{{ety}}};")
    return X, Y


def tangente():
    ymin, ymax, base, sx, sy = 0.0, 0.14, 40.0, 70.0, 0.04
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes_precio(out, ymin, ymax, base, sx, sy)
    pts = [(X(ymin + j * (ymax - ymin) / 70), Y(_precio_ref(ymin + j * (ymax - ymin) / 70))) for j in range(0, 71)]
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{coords(pts)}}};")
    y0, P0 = 0.06, _precio_ref(0.06)
    Ds = sum(t * (6 + (100 if t == 10 else 0)) / 1.06 ** (t + 1) for t in range(1, 11)) / P0
    tg = lambda yy: P0 * (1 - Ds * (yy - y0))
    out.append(rf"\draw[thick, dashed] ({X(0.01):.3f},{Y(tg(0.01)):.3f}) -- ({X(0.125):.3f},{Y(tg(0.125)):.3f});")
    out.append(rf"\fill ({X(y0):.3f},{Y(P0):.3f}) circle (1.7pt);")
    out.append(rf"\draw[densely dotted] ({X(y0):.3f},0) -- ({X(y0):.3f},{Y(P0):.3f}) -- (0,{Y(P0):.3f});")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[left] at (0,{Y(P0):.3f}) {{$P_0$}};")
    out.append(rf"\node[anchor=north east] at ({X(0.118):.3f},{Y(tg(0.118))-0.08:.3f}) {{pendiente $-D^*P_0$}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_tangente", "% Figura (Anexo I, I.6, «Duración modificada»): precio del bono de referencia y su tangente en y0 = 6 %.\n"
             "% Generar con: bash Code/generar_figura.sh anx_tangente\n" + "\n".join(out) + "\n")


def duracion_vencimiento():
    y = 0.06
    def D(c, T):
        p = precio(c, y, T)
        return sum(t * (c * 100 + (100 if t == T else 0)) / (1 + y) ** t for t in range(1, T + 1)) / p
    curvas = {0.02: [], 0.06: [], 0.10: []}
    for c in curvas:
        curvas[c] = [(T, D(c, T)) for T in list(range(1, 30)) + list(range(30, 101, 2))]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=13.5cm, height=6.4cm, axis lines=left, xmin=0, xmax=100, ymin=0, ymax=25,"
               r" xtick={0,20,40,60,80,100}, ytick={0,5,10,15,20,25}, /pgf/number format/use comma,"
               r" tick label style={font=\scriptsize}, label style={font=\footnotesize},"
               r" xlabel={Vencimiento, $T$ (años)}, ylabel={Duración, $D$ (años)}, clip=true]")
    out.append(r"\addplot[thick, black!50, densely dotted, domain=0:25] {x};")
    out.append(r"\addplot[thin, dashed, black, domain=0:100] {17.6667};")
    estilos = {0.02: "very thick", 0.06: "very thick, black!55", 0.10: "very thick, densely dashed"}
    for c, pts in curvas.items():
        out.append(rf"\addplot[{estilos[c]}, mark=none] coordinates {{{coords(pts)}}};")
    out.append(r"\node[anchor=south east, font=\footnotesize] at (axis cs:24,22.5) {$c=0$};")
    out.append(r"\node[anchor=south, font=\footnotesize] at (axis cs:46,20.2) {$c<y$};")
    out.append(r"\node[anchor=north, font=\footnotesize] at (axis cs:70,16.6) {$c\geq y$};")
    out.append(r"\node[anchor=south west, font=\footnotesize] at (axis cs:1,17.8) {$(1+y)/y$};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    mx = max(curvas[0.02], key=lambda x: x[1])
    escribir("anx_duracion_vencimiento", "% Figura (Anexo I, I.6, «Duración modificada»): duración frente al vencimiento con y = 6 % para\n"
             f"% cupones del 0 % (D = T), 2 %, 6 % y 10 %; con el 2 %, máximo de {mx[1]:.2f} años en T = {mx[0]}; asíntota 17,67.\n"
             "% Generar con: bash Code/generar_figura.sh anx_duracion_vencimiento\n" + "\n".join(out) + "\n")


def convexidad():
    ymin, ymax, base, sx, sy = 0.0, 0.14, 40.0, 70.0, 0.04
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes_precio(out, ymin, ymax, base, sx, sy)
    pts = [(X(ymin + j * (ymax - ymin) / 70), Y(_precio_ref(ymin + j * (ymax - ymin) / 70))) for j in range(0, 71)]
    out.append(rf"\draw[very thick] plot[smooth] coordinates {{{coords(pts)}}};")
    y0, P0 = 0.06, _precio_ref(0.06)
    Ds = sum(t * (6 + (100 if t == 10 else 0)) / 1.06 ** (t + 1) for t in range(1, 11)) / P0
    tg = lambda yy: P0 * (1 - Ds * (yy - y0))
    out.append(rf"\draw[thick, dashed] ({X(0.01):.3f},{Y(tg(0.01)):.3f}) -- ({X(0.11):.3f},{Y(tg(0.11)):.3f});")
    out.append(rf"\fill ({X(y0):.3f},{Y(P0):.3f}) circle (1.7pt);")
    for dy in (-0.05, 0.05):
        yy = y0 + dy
        out.append(rf"\draw[densely dotted] ({X(yy):.3f},0) -- ({X(yy):.3f},{Y(_precio_ref(yy)):.3f});")
        out.append(rf"\draw[line width=1.6pt, black!55] ({X(yy):.3f},{Y(tg(yy)):.3f}) -- ({X(yy):.3f},{Y(_precio_ref(yy)):.3f});")
    out.append(rf"\node[anchor=north west] at ({X(0.11)+0.05:.3f},{Y(tg(0.11))-0.05:.3f}) {{$\approx\tfrac12\,C\,(\Delta y)^2P_0$}};")
    out.append(rf"\node[below] at ({X(0.01):.3f},0) {{$y_0-\Delta y$}};")
    out.append(rf"\node[below] at ({X(y0):.3f},0) {{$y_0$}};")
    out.append(rf"\node[below] at ({X(0.11):.3f},0) {{$y_0+\Delta y$}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_convexidad", "% Figura (Anexo I, I.7, «Segundo orden»): curva de precios del bono de referencia, tangente en y0 = 6 % y\n"
             "% errores de la duración (segmentos grises) con cambios de 5 puntos. Generar con: bash Code/generar_figura.sh anx_convexidad\n"
             + "\n".join(out) + "\n")


def pesas_bala():
    ymin, ymax, base, sx, sy = 0.0, 0.14, 40.0, 70.0, 0.03
    w = 10 / 18
    bala = lambda yy: 100 * (1.06 / (1 + yy)) ** 10
    pesas = lambda yy: 100 * (w * (1.06 / (1 + yy)) ** 2 + (1 - w) * (1.06 / (1 + yy)) ** 20)
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes_precio(out, ymin, ymax, base, sx, sy, top=215)
    for f, est in ((pesas, "very thick"), (bala, "very thick, black!50")):
        pts = [(X(ymin + j * (ymax - ymin) / 70), Y(f(ymin + j * (ymax - ymin) / 70))) for j in range(0, 71)]
        out.append(rf"\draw[{est}] plot[smooth] coordinates {{{coords(pts)}}};")
    out.append(rf"\fill ({X(0.06):.3f},{Y(100):.3f}) circle (1.7pt);")
    out.append(rf"\draw[densely dotted] ({X(0.06):.3f},0) -- ({X(0.06):.3f},{Y(100):.3f}) -- (0,{Y(100):.3f});")
    out.append(rf"\node[below] at ({X(0.06):.3f},0) {{$y_0$}};")
    out.append(rf"\node[left] at (0,{Y(100):.3f}) {{$P_0$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.005):.3f},{Y(pesas(0.005)):.3f}) {{Pesas}};")
    out.append(rf"\node[anchor=north east] at ({X(0.012):.3f},{Y(bala(0.012))-0.05:.3f}) {{Bala}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_pesas_bala", "% Figura (Anexo I, I.7, «Determinantes»): valor de una cartera en bala (cupón cero a 10 años) y otra en\n"
             f"% pesas (cupones cero a 2 y 20 años, pesos {w:.4f} y {1-w:.4f}) con el mismo valor y la misma duración en y0 = 6 %.\n"
             f"% Valores: y = 0 %: pesas {pesas(0):.1f}, bala {bala(0):.1f}; y = 14 %: pesas {pesas(0.14):.1f}, bala {bala(0.14):.1f}.\n"
             "% Generar con: bash Code/generar_figura.sh anx_pesas_bala\n" + "\n".join(out) + "\n")


def convexidad_negativa():
    ymin, ymax, base, sx, sy = 0.01, 0.13, 40.0, 75.0, 0.045
    K, k = 104.0, 0.12
    amort = lambda yy: -math.log(math.exp(-k * _precio_ref(yy)) + math.exp(-k * K)) / k
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    X, Y = _ejes_precio(out, ymin, ymax, base, sx, sy, top=155)
    for f, est in ((_precio_ref, "very thick, black!45"), (amort, "very thick")):
        pts = [(X(ymin + j * (ymax - ymin) / 70), Y(f(ymin + j * (ymax - ymin) / 70))) for j in range(0, 71)]
        out.append(rf"\draw[{est}] plot[smooth] coordinates {{{coords(pts)}}};")
    out.append(rf"\draw[dashed] (0,{Y(K):.3f}) -- ({X(ymax):.3f},{Y(K):.3f});")
    out.append(rf"\node[left] at (0,{Y(K):.3f}) {{$K$}};")
    out.append(rf"\node[anchor=south west] at ({X(0.016):.3f},{Y(_precio_ref(0.016)):.3f}) {{Sin opción}};")
    out.append(rf"\node[anchor=north east] at ({X(0.03):.3f},{Y(amort(0.03))-0.08:.3f}) {{Amortizable}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_convexidad_negativa", "% Figura (Anexo I, I.7, «Convexidad negativa»): bono sin opción (el de referencia) y bono amortizable\n"
             "% esquemático con precio de rescate K = 104 (mínimo suave, k = 0,12). Generar con: bash Code/generar_figura.sh anx_convexidad_negativa\n"
             + "\n".join(out) + "\n")


# =====================  Tanda A4 (I.8 Gestión de carteras)  =====================
# anx_inmunizacion: rentabilidad realizada anual a cada horizonte H (2 a 20 años) del bono de referencia comprado a la par
#   (10 años, cupón del 6 %) si, justo después de la compra, el tipo pasa al 4 %, se queda en el 6 % o sube al 8 % para
#   siempre; cupones reinvertidos a ese tipo y venta en H (o reinversión del nominal desde el año 10). Con H = D = 7,80,
#   6,02 % en los dos escenarios extremos.
# anx_redington: excedente A - L de un pasivo cupón cero a 10 años (valor 100 con el 6 %) cubierto con (a) cupones cero a
#   5 y 15 años a partes iguales (misma duración, más dispersión) y (b) un cupón cero a 5 años (duración menor).
# anx_brecha: valor del capital de un banco (activo a 6 años, valor 100; pasivo a 1 año, valor 90) y de un fondo de
#   pensiones (activo a 8 años, 100; pasivo a 20 años, 90), en cupones cero, con y0 = 5 %.
def _rr(H, y1):
    W = 0.0
    for t in range(1, 11):
        cf = 6 + (100 if t == 10 else 0)
        W += cf * (1 + y1) ** (H - t)      # si t > H, es el valor actual en H del pago pendiente
    return (W / 100) ** (1 / H) - 1


def inmunizacion():
    Hs = [2 + 0.25 * j for j in range(0, 73)]
    series = {y1: [(H, 100 * _rr(H, y1)) for H in Hs] for y1 in (0.04, 0.06, 0.08)}
    lo = min(v for s in series.values() for _, v in s)
    hi = max(v for s in series.values() for _, v in s)
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=13cm, height=6.3cm, axis lines=left, xmin=2, xmax=20, ymin={math.floor(lo)}, ymax={math.ceil(hi)},"
               r" xtick={2,5,7.8,10,15,20}, xticklabels={$2$,$5$,$D$,$10$,$15$,$20$}, /pgf/number format/use comma,"
               r" tick label style={font=\scriptsize}, label style={font=\footnotesize},"
               r" xlabel={Horizonte, $H$ (años)}, ylabel={Rentabilidad realizada (\%)}, clip=false]")
    est = {0.04: "very thick", 0.06: "thick, black!45", 0.08: "very thick, densely dashed"}
    for y1, pts in series.items():
        out.append(rf"\addplot[{est[y1]}, mark=none] coordinates {{{coords(pts)}}};")
    out.append(rf"\draw[densely dotted] (axis cs:7.802,{math.floor(lo)}) -- (axis cs:7.802,{math.ceil(hi)});")
    out.append(r"\node[anchor=west, font=\footnotesize] at (axis cs:20.2,%.3f) {$y_1<y_0$};" % (100 * _rr(20, 0.04)))
    out.append(r"\node[anchor=west, font=\footnotesize] at (axis cs:20.2,6) {$y_1=y_0$};")
    out.append(r"\node[anchor=west, font=\footnotesize] at (axis cs:20.2,%.3f) {$y_1>y_0$};" % (100 * _rr(20, 0.08)))
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_inmunizacion", "% Figura (Anexo I, I.8, «Inmunización»): rentabilidad realizada a cada horizonte del bono de referencia\n"
             f"% tras un cambio inmediato y permanente del tipo al 4 %, 6 % u 8 %; con H = D, {100*_rr(7.802,0.04):.3f} % y {100*_rr(7.802,0.08):.3f} %.\n"
             "% Generar con: bash Code/generar_figura.sh anx_inmunizacion\n" + "\n".join(out) + "\n")


def redington():
    f = lambda yy, t: (1.06 / (1 + yy)) ** t
    L = lambda yy: 100 * f(yy, 10)
    A1 = lambda yy: 50 * f(yy, 5) + 50 * f(yy, 15)
    A2 = lambda yy: 100 * f(yy, 5)
    ys = [0.02 + 0.001 * j for j in range(0, 81)]
    s1 = [(100 * yy, A1(yy) - L(yy)) for yy in ys]
    s2 = [(100 * yy, A2(yy) - L(yy)) for yy in ys]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12cm, height=6.3cm, axis lines=middle, xmin=2, xmax=10.4, ymin=-28, ymax=18,"
               r" xtick={6}, xticklabels={$y_0$}, ytick={0}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={$y$}, ylabel={Excedente, $A-L$},"
               r" x label style={anchor=west}, y label style={anchor=south}, clip=false]")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords(s1)}}};")
    out.append(rf"\addplot[very thick, black!45, mark=none] coordinates {{{coords(s2)}}};")
    out.append(r"\node[anchor=south, font=\footnotesize] at (axis cs:3.6,3.2) {$D_A=D_L$, $M_A^2>M_L^2$};")
    out.append(r"\node[anchor=north west, font=\footnotesize] at (axis cs:2.4,-20) {$D_A<D_L$};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_redington", "% Figura (Anexo I, I.8, «Activos y pasivos»): excedente de dos carteras frente a un pasivo cupón cero a 10\n"
             f"% años; con y = 2 % y 10 %: inmunizada {A1(0.02)-L(0.02):.2f} y {A1(0.10)-L(0.10):.2f}; desajustada {A2(0.02)-L(0.02):.2f} y {A2(0.10)-L(0.10):.2f}.\n"
             "% Generar con: bash Code/generar_figura.sh anx_redington\n" + "\n".join(out) + "\n")


def brecha():
    g = lambda yy, t: (1.05 / (1 + yy)) ** t
    banco = lambda yy: 100 * g(yy, 6) - 90 * g(yy, 1)
    fondo = lambda yy: 100 * g(yy, 8) - 90 * g(yy, 20)
    ys = [0.01 + 0.001 * j for j in range(0, 81)]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12cm, height=6.6cm, axis lines=middle, xmin=1, xmax=9.4, ymin=-62, ymax=40,"
               r" xtick={5}, xticklabels={$y_0$}, ytick={0}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={$y$}, ylabel={Capital, $A-L$},"
               r" x label style={anchor=west}, y label style={anchor=south}, clip=true]")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords([(100*yy, banco(yy)) for yy in ys])}}};")
    out.append(rf"\addplot[very thick, densely dashed, mark=none] coordinates {{{coords([(100*yy, fondo(yy)) for yy in ys])}}};")
    out.append(r"\node[anchor=north east, font=\footnotesize] at (axis cs:9.3,-9) {Banco: $D_A>D_L$};")
    out.append(r"\node[anchor=south east, font=\footnotesize] at (axis cs:7.0,28) {Fondo de pensiones: $D_A<D_L$};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_brecha", "% Figura (Anexo I, I.8, «Balances»): valor del capital frente al tipo de interés de un banco (activo cupón cero\n"
             f"% a 6 años, 100; pasivo a 1 año, 90) y de un fondo de pensiones (activo a 8 años, 100; pasivo a 20 años, 90), y0 = 5 %;\n"
             f"% banco: {banco(0.01):.1f} con el 1 % y {banco(0.09):.1f} con el 9 %; fondo: {fondo(0.01):.1f} y {fondo(0.09):.1f}.\n"
             "% Generar con: bash Code/generar_figura.sh anx_brecha\n" + "\n".join(out) + "\n")


# =====================  Tanda A5 (I.9 Curvas, I.10 Estimación, I.11 Movimientos)  =====================
# anx_curvas: curvas al contado, a plazo (préstamo de un año que empieza en cada plazo) y par de una ETTI de
#   NELSON-SIEGEL con beta0 = 5, beta1 = -4, beta2 = 1 y tau = 3, todos los tipos en capitalización anual; par con
#   cupones anuales: c(T) = (1 - B(T)) / sum B(t). Esquemática.
# anx_nelson_siegel: cargas del nivel (1), la pendiente ((1 - e^{-m/tau})/(m/tau)) y la curvatura (la anterior menos
#   e^{-m/tau}) con tau = 2,5.
# anx_curvas_eeuu: rendimientos medios mensuales del Tesoro de EE. UU. (FRED: GS1M a GS30) en dic. 2006, dic. 2010,
#   jun. 2023 y oct. 2026; eje del plazo logarítmico.
# anx_componentes: cargas de los tres primeros componentes principales de las variaciones mensuales de GS3M, GS6M, GS1,
#   GS2, GS3, GS5, GS7 y GS10 (1982-2026), con la parte de la varianza que explica cada uno.
NS = dict(b0=5.0, b1=-3.0, b2=2.0, tau=2.5)


def _etiquetas(x_fin, x_rot, items, sep):
    """Rótulos al final de varias curvas que convergen: separa sus alturas al menos sep (unidades del eje) y une cada
    rótulo con el final de su curva con una línea guía fina. items = [(y_final, texto)]."""
    orden = sorted(items, key=lambda it: it[0])
    pos = [y for y, _ in orden]
    for _ in range(50):
        for i in range(1, len(pos)):
            if pos[i] - pos[i - 1] < sep:
                medio = (pos[i] + pos[i - 1]) / 2
                pos[i - 1], pos[i] = medio - sep / 2, medio + sep / 2
    out = []
    for (y, texto), yr in zip(orden, pos):
        out.append(rf"\draw[black!35, very thin] (axis cs:{x_fin},{y:.3f}) -- (axis cs:{x_rot},{yr:.3f});")
        out.append(rf"\node[anchor=west, font=\footnotesize, inner sep=1.5pt] at (axis cs:{x_rot},{yr:.3f}) {{{texto}}};")
    return out


def _ns_spot(m, b0=NS["b0"], b1=NS["b1"], b2=NS["b2"], tau=NS["tau"]):
    x = m / tau
    l1 = (1 - math.exp(-x)) / x
    return b0 + b1 * l1 + b2 * (l1 - math.exp(-x))


def _ns_fwd(m, b0=NS["b0"], b1=NS["b1"], b2=NS["b2"], tau=NS["tau"]):
    x = m / tau
    return b0 + b1 * math.exp(-x) + b2 * x * math.exp(-x)


def curvas():
    # Curva propia de la figura (más pendiente que la de NS por defecto, para que se distingan las tres) y todos los tipos
    # en capitalización anual: contado (1 + r)^m = e^{r_c m}, a plazo de un año en m y par con cupones anuales.
    p = dict(b0=5.0, b1=-4.0, b2=1.0, tau=3.0)
    rc = lambda m: _ns_spot(m, **p) / 100
    B = lambda t: math.exp(-rc(t) * t)
    ms = [0.25 * j for j in range(1, 81)]
    contado = [(m, 100 * (math.exp(rc(m)) - 1)) for m in ms]
    plazo = [(m, 100 * (B(m) / B(m + 1) - 1)) for m in ms]
    par = [(T, 100 * (1 - B(T)) / sum(B(t) for t in range(1, T + 1))) for T in range(1, 21)]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6.4cm, axis lines=left, xmin=0, xmax=20, ymin=0.5, ymax=6.2,"
               r" xtick={0,20}, xticklabels={$0$,$T$}, ytick=\empty, label style={font=\footnotesize},"
               r" xlabel={Plazo}, ylabel={Tipo}, clip=false]")
    out.append(rf"\addplot[very thick, black!45, mark=none] coordinates {{{coords(plazo)}}};")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords(contado)}}};")
    out.append(rf"\addplot[very thick, densely dashed, mark=none] coordinates {{{coords(par)}}};")
    out += _etiquetas(20, 21.2, [(plazo[-1][1], "a plazo"), (contado[-1][1], "al contado"), (par[-1][1], "par")], 0.42)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_curvas", "% Figura (Anexo I, I.9, «Tipos par»): curvas al contado, a plazo (un año) y par de una ETTI de NELSON-SIEGEL\n"
             f"% (beta0 = 5, beta1 = -4, beta2 = 1, tau = 3), tipos anuales; a 20 años: contado {contado[-1][1]:.2f}, plazo {plazo[-1][1]:.2f},"
             f" par {par[-1][1]:.2f}.\n% Generar con: bash Code/generar_figura.sh anx_curvas\n" + "\n".join(out) + "\n")


def nelson_siegel():
    tau = NS["tau"]
    ms = [0.05 + 0.25 * j for j in range(0, 120)]
    l1 = lambda m: (1 - math.exp(-m / tau)) / (m / tau)
    l2 = lambda m: l1(m) - math.exp(-m / tau)
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6cm, axis lines=left, xmin=0, xmax=30, ymin=0, ymax=1.15,"
               r" xtick={0,10,20,30}, ytick={0,0.5,1}, /pgf/number format/use comma, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={Plazo, $n$ (años)}, ylabel={Carga}, clip=false]")
    out.append(r"\addplot[very thick, black!45, mark=none, domain=0:30] {1};")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords([(m, l1(m)) for m in ms])}}};")
    out.append(rf"\addplot[very thick, densely dashed, mark=none] coordinates {{{coords([(m, l2(m)) for m in ms])}}};")
    out += _etiquetas(30, 31.2, [(1.0, r"nivel, $\beta_0$"), (l1(30), r"pendiente, $\beta_1$"),
                                 (l2(30), r"curvatura, $\beta_2$")], 0.12)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_nelson_siegel", "% Figura (Anexo I, I.10, «Modelos paramétricos»): cargas de los tres factores de NELSON-SIEGEL con tau = 2,5.\n"
             "% Generar con: bash Code/generar_figura.sh anx_nelson_siegel\n" + "\n".join(out) + "\n")


def _fred_mensual(codigo):
    return {d[:7]: v for d, v in serie(codigo).items()}


def curvas_eeuu():
    plazos = [("GS1M", 1 / 12), ("GS3M", 0.25), ("GS6M", 0.5), ("GS1", 1), ("GS2", 2), ("GS3", 3), ("GS5", 5), ("GS7", 7),
              ("GS10", 10), ("GS20", 20), ("GS30", 30)]
    datos = {c: _fred_mensual(c) for c, _ in plazos}
    fechas = [("2006-12", "dic. 2006", "thick, black!45"), ("2010-12", "dic. 2010", "very thick"),
              ("2023-06", "jun. 2023", "very thick, densely dashed"), ("2026-10", "oct. 2026", "very thick, black!70, densely dotted")]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=13cm, height=6.6cm, axis lines=left, xmode=log, xmin=0.08, xmax=30, ymin=0, ymax=6,"
               r" xtick={0.0833,0.25,0.5,1,2,5,10,30}, xticklabels={$1$ m,$3$ m,$6$ m,$1$,$2$,$5$,$10$,$30$},"
               r" ytick={0,1,2,3,4,5,6}, /pgf/number format/use comma, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={Plazo (años; escala logarítmica)}, ylabel={Rendimiento (\%)}, clip=false]")
    finales = []
    for f, et, est in fechas:
        pts = [(m, datos[c][f]) for c, m in plazos if f in datos[c]]
        out.append(rf"\addplot[{est}, mark=*, mark size=0.9pt] coordinates {{{coords(pts)}}};")
        finales.append((pts[-1][1], et))
    out += _etiquetas(30, 38, finales, 0.38)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    resumen = "; ".join(f"{et}: {datos['GS3M'][f]:.2f} a 3 meses y {datos['GS10'][f]:.2f} a 10 años" for f, et, _ in fechas)
    escribir("anx_curvas_eeuu", "% Figura (Anexo I, I.11, «Hechos»): curvas del Tesoro de EE. UU. (medias mensuales, FRED) en cuatro fechas;\n"
             f"% {resumen}.\n% Generar con: bash Code/generar_figura.sh anx_curvas_eeuu\n" + "\n".join(out) + "\n")


def componentes():
    import numpy as np
    plazos = [("GS3M", 0.25), ("GS6M", 0.5), ("GS1", 1), ("GS2", 2), ("GS3", 3), ("GS5", 5), ("GS7", 7), ("GS10", 10)]
    datos = {c: _fred_mensual(c) for c, _ in plazos}
    fechas = sorted(f for f in set.intersection(*[set(datos[c]) for c, _ in plazos]) if f >= "1982-01")
    X = np.array([[datos[c][f] for c, _ in plazos] for f in fechas])
    w, v = np.linalg.eigh(np.cov(np.diff(X, axis=0), rowvar=False))
    orden = np.argsort(w)[::-1]
    w, v = w[orden], v[:, orden]
    cuota = 100 * w / w.sum()
    # signos: nivel positivo; pendiente creciente con el plazo; curvatura positiva en los extremos
    if v[:, 0].sum() < 0: v[:, 0] *= -1
    if v[-1, 1] < v[0, 1]: v[:, 1] *= -1
    if v[0, 2] < 0: v[:, 2] *= -1
    nombres = ["Nivel", "Pendiente", "Curvatura"]
    est = ["very thick", "very thick, densely dashed", "thick, black!50"]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6.4cm, axis lines=left, xmode=log, xmin=0.22, xmax=10, ymin=-0.7, ymax=0.7,"
               r" xtick={0.25,0.5,1,2,3,5,7,10}, xticklabels={$3$ m,$6$ m,$1$,$2$,$3$,$5$,$7$,$10$},"
               r" ytick={-0.5,0,0.5}, /pgf/number format/use comma, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={Plazo (años; escala logarítmica)}, ylabel={Carga}, clip=false]")
    out.append(r"\draw[black!30] (axis cs:0.22,0) -- (axis cs:10,0);")
    finales = []
    for k in range(3):
        pts = [(m, float(v[i, k])) for i, (_, m) in enumerate(plazos)]
        out.append(rf"\addplot[{est[k]}, mark=*, mark size=0.9pt] coordinates {{{coords(pts)}}};")
        c = f"{cuota[k]:.1f}".replace(".", "{,}")
        finales.append((pts[-1][1], rf"{nombres[k]} (${c}\%$)"))
    out += _etiquetas(10, 12.5, finales, 0.13)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_componentes", "% Figura (Anexo I, I.11, «Factores»): cargas de los tres primeros componentes principales de las variaciones\n"
             f"% mensuales de los rendimientos del Tesoro de EE. UU. de 3 meses a 10 años, {fechas[0]} a {fechas[-1]} ({len(fechas)-1} meses);\n"
             f"% varianza explicada: {cuota[0]:.1f} %, {cuota[1]:.1f} % y {cuota[2]:.1f} % (acumulada {cuota[:3].sum():.1f} %).\n"
             "% Generar con: bash Code/generar_figura.sh anx_componentes\n" + "\n".join(out) + "\n")


# =====================  Tanda A6 (I.12 Expectativas, I.13 Primas, I.14 Modelos)  =====================
# anx_expectativas: tres sendas del tipo a un año esperado, E[i_k] = ib + (i0 - ib) e^{-0,35 k} (sube: i0 = 2,
#   ib = 5,5; constante: 3,8; baja: i0 = 6, ib = 2,5), y las curvas al contado de la hipótesis pura de las
#   expectativas, media de la senda (capitalización continua): r_n = ib + (i0 - ib)(1 - e^{-0,35 n})/(0,35 n). Esquemática.
# anx_plazo_realizado: tipo a plazo a un año dentro de un año, 2 y(2) - y(1) con los tipos continuos de KIM y WRIGHT
#   (FRED: THREEFY1 y THREEFY2, medias mensuales), frente al tipo a un año observado doce meses después, ambos en la
#   fecha a la que se refiere la previsión; recesiones del NBER (USREC).
# anx_prima: tipo corto esperado constante (4 %) y curvas con prima por plazo positiva, nula y negativa,
#   phi_n = 1,4 (1 - e^{-n/5}) y -1,0 (1 - e^{-n/5}). Esquemática.
# anx_prima_kw: tipo a 10 años de KIM y WRIGHT (THREEFY10), su prima por plazo (THREEFYTP10) y su diferencia, la media
#   de los tipos cortos esperados; medias mensuales desde 1990; recesiones del NBER.
# anx_vasicek: curvas de VASICEK sin prima de riesgo con ib = 4,5 %, kappa = 0,25 y sigma = 2 %, para i = 1,5 %, 4,5 %
#   y 7,5 %: r_n = r_inf + (i - r_inf) b_n + sigma^2 n b_n^2 / (4 kappa), b_n = (1 - e^{-kappa n})/(kappa n),
#   r_inf = ib - sigma^2/(2 kappa^2) = 4,18 %.
# anx_sombra: tipo efectivo de los fondos federales y tipo sombra de WU y XIA (Banco de la Reserva Federal de Atlanta),
#   datos de fin de mes, 2007-01 a 2022-02; recesiones del NBER.
def _anio(d):
    return int(d[:4]) + (int(d[5:7]) - 1) / 12


def _media_mensual(codigo):
    acc = {}
    for d, v in serie(codigo).items():
        acc.setdefault(d[:7], []).append(v)
    return {m: sum(x) / len(x) for m, x in acc.items()}


def _mas_meses(m, k):
    t = int(m[:4]) * 12 + int(m[5:7]) - 1 + k
    return f"{t // 12}-{t % 12 + 1:02d}"


def _bandas_recesion(desde, hasta, ymin, ymax):
    rec = serie("USREC")
    tramos, ini = [], None
    for d in sorted(rec):
        a = _anio(d)
        if a < desde or a > hasta:
            continue
        if rec[d] == 1 and ini is None:
            ini = a
        if rec[d] == 0 and ini is not None:
            tramos.append((ini, a))
            ini = None
    return [rf"\addplot[fill=black!10, draw=none] coordinates {{({a:.3f},{ymin}) ({a:.3f},{ymax}) ({b:.3f},{ymax})"
            rf" ({b:.3f},{ymin}) ({a:.3f},{ymin})}};" for a, b in tramos]


def expectativas():
    casos = [("sube", "creciente", 2.0, 5.5, "very thick"), ("constante", "plana", 3.8, 3.8, "thick, black!45"),
             ("baja", "invertida", 6.0, 2.5, "very thick, densely dashed")]
    a = 0.35
    senda = lambda i0, ib, k: ib + (i0 - ib) * math.exp(-a * k)
    curva = lambda i0, ib, n: i0 if n == 0 else ib + (i0 - ib) * (1 - math.exp(-a * n)) / (a * n)
    xs = [0.1 * j for j in range(0, 101)]
    comun = (r"width=6.2cm, height=5.2cm, axis lines=left, xmin=0, xmax=10, ymin=1.5, ymax=6.5, xtick={0,10},"
             r" ytick=\empty, title style={font=\footnotesize\bfseries}, label style={font=\footnotesize},"
             r" tick label style={font=\scriptsize}, clip=false")
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[name=pa, " + comun + r", xlabel={Años desde hoy, $k$}, ylabel={Tipo},"
               r" title={Tipo a un año esperado, $E[i_k]$}]")
    for _, _, i0, ib, est in casos:
        out.append(rf"\addplot[{est}, mark=none] coordinates {{{coords([(x, senda(i0, ib, x)) for x in xs])}}};")
    out += _etiquetas(10, 10.5, [(senda(i0, ib, 10), et) for et, _, i0, ib, _ in casos], 0.42)
    out.append(r"\end{axis}")
    out.append(r"\begin{axis}[at={(pa.outer east)}, anchor=outer west, xshift=1.5cm, " + comun +
               r", xlabel={Plazo, $n$}, title={Tipo al contado, $r_n$}]")
    for _, _, i0, ib, est in casos:
        out.append(rf"\addplot[{est}, mark=none] coordinates {{{coords([(x, curva(i0, ib, x)) for x in xs])}}};")
    out += _etiquetas(10, 10.5, [(curva(i0, ib, 10), et) for _, et, i0, ib, _ in casos], 0.42)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_expectativas", "% Figura (Anexo I, I.12, «Hipótesis»): sendas del tipo a un año esperado y curvas al contado de la\n"
             "% hipótesis pura de las expectativas (media de la senda); esquemática.\n"
             "% Generar con: bash Code/generar_figura.sh anx_expectativas\n" + "\n".join(out) + "\n")


def plazo_realizado():
    y1, y2 = _media_mensual("THREEFY1"), _media_mensual("THREEFY2")
    meses = [m for m in sorted(y1) if _mas_meses(m, 12) in y1 and m in y2]
    plazo = [(_anio(_mas_meses(m, 12)), 2 * y2[m] - y1[m]) for m in meses]
    real = [(_anio(_mas_meses(m, 12)), y1[_mas_meses(m, 12)]) for m in meses]
    x0, x1, ymin, ymax = plazo[0][0], plazo[-1][0], -0.5, 9
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=14cm, height=5.8cm, axis lines=left, xmin={x0:.3f}, xmax={x1:.3f}, ymin={ymin}, ymax={ymax},"
               r" xtick={1995,2000,2005,2010,2015,2020,2025}, ytick={0,2,4,6,8},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={Tipo a un año (\%)}, clip=false]")
    out += _bandas_recesion(x0, x1, ymin, ymax)
    out.append(rf"\draw[black!30] (axis cs:{x0:.3f},0) -- (axis cs:{x1:.3f},0);")
    out.append(rf"\addplot[thick, black!50, mark=none] coordinates {{{coords(plazo)}}};")
    out.append(rf"\addplot[line width=0.7pt, black, mark=none] coordinates {{{coords(real)}}};")
    out += _etiquetas(x1, x1 + 0.8, [(plazo[-1][1], "a plazo"), (real[-1][1], "realizado")], 0.55)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    err = [p - r for (_, p), (_, r) in zip(plazo, real)]
    escribir("anx_plazo_realizado", "% Figura (Anexo I, I.12, «Contraste»): tipo a plazo a un año dentro de un año (2 y2 - y1, KIM y WRIGHT)\n"
             f"% frente al tipo a un año observado un año después; previsiones de {meses[0]} a {meses[-1]}; error medio"
             f" {sum(err)/len(err):.2f}; a plazo > realizado en el {100*sum(e > 0 for e in err)/len(err):.1f} % de los meses.\n"
             "% Generar con: bash Code/generar_figura.sh anx_plazo_realizado\n" + "\n".join(out) + "\n")


def prima():
    base = 4.0
    xs = [0.2 * j for j in range(0, 101)]
    pos = lambda n: base + 1.4 * (1 - math.exp(-n / 5))
    neg = lambda n: base - 1.0 * (1 - math.exp(-n / 5))
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6cm, axis lines=left, xmin=0, xmax=20, ymin=2, ymax=6.2,"
               r" xtick={0,20}, xticklabels={$0$,$n$}, ytick={4}, yticklabels={$E[i_k]$}, label style={font=\footnotesize},"
               r" xlabel={Plazo}, ylabel={Tipo}, clip=false]")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords([(x, pos(x)) for x in xs])}}};")
    out.append(rf"\addplot[thick, black!45, mark=none] coordinates {{(0,{base}) (20,{base})}};")
    out.append(rf"\addplot[very thick, densely dashed, mark=none] coordinates {{{coords([(x, neg(x)) for x in xs])}}};")
    out.append(rf"\draw[<->, black!60] (axis cs:16,{base:.3f}) -- (axis cs:16,{pos(16):.3f}) node[midway, right] {{$\phi_n$}};")
    out += _etiquetas(20, 21.0, [(pos(20), r"$\phi_n>0$"), (base, r"$\phi_n=0$"), (neg(20), r"$\phi_n<0$")], 0.3)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_prima", "% Figura (Anexo I, I.13, «Riesgo»): tipo corto esperado constante y curvas con prima por plazo positiva,\n"
             "% nula y negativa; esquemática.\n% Generar con: bash Code/generar_figura.sh anx_prima\n" + "\n".join(out) + "\n")


def prima_kw():
    y10, tp = _media_mensual("THREEFY10"), _media_mensual("THREEFYTP10")
    meses = [m for m in sorted(y10) if m in tp]
    tipo = [(_anio(m), y10[m]) for m in meses]
    prima_ = [(_anio(m), tp[m]) for m in meses]
    esper = [(_anio(m), y10[m] - tp[m]) for m in meses]
    x0, x1, ymin, ymax = tipo[0][0], tipo[-1][0], -1.2, 9
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=14cm, height=6cm, axis lines=left, xmin={x0:.3f}, xmax={x1:.3f}, ymin={ymin}, ymax={ymax},"
               r" xtick={1990,1995,2000,2005,2010,2015,2020,2025}, ytick={0,2,4,6,8},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={Puntos porcentuales}, clip=false]")
    out += _bandas_recesion(x0, x1, ymin, ymax)
    out.append(rf"\draw[black!30] (axis cs:{x0:.3f},0) -- (axis cs:{x1:.3f},0);")
    out.append(rf"\addplot[line width=0.7pt, black, mark=none] coordinates {{{coords(tipo)}}};")
    out.append(rf"\addplot[thick, densely dashed, mark=none] coordinates {{{coords(esper)}}};")
    out.append(rf"\addplot[thick, black!50, mark=none] coordinates {{{coords(prima_)}}};")
    out += _etiquetas(x1, x1 + 0.8, [(tipo[-1][1], r"$r_{10}$"), (esper[-1][1], r"$r_{10}-\phi_{10}$"),
                                     (prima_[-1][1], r"$\phi_{10}$")], 0.6)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    mn = min(prima_, key=lambda p: p[1])
    escribir("anx_prima_kw", "% Figura (Anexo I, I.13, «Estimaciones»): tipo a 10 años de KIM y WRIGHT, su prima por plazo y la media\n"
             f"% de los tipos cortos esperados (diferencia), {meses[0]} a {meses[-1]}; último mes: {tipo[-1][1]:.2f} = "
             f"{esper[-1][1]:.2f} + {prima_[-1][1]:.2f}; prima mínima {mn[1]:.2f} en {mn[0]:.2f}.\n"
             "% Generar con: bash Code/generar_figura.sh anx_prima_kw\n" + "\n".join(out) + "\n")


def vasicek():
    ib, k, s = 4.5, 0.25, 0.02
    rinf = ib - 100 * s * s / (2 * k * k)
    b = lambda n: (1 - math.exp(-k * n)) / (k * n)
    r = lambda i, n: i if n == 0 else rinf + (i - rinf) * b(n) + 100 * s * s * n * b(n) ** 2 / (4 * k)
    xs = [0.25 * j for j in range(0, 121)]
    casos = [(1.5, r"$i<\bar\imath$", "very thick"), (4.5, r"$i=\bar\imath$", "thick, black!45"),
             (7.5, r"$i>\bar\imath$", "very thick, densely dashed")]
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6.2cm, axis lines=left, xmin=0, xmax=30, ymin=1, ymax=8,"
               r" xtick={0,10,20,30}, ytick={4.5}, yticklabels={$\bar\imath$}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, xlabel={Plazo, $n$ (años)}, ylabel={Tipo al contado, $r_n$}, clip=false]")
    out.append(rf"\draw[black!40, dashed] (axis cs:0,{rinf:.3f}) -- (axis cs:30,{rinf:.3f});")
    out.append(rf"\node[anchor=north west, font=\footnotesize, text=black!60, inner sep=1.5pt] at (axis cs:0.4,{rinf:.3f}) {{$r_\infty$}};")
    for i, _, est in casos:
        out.append(rf"\addplot[{est}, mark=none] coordinates {{{coords([(x, r(i, x)) for x in xs])}}};")
    out += _etiquetas(30, 31.0, [(r(i, 30), et) for i, et, _ in casos], 0.42)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_vasicek", "% Figura (Anexo I, I.14, «Equilibrio»): curvas de VASICEK sin prima de riesgo (ib = 4,5 %, kappa = 0,25,\n"
             f"% sigma = 2 %) para i = 1,5 %, 4,5 % y 7,5 %; r_inf = {rinf:.2f} %; a 30 años: "
             + ", ".join(f"{r(i, 30):.2f}" for i, _, _ in casos) + ".\n"
             "% Generar con: bash Code/generar_figura.sh anx_vasicek\n" + "\n".join(out) + "\n")


def sombra():
    import csv
    filas = list(csv.reader((DATOS / "wuxia_sombra.csv").open(encoding="utf-8")))[1:]
    datos = [(d[:7], float(ff), float(sh)) for d, ff, sh in filas if sh and "2007-01" <= d[:7] <= "2022-02"]
    ff = [(_anio(m), f) for m, f, _ in datos]
    sh = [(_anio(m), s) for m, _, s in datos]
    x0, x1, ymin, ymax = ff[0][0], ff[-1][0], -3.5, 5.5
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=14cm, height=5.8cm, axis lines=left, xmin={x0:.3f}, xmax={x1:.3f}, ymin={ymin}, ymax={ymax},"
               r" xtick={2008,2010,2012,2014,2016,2018,2020,2022}, ytick={-3,-2,-1,0,1,2,3,4,5},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={\%}, clip=false]")
    out += _bandas_recesion(x0, x1, ymin, ymax)
    out.append(rf"\draw[black!30] (axis cs:{x0:.3f},0) -- (axis cs:{x1:.3f},0);")
    out.append(rf"\addplot[line width=0.7pt, black, mark=none] coordinates {{{coords(ff)}}};")
    out.append(rf"\addplot[very thick, densely dashed, mark=none] coordinates {{{coords(sh)}}};")
    out.append(r"\node[anchor=south west, font=\footnotesize, inner sep=1.5pt] at (axis cs:2010.2,0.25) {fondos federales};")
    out.append(r"\node[anchor=west, font=\footnotesize, inner sep=1.5pt] at (axis cs:2015.6,-2.9) {tipo sombra};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    mn = min(datos, key=lambda t: t[2])
    escribir("anx_sombra", "% Figura (Anexo I, I.14, «Límite inferior»): tipo efectivo de los fondos federales y tipo sombra de WU y\n"
             f"% XIA, fin de mes, {datos[0][0]} a {datos[-1][0]}; mínimo del tipo sombra {mn[2]:.2f} en {mn[0]}.\n"
             "% Generar con: bash Code/generar_figura.sh anx_sombra\n" + "\n".join(out) + "\n")


# =====================  Tanda A7 (I.15 Información, I.16 Política)  =====================
# anx_pendiente_recesiones: GS10 menos TB3MS convertido a rendimiento equivalente, 365 d / (360 - 91 d), medias
#   mensuales desde 1953-04 (FRED); recesiones del NBER (USREC).
# anx_inflacion_implicita: inflación implícita a diez años (T10YIE) y a cinco años dentro de cinco (T5YIFR), medias
#   mensuales desde 2003 (FRED); línea de referencia en el 2 %; recesiones del NBER.
# anx_qe_eventos: rendimiento diario del Tesoro a diez años (DGS10) de octubre de 2008 a diciembre de 2009, con los ocho
#   anuncios de compras que estudian GAGNON et al. (2011): 25/11/2008, 1/12/2008, 16/12/2008, 28/1/2009, 18/3/2009,
#   12/8/2009, 23/9/2009 y 4/11/2009.
# anx_instrumentos: curva observada = media de los tipos cortos esperados + prima por plazo, y el tramo sobre el que actúa
#   cada instrumento; esquemática (e_n = 2 + 1,4 (1 - e^{-n/5}), phi_n = 1,1 (1 - e^{-n/8})).
def _bey(d):
    return 100 * 365 * (d / 100) / (360 - 91 * (d / 100))


def pendiente_recesiones():
    gs = {d[:7]: v for d, v in serie("GS10").items()}
    tb = {d[:7]: v for d, v in serie("TB3MS").items()}
    meses = sorted(m for m in gs if m in tb)
    pts = [(_anio(m), gs[m] - _bey(tb[m])) for m in meses]
    x0, x1, ymin, ymax = pts[0][0], pts[-1][0], -4, 5
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=15.2cm, height=5.8cm, axis lines=left, xmin={x0:.3f}, xmax={x1:.3f}, ymin={ymin}, ymax={ymax},"
               r" xtick={1960,1970,1980,1990,2000,2010,2020}, ytick={-4,-2,0,2,4},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={Puntos porcentuales}, clip=false]")
    out += _bandas_recesion(x0, x1, ymin, ymax)
    out.append(rf"\draw[black!40] (axis cs:{x0:.3f},0) -- (axis cs:{x1:.3f},0);")
    out.append(rf"\addplot[line width=0.6pt, black, mark=none] coordinates {{{coords(pts)}}};")
    out.append(r"\node[anchor=north, font=\scriptsize, text=black!70] at (axis cs:1966.8,-0.7) {1966-1967};")
    out.append(r"\node[anchor=north, font=\scriptsize, text=black!70] at (axis cs:2023.6,-1.9) {2022-2024};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    neg = [m for m, (_, v) in zip(meses, pts) if v < 0]
    escribir("anx_pendiente_recesiones", "% Figura (Anexo I, I.15, «Ciclo»): tipo a 10 años menos tipo a 3 meses (equivalente) en EE. UU.,\n"
             f"% {meses[0]} a {meses[-1]}; {len(neg)} meses con la curva invertida; recesiones del NBER sombreadas.\n"
             "% Generar con: bash Code/generar_figura.sh anx_pendiente_recesiones\n" + "\n".join(out) + "\n")


def inflacion_implicita():
    be, f55 = _media_mensual("T10YIE"), _media_mensual("T5YIFR")
    n_obs = {}
    for d in serie("T10YIE"):
        n_obs[d[:7]] = n_obs.get(d[:7], 0) + 1
    meses = [m for m in sorted(be) if m in f55 and n_obs[m] >= 15]   # sin el último mes si está incompleto
    p10 = [(_anio(m), be[m]) for m in meses]
    p55 = [(_anio(m), f55[m]) for m in meses]
    x0, x1, ymin, ymax = p10[0][0], p10[-1][0], 0, 3.2
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    out.append(rf"\begin{{axis}}[width=13.4cm, height=5.8cm, axis lines=left, xmin={x0:.3f}, xmax={x1:.3f}, ymin={ymin}, ymax={ymax},"
               r" xtick={2005,2010,2015,2020,2025}, ytick={0,1,2,3},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={\%}, clip=false]")
    out += _bandas_recesion(x0, x1, ymin, ymax)
    out.append(rf"\draw[black!40, densely dotted] (axis cs:{x0:.3f},2) -- (axis cs:{x1:.3f},2);")
    out.append(rf"\addplot[line width=0.7pt, black, mark=none] coordinates {{{coords(p10)}}};")
    out.append(rf"\addplot[thick, densely dashed, mark=none] coordinates {{{coords(p55)}}};")
    out += _etiquetas(x1, x1 + 0.6, [(p10[-1][1], "a 10 años"), (p55[-1][1], "a 5 años dentro de 5")], 0.32)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    mn = min(p10, key=lambda p: p[1]); mx = max(p10, key=lambda p: p[1])
    escribir("anx_inflacion_implicita", "% Figura (Anexo I, I.15, «Inflación»): inflación implícita a 10 años y a 5 años dentro de 5 en EE. UU.,\n"
             f"% {meses[0]} a {meses[-1]}; a 10 años: mínimo {mn[1]:.2f} ({mn[0]:.2f}), máximo {mx[1]:.2f} ({mx[0]:.2f}).\n"
             "% Generar con: bash Code/generar_figura.sh anx_inflacion_implicita\n" + "\n".join(out) + "\n")


def qe_eventos():
    import datetime as dt
    d10 = serie("DGS10")
    dec = lambda s: (lambda f: f.year + (f.timetuple().tm_yday - 1) / 365)(dt.date.fromisoformat(s))
    dias = [d for d in sorted(d10) if "2008-10-01" <= d <= "2009-12-31"]
    pts = [(dec(d), d10[d]) for d in dias]
    ev = ["2008-11-25", "2008-12-01", "2008-12-16", "2009-01-28", "2009-03-18", "2009-08-12", "2009-09-23", "2009-11-04"]
    ymin, ymax = 1.8, 4.2
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    ticks = [("2008-10-01", "oct. 2008"), ("2009-01-01", "ene. 2009"), ("2009-04-01", "abr. 2009"),
             ("2009-07-01", "jul. 2009"), ("2009-10-01", "oct. 2009")]
    out.append(rf"\begin{{axis}}[width=14cm, height=5.6cm, axis lines=left, xmin={pts[0][0]:.4f}, xmax={pts[-1][0]:.4f},"
               rf" ymin={ymin}, ymax={ymax}, xtick={{{','.join(f'{dec(t):.4f}' for t, _ in ticks)}}},"
               rf" xticklabels={{{','.join(e for _, e in ticks)}}}, ytick={{2,2.5,3,3.5,4}},"
               r" /pgf/number format/use comma, tick label style={font=\scriptsize}, label style={font=\footnotesize},"
               r" ylabel={Rendimiento (\%)}, clip=false]")
    for e in ev:
        out.append(rf"\draw[black!35, densely dashed] (axis cs:{dec(e):.4f},{ymin}) -- (axis cs:{dec(e):.4f},{ymax});")
    out.append(rf"\addplot[line width=0.6pt, black, mark=none] coordinates {{{coords(pts)}}};")
    i = sorted(d10).index("2009-03-18")
    caida = 100 * (d10["2009-03-18"] - d10[sorted(d10)[i - 1]])
    out.append(rf"\node[anchor=west, font=\scriptsize, text=black!70, inner sep=1.5pt] at (axis cs:{dec('2009-03-18') + 0.01:.4f},2.35)"
               rf" {{18/3/2009: ${caida:.0f}$ pb}};")
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    tot = sum(100 * (d10[e] - d10[sorted(d10)[sorted(d10).index(e) - 1]]) for e in ev)
    escribir("anx_qe_eventos", "% Figura (Anexo I, I.16, «Compras de bonos»): rendimiento diario del Tesoro a 10 años (DGS10), 2008-10 a\n"
             f"% 2009-12, y los ocho anuncios de GAGNON et al. (2011); suma de los cambios de un día: {tot:.0f} pb.\n"
             "% Generar con: bash Code/generar_figura.sh anx_qe_eventos\n" + "\n".join(out) + "\n")


def instrumentos():
    xs = [0.25 * j for j in range(0, 121)]
    e = lambda n: 2 + 1.4 * (1 - math.exp(-n / 5))
    phi = lambda n: 1.1 * (1 - math.exp(-n / 8))
    r = lambda n: e(n) + phi(n)
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(r"\begin{axis}[width=12.5cm, height=6.4cm, axis lines=left, xmin=0, xmax=30, ymin=0.8, ymax=5.6,"
               r" xtick={0,30}, xticklabels={$0$,$n$}, ytick=\empty, label style={font=\footnotesize},"
               r" xlabel={Plazo}, ylabel={Tipo}, clip=false]")
    out.append(rf"\addplot[very thick, mark=none] coordinates {{{coords([(x, r(x)) for x in xs])}}};")
    out.append(rf"\addplot[thick, densely dashed, mark=none] coordinates {{{coords([(x, e(x)) for x in xs])}}};")
    out.append(r"\draw[<->, thick] (axis cs:0.6,1.35) -- (axis cs:0.6,2.65);")
    out.append(r"\node[anchor=west, font=\footnotesize] at (axis cs:0.9,1.25) {tipo oficial};")
    out.append(rf"\draw[->, thick, black!70] (axis cs:7,{e(7) + 0.95:.3f}) to[bend left=25] (axis cs:7,{e(7) + 0.08:.3f});")
    out.append(rf"\node[anchor=south, font=\footnotesize] at (axis cs:7,{e(7) + 0.95:.3f}) {{orientación sobre los tipos}};")
    out.append(rf"\draw[<->, black!60] (axis cs:24,{e(24):.3f}) -- (axis cs:24,{r(24):.3f}) node[midway, left] {{$\phi_n$}};")
    out.append(rf"\draw[->, thick, black!70] (axis cs:25.5,{r(25.5) + 0.75:.3f}) -- (axis cs:25.5,{r(25.5) + 0.08:.3f});")
    out.append(rf"\node[anchor=south, font=\footnotesize, align=center] at (axis cs:25.5,{r(25.5) + 0.75:.3f}) {{compras y gestión\\ de la deuda}};")
    out.append(rf"\draw[line width=1.6pt, black!60] (axis cs:13.8,{r(15):.3f}) -- (axis cs:16.2,{r(15):.3f});")
    out.append(rf"\node[anchor=north, font=\footnotesize] at (axis cs:15,{r(15) - 0.12:.3f}) {{control de la curva}};")
    out += _etiquetas(30, 31.0, [(r(30), r"$r_n$"), (e(30), r"media de $E[i_k]$")], 0.35)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_instrumentos", "% Figura (Anexo I, I.16, introducción): curva = media de los tipos cortos esperados + prima por plazo, y el\n"
             "% tramo sobre el que actúa cada instrumento; esquemática.\n"
             "% Generar con: bash Code/generar_figura.sh anx_instrumentos\n" + "\n".join(out) + "\n")


if __name__ == "__main__":
    pendiente_recesiones()
    inflacion_implicita()
    qe_eventos()
    instrumentos()
    expectativas()
    plazo_realizado()
    prima()
    prima_kw()
    vasicek()
    sombra()
    curvas()
    nelson_siegel()
    curvas_eeuu()
    componentes()
    inmunizacion()
    redington()
    brecha()
    balanza()
    tangente()
    duracion_vencimiento()
    convexidad()
    pesas_bala()
    convexidad_negativa()
    perfiles()
    convergencia()
    precio_sucio()
    precio_rendimiento()
    fuentes()
    arbol_impago()
    diferencial_credito()
    clientelas()
    descomposicion()
    print("Escritas: anx_perfiles, anx_convergencia, anx_precio_sucio, anx_precio_rendimiento, anx_fuentes,"
          " anx_arbol_impago, anx_diferencial_credito, anx_clientelas, anx_descomposicion, anx_balanza, anx_tangente,"
          " anx_duracion_vencimiento, anx_convexidad, anx_pesas_bala, anx_convexidad_negativa, anx_inmunizacion,"
          " anx_redington, anx_brecha, anx_curvas, anx_nelson_siegel, anx_curvas_eeuu, anx_componentes,"
          " anx_expectativas, anx_plazo_realizado, anx_prima, anx_prima_kw, anx_vasicek, anx_sombra,"
          " anx_pendiente_recesiones, anx_inflacion_implicita, anx_qe_eventos, anx_instrumentos")
