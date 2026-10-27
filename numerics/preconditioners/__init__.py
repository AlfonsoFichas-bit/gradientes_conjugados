"""Precondicionadores disponibles."""

from __future__ import annotations

from ..types import Matrix, NumericalError
from .base import Preconditioner
from .jacobi import JacobiPreconditioner
from .ssor import SSORPreconditioner


def jacobi_preconditioner(A: Matrix) -> JacobiPreconditioner:
    """Construye el precondicionador de Jacobi."""
    return JacobiPreconditioner(A)


def ssor_preconditioner(A: Matrix, omega: float = 1.0) -> SSORPreconditioner:
    """Construye el precondicionador SSOR."""
    return SSORPreconditioner(A, omega)


def build_preconditioner(
    nombre: str, A: Matrix, omega: float = 1.0
) -> Preconditioner:
    """Fábrica por nombre: ``"jacobi"`` o ``"ssor"``."""
    clave = (nombre or "").strip().lower()
    if clave == "jacobi":
        return JacobiPreconditioner(A)
    if clave == "ssor":
        return SSORPreconditioner(A, omega)
    raise NumericalError(
        "PRECONDICIONADOR",
        f"Precondicionador desconocido: {nombre!r}. Use 'jacobi' o 'ssor'.",
        "precondicionador",
    )


__all__ = [
    "Preconditioner",
    "JacobiPreconditioner",
    "SSORPreconditioner",
    "jacobi_preconditioner",
    "ssor_preconditioner",
    "build_preconditioner",
]
