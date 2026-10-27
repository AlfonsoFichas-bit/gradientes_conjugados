"""Gradientes conjugados y su versión precondicionada.

Se recalcula el residuo verdadero ``r_k = b - A x_k`` en cada iteración (en
lugar de la recurrencia ``r_{k+1} = r_k - alpha A p_k``) para que el criterio
de parada refleje el error real del sistema.
"""

from __future__ import annotations

import math
import time

from ..norms import dot, matvec, norm2
from ..preconditioners.base import Preconditioner
from ..types import Matrix, NumericalError, SolverConfig, SolverResult, Vector
from ..validation import validate_config


def conjugate_gradient(
    A: Matrix,
    b: Vector,
    config: SolverConfig | None = None,
    preconditioner: Preconditioner | None = None,
    metodo: str | None = None,
) -> SolverResult:
    """Resuelve ``A x = b`` por gradientes conjugados (precondicionados o no).

    ``A`` debe ser simétrica definida positiva y ``M`` (si se entrega) también.
    """
    config = config or SolverConfig()
    n = len(A)
    validate_config(config, n)
    if len(b) != n:
        raise NumericalError(
            "DIM",
            f"El vector b tiene {len(b)} componentes; se esperaban {n}.",
            "b",
        )

    norma_b = norm2(b)
    if norma_b == 0.0:
        raise NumericalError(
            "B_CERO",
            "El vector b es nulo: el criterio ||r_k||/||b|| no está definido.",
            "b",
        )

    inicio = time.perf_counter()
    x = config.initial_guess(n)
    r = [bi - ai for bi, ai in zip(b, matvec(A, x))]
    historia = [norm2(r) / norma_b]

    nombre_precond = preconditioner.nombre if preconditioner is not None else "Ninguno"
    etiqueta = metodo or ("PCG" if preconditioner is not None else "CG")

    def resultado(
        iteraciones: int, convergido: bool, motivo: str
    ) -> SolverResult:
        return SolverResult(
            metodo=etiqueta,
            x=list(x),
            iteraciones=iteraciones,
            convergido=convergido,
            motivo=motivo,
            residuo_relativo=historia[-1],
            historia=list(historia),
            tiempo_ms=(time.perf_counter() - inicio) * 1000.0,
            extra={
                "precondicionador": nombre_precond,
                "norma_b": norma_b,
                "tol": config.tol,
                "max_iter": config.max_iter,
            },
        )

    if historia[-1] < config.tol:
        return resultado(0, True, "La aproximación inicial ya cumple la tolerancia.")

    z = preconditioner.apply(r) if preconditioner is not None else list(r)
    p = list(z)
    rho = dot(r, z)

    for k in range(1, config.max_iter + 1):
        q = matvec(A, p)
        p_dot_q = dot(p, q)
        if not math.isfinite(p_dot_q) or p_dot_q <= 0.0:
            return resultado(
                k - 1,
                False,
                "Descomposición numérica: p^T A p <= 0 (la matriz dejó de ser D.P. "
                "en aritmética finita).",
            )

        alpha = rho / p_dot_q
        x = [xi + alpha * pi for xi, pi in zip(x, p)]
        r = [bi - ai for bi, ai in zip(b, matvec(A, x))]
        historia.append(norm2(r) / norma_b)

        if historia[-1] < config.tol:
            return resultado(
                k,
                True,
                f"Convergencia: ||r_{k}||/||b|| = {historia[-1]:.3e} < {config.tol:.1e}.",
            )

        z = preconditioner.apply(r) if preconditioner is not None else list(r)
        rho_nuevo = dot(r, z)
        if not math.isfinite(rho_nuevo) or rho_nuevo <= 0.0:
            return resultado(
                k,
                False,
                "Descomposición numérica: r^T M^-1 r <= 0 en aritmética finita.",
            )
        beta = rho_nuevo / rho
        p = [zi + beta * pi for zi, pi in zip(z, p)]
        rho = rho_nuevo

    return resultado(
        config.max_iter,
        False,
        f"Se alcanzó N_max = {config.max_iter} sin cumplir la tolerancia "
        f"(||r||/||b|| = {historia[-1]:.3e}).",
    )


def cg(
    A: Matrix, b: Vector, config: SolverConfig | None = None
) -> SolverResult:
    """Gradientes conjugados simple (sin precondicionar)."""
    return conjugate_gradient(A, b, config=config, metodo="CG")


def pcg(
    A: Matrix,
    b: Vector,
    preconditioner: Preconditioner,
    config: SolverConfig | None = None,
) -> SolverResult:
    """Gradientes conjugados precondicionados."""
    if preconditioner is None:
        raise NumericalError(
            "PRECONDICIONADOR",
            "PCG requiere un precondicionador M.",
            "precondicionador",
        )
    return conjugate_gradient(
        A,
        b,
        config=config,
        preconditioner=preconditioner,
        metodo=f"PCG-{preconditioner.nombre}",
    )
