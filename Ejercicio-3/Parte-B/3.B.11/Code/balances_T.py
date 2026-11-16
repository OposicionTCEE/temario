#!/usr/bin/env python3
"""Balances en T del bloque III del 3.B.11 (la posición de inversión internacional), con la misma base que las
cuentas en T del bloque II (Code/cuentas_T.py): una T continua con bloques apilados, letra de 8 puntos.

En un balance, los activos exteriores van a la izquierda y los pasivos exteriores a la derecha, y la posición neta,
PII = AF - P, cierra cada bloque en el lado derecho (como el patrimonio neto de un balance).
  - b3_pii_construccion: balance al final de t-1 + variaciones del periodo (transacciones, revalorizaciones y otros
    cambios del volumen) = balance al final de t; las dos posiciones netas de arriba se suman en la de abajo.
  - b3_pii_composicion: la misma PII deudora (a < p) con dos composiciones, antes y después de una depreciación de la
    moneda nacional en una proporción delta: (a) pasivos en capital y en moneda nacional, la PII mejora;
    (b) pasivos en deuda a corto plazo y en divisas, la PII empeora.
Uso, desde la carpeta del tema (y registrar en la MISMA orden):
    python3 -I -B Code/balances_T.py && for f in b3_pii_construccion b3_pii_composicion; do bash Code/generar_figura.sh $f; done
Fuente: FMI (2009), cap. 7 (conciliación de la PII); SEC 2010 (balances).
"""
import os
import sys

FILA = 0.53          # alto de una fila (cm), el de Code/cuentas_T.py
SANGRIA = r'\hspace*{1em}'


def cabecera(lineas, x0, ancho, izq, der, y0=0.0):
    col = ancho / 2
    lineas += [
        rf'\node[font=\small\bfseries] at ({x0 + col / 2:.2f},{y0 + 0.4:.2f}) {{{izq}}};',
        rf'\node[font=\small\bfseries] at ({x0 + col + col / 2:.2f},{y0 + 0.4:.2f}) {{{der}}};',
        rf'\draw[thick] ({x0:.2f},{y0:.2f}) -- ({x0 + ancho:.2f},{y0:.2f});',
    ]


def bloques(lineas, x0, ancho, lista, prefijo, y0=0.0):
    """Dibuja bloques apilados (título a la izquierda, anotaciones a cada lado y saldo a la derecha).
    Devuelve la y final y los nombres de los nodos de saldo."""
    col = ancho / 2
    y = y0
    saldos = []
    for k, b in enumerate(lista):
        if k > 0:
            lineas.append(rf'\draw[black!55] ({x0:.2f},{y:.3f}) -- ({x0 + ancho:.2f},{y:.3f});')
        # fila 0: título; filas 1..n: anotaciones; fila n+1: saldo (a la derecha)
        lineas.append(rf'\node[ent, font=\footnotesize\bfseries] at ({x0 + 0.12:.2f},{y - FILA * 0.5 - 0.08:.3f}) {{{b["titulo"]}}};')
        n = max(len(b['izq']), len(b['der']))
        for lado, filas in (('izq', b['izq']), ('der', b['der'])):
            x = x0 + 0.12 if lado == 'izq' else x0 + col + 0.18
            for i, texto in enumerate(filas):
                yy = y - FILA * (i + 1.5) - 0.08
                lineas.append(rf'\node[ent] at ({x:.2f},{yy:.3f}) {{{texto}}};')
        ys = y - FILA * (n + 1.5) - 0.08
        nombre = f'{prefijo}{k}'
        lineas.append(rf'\node[sal] ({nombre}) at ({x0 + col + 0.18:.2f},{ys:.3f}) {{\textbf{{{b["saldo"]}}}}};')
        saldos.append(nombre)
        y -= FILA * (n + 2) + 0.16
    lineas.append(rf'\draw[thick] ({x0 + col:.2f},{y0:.2f}) -- ({x0 + col:.2f},{y:.3f});')
    return y, saldos


def inicio(comentario, ancho_col):
    return [
        f'% {comentario}',
        '% Generada por Code/balances_T.py (no editar a mano). En letras; fuente: FMI (2009), cap. 7; SEC 2010.',
        r'\begin{tikzpicture}[',
        r'  font=\footnotesize,',
        r'  >={Stealth[length=1.8mm]},',
        r'  every node/.append style={execute at begin node={\hyphenpenalty=10000\exhyphenpenalty=10000}},',
        rf'  ent/.style={{anchor=west, align=left, text width={ancho_col - 0.35:.2f}cm, inner sep=1.5pt}},',
        r'  sal/.style={anchor=west, align=left, inner sep=1.5pt},',
        r'  arr/.style={->, thick, black!55, rounded corners=2pt},',
        ']',
    ]


def construccion():
    ancho = 15.6
    lineas = inicio('Cuerpo, 4.1.1: del balance inicial al final; la posición neta final es la inicial más las '
                    'transacciones (CF), las revalorizaciones (RV) y los otros cambios del volumen (OV).', ancho / 2)
    cabecera(lineas, 0, ancho, 'Activos exteriores', 'Pasivos exteriores y posición neta')
    lista = [
        dict(titulo=r'Balance al final de $t-1$',
             izq=[r'Activos exteriores, $AF_{t-1}$'],
             der=[r'Pasivos exteriores, $P_{t-1}$'],
             saldo=r'Posición neta, $PII_{t-1}=AF_{t-1}-P_{t-1}$'),
        dict(titulo=r'Variaciones del periodo $t$',
             izq=[r'Transacciones: adquisición neta, $\Delta AF_t$', 'Revalorizaciones de los activos',
                  'Otros cambios del volumen de los activos'],
             der=[r'Transacciones: contracción neta, $\Delta P_t$', 'Revalorizaciones de los pasivos',
                  'Otros cambios del volumen de los pasivos'],
             saldo=r'Variación de la posición, $CF_t+RV_t+OV_t$'),
        dict(titulo=r'Balance al final de $t$',
             izq=[r'Activos exteriores, $AF_t$'],
             der=[r'Pasivos exteriores, $P_t$'],
             saldo=r'Posición neta, $PII_t=PII_{t-1}+CF_t+RV_t+OV_t$'),
    ]
    y, s = bloques(lineas, 0, ancho, lista, 'S')
    xr = ancho + 0.35
    lineas += [
        rf'\coordinate (X) at ({xr:.2f},0);',
        rf'\draw[arr] ({s[0]}.east) -- ({s[0]}.east -| X) |- ({s[2]}.east);',
        rf'\draw[thick, black!55] ({s[1]}.east) -- ({s[1]}.east -| X);',
        rf'\node[font=\small, fill=white, inner sep=1pt] at ({s[1]}.east -| X) {{$+$}};',
        r'\end{tikzpicture}%',
    ]
    return '\n'.join(lineas) + '\n'


def composicion():
    ancho = 7.3
    sep = 1.0
    lineas = inicio('Cuerpo, 4.1.2: la misma PII deudora (a < p) con dos composiciones, antes y después de una '
                    'depreciación de la moneda nacional en una proporción delta.', ancho / 2)
    paneles = [
        (r'(a) Pasivos en capital y en moneda nacional', [
            dict(titulo='Antes', izq=[r'En divisas, $a$'], der=[r'En moneda nacional, $p$'],
                 saldo=r'$PII=a-p<0$'),
            dict(titulo=r'Tras una depreciación, $\delta$', izq=[r'$a\,(1+\delta)$'], der=[r'$p$'],
                 saldo=r'$PII=a\,(1+\delta)-p\ \uparrow$'),
        ]),
        (r'(b) Pasivos en deuda a corto plazo y en divisas', [
            dict(titulo='Antes', izq=[r'En divisas, $a$'], der=[r'En divisas, $p$'],
                 saldo=r'$PII=a-p<0$'),
            dict(titulo=r'Tras una depreciación, $\delta$', izq=[r'$a\,(1+\delta)$'], der=[r'$p\,(1+\delta)$'],
                 saldo=r'$PII=(a-p)(1+\delta)\ \downarrow$'),
        ]),
    ]
    for j, (titulo, lista) in enumerate(paneles):
        x0 = j * (ancho + sep)
        lineas.append(rf'\node[font=\footnotesize\bfseries] at ({x0 + ancho / 2:.2f},1.05) {{{titulo}}};')
        cabecera(lineas, x0, ancho, 'Activos', 'Pasivos')
        bloques(lineas, x0, ancho, lista, f'P{j}S')
    lineas.append(r'\end{tikzpicture}%')
    return '\n'.join(lineas) + '\n'


def main():
    tema = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for nombre, f in (('b3_pii_construccion', construccion), ('b3_pii_composicion', composicion)):
        with open(os.path.join(tema, 'Img', nombre + '.tikz'), 'w', encoding='utf-8') as fh:
            fh.write(f())
        print('Escrito Img/' + nombre + '.tikz')


if __name__ == '__main__':
    sys.exit(main())
