#!/usr/bin/env python3
"""Mide las páginas de TEXTO del cuerpo del 3.B.3 (tope del usuario: 19-20 pp sin figuras ni notas al pie, 20/10/2026).

Crea una copia de main.tex en una carpeta temporal con \\footnote e \\imagenfit anulados, la compila dos veces con
pdflatex y escribe la página de inicio de cada bloque y apartado (del índice .stc). Si existe el material pendiente
en magenta, le pone un \\clearpage delante para que no se mezcle con el texto ya redactado.
Con el PDF resultante, `swift Code/pdf_lineas_por_pagina.swift <pdf>` da las líneas de cada página (para estimar la
última página de un bloque) y `swift Code/pdf_paginas_a_png.swift <pdf> <carpeta> 1.3 <páginas…>` las dibuja en PNG.
Uso, desde la carpeta del tema:  python3 Code/medir_paginas_texto.py
"""
import os
import re
import subprocess
import tempfile

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(TEMA, "main.tex"), encoding="utf-8").read()
s = s.replace("\\begin{document}", "\\begin{document}\n\\renewcommand{\\footnote}[1]{}"
              "\\renewcommand{\\imagenfit}[4][]{}\\renewcommand{\\imagenfithorizontal}[3]{}", 1)
s = s.replace("\\textcolor{magenta}{MATERIAL PENDIENTE", "\\clearpage\\textcolor{magenta}{MATERIAL PENDIENTE", 1)
s = s.replace("\\graphicspath{{Img/}}", "\\graphicspath{{" + os.path.join(TEMA, "Img") + "/}}")
tmp = tempfile.mkdtemp(prefix="medida_3B3_")
open(os.path.join(tmp, "medida.tex"), "w", encoding="utf-8").write(s)
for _ in range(2):
    subprocess.run(["/Library/TeX/texbin/pdflatex", "-interaction=nonstopmode", "medida.tex"], cwd=tmp,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
stc = open(os.path.join(tmp, "medida.stc"), encoding="utf-8", errors="ignore").read()
for num, titulo, pag in re.findall(r"numberline \{([0-9.]+)\}(.*?)\}\{(\d+)\}\{(?:section|subsection)", stc):
    print(f"{pag:>4}  {num:6s} {titulo[:80]}")
print("PDF de medida:", os.path.join(tmp, "medida.pdf"))
