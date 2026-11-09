"""3.B.14, figura b3_bandas (cuerpo, bloque 3, 4.3; notas del usuario, tanda 5 de los bloques 2-3, 09/11/2026): simulación
ilustrativa de un tipo de cambio con chartistas y fundamentalistas y una banda de costes de transacción alrededor del valor
fundamental, a partir de DE GRAUWE y GRIMALDI (2005). El valor fundamental es constante (cero) para que se vea que el tipo de cambio
se mueve sin noticias. Dentro de la banda, |s| <= C, a los fundamentalistas no les compensa operar y dominan los chartistas, que
extrapolan la tendencia: la variación de cada periodo es una fracción PERSIST de la anterior más un ruido. Fuera de la banda, los
fundamentalistas operan y empujan el tipo de cambio hacia dentro, con fuerza FUERZA sobre lo que se ha salido. No es una calibración:
solo ilustra el mecanismo. Imprime las coordenadas que se pegan en Img/b3_bandas.tikz.
Uso, desde la carpeta del tema: python3 -I Code/sim_b3_bandas.py [semilla]"""
import random
import sys

C = 2.5          # semiancho de la banda
PERSIST = 0.82   # peso de la última variación en la regla de los chartistas
RUIDO = 0.38     # desviación típica del ruido dentro de la banda
FUERZA = 0.55    # fuerza con que los fundamentalistas devuelven el tipo de cambio a la banda
T = 100


def simula(semilla):
    rnd = random.Random(semilla)
    s, m, serie = 0.0, 0.0, [0.0]
    for _ in range(T):
        if abs(s) <= C:
            m = PERSIST * m + rnd.gauss(0.0, RUIDO)
        else:
            signo = 1.0 if s > 0 else -1.0
            m = -FUERZA * (s - signo * C) - 0.2 * signo + rnd.gauss(0.0, 0.12)
        s += m
        serie.append(s)
    return serie


if __name__ == "__main__":
    semilla = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    serie = simula(semilla)
    fuera = sum(1 for v in serie if abs(v) > C)
    print("% semilla", semilla, "| máximo", round(max(serie), 2), "| mínimo", round(min(serie), 2), "| periodos fuera de la banda", fuera)
    print(" ".join("(%d,%.2f)" % (t, v) for t, v in enumerate(serie)))
