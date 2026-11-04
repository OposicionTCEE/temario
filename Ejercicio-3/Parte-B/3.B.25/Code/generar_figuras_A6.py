# Generador de las figuras TikZ de la tanda A6 del anexo II (3.B.25): anx_estados, anx_medidas, anx_breeden,
# anx_griegas, anx_theta_gamma, anx_minvar y anx_seguro. Escribe los .tikz con los valores calculados (parámetros en la
# cabecera de cada figura) y no necesita librerías externas.
# Uso, desde la carpeta del tema:  python3 Code/generar_figuras_A6.py Img
#   y después, para cada figura:  bash Code/generar_figura.sh anx_estados  (etc.)

import math, random, sys
out=sys.argv[1]
N=lambda x:0.5*(1+math.erf(x/math.sqrt(2)))
n=lambda x:math.exp(-x*x/2)/math.sqrt(2*math.pi)
def coords(pts): return " ".join(f"({a:.3f},{b:.3f})" for a,b in pts)
def w(name, body):
    open(f"{out}/{name}.tikz","w",encoding="utf-8").write(body)

# ---------- anx_estados ----------
w("anx_estados", r"""% Figura (Anexo II, «Precios de estado»): espacio de pagos con dos estados; cada cartera es un punto (x_1, x_2), su pago
% en cada estado. Con precios de estado positivos, psi, la recta de precio nulo, psi_1 x_1 + psi_2 x_2 = 0, solo pasa por el
% segundo y el cuarto cuadrante, y todo pago no negativo y no nulo (cuadrante sombreado) tiene precio positivo: no hay
% arbitraje. El bono paga (1,1) y vale e^{-rT} (discontinua: pagos con ese precio); los títulos de ARROW y DEBREU, e_1 y e_2,
% valen psi_1 y psi_2. Valores ilustrativos: psi proporcional a (1; 0,8); subyacente que paga (2; 0,55).
% Generar con: bash Code/generar_figura.sh anx_estados
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}, x=1.1cm, y=1.1cm]
  \fill[black!12] (0,0) rectangle (2.6,2.5);
  \draw[->] (-1.7,0) -- (2.9,0) node[below] {$x_1$};
  \draw[->] (0,-1.75) -- (0,2.85) node[left] {$x_2$};
  \draw[thick] (-1.28,1.6) -- (1.28,-1.6);
  \node[anchor=south east, inner sep=1pt] at (-1.28,1.6) {$\psi\cdot x=0$};
  \draw[dashed] (-0.3,2.625) -- (2.4,-0.75);
  \node[anchor=north west, inner sep=2pt] at (2.4,-0.75) {$\psi\cdot x=e^{-r_fT}$};
  \draw[->, very thick] (0,0) -- (0.75,0.6);
  \node[anchor=north west, inner sep=1pt] at (0.72,0.6) {$\psi$};
  \fill (1,1) circle (1.8pt); \node[anchor=south west, inner sep=2pt] at (1,1) {$\mathbf{1}$};
  \fill (2.0,0.55) circle (1.8pt); \node[anchor=west] at (2.0,0.55) {$(S_0u,\,S_0d)$};
  \fill (1,0) circle (1.8pt); \node[anchor=north] at (1,0) {$e_1$};
  \fill (0,1) circle (1.8pt); \node[anchor=east] at (0,1) {$e_2$};
  \node at (1.95,2.1) {$x\ge0$};
\end{tikzpicture}
""")

# ---------- anx_medidas ----------
s=0.3
def dens(x,drift):
    m=drift-0.5*s*s
    return math.exp(-(math.log(x)-m)**2/(2*s*s))/(x*s*math.sqrt(2*math.pi))
xs=[0.3+0.05*i for i in range(0,45)]
P=coords([(x,dens(x,0.20)) for x in xs]); Q=coords([(x,dens(x,0.02)) for x in xs])
w("anx_medidas", r"""% Figura (Anexo II, «Cambio de medida»): densidad del precio al vencimiento con las probabilidades reales, P (continua), y con
% las neutrales al riesgo, Q (discontinua). El teorema de GIRSANOV cambia la tendencia, de mu a r, pero no la volatilidad: Q
% desplaza la distribución hacia abajo y da más peso a los estados malos. Lognormales con S_0 = 1, sigma = 30 %, T = 1,
% mu = 20 % y r = 2 % (ilustrativos; medias S_0 e^{mu T} = 1,22 y S_0 e^{rT} = 1,02).
% Generar con: bash Code/generar_figura.sh anx_medidas
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}, x=2.4cm, y=1.6cm]
  \draw[->] (0,0) -- (2.75,0) node[below] {$S_T$};
  \draw[->] (0,0) -- (0,1.7);
  \draw[very thick] plot[smooth] coordinates {""" + P + r"""};
  \draw[very thick, dashed] plot[smooth] coordinates {""" + Q + r"""};
  \draw[dotted] (1.2214,0) -- (1.2214,1.10);
  \draw[dotted] (1.0202,0) -- (1.0202,1.32);
  \node[anchor=north east, inner xsep=1pt] at (1.0202,0) {$S_0e^{r_fT}$};
  \node[anchor=north west, inner xsep=1pt] at (1.2214,0) {$S_0e^{\mu T}$};
  \node[anchor=south west] at (1.5,0.65) {$\mathbb{P}$};
  \node[anchor=east] at (0.7,1.12) {$\mathbb{Q}$};
\end{tikzpicture}
""")

# ---------- anx_breeden ----------
S0=2.0; rT=0.05; v=0.35
def c(K):
    d1=(math.log(S0/K)+rT+0.5*v*v)/v; d2=d1-v
    return S0*N(d1)-K*math.exp(-rT)*N(d2)
def qd(K):
    m=math.log(S0)+rT-0.5*v*v
    return math.exp(-rT)*math.exp(-(math.log(K)-m)**2/(2*v*v))/(K*v*math.sqrt(2*math.pi))
Ks=[0.8+0.1*i for i in range(0,29)]
X=lambda K:K-0.6
CK=coords([(X(K),c(K)) for K in Ks]); QD=coords([(X(K),qd(K)) for K in Ks])
band=[1.8+0.05*i for i in range(0,17)]
QB=coords([(X(K),qd(K)) for K in band])
k0,dk=2.2,0.8
w("anx_breeden", r"""% Figura (Anexo II, «Precios implícitos»): (a) precio de una call frente a su precio de ejercicio, decreciente y convexo; la
% cuerda entre K_1 y K_3 queda por encima del precio en K_2, y la diferencia es el precio de la mariposa,
% que no puede ser negativo. (b) Segunda derivada del precio respecto a K: la densidad neutral al riesgo descontada,
% e^{-rT} q(K) (BREEDEN y LITZENBERGER, 1978); el área sombreada, de anchura K_2 - K_1, es el precio de un título que paga si S_T
% termina cerca de K_2. Valores ilustrativos: S_0 = 2, rT = 0,05, sigma raíz de T = 0,35, K_2 = 2,2, K_2 - K_1 = 0,8.
% Generar con: bash Code/generar_figura.sh anx_breeden
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Precio de la call ----------------
  \begin{scope}[x=1.2cm, y=2.0cm]
    \node[font=\footnotesize\bfseries] at (1.6,1.55) {(a) Precio de la \textit{call}};
    \draw[->] (0,0) -- (3.3,0) node[below] {$K$};
    \draw[->] (0,0) -- (0,1.38) node[left] {$c$};
    \draw[very thick] plot[smooth] coordinates {""" + CK + r"""};
    \draw[dashed] (""" + f"{X(k0-dk):.3f},{c(k0-dk):.3f}" + r""") -- (""" + f"{X(k0+dk):.3f},{c(k0+dk):.3f}" + r""");
    \foreach \k/\c in {""" + f"{X(k0-dk):.3f}/{c(k0-dk):.3f}, {X(k0):.3f}/{c(k0):.3f}, {X(k0+dk):.3f}/{c(k0+dk):.3f}" + r"""} { \fill (\k,\c) circle (1.6pt); \draw[dotted] (\k,0) -- (\k,\c); }
    \node[anchor=north] at (""" + f"{X(k0-dk):.3f}" + r""",0) {$K_1$};
    \node[anchor=north] at (""" + f"{X(k0):.3f}" + r""",0) {$K_2$};
    \node[anchor=north] at (""" + f"{X(k0+dk):.3f}" + r""",0) {$K_3$};
  \end{scope}
  % ---------------- (b) Precios de estado ----------------
  \begin{scope}[xshift=6.6cm, x=1.2cm, y=3.0cm]
    \node[font=\footnotesize\bfseries] at (1.6,1.0333) {(b) Precios de estado};
    \fill[black!22] (""" + f"{X(1.8):.3f}" + r""",0) -- plot[smooth] coordinates {""" + QB + r"""} -- (""" + f"{X(2.6):.3f}" + r""",0) -- cycle;
    \draw[->] (0,0) -- (3.3,0) node[below] {$K$};
    \draw[->] (0,0) -- (0,0.92);
    \draw[very thick] plot[smooth] coordinates {""" + QD + r"""};
    \draw[dotted] (""" + f"{X(k0):.3f},0) -- ({X(k0):.3f},{qd(k0):.3f}" + r""");
    \node[anchor=north] at (""" + f"{X(k0):.3f}" + r""",0) {$K_2$};
    \node[anchor=south west] at (""" + f"{X(1.85):.3f},{qd(1.85)+0.01:.3f}" + r""") {$e^{-r_fT}q(K)=\dfrac{\partial^2c}{\partial K^2}$};
  \end{scope}
\end{tikzpicture}
""")

# ---------- anx_griegas ----------
K=2.0; sg=0.2
def greeks(S,T):
    d1=(math.log(S/K)+0.5*sg*sg*T)/(sg*math.sqrt(T))
    return N(d1), n(d1)/(S*sg*math.sqrt(T)), S*n(d1)*math.sqrt(T)
Ss=[1.2+0.04*i for i in range(0,41)]
Xg=lambda S:(S-1.2)*2.5
def curve(T,i,scale=1.0): return coords([(Xg(S),greeks(S,T)[i]*scale) for S in Ss])
body=r"""% Figura (Anexo II, «Griegas»): delta, gamma y vega de una call frente al precio del subyacente, con un plazo corto, T_1
% (continua), y uno largo, T_2 (discontinua). Con el plazo corto, la delta pasa bruscamente de 0 a 1 cerca de K y la gamma se
% concentra allí; con el largo, la vega es mayor. BLACK-SCHOLES con K = 2, r = 0, sigma = 20 %, T_1 = 0,25 y T_2 = 2.
% Eje horizontal de 1,2 a 2,8; escalas verticales distintas en cada panel.
% Generar con: bash Code/generar_figura.sh anx_griegas
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
"""
panels=[("(a) Delta",0,2.0,"\\Delta",[(0,"0"),(1,"1")]),("(b) Gamma",1,1.0,"\\Gamma",[]),("(c) Vega",2,1.75,"\\nu",[])]
for k,(title,i,ysc,lab,ticks) in enumerate(panels):
    ymax={0:1.0,1:2.02,2:1.13}[i]
    body+=f"""  % ---------------- {title} ----------------
  \\begin{{scope}}[xshift={k*5.2:.1f}cm, x=1.0cm, y={ysc}cm]
    \\node[font=\\footnotesize\\bfseries] at (2.0,{2.55/ysc:.3f}) {{{title}}};
    \\draw[->] (0,0) -- (4.35,0) node[below] {{$S$}};
    \\draw[->] (0,0) -- (0,{2.25/ysc:.3f}) node[left] {{${lab}$}};
    \\draw[very thick] plot[smooth] coordinates {{{curve(0.25,i)}}};
    \\draw[very thick, dashed] plot[smooth] coordinates {{{curve(2.0,i)}}};
    \\draw (2.0,{0.06/ysc:.3f}) -- (2.0,{-0.06/ysc:.3f}); \\node[below] at (2.0,0) {{$K$}};
"""
    if i==0:
        body+="""    \\draw[dotted] (0,1) -- (4.0,1); \\node[left] at (0,1) {$1$};
    \\node[anchor=west] at (1.95,0.25) {$T_1$};
    \\node[anchor=south] at (0.4,0.17) {$T_2$};
"""
    if i==1:
        body+="""    \\node[anchor=west] at (2.25,1.9) {$T_1$};
    \\node[anchor=south] at (0.7,0.66) {$T_2$};
"""
    if i==2:
        body+="""    \\node[anchor=west] at (2.35,0.42) {$T_1$};
    \\node[anchor=south] at (2.2,1.14) {$T_2$};
"""
    body+="  \\end{scope}\n"
body+="\\end{tikzpicture}\n"
w("anx_griegas", body)

# ---------- anx_theta_gamma ----------
w("anx_theta_gamma", r"""% Figura (Anexo II, «Theta y gamma»): resultado durante un intervalo corto de una opción comprada y cubierta en delta, frente
% al movimiento del subyacente: la curvatura da 1/2 Gamma dS^2 (discontinua) con cualquier movimiento y el paso del
% tiempo resta Theta dt (punteada); el resultado (continua) es positivo si |dS| supera sigma S raíz de dt.
% Unidades: dS en múltiplos de sigma S raíz de dt; Gamma S^2 = 1.
% Generar con: bash Code/generar_figura.sh anx_theta_gamma
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}, x=1.25cm, y=1.25cm]
  \draw[->] (-2.5,0) -- (2.6,0) node[below] {$dS$};
  \draw[->] (0,-0.85) -- (0,2.05) node[left] {$d\Pi$};
  \draw[dashed] plot[domain=-1.9:1.9, samples=50] (\x,{0.5*\x*\x});
  \draw[dotted, thick] (-2.15,-0.5) -- (2.15,-0.5);
  \draw[very thick] plot[domain=-2.1:2.1, samples=60] (\x,{0.5*(\x*\x-1)});
  \fill (-1,0) circle (1.6pt); \fill (1,0) circle (1.6pt);
  \node[anchor=north east, inner xsep=1pt] at (-1,0) {$-\sigma S\sqrt{dt}$};
  \node[anchor=north west, inner xsep=1pt] at (1,0) {$\sigma S\sqrt{dt}$};
  \node[anchor=east] at (-2.15,-0.5) {$\Theta\,dt$};
  \node[anchor=south] at (1.9,1.81) {$\tfrac{1}{2}\Gamma\,dS^2$};
\end{tikzpicture}
""")

# ---------- anx_minvar ----------
random.seed(5)
pts=[]
for i in range(70):
    f=random.gauss(0,1); e=random.gauss(0,1)
    pts.append((f,0.8*f+0.45*e))
mx=sum(p[0] for p in pts)/70; my=sum(p[1] for p in pts)/70
cov=sum((a-mx)*(b-my) for a,b in pts)/69; vx=sum((a-mx)**2 for a,_ in pts)/69
h=cov/vx
dots=", ".join(f"{a:.2f}/{b:.2f}" for a,b in pts)
x1,x2=-2.4,2.4
w("anx_minvar", r"""% Figura (Anexo II, «Mínima varianza»): nube de cambios del precio expuesto, dS, frente a los del futuro, dF; la
% razón de cobertura de mínima varianza, h^*, es la pendiente de la recta de regresión, y la dispersión en torno a ella es el
% riesgo que queda. Simulación: dF normal estándar, dS = 0,8 dF + 0,45 e, 70 observaciones, semilla 5
% (h^* estimada = """ + f"{h:.2f}".replace('.',',') + r""").
% Generar con: bash Code/generar_figura.sh anx_minvar
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}, x=0.85cm, y=0.85cm]
  \draw[->] (-2.7,0) -- (2.8,0) node[below] {$dF$};
  \draw[->] (0,-2.7) -- (0,2.75) node[left] {$dS$};
  \foreach \x/\y in {""" + dots + r"""} \fill[black!55] (\x,\y) circle (1.3pt);
  \draw[very thick] (""" + f"{x1},{my+h*(x1-mx):.3f}) -- ({x2},{my+h*(x2-mx):.3f}" + r""");
  \node[anchor=west] at (""" + f"{x2},{my+h*(x2-mx):.3f}" + r""") {$h^*$};
\end{tikzpicture}
""")

# ---------- anx_seguro ----------
rT=0.05; v=0.35
def call(S):
    d1=(math.log(S/2.0)+rT+0.5*v*v)/v; d2=d1-v
    return S*N(d1)-2.0*math.exp(-rT)*N(d2), N(d1)
Ss2=[0.4+0.1*i for i in range(0,29)]
INS=coords([(S,call(S)[0]+2.0*math.exp(-rT)) for S in Ss2])
ND=coords([(S,call(S)[1]) for S in Ss2])
fl=2.0*math.exp(-rT)
w("anx_seguro", r"""% Figura (Anexo II, «Seguro de carteras»): (a) valor de la cartera asegurada, el subyacente más una put, igual a una call más
% un bono, S + p = c + K e^{-rT} (continua), frente al de la cartera sin asegurar, S (discontinua): nunca baja del suelo
% K e^{-rT}. (b) Unidades del subyacente en la réplica, N(d_1): aumentan cuando sube el precio y disminuyen cuando baja, de
% modo que la estrategia compra en las subidas y vende en las caídas. BLACK-SCHOLES con K = 2, rT = 0,05 y sigma raíz de
% T = 0,35 (ilustrativos).
% Generar con: bash Code/generar_figura.sh anx_seguro
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Cartera asegurada ----------------
  \begin{scope}[x=1.0cm, y=0.85cm]
    \node[font=\footnotesize\bfseries] at (1.8,3.85) {(a) Cartera asegurada};
    \draw[->] (0,0) -- (3.75,0) node[below] {$S$};
    \draw[->] (0,0) -- (0,3.55);
    \draw[dashed] (0,0) -- (3.2,3.2);
    \draw[dotted] (0,""" + f"{fl:.3f}) -- (3.2,{fl:.3f}" + r""");
    \draw[very thick] plot[smooth] coordinates {""" + INS + r"""};
    \node[anchor=east] at (0,""" + f"{fl:.3f}" + r""") {$Ke^{-r_fT}$};
    \node[anchor=north west] at (1.2,1.15) {$S$};
    \node[anchor=south east] at (2.3,2.55) {$S+p$};
    \draw (2,0.06) -- (2,-0.06); \node[below] at (2,0) {$K$};
  \end{scope}
  % ---------------- (b) Unidades del subyacente ----------------
  \begin{scope}[xshift=6.3cm, x=1.0cm, y=2.6cm]
    \node[font=\footnotesize\bfseries] at (1.8,1.2654) {(b) Unidades del subyacente};
    \draw[->] (0,0) -- (3.75,0) node[below] {$S$};
    \draw[->] (0,0) -- (0,1.17);
    \draw[dotted] (0,1) -- (3.3,1); \node[left] at (0,1) {$1$};
    \draw[very thick] plot[smooth] coordinates {""" + ND + r"""};
    \node[anchor=west] at (3.2,0.92) {$N(d_1)$};
    \draw (2,0.023) -- (2,-0.023); \node[below] at (2,0) {$K$};
  \end{scope}
\end{tikzpicture}
""")
print("h",h)
