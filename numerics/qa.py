"""Módulo de pruebas funcionales (QA) ejecutable sin interfaz gráfica.

Cada caso sigue el formato exigido: Entrada, Resultado Esperado, Resultado
Obtenido y Conclusión. La web solo muestra el resultado de ``run_qa``.
"""

from __future__ import annotations

import copy

from .experiment import analyze, run_all, run_scenario
from .matrix import build_A, build_b
from .norms import max_abs_vector_diff
from .scenarios import get_scenario
from .types import NumericalError, QACase, SolverConfig, Vector
from .validation import validate_system


def _prueba_escenarios(config: SolverConfig) -> QACase:
    resultados = run_all(config)
    fallos: list[str] = []
    metodos_totales = 0
    metodos_ok = 0
    residuo_max = 0.0

    for resultado in resultados:
        if not resultado.referencia.convergido:
            fallos.append(f"{resultado.escenario.id}: falló Cholesky")
        for clave, metodo in resultado.metodos.items():
            metodos_totales += 1
            if metodo.convergido and metodo.residuo_relativo < config.tol:
                metodos_ok += 1
            else:
                fallos.append(
                    f"{resultado.escenario.id}/{clave}: residuo "
                    f"{metodo.residuo_relativo:.2e}"
                )
            residuo_max = max(residuo_max, metodo.residuo_relativo)

    ok = len(resultados) == 3 and not fallos
    detalle = {
        "escenarios": [r.escenario.id for r in resultados],
        "metodos_ok": metodos_ok,
        "metodos_totales": metodos_totales,
        "residuo_max": residuo_max,
        "fallos": fallos,
    }
    return QACase(
        id=1,
        nombre="Carga de escenarios",
        entrada="Ejecutar los escenarios Ideal, Bajo Estrés y Mal Condicionado "
        f"con tol = {config.tol:.1e} y N_max = {config.max_iter}.",
        esperado="Los tres escenarios se cargan y todos los métodos (Cholesky, "
        "CG, PCG-Jacobi y PCG-SSOR) convergen bajo la tolerancia.",
        obtenido=(
            f"{len(resultados)}/3 escenarios procesados; {metodos_ok}/"
            f"{metodos_totales} métodos convergidos; residuo máximo "
            f"{residuo_max:.2e}."
            + (" Fallos: " + "; ".join(fallos) if fallos else "")
        ),
        conclusion=(
            "El sistema procesa íntegramente los tres escenarios sin errores."
            if ok
            else "Existen fallos de convergencia o de carga que deben corregirse."
        ),
        ok=ok,
        detalle=detalle,
    )


def _prueba_matriz_invalida() -> QACase:
    casos: list[tuple[str, list[list[float]], Vector, str]] = [
        (
            "matriz asimétrica",
            [[2.0, 1.0], [0.0, 2.0]],
            [1.0, 1.0],
            "ASIMETRICA",
        ),
        (
            "matriz simétrica no definida positiva",
            [[1.0, 2.0], [2.0, 1.0]],
            [1.0, 1.0],
            "NO_SPD",
        ),
        (
            "dimensión incompatible",
            [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]],
            [1.0, 1.0],
            "DIM",
        ),
        (
            "componente no numérica",
            [[2.0, "a"], ["a", 2.0]],
            [1.0, 1.0],
            "NO_NUMERICO",
        ),
        (
            "componente NaN",
            [[2.0, float("nan")], [float("nan"), 2.0]],
            [1.0, 1.0],
            "NO_FINITO",
        ),
    ]

    capturados: list[dict] = []
    fallos: list[str] = []
    for nombre, A, b, codigo in casos:
        try:
            validate_system(A, b)  # type: ignore[arg-type]
        except NumericalError as error:
            capturados.append({"caso": nombre, "codigo": error.code, "mensaje": error.message})
            if error.code != codigo:
                fallos.append(f"{nombre}: se esperaba {codigo}, se obtuvo {error.code}")
        except Exception as error:  # noqa: BLE001 - el QA debe detectar fallos genéricos
            fallos.append(f"{nombre}: excepción no controlada {type(error).__name__}")
        else:
            fallos.append(f"{nombre}: la validación no detectó el error")

    ok = not fallos
    return QACase(
        id=2,
        nombre="Validación de matriz no válida",
        entrada="Cinco sistemas inválidos: asimétrico, no D.P., dimensión "
        "incompatible, valor no numérico y NaN.",
        esperado="Cada caso se rechaza con un NumericalError informativo "
        "(ASIMETRICA, NO_SPD, DIM, NO_NUMERICO, NO_FINITO) sin bloquear la app.",
        obtenido="; ".join(
            f"{c['caso']} → {c['codigo']}" for c in capturados
        )
        + (" Fallos: " + "; ".join(fallos) if fallos else ""),
        conclusion=(
            "Las entradas inválidas se capturan y se informan de forma controlada."
            if ok
            else "Algún caso inválido no fue detectado o produjo una excepción genérica."
        ),
        ok=ok,
        detalle={"casos": capturados, "fallos": fallos},
    )


def _prueba_edicion(config: SolverConfig) -> QACase:
    spec = get_scenario("ideal")
    A = build_A(spec.rigidez, spec.rho)
    b = build_b(A, spec.ajuste_objetivo)
    original = analyze(A, b, spec=spec, config=config)

    A_editada = copy.deepcopy(A)
    delta = 0.08
    A_editada[0][1] += delta
    A_editada[1][0] += delta
    editado = analyze(A_editada, b, spec=spec, config=config)

    diferencia = max_abs_vector_diff(original.referencia.x, editado.referencia.x)
    residuo = editado.metodos["pcg_jacobi"].residuo_relativo
    convergido = (
        editado.metodos["cg"].convergido
        and editado.metodos["pcg_jacobi"].convergido
        and editado.metodos["pcg_ssor"].convergido
    )
    sigue_spd = editado.diagnostico.autovalor_min > 0.0
    ok = diferencia > 1e-6 and convergido and sigue_spd and residuo < config.tol

    return QACase(
        id=3,
        nombre="Edición dinámica y reactividad",
        entrada=f"Escenario Ideal con a_12 y a_21 incrementados en {delta:.2f}.",
        esperado="La solución de referencia, GCP y las métricas se recalculan; "
        "el sistema editado sigue siendo D.P. y converge.",
        obtenido=(
            f"Cambio máximo en la solución de referencia: {diferencia:.3e}; "
            f"lambda_min = {editado.diagnostico.autovalor_min:.3e}; "
            f"residuo PCG-Jacobi = {residuo:.2e}; convergencia = "
            f"{'sí' if convergido else 'no'}."
        ),
        conclusion=(
            "La edición de coeficientes se refleja de inmediato y el sistema "
            "mantiene las propiedades matemáticas exigidas."
            if ok
            else "La edición no produjo un recálculo válido o rompió la convergencia."
        ),
        ok=ok,
        detalle={
            "delta": delta,
            "cambio_maximo_referencia": diferencia,
            "autovalor_min": editado.diagnostico.autovalor_min,
            "residuo_pcg_jacobi": residuo,
        },
    )


def _prueba_precondicionamiento(config: SolverConfig) -> QACase:
    resultado = run_scenario("mal", config)
    iter_cg = resultado.metodos["cg"].iteraciones
    iter_jacobi = resultado.metodos["pcg_jacobi"].iteraciones
    iter_ssor = resultado.metodos["pcg_ssor"].iteraciones
    ok = (
        resultado.metodos["cg"].convergido
        and resultado.metodos["pcg_jacobi"].convergido
        and resultado.metodos["pcg_ssor"].convergido
        and iter_jacobi <= iter_cg
        and iter_ssor <= iter_cg
    )
    return QACase(
        id=4,
        nombre="Comparativa de eficiencia del precondicionamiento",
        entrada="Escenario Mal Condicionado con tolerancia "
        f"{config.tol:.1e} y N_max = {config.max_iter}.",
        esperado="GCP (Jacobi y SSOR) converge en un número de iteraciones "
        "menor o igual que GC simple.",
        obtenido=(
            f"GC = {iter_cg} iteraciones; PCG-Jacobi = {iter_jacobi}; "
            f"PCG-SSOR = {iter_ssor}. "
            f"kappa(A) = {resultado.diagnostico.kappa_A:.3e}; "
            f"kappa(M^-1 A) Jacobi = "
            f"{resultado.metricas['pcg_jacobi'].kappa_precondicionada:.3e}; "
            f"SSOR = {resultado.metricas['pcg_ssor'].kappa_precondicionada:.3e}."
        ),
        conclusion=(
            "El precondicionamiento reduce o iguala el esfuerzo iterativo en el "
            "escenario mal condicionado."
            if ok
            else "El precondicionamiento no mejoró el conteo de iteraciones."
        ),
        ok=ok,
        detalle={
            "iter_cg": iter_cg,
            "iter_jacobi": iter_jacobi,
            "iter_ssor": iter_ssor,
            "kappa_A": resultado.diagnostico.kappa_A,
            "kappa_jacobi": resultado.metricas["pcg_jacobi"].kappa_precondicionada,
            "kappa_ssor": resultado.metricas["pcg_ssor"].kappa_precondicionada,
        },
    )


def run_qa(config: SolverConfig | None = None) -> list[QACase]:
    """Ejecuta las cuatro pruebas funcionales obligatorias."""
    config = config or SolverConfig()
    return [
        _prueba_escenarios(config),
        _prueba_matriz_invalida(),
        _prueba_edicion(config),
        _prueba_precondicionamiento(config),
    ]
