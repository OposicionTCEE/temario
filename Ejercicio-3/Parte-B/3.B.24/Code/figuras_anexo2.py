"""Figuras del anexo II del 3.B.24 (Mercados de renta fija). Escribe los .tikz en Img/.

Uso, desde la carpeta del tema:  python3 -B Code/figuras_anexo2.py
y después, para cada figura:   bash Code/generar_figura.sh anx_hitos   (y lo mismo con las demás)

Usa escribir() de figuras_anexo1.py (1,5 pt de margen arriba y abajo).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_anexo1 import escribir, coords, serie, _anio, _etiquetas  # noqa: E402


# =====================  Tanda A8 (II.1 Historia, II.2 Instrumentos)  =====================
# anx_hitos: cronología esquemática (escala no proporcional) de los hitos que estudia II.1.
# anx_prelacion: orden de cobro de los acreedores de un banco europeo; esquemática.
# anx_cedulas_titulizacion: bono garantizado (doble recurso) frente a titulización (venta a un fondo y tramos).
HITOS = [(r"h.~1800 a.~C.", "Hammurabi limita el interés"), ("1262", r"Monte Vecchio\\de Venecia"),
         ("1694", "Banco de Inglaterra"), ("1751", "consols"), ("1820-1830", r"impagos\\latinoamericanos"),
         ("años cincuenta", "eurodólares"), ("1963", "primer eurobono"), ("1982", "crisis de la deuda"),
         ("1989", "Plan Brady y primer bono global"), ("1999", "euro"), ("2007", "primer bono verde"),
         ("2008", "crisis financiera"), ("2021", "NextGenerationEU")]


def hitos():
    paso = 1.12
    out = [r"\begin{tikzpicture}[font=\scriptsize]"]
    x_fin = paso * (len(HITOS) - 1)
    out.append(rf"\draw[black!55, line width=0.8pt, -{{Stealth[length=5pt]}}] (-0.3,0) -- ({x_fin + 0.5:.2f},0);")
    for k, (anio, texto) in enumerate(HITOS):
        x = paso * k
        arriba = k % 2 == 0
        y = 0.55 if arriba else -0.55
        ancla = "south" if arriba else "north"
        out.append(rf"\fill ({x:.2f},0) circle (1.6pt);")
        out.append(rf"\draw[black!40] ({x:.2f},0) -- ({x:.2f},{y:.2f});")
        out.append(rf"\node[anchor={ancla}, text width=2.1cm, align=center, inner sep=1.5pt] at ({x:.2f},{y:.2f})"
                   rf" {{\textbf{{{anio}}}\\{texto}}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_hitos", "% Figura (Anexo II, II.1, introducción): cronología de los mercados de deuda; escala no proporcional.\n"
             "% Generar con: bash Code/generar_figura.sh anx_hitos\n" + "\n".join(out) + "\n")


CAPAS = [("Bonos garantizados (cédulas)", "sobre su cartera de cobertura", "black!6"),
         ("Deuda sénior preferente", "", "black!12"),
         ("Deuda sénior no preferente", "", "black!20"),
         ("Deuda subordinada (Tier 2)", "", "black!30"),
         ("Capital adicional (AT1, CoCos)", "", "black!42"),
         ("Acciones", "", "black!56")]


def prelacion():
    ancho, alto = 6.8, 0.62
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=5pt]}]"]
    n = len(CAPAS)
    for k, (texto, nota, color) in enumerate(CAPAS):
        y1 = (n - k) * alto
        y0 = y1 - alto
        txt = texto if not nota else rf"{texto} \textit{{\scriptsize {nota}}}"
        color_texto = "white" if k >= n - 2 else "black"
        out.append(rf"\draw[fill={color}, draw=black!55] (0,{y0:.3f}) rectangle ({ancho},{y1:.3f});")
        out.append(rf"\node[text={color_texto}] at ({ancho / 2:.2f},{(y0 + y1) / 2:.3f}) {{{txt}}};")
    tope = n * alto
    out.append(rf"\draw[->, thick] (-0.45,{tope - 0.1:.2f}) -- (-0.45,0.1);")
    out.append(rf"\node[anchor=east, align=right] at (-0.6,{tope - 0.25:.2f}) {{cobra\\antes}};")
    out.append(r"\node[anchor=east, align=right] at (-0.6,0.3) {absorbe antes\\las pérdidas};")
    out.append(rf"\draw[->, thick] ({ancho + 0.45:.2f},{tope - 0.1:.2f}) -- ({ancho + 0.45:.2f},0.1);")
    out.append(rf"\node[anchor=west, align=left] at ({ancho + 0.6:.2f},{tope / 2:.2f}) {{más pérdida en caso\\de impago y más\\rendimiento exigido}};")
    out.append(r"\end{tikzpicture}")
    escribir("anx_prelacion", "% Figura (Anexo II, II.2, «Garantía y prelación»): orden de cobro de los acreedores de un banco europeo.\n"
             "% Generar con: bash Code/generar_figura.sh anx_prelacion\n" + "\n".join(out) + "\n")


def cedulas_titulizacion():
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=5pt]},"
           r" caja/.style={draw=black!60, rounded corners=1pt, align=center, inner sep=3pt}]"]
    # (a) bono garantizado: el banco conserva los préstamos; doble recurso del tenedor (inversores debajo)
    out.append(r"\node[font=\footnotesize\bfseries] at (2.3,3.5) {Bono garantizado (cédula)};")
    out.append(r"\draw[black!60, rounded corners=2pt] (0,0) rectangle (4.6,3.0);")
    out.append(r"\node[anchor=north] at (2.3,2.95) {Banco emisor};")
    out.append(r"\node[caja, fill=black!12, minimum width=1.9cm, minimum height=1.6cm] (cob) at (1.2,1.25) {Préstamos\\de cobertura};")
    out.append(r"\node[caja, minimum width=1.9cm, minimum height=1.6cm] (pas) at (3.4,1.25) {Cédulas\\y resto\\del pasivo};")
    out.append(r"\node[caja, fill=black!5] (ten) at (2.3,-1.45) {Tenedores de cédulas};")
    out.append(r"\draw[->, thick] ([xshift=-0.45cm]ten.north) -- node[left, font=\scriptsize] {2} (cob.south);")
    out.append(r"\draw[->, thick] ([xshift=0.45cm]ten.north) -- node[right, font=\scriptsize] {1} (3.4,0);")
    out.append(r"\node[align=center, font=\scriptsize, anchor=north] at (2.3,-1.85) {1: derecho frente al banco\\2: preferencia sobre la cobertura};")
    # (b) titulización: el banco vende los préstamos a un fondo que emite bonos por tramos (inversores debajo)
    dx = 5.6
    out.append(rf"\node[font=\footnotesize\bfseries] at ({dx + 3.4:.2f},3.5) {{Titulización}};")
    out.append(rf"\node[caja, fill=black!5] (ori) at ({dx + 0.85:.2f},1.15) {{Banco\\originador}};")
    out.append(rf"\draw[black!60, rounded corners=2pt] ({dx + 3.0:.2f},0) rectangle ({dx + 6.5:.2f},3.0);")
    out.append(rf"\node[anchor=north] at ({dx + 4.75:.2f},2.95) {{Fondo de titulización}};")
    out.append(rf"\node[caja, fill=black!12, minimum width=1.6cm, minimum height=1.9cm] (pre) at ({dx + 3.9:.2f},1.15) {{Préstamos}};")
    for k, (tramo, color) in enumerate([("sénior", "black!5"), ("intermedio", "black!18"), ("subordinado", "black!35")]):
        y = 1.8 - 0.62 * k
        out.append(rf"\node[caja, fill={color}, minimum width=1.65cm, minimum height=0.55cm] (t{k}) at ({dx + 5.6:.2f},{y:.2f}) {{{tramo}}};")
    out.append(rf"\node[caja, fill=black!5] (inv) at ({dx + 4.75:.2f},-1.45) {{Inversores}};")
    out.append(r"\draw[->, thick] (ori.east) -- node[above, font=\scriptsize, align=center] {vende\\los préstamos} (pre.west);")
    out.append(rf"\draw[->, thick] ({dx + 4.75:.2f},0) -- node[right, font=\scriptsize] {{bonos por tramos}} (inv.north);")
    out.append(r"\end{tikzpicture}")
    escribir("anx_cedulas_titulizacion", "% Figura (Anexo II, II.2, «Garantía y prelación»): bono garantizado frente a titulización; esquemática.\n"
             "% Generar con: bash Code/generar_figura.sh anx_cedulas_titulizacion\n" + "\n".join(out) + "\n")


if __name__ == "__main__":
    hitos()
    prelacion()
    cedulas_titulizacion()
    print("Escritas: anx_hitos, anx_prelacion, anx_cedulas_titulizacion")
