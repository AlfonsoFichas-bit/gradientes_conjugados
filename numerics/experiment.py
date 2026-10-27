"""Orquestación de un experimento completo por escenario.

Une construcción del sistema, solución de referencia (Cholesky), GC, GCP con
Jacobi, GCP con SSOR, diagnóstico espectral y métricas de error.
"""

from __future__ import annotations

from dataclasses import replace

from .linalg.cholesky import cholesky, cholesky_solve
from .linalg.eigen import jacobi_eigenvalues
from .matrix import build_A, build_b
from .metrics import build_metrics, global_relative_residual
from .norms import max_abs_diff, transpose
from .preconditioners.jacobi import JacobiPreconditioner
from .preconditioners.ssor import SSORPreconditioner
from .scenarios import SCENARIOS, get_scenario
from .solvers.cg import cg, pcg
from .types import (
    Diagnostics,
    Matrix,
    NumericalError,
    ScenarioResult,
    ScenarioSpec,
    SolverConfig,
    SolverResult,
    Vector,
)
from .validation import validate_config, validate_scenario, validate_system

INTERPRETACION_FINANCIERA = {
    "ideal": (
        "Con baja interdependencia, el ajuste se lee casi línea por línea: se "
        "recorta consultoría y software (x1, x3) y se refuerzan hardware, "
        "conectividad y soporte (x2, x4, x5). El sistema está bien condicionado "
        "y ambos métodos reproducen la referencia con pocas iteraciones."
    ),
    "estres": (
        "El choque de costos obliga a un ajuste más profundo y acoplado. El "
        "recorte de consultoría y software financia el refuerzo de hardware y "
        "conectividad, pero ahora las líneas se mueven en bloque: el "
        "condicionamiento moderado hace que el número de iteraciones y el error "
        "sean más sensibles a la tolerancia."
    ),
    "mal": (
        "La disparidad de escalas domina el problema: pequeñas variaciones en las "
        "líneas marginales (d1, d2) producen cambios grandes en la solución. El "
        "GC simple pierde dígitos y roza el límite de iteraciones; los "
        "precondicionadores reducen kappa(M^-1 A) en varios órdenes de magnitud. "
        "En la práctica, el ajuste debe interpretarse con cautela y acompañarse "
        "de validación de datos."
    ),
}


def analyze(
    A: Matrix,
    b: Vector,
    spec: ScenarioSpec | None = None,
    config: SolverConfig | None = None,
    base: Vector | None = None,
) -> ScenarioResult:
    """Analiza un sistema ``A x = b`` ya construido.

    Si no se entrega ``spec`` se genera uno sintético para la edición
    interactiva de coeficientes (Módulo 4).
    """
    config = config or SolverConfig()
    validate_system(A, b)
    n = len(A)
    validate_config(config, n)

    A_f = [[float(v) for v in fila] for fila in A]
    b_f = [float(v) for v in b]

    autovalores = jacobi_eigenvalues(A_f)
    kappa_a = autovalores[-1] / autovalores[0]
    L = cholesky(A_f)
    pivotes = [L[i][i] ** 2 for i in range(n)]
    simetria = max_abs_diff(A_f, transpose(A_f))

    x_ref = cholesky_solve(L, b_f)
    residuo_ref = global_relative_residual(A_f, x_ref, b_f)

    referencia = SolverResult(
        metodo="Cholesky",
        x=x_ref,
        iteraciones=0,
        convergido=True,
        motivo="Factorización directa A = L L^T (solución de referencia).",
        residuo_relativo=residuo_ref,
        historia=[residuo_ref],
        tiempo_ms=0.0,
        extra={
            "factorizacion": "Cholesky",
            "pivotes": pivotes,
            "kappa_A": kappa_a,
        },
    )

    jacobi = JacobiPreconditioner(A_f)
    ssor = SSORPreconditioner(A_f, config.omega)

    resultado_cg = cg(A_f, b_f, config)
    resultado_jacobi = pcg(A_f, b_f, jacobi, config)
    resultado_ssor = pcg(A_f, b_f, ssor, config)

    metodos = {
        "cg": resultado_cg,
        "pcg_jacobi": resultado_jacobi,
        "pcg_ssor": resultado_ssor,
    }

    if spec is None:
        spec = ScenarioSpec(
            id="personalizado",
            nombre="Sistema personalizado",
            descripcion="Sistema editado manualmente desde el simulador.",
            justificacion=(
                "Los coeficientes de A y el vector b fueron ingresados por el "
                "usuario; el diagnóstico verifica que el sistema siga siendo "
                "simétrico y definido positivo."
            ),
            rho=0.0,
            rigidez=[A_f[i][i] for i in range(n)],
            base=list(base) if base is not None else [0.0] * n,
            ajuste_objetivo=list(x_ref),
            etiquetas=[f"x_{i + 1}" for i in range(n)],
        )
    elif base is not None:
        spec = replace(spec, base=list(base))

    etiquetas = spec.etiquetas
    metricas = {
        "cg": build_metrics(
            "CG", resultado_cg.x, x_ref, A_f, b_f, None, etiquetas, spec.unidad
        ),
        "pcg_jacobi": build_metrics(
            "PCG-Jacobi", resultado_jacobi.x, x_ref, A_f, b_f, jacobi, etiquetas, spec.unidad
        ),
        "pcg_ssor": build_metrics(
            "PCG-SSOR", resultado_ssor.x, x_ref, A_f, b_f, ssor, etiquetas, spec.unidad
        ),
    }

    diagnostico = Diagnostics(
        simetria_max=simetria,
        autovalores=autovalores,
        autovalor_min=autovalores[0],
        autovalor_max=autovalores[-1],
        pivotes_cholesky=pivotes,
        es_spd_cholesky=all(p > 0.0 for p in pivotes),
        kappa_A=kappa_a,
    )

    presupuesto_final = [
        b_i + x_i for b_i, x_i in zip(spec.base, resultado_jacobi.x)
    ]

    return ScenarioResult(
        escenario=spec,
        A=A_f,
        b=b_f,
        referencia=referencia,
        metodos=metodos,
        metricas=metricas,
        diagnostico=diagnostico,
        presupuesto_final=presupuesto_final,
        parametros=SolverConfig(
            tol=config.tol,
            max_iter=config.max_iter,
            x0=list(config.x0) if config.x0 is not None else None,
            omega=config.omega,
        ),
    )


def run_scenario(
    escenario: str | ScenarioSpec, config: SolverConfig | None = None
) -> ScenarioResult:
    """Ejecuta un escenario predefinido (por id o instancia)."""
    spec = get_scenario(escenario) if isinstance(escenario, str) else escenario
    validate_scenario(spec)
    A = build_A(spec.rigidez, spec.rho)
    b = build_b(A, spec.ajuste_objetivo)
    return analyze(A, b, spec=spec, config=config)


def run_all(config: SolverConfig | None = None) -> list[ScenarioResult]:
    """Ejecuta los tres escenarios obligatorios en orden."""
    return [run_scenario(spec, config) for spec in SCENARIOS]


def run_custom(
    A: Matrix,
    b: Vector,
    base_spec: ScenarioSpec,
    config: SolverConfig | None = None,
) -> ScenarioResult:
    """Analiza un sistema editado manualmente a partir de un escenario base.

    Conserva las cinco categorías, el presupuesto base y la unidad del escenario
    de referencia, pero reemplaza ``A`` y ``b`` por los valores ingresados. La
    solución de Cholesky pasa a ser el ajuste objetivo de la verificación, de
    modo que ``E_a``, ``E_r`` y ``E_p`` midan el error de los métodos iterativos
    contra la referencia directa del sistema editado.

    Lanza ``NumericalError`` si el sistema no conserva la dimensión, no es
    simétrico o no es definido positivo.
    """
    if not isinstance(A, list) or len(A) != len(base_spec.base):
        raise NumericalError(
            "DIM",
            "El sistema editado debe conservar las "
            f"{len(base_spec.base)} categorías del escenario {base_spec.nombre}.",
            "A",
        )
    validate_system(A, b)

    spec = ScenarioSpec(
        id="personalizado",
        nombre=f"{base_spec.nombre} · editado",
        descripcion=(
            "Sistema con coeficientes de A y componentes de b ingresados "
            "manualmente en el Módulo 4."
        ),
        justificacion=(
            "La edición conserva las categorías y el presupuesto base. El "
            "diagnóstico verifica que A siga siendo simétrica y definida "
            "positiva; los errores se miden contra la solución de Cholesky "
            "recalculada para este sistema."
        ),
        rho=0.0,
        rigidez=[float(A[i][i]) for i in range(len(A))],
        base=list(base_spec.base),
        ajuste_objetivo=[0.0] * len(base_spec.base),
        etiquetas=list(base_spec.etiquetas),
        unidad=base_spec.unidad,
    )
    resultado = analyze(A, b, spec=spec, config=config)
    resultado.escenario = replace(
        resultado.escenario, ajuste_objetivo=list(resultado.referencia.x)
    )
    return resultado


def scenario_summary(resultado: ScenarioResult) -> dict:
    """Resumen escalar y vectorial listo para tablas comparativas."""
    jacobi = resultado.metricas["pcg_jacobi"]
    ssor = resultado.metricas["pcg_ssor"]
    cg_m = resultado.metricas["cg"]
    return {
        "id": resultado.escenario.id,
        "nombre": resultado.escenario.nombre,
        "x_referencia": resultado.referencia.x,
        "x_cg": resultado.metodos["cg"].x,
        "x_pcg_jacobi": resultado.metodos["pcg_jacobi"].x,
        "x_pcg_ssor": resultado.metodos["pcg_ssor"].x,
        "iter_cg": resultado.metodos["cg"].iteraciones,
        "iter_jacobi": resultado.metodos["pcg_jacobi"].iteraciones,
        "iter_ssor": resultado.metodos["pcg_ssor"].iteraciones,
        "kappa_A": cg_m.kappa_A,
        "kappa_jacobi": jacobi.kappa_precondicionada,
        "kappa_ssor": ssor.kappa_precondicionada,
        "residuo_cg": resultado.metodos["cg"].residuo_relativo,
        "residuo_jacobi": resultado.metodos["pcg_jacobi"].residuo_relativo,
        "residuo_ssor": resultado.metodos["pcg_ssor"].residuo_relativo,
        "error_max_jacobi": jacobi.error_absoluto_max,
        "convergieron": {
            "cg": resultado.metodos["cg"].convergido,
            "pcg_jacobi": resultado.metodos["pcg_jacobi"].convergido,
            "pcg_ssor": resultado.metodos["pcg_ssor"].convergido,
        },
        "presupuesto_base": resultado.escenario.base,
        "presupuesto_final": resultado.presupuesto_final,
        "interpretacion": INTERPRETACION_FINANCIERA.get(resultado.escenario.id, ""),
    }


__all__ = [
    "analyze",
    "run_scenario",
    "run_custom",
    "run_all",
    "scenario_summary",
    "INTERPRETACION_FINANCIERA",
]
