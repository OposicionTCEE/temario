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
    out.append(r"\node[caja, fill=black!5] (ten) at (1.75,-1.05) {Tenedores\\de cédulas};")
    out.append(r"\draw[->, thick] ([xshift=-0.3cm]ten.north) -- node[left, font=\scriptsize] {2} (cob.south);")
    out.append(r"\draw[->, thick] ([xshift=0.3cm]ten.north) -- node[right, font=\scriptsize] {1} (3.4,0);")
    out.append(r"\node[align=left, font=\scriptsize, anchor=west] at (2.85,-1.05) {1: derecho frente al banco\\2: preferencia sobre\\la cobertura};")
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
    out.append(rf"\node[caja, fill=black!5] (inv) at ({dx + 4.75:.2f},-1.05) {{Inversores}};")
    out.append(r"\draw[->, thick] (ori.east) -- node[above, font=\scriptsize, align=center] {vende\\los préstamos} (pre.west);")
    out.append(rf"\draw[->, thick] ({dx + 4.75:.2f},0) -- node[right, font=\scriptsize] {{bonos por tramos}} (inv.north);")
    out.append(r"\end{tikzpicture}")
    escribir("anx_cedulas_titulizacion", "% Figura (Anexo II, II.2, «Garantía y prelación»): bono garantizado frente a titulización; esquemática.\n"
             "% Generar con: bash Code/generar_figura.sh anx_cedulas_titulizacion\n" + "\n".join(out) + "\n")


# =====================  Tanda A9 (II.3 Emisión, II.4 Negociación, II.5 Segmentos)  =====================
# anx_mercado_secundario: los dos niveles del mercado secundario (inversores y creadores de mercado; creadores de
#   mercado entre sí) y la compensación y liquidación; esquemática.
# anx_diferenciales_euro: rendimiento a 10 años de España, Italia, Portugal y Francia menos el de Alemania (OCDE, FRED:
#   IRLTLT01xxM156N), medias mensuales desde 1993-07; líneas en el euro (1999-01), el compromiso del BCE (2012-07) y el
#   instrumento para la protección de la transmisión (2022-07). Grecia no se dibuja (27,4 puntos en 2012-02).
def mercado_secundario():
    out = [r"\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=5pt]},"
           r" caja/.style={draw=black!60, rounded corners=2pt, align=center, inner sep=4pt}]"]
    out.append(r"\node[caja, fill=black!5, text width=3.0cm] (inv) at (0,0) {Inversores finales\\{\scriptsize fondos, aseguradoras,"
               r" bancos, bancos centrales}};")
    out.append(r"\node[caja, fill=black!15, text width=3.0cm] (cm) at (5.6,0) {Creadores de mercado\\{\scriptsize inventario propio}};")
    out.append(r"\node[caja, fill=black!5, text width=3.0cm] (cm2) at (11.2,0) {Otros creadores\\de mercado};")
    out.append(r"\draw[<->, thick] (inv.east) -- node[above, font=\scriptsize, align=center] {precios de compra y venta}"
               r" node[below, font=\scriptsize, align=center] {teléfono o plataformas\\con varios creadores} (cm.west);")
    out.append(r"\draw[<->, thick] (cm.east) -- node[above, font=\scriptsize, align=center] {cobertura y reparto}"
               r" node[below, font=\scriptsize, align=center] {plataformas entre\\intermediarios} (cm2.west);")
    out.append(r"\node[caja, fill=black!10, text width=12.4cm] (liq) at (5.6,-2.4) {Compensación y liquidación:"
               r" cámaras de contrapartida central y depositarios centrales};")
    for n in ("inv", "cm", "cm2"):
        out.append(rf"\draw[->, black!50, densely dashed] ({n}.south) -- ({n}.south |- liq.north);")
    out.append(r"\end{tikzpicture}")
    escribir("anx_mercado_secundario", "% Figura (Anexo II, II.4, «Estructura»): niveles del mercado secundario de bonos; esquemática.\n"
             "% Generar con: bash Code/generar_figura.sh anx_mercado_secundario\n" + "\n".join(out) + "\n")


PAISES = [("IRLTLT01ESM156N", "España", "very thick"), ("IRLTLT01ITM156N", "Italia", "thick, densely dashed"),
          ("IRLTLT01PTM156N", "Portugal", "thick, black!45"), ("IRLTLT01FRM156N", "Francia", "thick, densely dotted")]


def diferenciales_euro():
    de = {d[:7]: v for d, v in serie("IRLTLT01DEM156N").items()}
    out = [r"\begin{tikzpicture}[font=\footnotesize]"]
    x0, x1, ymin, ymax = 1993.5, 2026.75, -0.6, 12.8
    out.append(rf"\begin{{axis}}[width=14cm, height=6.2cm, axis lines=left, xmin={x0}, xmax={x1}, ymin={ymin}, ymax={ymax},"
               r" xtick={1995,2000,2005,2010,2015,2020,2025}, ytick={0,2,4,6,8,10,12},"
               r" /pgf/number format/use comma, /pgf/number format/1000 sep={}, tick label style={font=\scriptsize},"
               r" label style={font=\footnotesize}, ylabel={Puntos porcentuales}, clip=false]")
    out.append(rf"\draw[black!30] (axis cs:{x0},0) -- (axis cs:{x1},0);")
    for x, txt in ((1999.0, "euro"), (2012.5, "BCE, 2012"), (2022.5, "BCE, 2022")):
        out.append(rf"\draw[black!35, densely dashed] (axis cs:{x:.2f},{ymin}) -- (axis cs:{x:.2f},{ymax});")
        out.append(rf"\node[anchor=south, font=\scriptsize, text=black!65] at (axis cs:{x:.2f},{ymax}) {{{txt}}};")
    finales = []
    resumen = []
    for codigo, nombre, est in PAISES:
        x = {d[:7]: v for d, v in serie(codigo).items()}
        meses = [m for m in sorted(x) if m in de and m >= "1993-07"]
        pts = [(_anio(m), x[m] - de[m]) for m in meses]
        out.append(rf"\addplot[{est}, mark=none] coordinates {{{coords(pts)}}};")
        finales.append((pts[-1][1], nombre))
        mx = max(pts, key=lambda p: p[1])
        resumen.append(f"{nombre}: máx. {mx[1]:.2f} ({mx[0]:.2f}), último {pts[-1][1]:.2f} ({meses[-1]})")
    out += _etiquetas(x1, x1 + 0.6, finales, 0.75)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    escribir("anx_diferenciales_euro", "% Figura (Anexo II, II.5, «Deuda pública»): primas a 10 años frente a Alemania, medias mensuales (OCDE);\n"
             f"% {'; '.join(resumen)}.\n% Generar con: bash Code/generar_figura.sh anx_diferenciales_euro\n" + "\n".join(out) + "\n")


if __name__ == "__main__":
    hitos()
    prelacion()
    cedulas_titulizacion()
    mercado_secundario()
    diferenciales_euro()
    print("Escritas: anx_hitos, anx_prelacion, anx_cedulas_titulizacion, anx_mercado_secundario, anx_diferenciales_euro")
