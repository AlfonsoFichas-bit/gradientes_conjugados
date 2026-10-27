"""Precondicionador SSOR.

Para ``0 < omega < 2`` la matriz

    M = 1/(omega (2 - omega)) * (D + omega L) D^-1 (D + omega U)

es simétrica definida positiva. Se aplica resolviendo dos sustituciones
triangulares, sin invertir ``M``:

    (D + omega L) u = omega (2 - omega) r
    (D + omega U) z = D u

que equivalen a ``z = M^-1 r``.
"""

from __future__ import annotations

import math
from typing import Any

from ..types import Matrix, NumericalError, Vector
from .base import Preconditioner


class SSORPreconditioner(Preconditioner):
    """Precondicionador SSOR con parámetro de relajación ``omega``."""

    nombre = "SSOR"
    descripcion = "Precondicionador SSOR simétrico (barrido directo e inverso)."

    def __init__(self, A: Matrix, omega: float = 1.0) -> None:
        n = len(A)
        if n == 0 or any(len(fila) != n for fila in A):
            raise NumericalError(
                "DIM", "La matriz debe ser cuadrada para construir SSOR.", "A"
            )
        if not isinstance(omega, (int, float)) or not math.isfinite(float(omega)):
            raise NumericalError("OMEGA", "El parámetro omega debe ser finito.", "omega")
        if not 0.0 < float(omega) < 2.0:
            raise NumericalError(
                "OMEGA",
                f"El parámetro omega debe cumplir 0 < omega < 2; se recibió "
                f"{float(omega):.4f}.",
                "omega",
            )
        self._A = [[float(v) for v in fila] for fila in A]
        self._omega = float(omega)
        self._n = n
        self._diag: Vector = []
        for i in range(n):
            valor = self._A[i][i]
            if not math.isfinite(valor) or valor <= 0.0:
                raise NumericalError(
                    "DIAG",
                    f"El elemento diagonal a_{i + 1},{i + 1} debe ser positivo; "
                    f"se recibió {valor:.3e}.",
                    "A",
                )
            self._diag.append(valor)

    @property
    def omega(self) -> float:
        return self._omega

    def apply(self, r: Vector) -> Vector:
        if len(r) != self._n:
            raise NumericalError(
                "DIM", "El residuo no coincide con la dimensión del precondicionador.", "b"
            )
        n = self._n
        w = self._omega
        factor = w * (2.0 - w)
        A = self._A
        d = self._diag

        u = [0.0] * n
        for i in range(n):
            acumulado = math.fsum(A[i][j] * u[j] for j in range(i))
            u[i] = (factor * r[i] - w * acumulado) / d[i]

        z = [0.0] * n
        for i in range(n - 1, -1, -1):
            acumulado = math.fsum(A[i][j] * z[j] for j in range(i + 1, n))
            z[i] = u[i] - (w * acumulado) / d[i]
        return z

    def matrix(self) -> Matrix:
        n = self._n
        w = self._omega
        A = self._A
        d = self._diag
        B = [[0.0] * n for _ in range(n)]
        for i in range(n):
            B[i][i] = d[i]
            for j in range(i):
                B[i][j] = w * A[i][j]
        T = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1):
                T[i][j] = math.fsum(B[i][k] * B[j][k] / d[k] for k in range(j + 1))
                T[j][i] = T[i][j]
        factor = 1.0 / (w * (2.0 - w))
        return [[factor * valor for valor in fila] for fila in T]

    def parametros(self) -> dict[str, Any]:
        return {"omega": self._omega}
