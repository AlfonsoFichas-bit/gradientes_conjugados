"""Construcción de la matriz del modelo y del término independiente.

Modelo financiero
-----------------
``A = D^(1/2) R D^(1/2)``, donde:

* ``D = diag(d_i)`` mide la *rigidez* (inercia) de cada línea presupuestaria.
* ``R_ij = rho^|i-j|`` es una matriz de correlación AR(1) que representa la
  interdependencia entre categorías contiguas.
* ``b = A x*`` se construye a partir de un ajuste objetivo ``x*`` conocido,
  de modo que la solución exacta queda disponible para verificar el software
  (no es una proyección financiera).
"""

from __future__ import annotations

import math

from .norms import matvec
from .types import Matrix, NumericalError, Vector

RHO_TOL = 1e-12


def build_A(rigidez: Vector, rho: float) -> Matrix:
    """Construye ``A = D^(1/2) R D^(1/2)`` con ``R_ij = rho^|i-j|``.

    Parámetros
    ----------
    rigidez:
        Vector de rigideces ``d_i > 0`` (una por categoría).
    rho:
        Correlación entre categorías contiguas; debe cumplir ``|rho| < 1``.

    Raises
    ------
    NumericalError
        Si la dimensión es menor que 2, alguna rigidez no es positiva o
        ``rho`` está fuera del intervalo abierto ``(-1, 1)``.
    """
    n = len(rigidez)
    if n < 2:
        raise NumericalError(
            "DIM",
            f"La matriz debe tener al menos 2 filas; se recibieron {n}.",
            "rigidez",
        )
    if not isinstance(rho, (int, float)) or not math.isfinite(rho):
        raise NumericalError("RHO", "El parámetro rho debe ser un número finito.", "rho")
    if abs(rho) >= 1.0:
        raise NumericalError(
            "RHO",
            f"El parámetro rho debe cumplir |rho| < 1; se recibió {rho:.4f}.",
            "rho",
        )
    for i, d in enumerate(rigidez):
        if not isinstance(d, (int, float)) or not math.isfinite(d) or d <= 0.0:
            raise NumericalError(
                "RIGIDEZ",
                f"La rigidez d_{i + 1} debe ser un número finito mayor que cero; "
                f"se recibió {d!r}.",
                "rigidez",
            )

    raiz = [math.sqrt(float(d)) for d in rigidez]
    A: Matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            valor = raiz[i] * raiz[j] * (rho ** abs(i - j))
            A[i][j] = valor
            A[j][i] = valor
    return A


def build_b(A: Matrix, ajuste_objetivo: Vector) -> Vector:
    """Calcula ``b = A x*`` para que ``x*`` sea la solución exacta del sistema."""
    if len(A) != len(ajuste_objetivo):
        raise NumericalError(
            "DIM",
            f"El ajuste objetivo tiene {len(ajuste_objetivo)} componentes; "
            f"se esperaban {len(A)}.",
            "ajuste_objetivo",
        )
    return matvec(A, ajuste_objetivo)


def ar1_precision(n: int, rho: float) -> Matrix:
    """Inversa exacta de la matriz de correlación ``R_ij = rho^|i-j|``.

    ``R^-1`` es tridiagonal y simétrica:

    * diagonal: ``1`` en los extremos y ``1 + rho^2`` en el interior,
    * fuera de la diagonal: ``-rho``,

    todo dividido por ``1 - rho^2``. Para ``|rho| < 1`` es estrictamente
    diagonalmente dominante, lo que demuestra formalmente que ``R`` es D.P.
    """
    if n < 2:
        raise NumericalError("DIM", "Se requieren al menos 2 filas.", "n")
    if not isinstance(rho, (int, float)) or not math.isfinite(rho) or abs(rho) >= 1.0:
        raise NumericalError(
            "RHO", f"El parámetro rho debe cumplir |rho| < 1; se recibió {rho!r}.", "rho"
        )
    factor = 1.0 / (1.0 - rho * rho)
    P: Matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        P[i][i] = ((1.0 if i in (0, n - 1) else 1.0 + rho * rho)) * factor
        if i + 1 < n:
            P[i][i + 1] = -rho * factor
            P[i + 1][i] = -rho * factor
    return P
