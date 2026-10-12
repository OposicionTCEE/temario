"""Modelo PC (Portfolio Choice) de GODLEY y LAVOIE (2007, cap. 4): economía cerrada con hogares, empresas,
Gobierno y banco central; los hogares reparten su riqueza entre dinero (H) y letras del Tesoro (B).

Genera Img/PC_simulacion.tikz (dos paneles pgfplots). Después: bash Code/generar_figura.sh PC_simulacion

Ecuaciones:
    Y   = C + G
    YD  = Y - T + r(-1)*Bh(-1)                       renta disponible (incluye intereses de las letras)
    T   = theta*(Y + r(-1)*Bh(-1))                   impuestos sobre la renta y los intereses
    V   = V(-1) + (YD - C)                           riqueza
    C   = a1*YD + a2*V(-1)                           consumo
    Hh  = V - Bh                                     dinero (restricción de suma)
    Bh  = V*(l0 + l1*r - l2*YD/V)                    demanda de letras (elección de cartera de TOBIN)
    Bs  = Bs(-1) + (G + r(-1)*Bs(-1)) - (T + r(-1)*Bcb(-1))   emisión de letras por el Gobierno
    Bcb = Bs - Bh                                    el banco central compra las letras que no quieren los hogares
    Hs  = Hs(-1) + (Bcb - Bcb(-1))                   el banco central emite dinero al comprarlas (redundante: Hs = Hh)
    r   = r_barra                                    el banco central fija el tipo de interés
Parámetros de GODLEY y LAVOIE (2007): a1 = 0.6, a2 = 0.4, theta = 0.2, l0 = 0.635, l1 = 5, l2 = 0.01, G = 20, r = 0.025.
Experimento: desde el estado estacionario, el tipo de interés pasa del 2,5 % al 3,5 % en el periodo 5.
"""
from pathlib import Path

a1, a2, th, l0, l1, l2, G = 0.6, 0.4, 0.2, 0.635, 5.0, 0.01, 20.0

def paso(estado, r_ant, r):
    V_1, Bh_1, Bs_1, Bcb_1, Hs_1 = estado
    Y = (a1 * (1 - th) * r_ant * Bh_1 + a2 * V_1 + G) / (1 - a1 * (1 - th))
    T = th * (Y + r_ant * Bh_1)
    YD = Y - T + r_ant * Bh_1
    C = a1 * YD + a2 * V_1
    V = V_1 + YD - C
    Bh = V * (l0 + l1 * r - l2 * YD / V)
    Hh = V - Bh
    Bs = Bs_1 + (G + r_ant * Bs_1) - (T + r_ant * Bcb_1)
    Bcb = Bs - Bh
    Hs = Hs_1 + (Bcb - Bcb_1)
    assert abs(Hs - Hh) < 1e-7, "Falla la ecuación redundante"
    return (V, Bh, Bs, Bcb, Hs), dict(Y=Y, T=T, YD=YD, C=C, V=V, Bh=Bh, Hh=Hh, def_=G + r_ant * Bs_1 - T - r_ant * Bcb_1)

# Estado estacionario con r = 2,5 %: se simula desde una economía vacía hasta que converge
r0, r1 = 0.025, 0.035
# Punto de partida coherente: riqueza inicial mínima (V = 1) en forma de dinero (Hh = Hs = 1), sin letras
estado = (1.0, 0.0, 0.0, 0.0, 1.0)
for _ in range(2000):
    estado, _ = paso(estado, r0, r0)

serie = []
r_ant = r0
for t in range(0, 61):
    r = r1 if t >= 5 else r0
    estado, x = paso(estado, r_ant, r)
    serie.append((t, x["Y"], x["YD"], x["C"], x["V"], x["Bh"] / x["V"], x["def_"]))
    r_ant = r

def coords(i, factor=1.0):
    return " ".join(f"({s[0]},{s[i]*factor:.4f})" for s in serie)

tikz = r"""% Figura: simulación del modelo PC de GODLEY y LAVOIE (2007, cap. 4): subida del tipo de interés del 2,5 al 3,5 por ciento en el periodo 5. Generada por Code/sim_PC.py (no editar a mano).
\begin{tikzpicture}
\begin{axis}[name=izq, width=8.2cm, height=6.2cm, xmin=0, xmax=60, ymin=80, ymax=118,
  xlabel={Periodo}, title={\small Renta, renta disponible y consumo},
  legend style={font=\scriptsize, at={(0.97,0.55)}, anchor=east, draw=black!30}, legend cell align=left,
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[blue!70!black, very thick] coordinates {CY};
  \addlegendentry{$Y$ (renta)}
  \addplot[red!70!black, thick, dashed] coordinates {CYD};
  \addlegendentry{$YD$ (renta disponible)}
  \addplot[green!50!black, thick, dotted] coordinates {CC};
  \addlegendentry{$C$ (consumo)}
\end{axis}
\begin{axis}[at={(izq.east)}, anchor=west, xshift=1.4cm, width=8.2cm, height=6.2cm, xmin=0, xmax=60,
  xlabel={Periodo}, title={\small Proporción de letras en la riqueza de los hogares},
  ylabel={\scriptsize $B_h/V$ (\%)},
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[violet!80!black, very thick] coordinates {CB};
\end{axis}
\end{tikzpicture}
"""
for clave, valor in {"CYD": coords(2), "CY": coords(1), "CC": coords(3), "CB": coords(5, 100)}.items():
    tikz = tikz.replace(clave, valor)
destino = Path(__file__).resolve().parent.parent / "Img" / "PC_simulacion.tikz"
destino.write_text(tikz, encoding="utf-8")
print("Escrito", destino)
for t in (4, 5, 6, 10, 60):
    print(t, [round(v, 3) for v in serie[t][1:]])
