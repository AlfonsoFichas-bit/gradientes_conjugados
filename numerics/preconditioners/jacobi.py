"""Precondicionador de Jacobi (diagonal)."""

from __future__ import annotations

import math
from typing import Any

from ..types import Matrix, NumericalError, Vector
from .base import Preconditioner


class JacobiPreconditioner(Preconditioner):
    """``M = diag(a_11, ..., a_nn)``.

    Corrige el mal escalamiento de la diagonal; es el precondicionador por
    defecto del proyecto.
    """

    nombre = "Jacobi"
    descripcion = "Precondicionador diagonal M = diag(A)."

    def __init__(self, A: Matrix) -> None:
        n = len(A)
        if n == 0 or any(len(fila) != n for fila in A):
            raise NumericalError(
                "DIM", "La matriz debe ser cuadrada para construir Jacobi.", "A"
            )
        self._diag: Vector = []
        for i in range(n):
            valor = float(A[i][i])
            if not math.isfinite(valor) or valor <= 0.0:
                raise NumericalError(
                    "DIAG",
                    f"El elemento diagonal a_{i + 1},{i + 1} debe ser positivo; "
                    f"se recibió {valor:.3e}.",
                    "A",
                )
            self._diag.append(valor)
        self._n = n

    def apply(self, r: Vector) -> Vector:
        if len(r) != self._n:
            raise NumericalError(
                "DIM", "El residuo no coincide con la dimensión del precondicionador.", "b"
            )
        return [ri / di for ri, di in zip(r, self._diag)]

    def matrix(self) -> Matrix:
        n = self._n
        M = [[0.0] * n for _ in range(n)]
        for i, valor in enumerate(self._diag):
            M[i][i] = valor
        return M

    def parametros(self) -> dict[str, Any]:
        return {"diagonal": list(self._diag)}
