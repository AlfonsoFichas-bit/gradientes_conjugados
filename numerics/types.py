"""Estructuras de datos compartidas por el núcleo numérico.

Todas las estructuras exponen ``to_dict`` para que la capa web
(Django + Inertia) las serialice a JSON sin conversiones adicionales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Matrix = list[list[float]]
Vector = list[float]


class NumericalError(Exception):
    """Error de validación o de ejecución, apto para mostrarse al usuario.

    Nunca debe escapar como traza de Python hacia la interfaz: la capa web
    captura ``NumericalError`` y muestra ``message``.
    """

    def __init__(self, code: str, message: str, field_name: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field_name = field_name

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "field": self.field_name}


class NotPositiveDefiniteError(NumericalError):
    """La matriz tiene un pivote de Cholesky no positivo (no es D.P.)."""

    def __init__(self, index: int, pivot: float) -> None:
        super().__init__(
            "NO_SPD",
            f"La matriz no es definida positiva: el pivote {index + 1} "
            f"de Cholesky vale {pivot:.3e}.",
            "A",
        )
        self.index = index
        self.pivot = pivot


@dataclass(slots=True)
class SolverConfig:
    """Parámetros de ejecución del criterio de parada."""

    tol: float = 1e-6
    max_iter: int = 200
    x0: Vector | None = None
    omega: float = 1.0

    def initial_guess(self, n: int) -> Vector:
        if self.x0 is None:
            return [0.0] * n
        if len(self.x0) != n:
            raise NumericalError(
                "X0_DIM",
                f"El vector inicial x0 tiene {len(self.x0)} componentes; se esperaban {n}.",
                "x0",
            )
        return list(self.x0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tol": self.tol,
            "max_iter": self.max_iter,
            "x0": self.x0,
            "omega": self.omega,
        }


@dataclass(slots=True)
class SolverResult:
    """Resultado de un método (directo o iterativo)."""

    metodo: str
    x: Vector
    iteraciones: int
    convergido: bool
    motivo: str
    residuo_relativo: float
    historia: list[float] = field(default_factory=list)
    tiempo_ms: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metodo": self.metodo,
            "x": self.x,
            "iteraciones": self.iteraciones,
            "convergido": self.convergido,
            "motivo": self.motivo,
            "residuo_relativo": self.residuo_relativo,
            "historia": self.historia,
            "tiempo_ms": self.tiempo_ms,
            "extra": self.extra,
        }


@dataclass(slots=True)
class VariableError:
    """Errores absoluto, relativo y porcentual de una variable."""

    indice: int
    variable: str
    referencia: float
    obtenido: float
    absoluto: float
    relativo: float | None
    porcentual: float | None
    nota: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "indice": self.indice,
            "variable": self.variable,
            "referencia": self.referencia,
            "obtenido": self.obtenido,
            "absoluto": self.absoluto,
            "relativo": self.relativo,
            "porcentual": self.porcentual,
            "nota": self.nota,
        }


@dataclass(slots=True)
class Metrics:
    """Métricas de error y condicionamiento para un método iterativo."""

    metodo: str
    errores: list[VariableError]
    residuo_relativo_global: float
    error_absoluto_max: float
    kappa_A: float
    kappa_precondicionada: float
    reduccion_condicion: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "metodo": self.metodo,
            "errores": [e.to_dict() for e in self.errores],
            "residuo_relativo_global": self.residuo_relativo_global,
            "error_absoluto_max": self.error_absoluto_max,
            "kappa_A": self.kappa_A,
            "kappa_precondicionada": self.kappa_precondicionada,
            "reduccion_condicion": self.reduccion_condicion,
        }


@dataclass(slots=True)
class Diagnostics:
    """Verificación numérica de las propiedades exigidas a ``A``."""

    simetria_max: float
    autovalores: list[float]
    autovalor_min: float
    autovalor_max: float
    pivotes_cholesky: list[float]
    es_spd_cholesky: bool
    kappa_A: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "simetria_max": self.simetria_max,
            "autovalores": self.autovalores,
            "autovalor_min": self.autovalor_min,
            "autovalor_max": self.autovalor_max,
            "pivotes_cholesky": self.pivotes_cholesky,
            "es_spd_cholesky": self.es_spd_cholesky,
            "kappa_A": self.kappa_A,
        }


@dataclass(slots=True)
class ScenarioSpec:
    """Definición de un escenario financiero."""

    id: str
    nombre: str
    descripcion: str
    justificacion: str
    rho: float
    rigidez: Vector
    base: Vector
    ajuste_objetivo: Vector
    etiquetas: list[str]
    unidad: str = "millones de Bs"

    @property
    def n(self) -> int:
        return len(self.rigidez)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "justificacion": self.justificacion,
            "rho": self.rho,
            "rigidez": self.rigidez,
            "base": self.base,
            "ajuste_objetivo": self.ajuste_objetivo,
            "etiquetas": self.etiquetas,
            "unidad": self.unidad,
            "n": self.n,
        }


@dataclass(slots=True)
class ScenarioResult:
    """Resultado completo de un escenario."""

    escenario: ScenarioSpec
    A: Matrix
    b: Vector
    referencia: SolverResult
    metodos: dict[str, SolverResult]
    metricas: dict[str, Metrics]
    diagnostico: Diagnostics
    presupuesto_final: Vector
    parametros: SolverConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "escenario": self.escenario.to_dict(),
            "A": self.A,
            "b": self.b,
            "referencia": self.referencia.to_dict(),
            "metodos": {k: v.to_dict() for k, v in self.metodos.items()},
            "metricas": {k: v.to_dict() for k, v in self.metricas.items()},
            "diagnostico": self.diagnostico.to_dict(),
            "presupuesto_final": self.presupuesto_final,
            "parametros": self.parametros.to_dict(),
        }


@dataclass(slots=True)
class QACase:
    """Caso de prueba funcional con formato Entrada/Esperado/Obtenido/Conclusión."""

    id: int
    nombre: str
    entrada: str
    esperado: str
    obtenido: str
    conclusion: str
    ok: bool
    detalle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "entrada": self.entrada,
            "esperado": self.esperado,
            "obtenido": self.obtenido,
            "conclusion": self.conclusion,
            "ok": self.ok,
            "detalle": self.detalle,
        }
