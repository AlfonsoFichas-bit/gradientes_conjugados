"""Métricas de error por variable y análisis de condicionamiento."""

from __future__ import annotations

import math

from .linalg.cholesky import cholesky, forward_substitution
from .linalg.eigen import jacobi_eigenvalues
from .norms import matvec, norm2
from .preconditioners.base import Preconditioner
from .types import Matrix, Metrics, NumericalError, VariableError, Vector

_CERO = 0.0


def kappa(A: Matrix) -> float:
    """Número de condición espectral ``kappa_2(A)`` para ``A`` simétrica D.P."""
    autovalores = jacobi_eigenvalues(A)
    if autovalores[0] <= 0.0:
        raise NumericalError(
            "NO_SPD",
            "No se puede calcular kappa(A): la matriz no es definida positiva.",
            "A",
        )
    return autovalores[-1] / autovalores[0]


def _matriz_de(M: Matrix | Preconditioner) -> Matrix:
    return M.matrix() if isinstance(M, Preconditioner) else M


def kappa_preconditioned(
    A: Matrix, M: Matrix | Preconditioner | None
) -> float:
    """``kappa_2(M^-1 A)`` calculado como ``kappa_2(C)`` con
    ``C = M^(-1/2) A M^(-1/2)`` (semejante a ``M^-1 A`` y simétrica).

    ``M = None`` equivale a ``M = I`` (GC sin precondicionar).
    """
    if M is None:
        return kappa(A)

    matriz_m = _matriz_de(M)
    if any(not math.isfinite(v) for fila in matriz_m for v in fila):
        raise NumericalError(
            "PRECONDICIONADOR", "El precondicionador contiene valores no finitos.", "M"
        )
    L = cholesky(matriz_m)
    n = len(A)

    # Y = L^-1 A
    Y: Matrix = [[0.0] * n for _ in range(n)]
    for j in range(n):
        columna = forward_substitution(L, [float(A[i][j]) for i in range(n)])
        for i in range(n):
            Y[i][j] = columna[i]

    # C = L^-1 Y^T, simétrica por construcción (se promedia para limpiar redondeo)
    C: Matrix = [[0.0] * n for _ in range(n)]
    for j in range(n):
        fila = forward_substitution(L, [Y[j][i] for i in range(n)])
        for i in range(n):
            C[i][j] = fila[i]
    for i in range(n):
        for j in range(i + 1, n):
            promedio = 0.5 * (C[i][j] + C[j][i])
            C[i][j] = promedio
            C[j][i] = promedio

    autovalores = jacobi_eigenvalues(C)
    if autovalores[0] <= 0.0:
        raise NumericalError(
            "NO_SPD",
            "M^-1 A no es definida positiva: revise el precondicionador.",
            "M",
        )
    return autovalores[-1] / autovalores[0]


def global_relative_residual(A: Matrix, x: Vector, b: Vector) -> float:
    """``||b - A x||_2 / ||b||_2`` (requiere ``||b||_2 != 0``)."""
    norma_b = norm2(b)
    if norma_b == 0.0:
        raise NumericalError(
            "B_CERO", "El residuo relativo no está definido para b = 0.", "b"
        )
    r = [bi - ai for bi, ai in zip(b, matvec(A, x))]
    return norm2(r) / norma_b


def variable_errors(
    referencia: Vector,
    obtenido: Vector,
    etiquetas: list[str] | None = None,
    unidad: str = "millones de Bs",
) -> list[VariableError]:
    """Calcula ``E_a``, ``E_r`` y ``E_p`` para cada variable."""
    if len(referencia) != len(obtenido):
        raise NumericalError(
            "DIM", "Las soluciones comparadas tienen dimensiones distintas.", "x"
        )
    errores: list[VariableError] = []
    for i, (ref, obt) in enumerate(zip(referencia, obtenido)):
        absoluto = abs(ref - obt)
        etiqueta = etiquetas[i] if etiquetas and i < len(etiquetas) else f"x_{i + 1}"
        if ref == _CERO:
            relativo = None
            porcentual = None
            nota = (
                "Error relativo y porcentual no definidos: la solución de "
                "referencia es cero en esta componente."
            )
        else:
            relativo = absoluto / abs(ref)
            porcentual = relativo * 100.0
            nota = f"Error absoluto expresado en {unidad}."
        errores.append(
            VariableError(
                indice=i,
                variable=etiqueta,
                referencia=ref,
                obtenido=obt,
                absoluto=absoluto,
                relativo=relativo,
                porcentual=porcentual,
                nota=nota,
            )
        )
    return errores


def build_metrics(
    metodo: str,
    x: Vector,
    x_referencia: Vector,
    A: Matrix,
    b: Vector,
    M: Matrix | Preconditioner | None,
    etiquetas: list[str] | None = None,
    unidad: str = "millones de Bs",
) -> Metrics:
    """Construye el bloque de métricas de un método iterativo."""
    errores = variable_errors(x_referencia, x, etiquetas, unidad)
    k_a = kappa(A)
    k_m = kappa_preconditioned(A, M)
    return Metrics(
        metodo=metodo,
        errores=errores,
        residuo_relativo_global=global_relative_residual(A, x, b),
        error_absoluto_max=max((e.absoluto for e in errores), default=0.0),
        kappa_A=k_a,
        kappa_precondicionada=k_m,
        reduccion_condicion=(k_a / k_m) if k_m > 0.0 else float("inf"),
    )
