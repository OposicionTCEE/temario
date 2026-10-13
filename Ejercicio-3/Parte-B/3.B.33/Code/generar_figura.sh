#!/bin/bash
# Genera Img/<nombre>.pdf a partir de Img/<nombre>.tikz (solo el tikzpicture) con el pdflatex de MacTeX.
# Uso, desde la carpeta del tema:  bash Code/generar_figura.sh SCN_matriz_vacia
set -e
TEMA="$(cd "$(dirname "$0")/.." && pwd)"
NOMBRE="$1"
TMP="$(mktemp -d)"
cat > "$TMP/wrap.tex" <<'TEX'
\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{mathptmx}
\usepackage{ebgaramond}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{matrix,positioning,calc,fit,arrows.meta,decorations.pathreplacing}
\begin{document}
\hoffset=-1in \voffset=-1in
\newsavebox{\fig}
\sbox{\fig}{\input{\figfile}}
\pdfpagewidth=\wd\fig \pdfpageheight=\dimexpr\ht\fig+\dp\fig\relax
\shipout\hbox{\usebox{\fig}}
\end{document}
TEX
cd "$TMP"
/Library/TeX/texbin/pdflatex -interaction=nonstopmode -jobname="$NOMBRE" "\def\figfile{$TEMA/Img/$NOMBRE.tikz}\input{wrap.tex}" > "$NOMBRE.log" 2>&1 || true
if [ -f "$NOMBRE.pdf" ]; then cp "$NOMBRE.pdf" "$TEMA/Img/"; echo "Generado Img/$NOMBRE.pdf"; else grep -E "^!" -A3 "$NOMBRE.log"; exit 1; fi
