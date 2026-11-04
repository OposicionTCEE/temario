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
    sx, sy, base = 1.2, 0.1, 70.0          # cm por año, cm por unidad de precio, precio en el eje
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]"]
    out.append(rf"\draw[->] (0,0) -- ({T*sx+1.4},0);")
    out.append(rf"\node[anchor=north east] at ({T*sx+1.4},-0.05) {{Tiempo}};")
    out.append(r"\draw[->] (0,0) -- (0,6.4) node[above] {Precio};")
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


if __name__ == "__main__":
    perfiles()
    convergencia()
    precio_sucio()
    precio_rendimiento()
    fuentes()
    print("Escritas: anx_perfiles, anx_convergencia, anx_precio_sucio, anx_precio_rendimiento, anx_fuentes")
