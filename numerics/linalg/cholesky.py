"""Factorización de Cholesky ``A = L L^T`` para matrices simétricas D.P."""

from __future__ import annotations

import math

from ..types import Matrix, NotPositiveDefiniteError, NumericalError, Vector


def cholesky(A: Matrix) -> Matrix:
    """Calcula el factor triangular inferior ``L`` tal que ``A = L L^T``.

    Solo se lee el triángulo inferior de ``A``. Si aparece un pivote no
    positivo (o no finito) se lanza ``NotPositiveDefiniteError``: es la
    verificación numérica del criterio de Sylvester.
    """
    n = len(A)
    if n == 0 or any(len(fila) != n for fila in A):
        raise NumericalError(
            "DIM", "La matriz debe ser cuadrada y no vacía para aplicar Cholesky.", "A"
        )

    L: Matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            acumulado = math.fsum(L[i][k] * L[j][k] for k in range(j))
            valor = A[i][j] - acumulado
            if i == j:
                if not math.isfinite(valor) or valor <= 0.0:
                    raise NotPositiveDefiniteError(i, valor)
                L[i][i] = math.sqrt(valor)
            else:
                L[i][j] = valor / L[j][j]
    return L


def forward_substitution(L: Matrix, b: Vector, unit_diagonal: bool = False) -> Vector:
    """Resuelve ``L y = b`` para ``L`` triangular inferior."""
    n = len(L)
    y = [0.0] * n
    for i in range(n):
        acumulado = math.fsum(L[i][j] * y[j] for j in range(i))
        if unit_diagonal:
            y[i] = b[i] - acumulado
        else:
            if L[i][i] == 0.0:
                raise NumericalError("SINGULAR", "Diagonal nula en la sustitución directa.", "A")
            y[i] = (b[i] - acumulado) / L[i][i]
    return y


def solve_lt(L: Matrix, y: Vector) -> Vector:
    """Resuelve ``L^T x = y`` sin materializar la transpuesta."""
    n = len(L)
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        acumulado = math.fsum(L[j][i] * x[j] for j in range(i + 1, n))
        if L[i][i] == 0.0:
            raise NumericalError(
                "SINGULAR", "Diagonal nula en la sustitución inversa.", "A"
            )
        x[i] = (y[i] - acumulado) / L[i][i]
    return x


def cholesky_solve(L: Matrix, b: Vector) -> Vector:
    """Resuelve ``A x = b`` usando ``L`` ya calculado."""
    if len(L) != len(b):
        raise NumericalError(
            "DIM",
            f"El vector b tiene {len(b)} componentes; se esperaban {len(L)}.",
            "b",
        )
    y = forward_substitution(L, b)
    return solve_lt(L, y)


def inverse_from_cholesky(L: Matrix) -> Matrix:
    """Inversa de ``A`` a partir de ``L`` (usada para verificar ``kappa(A)``)."""
    n = len(L)
    columnas = []
    for j in range(n):
        e = [0.0] * n
        e[j] = 1.0
        columnas.append(cholesky_solve(L, e))
    return [[columnas[j][i] for j in range(n)] for i in range(n)]
