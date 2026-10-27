"""Núcleo numérico del simulador presupuestario (USIE / Consejo de la Magistratura).

El paquete no importa Django ni frameworks web: puede ejecutarse desde la CLI,
desde pruebas unitarias o desde la capa Django + Inertia.
"""

from .experiment import (
    INTERPRETACION_FINANCIERA,
    analyze,
    run_all,
    run_custom,
    run_scenario,
    scenario_summary,
)
from .linalg import (
    cholesky,
    cholesky_solve,
    inverse_from_cholesky,
    jacobi_eigenvalues,
    lu_factor,
    lu_solve,
)
from .matrix import build_A, ar1_precision, build_b
from .metrics import (
    build_metrics,
    global_relative_residual,
    kappa,
    kappa_preconditioned,
    variable_errors,
)
from .norms import dot, matvec, norm2, residual, transpose
from .preconditioners import (
    JacobiPreconditioner,
    Preconditioner,
    SSORPreconditioner,
    build_preconditioner,
    jacobi_preconditioner,
    ssor_preconditioner,
)
from .qa import run_qa
from .scenarios import (
    AVISO_DATOS,
    BASE,
    CATEGORIAS,
    ESTRES,
    IDEAL,
    MAL_CONDICIONADO,
    PROCEDENCIA,
    SCENARIOS,
    get_scenario,
)
from .solvers import cg, conjugate_gradient, pcg
from .types import (
    Diagnostics,
    Matrix,
    Metrics,
    NotPositiveDefiniteError,
    NumericalError,
    QACase,
    ScenarioResult,
    ScenarioSpec,
    SolverConfig,
    SolverResult,
    VariableError,
    Vector,
)
from .validation import (
    validate_config,
    validate_matrix,
    validate_scenario,
    validate_system,
    validate_vector,
)

__all__ = [
    # Tipos
    "Matrix",
    "Vector",
    "NumericalError",
    "NotPositiveDefiniteError",
    "SolverConfig",
    "SolverResult",
    "VariableError",
    "Metrics",
    "Diagnostics",
    "ScenarioSpec",
    "ScenarioResult",
    "QACase",
    # Álgebra lineal
    "build_A",
    "ar1_precision",
    "build_b",
    "dot",
    "norm2",
    "matvec",
    "residual",
    "transpose",
    "cholesky",
    "cholesky_solve",
    "inverse_from_cholesky",
    "jacobi_eigenvalues",
    "lu_factor",
    "lu_solve",
    # Métricas
    "kappa",
    "kappa_preconditioned",
    "global_relative_residual",
    "variable_errors",
    "build_metrics",
    # Precondicionadores
    "Preconditioner",
    "JacobiPreconditioner",
    "SSORPreconditioner",
    "jacobi_preconditioner",
    "ssor_preconditioner",
    "build_preconditioner",
    # Solvers
    "cg",
    "pcg",
    "conjugate_gradient",
    # Escenarios y experimentos
    "SCENARIOS",
    "IDEAL",
    "ESTRES",
    "MAL_CONDICIONADO",
    "CATEGORIAS",
    "BASE",
    "AVISO_DATOS",
    "PROCEDENCIA",
    "get_scenario",
    "analyze",
    "run_scenario",
    "run_custom",
    "run_all",
    "scenario_summary",
    "INTERPRETACION_FINANCIERA",
    # QA y validación
    "run_qa",
    "validate_matrix",
    "validate_vector",
    "validate_system",
    "validate_config",
    "validate_scenario",
]
