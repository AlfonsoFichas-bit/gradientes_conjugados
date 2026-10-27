"""Métodos iterativos disponibles."""

from .cg import cg, conjugate_gradient, pcg

__all__ = ["cg", "pcg", "conjugate_gradient"]
