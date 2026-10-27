"""Operaciones vectoriales y matriciales básicas.

Se usan ``math.fsum`` en los productos internos para reducir el error de
redondeo acumulado: el escenario mal condicionado lo necesita.
"""

from __future__ import annotations

import math

from .types import Matrix, Vector


def dot(u: Vector, v: Vector) -> float:
    """Producto interno ``u·v`` con suma compensada."""
    if len(u) != len(v):
        raise ValueError("Los vectores no tienen la misma dimensión.")
    return math.fsum(a * b for a, b in zip(u, v))


def norm2(v: Vector) -> float:
    """Norma euclidiana ``||v||_2``."""
    return math.sqrt(dot(v, v))


def matvec(A: Matrix, x: Vector) -> Vector:
    """Producto matriz-vector ``A x``."""
    n = len(A)
    if len(x) != n:
        raise ValueError("Dimensiones incompatibles en el producto A x.")
    return [math.fsum(aij * xj for aij, xj in zip(fila, x)) for fila in A]


def transpose(A: Matrix) -> Matrix:
    """Transpuesta de ``A``."""
    n = len(A)
    return [[A[i][j] for i in range(n)] for j in range(n)]


def max_abs(A: Matrix) -> float:
    """Máximo valor absoluto de una matriz."""
    return max((abs(v) for fila in A for v in fila), default=0.0)


def max_abs_diff(A: Matrix, B: Matrix) -> float:
    """Máxima diferencia en valor absoluto entre dos matrices."""
    return max(
        (abs(A[i][j] - B[i][j]) for i in range(len(A)) for j in range(len(A))),
        default=0.0,
    )


def max_abs_vector_diff(u: Vector, v: Vector) -> float:
    """Máxima diferencia en valor absoluto entre dos vectores."""
    return max((abs(a - b) for a, b in zip(u, v)), default=0.0)


def residual(A: Matrix, x: Vector, b: Vector) -> Vector:
    """Residuo ``r = b - A x``."""
    return [bi - ai for bi, ai in zip(b, matvec(A, x))]
