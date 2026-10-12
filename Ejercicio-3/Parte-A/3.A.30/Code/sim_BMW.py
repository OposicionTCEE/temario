"""Modelo BMW (Bank Money World) de GODLEY y LAVOIE (2007, cap. 7): economía cerrada sin Gobierno,
con empresas que invierten financiándose con préstamos bancarios y hogares que ahorran en depósitos.

Genera Img/BMW_simulacion.tikz (dos paneles pgfplots). Después: bash Code/generar_figura.sh BMW_simulacion

Ecuaciones (precios y productividad iguales a 1; rl = rm = r constante):
    Y   = C + I                                  producción = demanda
    AF  = delta * K(-1)                          fondos de amortización = depreciación
    WB  = Y - r*L(-1) - AF                       salarios: lo que queda tras pagar intereses y amortizar
    YD  = WB + r*M(-1)                           renta disponible: salarios e intereses de los depósitos
    C   = a0 + a1*YD + a2*M(-1)                  consumo
    KT  = kappa * Y(-1)                          capital deseado
    I   = gamma*(KT - K(-1)) + delta*K(-1)       inversión (acelerador más reposición)
    K   = K(-1) + I - delta*K(-1)                capital
    L   = L(-1) + I - AF                         préstamos: la inversión neta se financia con crédito
    M   = M(-1) + YD - C                         depósitos: el ahorro de los hogares
    Ms  = Ms(-1) + (L - L(-1))                   oferta de depósitos = préstamos concedidos (redundante: Ms = M)
Parámetros de GODLEY y LAVOIE (2007): a0 = 25, a1 = 0.75, a2 = 0.10, delta = 0.10, gamma = 0.15, kappa = 1, r = 0.025.
Estado estacionario: Y* = a0 / [(1 - a1)(1 - delta*kappa) - a2*kappa]  (= 200 con los parámetros de referencia).
Experimentos (periodo 5): (a) a0 de 25 a 28 (más consumo autónomo); (b) a1 de 0,75 a 0,74 (paradoja del ahorro).
"""
from pathlib import Path

PAR = dict(a0=25.0, a1=0.75, a2=0.10, delta=0.10, gamma=0.15, kappa=1.0, r=0.025)

def estado_estacionario(p):
    Y = p["a0"] / ((1 - p["a1"]) * (1 - p["delta"] * p["kappa"]) - p["a2"] * p["kappa"])
    K = p["kappa"] * Y
    return Y, K, K, K  # Y, K, L, M (en el estado estacionario L = M = K)

def simular(cambio, t_choque=5, T_fin=80):
    p = dict(PAR)
    Y_1, K_1, L_1, M_1 = estado_estacionario(p)
    Ms_1 = M_1
    serie = []
    for t in range(T_fin + 1):
        if t == t_choque:
            p.update(cambio)
        a0, a1, a2, d, g, k, r = (p[x] for x in ("a0", "a1", "a2", "delta", "gamma", "kappa", "r"))
        AF = d * K_1
        I = g * (k * Y_1 - K_1) + d * K_1
        # Y = C + I con C = a0 + a1*(Y - r*L_1 - AF + r*M_1) + a2*M_1
        Y = (a0 + a1 * (-r * L_1 - AF + r * M_1) + a2 * M_1 + I) / (1 - a1)
        WB = Y - r * L_1 - AF
        YD = WB + r * M_1
        C = a0 + a1 * YD + a2 * M_1
        K = K_1 + I - d * K_1
        L = L_1 + I - AF
        M = M_1 + YD - C
        Ms = Ms_1 + (L - L_1)
        assert abs(M - Ms) < 1e-8, "Falla la ecuación redundante"
        serie.append((t, Y, C, I, L, M, K))
        Y_1, K_1, L_1, M_1, Ms_1 = Y, K, L, M, Ms
    return serie

a = simular({"a0": 28.0})
b = simular({"a1": 0.74})

def coords(serie, i):
    return " ".join(f"({x[0]},{x[i]:.3f})" for x in serie)

tikz = r"""% Figura: simulación del modelo BMW de GODLEY y LAVOIE (2007, cap. 7). Generada por Code/sim_BMW.py (no editar a mano).
\begin{tikzpicture}
\begin{axis}[name=izq, width=8.2cm, height=6.2cm, xmin=0, xmax=80, ymin=150, ymax=240,
  xlabel={Periodo}, title={\small (a) Más consumo autónomo ($\alpha_0$: 25 $\to$ 28)},
  legend style={font=\scriptsize, at={(0.98,0.03)}, anchor=south east, draw=black!30}, legend cell align=left,
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[blue!70!black, very thick] coordinates {AY};
  \addlegendentry{$Y$ (producción)}
  \addplot[red!70!black, thick, dashed] coordinates {AL};
  \addlegendentry{$L=M$ (préstamos = depósitos)}
\end{axis}
\begin{axis}[at={(izq.east)}, anchor=west, xshift=1.4cm, width=8.2cm, height=6.2cm, xmin=0, xmax=80, ymin=150, ymax=240,
  xlabel={Periodo}, title={\small (b) Paradoja del ahorro ($\alpha_1$: 0,75 $\to$ 0,74)},
  legend style={font=\scriptsize, at={(0.98,0.97)}, anchor=north east, draw=black!30}, legend cell align=left,
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[blue!70!black, very thick] coordinates {BY};
  \addlegendentry{$Y$ (producción)}
  \addplot[red!70!black, thick, dashed] coordinates {BL};
  \addlegendentry{$L=M$ (préstamos = depósitos)}
\end{axis}
\end{tikzpicture}
"""
for clave, valor in {"AY": coords(a, 1), "AL": coords(a, 4), "BY": coords(b, 1), "BL": coords(b, 4)}.items():
    tikz = tikz.replace(clave, valor)
destino = Path(__file__).resolve().parent.parent / "Img" / "BMW_simulacion.tikz"
destino.write_text(tikz, encoding="utf-8")
print("Escrito", destino)
for nombre, s in (("(a)", a), ("(b)", b)):
    print(nombre, "t=4:", [round(v, 2) for v in s[4][1:]], " t=5:", [round(v, 2) for v in s[5][1:]], " t=6:", [round(v, 2) for v in s[6][1:]], " final:", [round(v, 2) for v in s[-1][1:]])
