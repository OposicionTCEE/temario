"""Figuras calculadas del bloque 2 del cuerpo (T12): escribe Img/b2_valor.tikz y Img/b2_delta.tikz.

Uso, desde la carpeta del tema:  python3 Code/generar_figuras_T12.py Img
Después: bash Code/generar_figura.sh b2_valor  y  bash Code/generar_figura.sh b2_delta

Precios de BLACK-SCHOLES de una call sobre un activo sin rentas, c = S N(d1) - K e^{-r_f T} N(d2), con
d1 = [ln(S/K) + r_f T + v^2/2]/v, d2 = d1 - v y v = sigma raíz de T. Valores ilustrativos.
"""
import math
import os
import sys

N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def call(S, K, rT, v):
    d1 = (math.log(S / K) + rT + 0.5 * v * v) / v
    return S * N(d1) - K * math.exp(-rT) * N(d1 - v), N(d1)


def coords(puntos):
    return " ".join(f"({x:.3f},{y:.3f})" for x, y in puntos)


def b2_valor():
    """Valor de una call con dos volatilidades frente a su cota inferior max{S - K e^{-r_f T}, 0}."""
    K, rT = 2.0, 0.05
    disc = K * math.exp(-rT)
    xs = [0.8 + 0.05 * i for i in range(53)]          # S de 0,8 a 3,4
    baja = [(x, call(x, K, rT, 0.20)[0]) for x in xs]
    alta = [(x, call(x, K, rT, 0.45)[0]) for x in xs]
    return rf"""% Figura (cuerpo, 2.2 «Opciones»): el valor de la volatilidad. Precio de una call (BLACK-SCHOLES, activo sin rentas) frente
% al precio del subyacente con una volatilidad baja, sigma_1 (continua), y una alta, sigma_2 (discontinua), y su cota
% inferior, max{{S - K e^{{-r_f T}}, 0}} (fina). La distancia entre cada curva y la cota es el valor de la protección frente a
% la caída, que crece con la volatilidad. Valores ilustrativos: K = 2, r_f T = 0,05, sigma_1 raíz de T = 0,20 y
% sigma_2 raíz de T = 0,45. Generado por Code/generar_figuras_T12.py; generar el PDF con: bash Code/generar_figura.sh b2_valor
\begin{{tikzpicture}}[font=\footnotesize, >={{Stealth[length=4pt]}}, x=3.1cm, y=2.4cm]
  \draw[->] (0.8,0) -- (3.55,0) node[below] {{$S$}};
  \draw[->] (0.8,0) -- (0.8,1.75) node[left] {{$c$}};
  \draw[thin] (0.8,0) -- ({disc:.3f},0) -- (3.4,{3.4 - disc:.3f});
  \draw[very thick] plot coordinates {{{coords(baja)}}};
  \draw[very thick, dashed] plot coordinates {{{coords(alta)}}};
  \node[anchor=west] at (3.4,{baja[-1][1]:.3f}) {{$\sigma_1$}};
  \node[anchor=west] at (3.4,{alta[-1][1] + 0.06:.3f}) {{$\sigma_2>\sigma_1$}};
  \node[anchor=north west] at (2.62,{2.62 - disc - 0.02:.3f}) {{$\max\{{S-Ke^{{-r_fT}},0\}}$}};
  \draw ({disc:.3f},0.04) -- ({disc:.3f},-0.04);
  \node[below] at ({disc:.3f},0) {{$Ke^{{-r_fT}}$}};
\end{{tikzpicture}}
"""


def b2_delta():
    """Tangente (cobertura delta) y curvatura (gamma) del precio de una call."""
    K, rT, v, S0, h = 2.0, 0.05, 0.35, 2.0, 0.55
    xs = [1.15 + 0.05 * i for i in range(36)]         # S de 1,15 a 2,90
    curva = [(x, call(x, K, rT, v)[0]) for x in xs]
    c0, delta = call(S0, K, rT, v)
    tang = lambda x: c0 + delta * (x - S0)
    pts = []
    for x in (S0 - h, S0 + h):
        pts.append((x, call(x, K, rT, v)[0], tang(x)))
    (xa, ca, ta), (xb, cb, tb) = pts
    return rf"""% Figura (cuerpo, 2.4 «Cobertura»): la cobertura delta y la curvatura. Precio de una call (gruesa) frente al del
% subyacente y su tangente en S_0 (fina), que es el valor de la cartera réplica de Delta = N(d_1) unidades del subyacente y
% un préstamo, sin recomponer. Si el precio se mueve de S_0 a S_0 - Delta S o a S_0 + Delta S, la opción vale más que la
% réplica (tramos gruesos verticales): es la curvatura, aproximadamente 1/2 Gamma (Delta S)^2, que gana quien tiene la
% opción y pierde quien la ha vendido y se ha cubierto en delta. Valores ilustrativos: K = 2, r_f T = 0,05, sigma raíz de
% T = 0,35, S_0 = 2, Delta S = 0,55 (Delta = {delta:.3f}). Generado por Code/generar_figuras_T12.py; generar el PDF con:
% bash Code/generar_figura.sh b2_delta
\begin{{tikzpicture}}[font=\footnotesize, >={{Stealth[length=4pt]}}, x=4.4cm, y=4.4cm]
  \draw[->] (1.15,{min(ta, 0) - 0.05:.3f}) -- (3.05,{min(ta, 0) - 0.05:.3f}) node[below] {{$S$}};
  \draw[->] (1.15,{min(ta, 0) - 0.05:.3f}) -- (1.15,1.05) node[left] {{$c$}};
  \draw[very thick] plot coordinates {{{coords(curva)}}};
  \draw[thin] ({xa - 0.25:.3f},{tang(xa - 0.25):.3f}) -- ({xb + 0.25:.3f},{tang(xb + 0.25):.3f});
  \node[anchor=west] at (2.90,{curva[-1][1]:.3f}) {{$c(S)$}};
  \node[anchor=north west] at ({xb + 0.25:.3f},{tang(xb + 0.25):.3f}) {{$c_0+\Delta\,(S-S_0)$}};
  \fill ({S0:.3f},{c0:.3f}) circle (1.5pt);
  \draw[dotted] ({S0:.3f},{min(ta, 0) - 0.05:.3f}) -- ({S0:.3f},{c0:.3f});
  \node[below] at ({S0:.3f},{min(ta, 0) - 0.05:.3f}) {{$S_0$}};
  \draw[line width=1.6pt] ({xa:.3f},{ta:.3f}) -- ({xa:.3f},{ca:.3f});
  \draw[line width=1.6pt] ({xb:.3f},{tb:.3f}) -- ({xb:.3f},{cb:.3f});
  \draw[dotted] ({xa:.3f},{min(ta, 0) - 0.05:.3f}) -- ({xa:.3f},{ta:.3f});
  \draw[dotted] ({xb:.3f},{min(ta, 0) - 0.05:.3f}) -- ({xb:.3f},{tb:.3f});
  \node[below] at ({xa:.3f},{min(ta, 0) - 0.05:.3f}) {{$S_0-\Delta S$}};
  \node[below] at ({xb:.3f},{min(ta, 0) - 0.05:.3f}) {{$S_0+\Delta S$}};
  \node[anchor=west] at ({xb + 0.02:.3f},{(tb + cb) / 2:.3f}) {{$\approx\tfrac12\,\Gamma\,(\Delta S)^2$}};
\end{{tikzpicture}}
"""


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "Img"
    for nombre, texto in (("b2_valor", b2_valor()), ("b2_delta", b2_delta())):
        with open(os.path.join(carpeta, nombre + ".tikz"), "w", encoding="utf-8") as f:
            f.write(texto)
        print("Escrito", nombre)
