"""Autovalores de matrices simétricas mediante el método de Jacobi cíclico.

Se usa para verificar ``lambda_min > 0`` (demostración numérica de que ``A``
es definida positiva) y para calcular ``kappa(A)`` y ``kappa(M^-1 A)``.
"""

from __future__ import annotations

import math

from ..types import Matrix, NumericalError


def jacobi_eigenvalues(
    A: Matrix, tol: float = 1e-14, max_sweeps: int = 100
) -> list[float]:
    """Devuelve los autovalores de ``A`` (simétrica) ordenados de menor a mayor.

    El método aplica rotaciones de Jacobi hasta que la norma de la parte
    fuera de la diagonal es despreciable frente a la escala de la matriz.
    """
    n = len(A)
    if n == 0 or any(len(fila) != n for fila in A):
        raise NumericalError("DIM", "La matriz debe ser cuadrada y no vacía.", "A")
    if n == 1:
        return [float(A[0][0])]

    a = [[float(v) for v in fila] for fila in A]
    escala = max(1.0, max(abs(v) for fila in a for v in fila))

    for _ in range(max_sweeps):
        fuera = math.sqrt(
            math.fsum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        )
        if fuera <= tol * escala:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = a[p][q]
                if abs(apq) <= 1e-18 * escala:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * apq)
                if theta >= 0.0:
                    t = 1.0 / (theta + math.sqrt(1.0 + theta * theta))
                else:
                    t = -1.0 / (-theta + math.sqrt(1.0 + theta * theta))
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = t * c
                app = a[p][p]
                aqq = a[q][q]
                a[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
                a[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
                a[p][q] = 0.0
                a[q][p] = 0.0
                for k in range(n):
                    if k == p or k == q:
                        continue
                    akp = a[k][p]
                    akq = a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[p][k] = a[k][p]
                    a[k][q] = s * akp + c * akq
                    a[q][k] = a[k][q]

    autovalores = sorted(a[i][i] for i in range(n))
    if any(not math.isfinite(v) for v in autovalores):
        raise NumericalError(
            "EIGEN", "El cálculo de autovalores produjo valores no finitos.", "A"
        )
    return autovalores
