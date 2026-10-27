"""Factorización LU con pivoteo parcial (Doolittle).

Se utiliza como *oráculo de prueba* del método de referencia: la solución de
Cholesky debe coincidir con la de LU para los sistemas bien planteados.
"""

from __future__ import annotations

import math

from ..types import Matrix, NumericalError, Vector

_EPS = 1e-300


def lu_factor(A: Matrix) -> tuple[Matrix, list[int]]:
    """Factoriza ``P A = L U`` y devuelve ``(LU, perm)``.

    ``LU`` guarda ``L`` (sin la diagonal unitaria) bajo la diagonal y ``U``
    sobre ella. ``perm`` es la permutación de filas aplicada.
    """
    n = len(A)
    if n == 0 or any(len(fila) != n for fila in A):
        raise NumericalError("DIM", "La matriz debe ser cuadrada y no vacía.", "A")

    LU = [list(fila) for fila in A]
    perm = list(range(n))

    for k in range(n):
        pivote = max(range(k, n), key=lambda i: abs(LU[i][k]))
        if abs(LU[pivote][k]) < _EPS:
            raise NumericalError(
                "SINGULAR",
                f"La matriz es singular: pivote nulo en la columna {k + 1}.",
                "A",
            )
        if pivote != k:
            LU[k], LU[pivote] = LU[pivote], LU[k]
            perm[k], perm[pivote] = perm[pivote], perm[k]
        for i in range(k + 1, n):
            LU[i][k] /= LU[k][k]
            factor = LU[i][k]
            for j in range(k + 1, n):
                LU[i][j] -= factor * LU[k][j]
    return LU, perm


def lu_solve(LU: Matrix, perm: list[int], b: Vector) -> Vector:
    """Resuelve ``A x = b`` con la factorización devuelta por ``lu_factor``."""
    n = len(LU)
    if len(b) != n:
        raise NumericalError(
            "DIM",
            f"El vector b tiene {len(b)} componentes; se esperaban {n}.",
            "b",
        )
    y = [b[perm[i]] for i in range(n)]
    for i in range(n):
        y[i] = math.fsum([y[i]] + [-LU[i][j] * y[j] for j in range(i)])
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        acumulado = math.fsum(LU[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (y[i] - acumulado) / LU[i][i]
    return x
