"""Figura del cuerpo (S4, 2.3 «BLACK-SCHOLES-MERTON»): caminos de un movimiento browniano geométrico y banda de dispersión.

Escribe Img/b2_browniano.tikz. Uso, desde la carpeta del tema:  python3 Code/generar_b2_browniano.py Img
Después: bash Code/generar_figura.sh b2_browniano

Cuatro caminos ilustrativos de S_t = S_0 exp(-sigma^2 t / 2 + sigma W_t), con S_0 = 1,5, sigma = 0,35 y T = 1, en 80
pasos, con una semilla fija. La banda es S_0 exp(-sigma^2 t / 2 +- 1,645 sigma raíz de t): contiene el 90 % de los caminos
en cada fecha y se ensancha con la raíz del tiempo, más hacia arriba que hacia abajo.
"""
import math
import random
import sys

S0, SIGMA, T, PASOS, SEMILLA = 1.5, 0.35, 1.0, 80, 1463
ESC_X, ESC_Y, Y0 = 6.0, 1.9, 0.55   # cm por unidad de tiempo y de precio; precio en el eje horizontal


def camino(rng):
    dt = T / PASOS
    s, w, puntos = S0, 0.0, [(0.0, S0)]
    for i in range(1, PASOS + 1):
        w += rng.gauss(0.0, math.sqrt(dt))
        s = S0 * math.exp(-SIGMA ** 2 * i * dt / 2 + SIGMA * w)
        puntos.append((i * dt, s))
    return puntos


def banda(signo):
    return [(t, S0 * math.exp(-SIGMA ** 2 * t / 2 + signo * 1.645 * SIGMA * math.sqrt(t)))
            for t in [i * T / 40 for i in range(41)]]


def coords(puntos):
    return " ".join(f"({t * ESC_X:.3f},{(s - Y0) * ESC_Y:.3f})" for t, s in puntos)


def main(carpeta):
    rng = random.Random(SEMILLA)
    caminos = [camino(rng) for _ in range(4)]
    for c in caminos:
        print(f"min {min(s for _, s in c):.2f}  max {max(s for _, s in c):.2f}  final {c[-1][1]:.2f}")
    arriba, abajo = banda(+1), banda(-1)
    ytop = (arriba[-1][1] - Y0) * ESC_Y
    ybot = (abajo[-1][1] - Y0) * ESC_Y
    ys0 = (S0 - Y0) * ESC_Y
    lineas = [
        "% Figura (cuerpo, 2.3 «BLACK-SCHOLES-MERTON»): el movimiento browniano geométrico. Cuatro caminos ilustrativos del",
        "% precio del subyacente, que cambia en cada instante en un porcentaje aleatorio, independiente de los anteriores y de",
        "% tamaño típico constante (la volatilidad), y la banda que contiene el 90 % de los caminos: se ensancha con la raíz del",
        "% tiempo, y más hacia arriba que hacia abajo, porque el precio no baja de cero. S_0 = 1,5, sigma = 0,35, T = 1.",
        "% Generado por Code/generar_b2_browniano.py; generar el PDF con: bash Code/generar_figura.sh b2_browniano",
        "\\begin{tikzpicture}[font=\\footnotesize, >={Stealth[length=4pt]}]",
        f"  \\fill[black!10] plot coordinates {{{coords(arriba)}}} -- plot coordinates {{{coords(list(reversed(abajo)))}}} -- cycle;",
        f"  \\draw[dashed] plot coordinates {{{coords(arriba)}}};",
        f"  \\draw[dashed] plot coordinates {{{coords(abajo)}}};",
    ]
    for c in caminos:
        lineas.append(f"  \\draw[thin] plot coordinates {{{coords(c)}}};")
    lineas += [
        f"  \\draw[->] (0,0) -- ({T * ESC_X + 0.6:.2f},0) node[below] {{$t$}};",
        f"  \\draw[->] (0,0) -- (0,{ytop + 0.5:.2f}) node[left] {{$S_t$}};",
        f"  \\draw ({T * ESC_X:.3f},0.08) -- ({T * ESC_X:.3f},-0.08) node[below] {{$T$}};",
        "  \\node[below left=0pt] at (0,0) {$0$};",
        f"  \\node[left] at (0,{ys0:.3f}) {{$S_0$}};",
        f"  \\draw[gray] ({T * ESC_X * 0.72:.3f},{(banda(+1)[29][1] - Y0) * ESC_Y:.3f}) -- ({T * ESC_X * 0.55:.3f},{ytop + 0.25:.3f});",
        f"  \\node[anchor=south, align=center] at ({T * ESC_X * 0.55:.3f},{ytop + 0.2:.3f}) {{banda del 90\\,\\% de los caminos:\\\\se ensancha con $\\sqrt t$}};",
        f"  \\node[anchor=west, align=left] at ({T * ESC_X + 0.15:.3f},{ytop:.3f}) {{más amplia\\\\hacia arriba}};",
        f"  \\node[anchor=west, align=left] at ({T * ESC_X + 0.15:.3f},{ybot:.3f}) {{más estrecha\\\\hacia abajo}};",
        "\\end{tikzpicture}",
    ]
    with open(f"{carpeta}/b2_browniano.tikz", "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print("Escrito", f"{carpeta}/b2_browniano.tikz")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Img")
