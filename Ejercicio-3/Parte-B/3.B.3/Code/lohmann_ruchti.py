"""Efecto LOHMANN-RUCHTI: flota de k barcos de vida n, amortización lineal y reinversión de las cuotas.

Cada año se amortiza 1/n del precio de cada barco vivo y la cuota se reinvierte en barcos nuevos (divisibles).
Los barcos se retiran al cumplir n años. Escribe las coordenadas de la figura Img/lohmann_ruchti.tikz.
Uso, desde la carpeta del tema: python3 Code/lohmann_ruchti.py
"""
k, n, T = 10.0, 10, 40
compras = {0: k}
flota = [k]
for t in range(1, T + 1):
    vivos = {s: c for s, c in compras.items() if t - n < s <= t - 1 or (s == t - n)}
    cuota = sum(c for s, c in compras.items() if t - n <= s <= t - 1) / n
    compras[t] = cuota
    flota.append(sum(c for s, c in compras.items() if t - n < s <= t))
limite = 2 * n / (n + 1) * k
print('límite 2n/(n+1)k =', round(limite, 3))
print(' '.join(f'({t},{f:.3f})' for t, f in enumerate(flota)))
