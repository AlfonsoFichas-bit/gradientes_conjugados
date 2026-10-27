"""Validaciones matemáticas de entrada.

Todas las funciones lanzan ``NumericalError`` (nunca excepciones genéricas)
para que la capa web pueda mostrar el problema al usuario sin bloquearse.
"""

from __future__ import annotations

import math
import numbers

from .linalg.cholesky import cholesky
from .norms import norm2
from .types import Matrix, NumericalError, ScenarioSpec, SolverConfig, Vector

_SIM_TOL = 1e-10


def _es_numero(valor: object) -> bool:
    return isinstance(valor, numbers.Real) and not isinstance(valor, bool)


def validate_matrix(A: Matrix) -> None:
    """Verifica dimensión, valores finitos, simetría y definición positiva."""
    if not isinstance(A, list) or len(A) == 0:
        raise NumericalError("VACIO", "La matriz A está vacía.", "A")
    n = len(A)
    for i, fila in enumerate(A):
        if not isinstance(fila, list) or len(fila) != n:
            raise NumericalError(
                "DIM",
                f"La matriz A debe ser cuadrada de orden {n}; la fila {i + 1} "
                f"tiene {len(fila) if isinstance(fila, list) else 1} componentes.",
                "A",
            )
        for j, valor in enumerate(fila):
            if not _es_numero(valor):
                raise NumericalError(
                    "NO_NUMERICO",
                    f"El coeficiente a_{i + 1},{j + 1} no es numérico: {valor!r}.",
                    "A",
                )
            if not math.isfinite(float(valor)):
                raise NumericalError(
                    "NO_FINITO",
                    f"El coeficiente a_{i + 1},{j + 1} no es finito.",
                    "A",
                )

    escala = max(1.0, max(abs(float(v)) for fila in A for v in fila))
    for i in range(n):
        for j in range(i + 1, n):
            diferencia = abs(float(A[i][j]) - float(A[j][i]))
            if diferencia > _SIM_TOL * escala:
                raise NumericalError(
                    "ASIMETRICA",
                    f"La matriz A no es simétrica: |a_{i + 1},{j + 1} - "
                    f"a_{j + 1},{i + 1}| = {diferencia:.3e}.",
                    "A",
                )

    # Criterio de Sylvester numérico: si Cholesky termina, A es D.P.
    cholesky([[float(v) for v in fila] for fila in A])


def validate_vector(b: Vector, n: int, nombre: str = "b") -> None:
    """Verifica que ``b`` tenga ``n`` componentes numéricas y finitas."""
    if not isinstance(b, list) or len(b) != n:
        recibido = len(b) if isinstance(b, list) else 1
        raise NumericalError(
            "DIM",
            f"El vector {nombre} tiene {recibido} componentes; se esperaban {n}.",
            nombre,
        )
    for i, valor in enumerate(b):
        if not _es_numero(valor):
            raise NumericalError(
                "NO_NUMERICO",
                f"La componente {nombre}_{i + 1} no es numérica: {valor!r}.",
                nombre,
            )
        if not math.isfinite(float(valor)):
            raise NumericalError(
                "NO_FINITO",
                f"La componente {nombre}_{i + 1} no es finita.",
                nombre,
            )


def validate_system(A: Matrix, b: Vector) -> None:
    """Valida el sistema completo ``A x = b``."""
    validate_matrix(A)
    validate_vector(b, len(A))
    if norm2([float(v) for v in b]) == 0.0:
        raise NumericalError(
            "B_CERO",
            "El vector b es nulo: el criterio ||r_k||/||b|| no está definido.",
            "b",
        )


def validate_config(config: SolverConfig, n: int) -> None:
    """Valida tolerancia, iteraciones máximas, x0 y omega."""
    if not _es_numero(config.tol) or not math.isfinite(float(config.tol)):
        raise NumericalError("TOL", "La tolerancia debe ser un número finito.", "tol")
    if config.tol <= 0.0:
        raise NumericalError(
            "TOL", "La tolerancia debe ser estrictamente positiva.", "tol"
        )
    if not isinstance(config.max_iter, int) or isinstance(config.max_iter, bool):
        raise NumericalError(
            "MAX_ITER", "El número máximo de iteraciones debe ser entero.", "max_iter"
        )
    if config.max_iter < 1:
        raise NumericalError(
            "MAX_ITER", "El número máximo de iteraciones debe ser al menos 1.", "max_iter"
        )
    if config.x0 is not None:
        try:
            validate_vector(config.x0, n, "x0")
        except NumericalError as error:
            raise NumericalError("X0_DIM", error.message, "x0") from error
    if not _es_numero(config.omega) or not math.isfinite(float(config.omega)):
        raise NumericalError("OMEGA", "El parámetro omega debe ser finito.", "omega")
    if not 0.0 < config.omega < 2.0:
        raise NumericalError(
            "OMEGA",
            f"El parámetro omega debe cumplir 0 < omega < 2; se recibió "
            f"{config.omega:.4f}.",
            "omega",
        )


def validate_scenario(spec: ScenarioSpec) -> None:
    """Valida la estructura de un escenario financiero."""
    if not isinstance(spec, ScenarioSpec):
        raise NumericalError("ESCENARIO", "El escenario no es válido.", "escenario")
    n = len(spec.rigidez)
    if n < 2:
        raise NumericalError(
            "DIM", "El escenario debe tener al menos 2 variables.", "rigidez"
        )
    if len(spec.base) != n or len(spec.ajuste_objetivo) != n or len(spec.etiquetas) != n:
        raise NumericalError(
            "DIM",
            "Las rigideces, el presupuesto base, el ajuste objetivo y las "
            "etiquetas deben tener la misma dimensión.",
            "escenario",
        )
    validate_vector(spec.base, n, "base")
    validate_vector(spec.ajuste_objetivo, n, "ajuste_objetivo")
    if any(v < 0.0 for v in spec.base):
        raise NumericalError(
            "BASE", "El presupuesto base no puede tener valores negativos.", "base"
        )
