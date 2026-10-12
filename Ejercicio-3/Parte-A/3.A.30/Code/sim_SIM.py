"""Modelo SIM de GODLEY y LAVOIE (2007, cap. 3): economía cerrada con Gobierno y hogares y dinero público.

Genera Img/SIM_simulacion.tikz (dos paneles pgfplots). Después: bash Code/generar_figura.sh SIM_simulacion

Ecuaciones (salario por unidad de trabajo W = 1, por lo que Y = W*N):
    Y   = C + G                 producción = demanda
    T   = theta * Y             impuestos
    YD  = Y - T                 renta disponible
    C   = a1 * YD + a2 * H(-1)  consumo (renta y riqueza heredada)
    dH  = YD - C                ahorro de los hogares = dinero que acumulan
    dHs = G - T                 déficit público = dinero que emite el Gobierno (ecuación redundante: Hs = H)
Parámetros de GODLEY y LAVOIE (2007): a1 = 0.6, a2 = 0.4, theta = 0.2, G = 20.
Experimento: desde el estado estacionario con G = 20, el gasto público pasa a G = 25 en el periodo 5.
"""
from pathlib import Path

a1, a2, theta = 0.6, 0.4, 0.2
G0, G1, t_choque, T_fin = 20.0, 25.0, 5, 60

# Estado estacionario inicial: Y* = G/theta, YD* = (1-theta)Y*, H* = (1-a1)/a2 * YD*
Y0 = G0 / theta
H_prev = (1 - a1) / a2 * (1 - theta) * Y0
Hs_prev = H_prev

serie = []
for t in range(0, T_fin + 1):
    G = G1 if t >= t_choque else G0
    # Solución del periodo: Y = [G + a2*H(-1)] / [1 - a1*(1-theta)]
    Y = (G + a2 * H_prev) / (1 - a1 * (1 - theta))
    T = theta * Y
    YD = Y - T
    C = a1 * YD + a2 * H_prev
    H = H_prev + YD - C
    Hs = Hs_prev + G - T
    assert abs(H - Hs) < 1e-9, "Falla la ecuación redundante"
    serie.append((t, Y, YD, C, H, G - T, G))
    H_prev, Hs_prev = H, Hs

def coords(i):
    return " ".join(f"({r[0]},{r[i]:.3f})" for r in serie)

tikz = r"""% Figura: simulación del modelo SIM de GODLEY y LAVOIE (2007) ante un aumento del gasto público de 20 a 25 en el periodo 5.
% Generada por Code/sim_SIM.py (no editar a mano). Parámetros: a1 = 0,6; a2 = 0,4; theta = 0,2.
\begin{tikzpicture}
\begin{axis}[name=izq, width=8.2cm, height=6.2cm, xmin=0, xmax=%(T)d, ymin=40, ymax=135,
  xlabel={Periodo}, title={\small Renta, renta disponible y consumo},
  legend style={font=\scriptsize, at={(0.98,0.03)}, anchor=south east, draw=black!30}, legend cell align=left,
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[blue!70!black, very thick] coordinates {%(Y)s};
  \addlegendentry{$Y$ (renta)}
  \addplot[red!70!black, thick, dashed] coordinates {%(YD)s};
  \addlegendentry{$YD$ (renta disponible)}
  \addplot[green!50!black, thick, dotted] coordinates {%(C)s};
  \addlegendentry{$C$ (consumo)}
  \addplot[black!50, thin] coordinates {(0,125) (%(T)d,125)};
  \node[font=\scriptsize, text=black!60, anchor=south east] at (axis cs:%(T)d,125) {$G_1/\theta=125$};
\end{axis}
\begin{axis}[at={(izq.east)}, anchor=west, xshift=1.6cm, width=8.2cm, height=6.2cm, xmin=0, xmax=%(T)d,
  xlabel={Periodo}, title={\small Riqueza de los hogares y déficit público},
  axis y line*=left, ymin=70, ymax=110, ylabel={\scriptsize $H$}, 
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, grid=major, grid style={black!10}]
  \addplot[violet!80!black, very thick] coordinates {%(H)s};
  \label{plot:H}
\end{axis}
\begin{axis}[at={(izq.east)}, anchor=west, xshift=1.6cm, width=8.2cm, height=6.2cm, xmin=0, xmax=%(T)d,
  axis y line*=right, axis x line=none, ymin=-1, ymax=4, ylabel={\scriptsize $G-T$},
  tick label style={font=\scriptsize}, label style={font=\scriptsize},
  legend style={font=\scriptsize, at={(0.98,0.97)}, anchor=north east, draw=black!30}, legend cell align=left]
  \addlegendimage{violet!80!black, very thick}\addlegendentry{$H$ (dinero de los hogares, eje izq.)}
  \addplot[orange!80!black, thick, dashed] coordinates {%(D)s};
  \addlegendentry{$G-T$ (déficit, eje dcho.)}
\end{axis}
\end{tikzpicture}
"""
for clave, valor in {"%(T)d": str(T_fin), "%(Y)s": coords(1), "%(YD)s": coords(2), "%(C)s": coords(3), "%(H)s": coords(4), "%(D)s": coords(5)}.items():
    tikz = tikz.replace(clave, valor)

destino = Path(__file__).resolve().parent.parent / "Img" / "SIM_simulacion.tikz"
destino.write_text(tikz, encoding="utf-8")
print("Escrito", destino)
print("Periodo 5:", [round(x, 2) for x in serie[5][1:6]], " final:", [round(x, 2) for x in serie[-1][1:6]])
print("Multiplicador de impacto:", round((serie[5][1] - Y0) / (G1 - G0), 3), " de largo plazo:", round((serie[-1][1] - Y0) / (G1 - G0), 3))
