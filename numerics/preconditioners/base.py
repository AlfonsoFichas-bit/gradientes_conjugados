"""Interfaz común de los precondicionadores."""

from __future__ import annotations

from typing import Any

from ..types import Matrix, Vector


class Preconditioner:
    """Precondicionador simétrico definido positivo ``M``.

    ``apply(r)`` debe resolver ``M z = r`` sin invertir ``M`` explícitamente.
    """

    nombre = "M"
    descripcion = ""

    def apply(self, r: Vector) -> Vector:  # pragma: no cover - interfaz
        raise NotImplementedError

    def matrix(self) -> Matrix:  # pragma: no cover - interfaz
        """Devuelve la matriz explícita ``M`` (para calcular ``kappa``)."""
        raise NotImplementedError

    def parametros(self) -> dict[str, Any]:
        return {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "parametros": self.parametros(),
        }
