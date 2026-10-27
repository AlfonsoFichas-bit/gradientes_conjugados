"""Vistas del simulador. Toda la matemática vive en ``numerics``."""

from __future__ import annotations

import json
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from inertia import inertia

from numerics import (
    AVISO_DATOS,
    CATEGORIAS,
    INTERPRETACION_FINANCIERA,
    PROCEDENCIA,
    NumericalError,
    SolverConfig,
    get_scenario,
    run_all,
    run_custom,
    run_qa,
    scenario_summary,
)

logger = logging.getLogger(__name__)

_LIMITE_CUERPO = 64_000

PROYECTO = {
    "titulo": "Asignación presupuestaria bajo incertidumbre",
    "subtitulo": (
        "Un sistema lineal simétrico definido positivo resuelto con Cholesky, "
        "gradientes conjugados y gradientes conjugados precondicionados"
    ),
    "institucion": "USIE — Consejo de la Magistratura (La Paz, Bolivia)",
    "estudiante": os.environ.get("NOMBRE_ESTUDIANTE", "Nombre del estudiante"),
    "carrera": "Informática",
    "facultad": "Facultad de Ciencias Puras y Naturales — UMSA",
    "mencion": "Desarrollo de Sistemas",
    "materia": "Métodos Numéricos",
    "gestion": "2026",
    "dimension": 5,
}

REFERENCIAS = [
    (
        "Suñagua S., P. (2020). Método de Gradientes Conjugados Precondicionado. "
        "Revista Boliviana de Matemática UMSA, 4, 2–7."
    ),
    (
        "Golub, G. H., & Van Loan, C. F. (2013). Matrix Computations (4th ed.). "
        "Johns Hopkins University Press."
    ),
    (
        "Saad, Y. (2003). Iterative Methods for Sparse Linear Systems (2nd ed.). "
        "SIAM."
    ),
]


def _payload() -> dict:
    resultados = run_all()
    casos = run_qa()
    escenarios = [
        {
            "resultado": resultado.to_dict(),
            "resumen": scenario_summary(resultado),
            "interpretacion": INTERPRETACION_FINANCIERA.get(resultado.escenario.id, ""),
        }
        for resultado in resultados
    ]
    aprobadas = sum(1 for caso in casos if caso.ok)
    return {
        "proyecto": PROYECTO,
        "aviso": AVISO_DATOS,
        "procedencia": PROCEDENCIA,
        "categorias": CATEGORIAS,
        "escenarios": escenarios,
        "qa": [caso.to_dict() for caso in casos],
        "qa_aprobadas": aprobadas,
        "qa_total": len(casos),
        "referencias": REFERENCIAS,
    }


@require_GET
@ensure_csrf_cookie
@inertia("Home")
def home(request):
    """Módulos 1–10 en una sola página (versión base)."""
    return _payload()


def _entero(datos: dict, clave: str, defecto: int) -> int:
    valor = datos.get(clave, defecto)
    if isinstance(valor, bool):
        raise NumericalError("CONFIG", f"El parámetro {clave} debe ser entero.", clave)
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise NumericalError(
            "CONFIG", f"El parámetro {clave} debe ser entero.", clave
        ) from exc
    if isinstance(valor, float) and not valor.is_integer():
        raise NumericalError("CONFIG", f"El parámetro {clave} debe ser entero.", clave)
    return numero


def _real(datos: dict, clave: str, defecto: float) -> float:
    valor = datos.get(clave, defecto)
    if isinstance(valor, bool):
        raise NumericalError("CONFIG", f"El parámetro {clave} debe ser numérico.", clave)
    try:
        return float(valor)
    except (TypeError, ValueError) as exc:
        raise NumericalError(
            "CONFIG", f"El parámetro {clave} debe ser numérico.", clave
        ) from exc


def _interpretacion_editada(resultado) -> str:
    kappa_a = resultado.diagnostico.kappa_A
    if kappa_a < 100.0:
        nivel = "bien condicionado"
    elif kappa_a < 1.0e4:
        nivel = "moderadamente condicionado"
    else:
        nivel = "mal condicionado"
    cg = resultado.metodos["cg"]
    jacobi = resultado.metodos["pcg_jacobi"]
    ssor = resultado.metodos["pcg_ssor"]
    return (
        f"El sistema editado está {nivel} (κ(A) = {kappa_a:.3g}). "
        f"GC usó {cg.iteraciones} iteraciones, PCG-Jacobi {jacobi.iteraciones} y "
        f"PCG-SSOR {ssor.iteraciones}; el residuo relativo de PCG-Jacobi es "
        f"{jacobi.residuo_relativo:.2e}. Los errores se miden contra la solución "
        "directa de Cholesky recalculada con los coeficientes ingresados."
    )


@require_POST
def resolver(request):
    """Recalcula un sistema editado con el núcleo numérico (Módulo 4).

    Espera ``{escenario_id, A, b, x0, tol, max_iter, omega}``. Devuelve el mismo
    formato que un escenario, más el resumen y una interpretación. Los errores
    de dominio (matriz asimétrica, no SPD, dimensión, tolerancia) se responden
    con HTTP 200 y ``ok: false``: así el navegador no registra un error de red
    por una validación que la interfaz ya muestra. Los cuerpos mal formados sí
    usan 400/413 y los fallos inesperados, 500.
    """
    if len(request.body) > _LIMITE_CUERPO:
        return JsonResponse(
            {
                "ok": False,
                "error": {
                    "code": "TAMANO",
                    "message": "La solicitud excede el tamaño permitido.",
                    "field": None,
                },
            },
            status=413,
        )

    try:
        datos = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "ok": False,
                "error": {
                    "code": "JSON",
                    "message": "El cuerpo de la solicitud no es JSON válido.",
                    "field": None,
                },
            },
            status=400,
        )

    if not isinstance(datos, dict):
        return JsonResponse(
            {
                "ok": False,
                "error": {
                    "code": "JSON",
                    "message": "Se esperaba un objeto JSON con A, b y escenario_id.",
                    "field": None,
                },
            },
            status=400,
        )

    try:
        base_spec = get_scenario(str(datos.get("escenario_id", "ideal")))
        A = datos.get("A")
        b = datos.get("b")
        if not isinstance(A, list) or not isinstance(b, list):
            raise NumericalError(
                "DIM", "Los campos A y b deben ser listas numéricas.", "A"
            )
        x0 = datos.get("x0")
        if x0 is not None and not isinstance(x0, list):
            raise NumericalError(
                "X0_DIM", "El vector inicial x0 debe ser una lista numérica.", "x0"
            )
        config = SolverConfig(
            tol=_real(datos, "tol", 1e-6),
            max_iter=_entero(datos, "max_iter", 200),
            x0=x0,
            omega=_real(datos, "omega", 1.0),
        )
        resultado = run_custom(A, b, base_spec, config)
    except NumericalError as exc:
        return JsonResponse({"ok": False, "error": exc.to_dict()})
    except Exception:  # noqa: BLE001 - la API nunca debe filtrar trazas
        logger.exception("Fallo inesperado al resolver un sistema editado")
        return JsonResponse(
            {
                "ok": False,
                "error": {
                    "code": "INTERNO",
                    "message": "Ocurrió un error interno al recalcular el sistema.",
                    "field": None,
                },
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "resultado": resultado.to_dict(),
            "resumen": scenario_summary(resultado),
            "interpretacion": _interpretacion_editada(resultado),
        }
    )


@require_GET
def salud(request):
    """Endpoint de salud para el despliegue."""
    return JsonResponse({"ok": True, "nucleo": "numerics"})
