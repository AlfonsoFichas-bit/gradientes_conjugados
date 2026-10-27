"""Interfaz de línea de comandos del núcleo numérico.

Ejemplos::

    python -m numerics.cli
    python -m numerics.cli --scenario mal --tol 1e-8
    python -m numerics.cli --json > resultados.json
    python -m numerics.cli --qa
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from .experiment import run_all, run_scenario, scenario_summary
from .qa import run_qa
from .scenarios import AVISO_DATOS, SCENARIOS
from .types import NumericalError, ScenarioResult, SolverConfig


def _fmt(valor: float | None, digitos: int = 6) -> str:
    if valor is None:
        return "—"
    if valor == 0.0:
        return "0"
    return f"{valor:.{digitos}g}"


def _fmt_vector(valor: list[float], digitos: int = 4) -> str:
    return "[" + ", ".join(f"{v:.{digitos}f}" for v in valor) + "]"


def _config_desde_args(args: argparse.Namespace) -> SolverConfig:
    x0 = None
    if args.x0 is not None:
        try:
            x0 = [float(parte) for parte in args.x0.split(",") if parte.strip() != ""]
        except ValueError as error:
            raise NumericalError(
                "X0", f"No se pudo interpretar x0 = {args.x0!r}: {error}", "x0"
            ) from error
    return SolverConfig(tol=args.tol, max_iter=args.max_iter, x0=x0, omega=args.omega)


def _cabecera() -> None:
    print("=" * 78)
    print(" SIMULADOR DE AJUSTES PRESUPUESTARIOS — USIE / CONSEJO DE LA MAGISTRATURA")
    print(" Métodos Numéricos · Desarrollo de Sistemas · UMSA")
    print("=" * 78)
    print(f" Aviso: {AVISO_DATOS}")
    print()


def _imprimir_escenario(resultado: ScenarioResult, indice: int) -> None:
    spec = resultado.escenario
    diag = resultado.diagnostico
    print("-" * 78)
    print(f" ESCENARIO {indice}: {spec.nombre}  (id = {spec.id})")
    print("-" * 78)
    print(f" {spec.descripcion}")
    print(f" rho = {spec.rho:.2f}  |  lambda_min = {_fmt(diag.autovalor_min, 4)}"
          f"  |  lambda_max = {_fmt(diag.autovalor_max, 4)}"
          f"  |  kappa(A) = {_fmt(diag.kappa_A, 4)}")
    print(f" Simetría máxima |a_ij - a_ji| = {_fmt(diag.simetria_max, 3)}"
          f"  |  menores de Cholesky > 0: "
          f"{'sí' if diag.es_spd_cholesky else 'no'}")
    print()
    print(f" {'Método':<12} {'Iter':>5} {'Residuo rel.':>13} "
          f"{'kappa(M^-1A)':>13} {'Error máx':>12}  Estado")
    for clave in ("cg", "pcg_jacobi", "pcg_ssor"):
        metodo = resultado.metodos[clave]
        metrica = resultado.metricas[clave]
        estado = "OK" if metodo.convergido else "NO CONVERGIÓ"
        print(
            f" {metodo.metodo:<12} {metodo.iteraciones:>5} "
            f"{_fmt(metodo.residuo_relativo, 4):>13} "
            f"{_fmt(metrica.kappa_precondicionada, 4):>13} "
            f"{_fmt(metrica.error_absoluto_max, 4):>12}  {estado}"
        )
    print()
    print(" Errores por variable (PCG-Jacobi, unidad: MM Bs):")
    print(f" {'Variable':<38} {'x_ref':>10} {'x_GCP':>10} {'Ea':>11} {'Ep (%)':>11}")
    for error in resultado.metricas["pcg_jacobi"].errores:
        porcentual = "—" if error.porcentual is None else f"{error.porcentual:.3e}"
        print(
            f" {error.variable[:38]:<38} {error.referencia:>10.4f} "
            f"{error.obtenido:>10.4f} {error.absoluto:>11.3e} {porcentual:>11}"
        )
    print()
    print(f" Presupuesto base:  {_fmt_vector(spec.base)}")
    print(f" Ajuste (PCG-Jacobi): {_fmt_vector(resultado.metodos['pcg_jacobi'].x)}")
    print(f" Presupuesto final: {_fmt_vector(resultado.presupuesto_final)}")
    print()


def _imprimir_resumen(resultados: list[ScenarioResult]) -> None:
    print("=" * 78)
    print(" RESUMEN COMPARATIVO")
    print("=" * 78)
    print(
        f" {'Escenario':<14} {'It.CG':>6} {'It.Jac':>7} {'It.SSOR':>8} "
        f"{'kappa(A)':>11} {'k(Jac)':>11} {'k(SSOR)':>11}  Conv."
    )
    for resultado in resultados:
        resumen = scenario_summary(resultado)
        convergencia = all(resumen["convergieron"].values())
        print(
            f" {resultado.escenario.nombre[:14]:<14} "
            f"{resumen['iter_cg']:>6} {resumen['iter_jacobi']:>7} "
            f"{resumen['iter_ssor']:>8} {_fmt(resumen['kappa_A'], 4):>11} "
            f"{_fmt(resumen['kappa_jacobi'], 4):>11} "
            f"{_fmt(resumen['kappa_ssor'], 4):>11}  "
            f"{'sí' if convergencia else 'no'}"
        )
    print()


def _imprimir_qa(casos) -> None:
    print("=" * 78)
    print(" MÓDULO DE PRUEBAS FUNCIONALES (QA)")
    print("=" * 78)
    for caso in casos:
        estado = "OK" if caso.ok else "FALLO"
        print(f"\n Prueba {caso.id}: {caso.nombre} — {estado}")
        print(f"   Entrada:    {caso.entrada}")
        print(f"   Esperado:   {caso.esperado}")
        print(f"   Obtenido:   {caso.obtenido}")
        print(f"   Conclusión: {caso.conclusion}")
    total = sum(1 for caso in casos if caso.ok)
    print(f"\n Resultado global: {total}/{len(casos)} pruebas aprobadas.")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(
        prog="numerics",
        description="Núcleo numérico del simulador de ajustes presupuestarios.",
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON.")
    parser.add_argument("--qa", action="store_true", help="Ejecutar pruebas funcionales.")
    parser.add_argument(
        "--scenario",
        default="todos",
        choices=["todos", *[s.id for s in SCENARIOS]],
        help="Escenario a ejecutar (por defecto: todos).",
    )
    parser.add_argument("--tol", type=float, default=1e-6, help="Tolerancia relativa.")
    parser.add_argument(
        "--max-iter", type=int, default=200, dest="max_iter", help="N máximo."
    )
    parser.add_argument("--omega", type=float, default=1.0, help="Omega de SSOR.")
    parser.add_argument(
        "--x0", default=None, help="Vector inicial separado por comas (por defecto: ceros)."
    )
    args = parser.parse_args(argv)

    try:
        config = _config_desde_args(args)

        if args.qa:
            casos = run_qa(config)
            if args.json:
                print(
                    json.dumps(
                        {
                            "aviso": AVISO_DATOS,
                            "config": config.to_dict(),
                            "qa": [caso.to_dict() for caso in casos],
                            "aprobadas": sum(1 for caso in casos if caso.ok),
                            "total": len(casos),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                _imprimir_qa(casos)
            return 0 if all(caso.ok for caso in casos) else 1

        inicio = time.perf_counter()
        if args.scenario == "todos":
            resultados = run_all(config)
        else:
            resultados = [run_scenario(args.scenario, config)]
        duracion = (time.perf_counter() - inicio) * 1000.0

        if args.json:
            print(
                json.dumps(
                    {
                        "aviso": AVISO_DATOS,
                        "config": config.to_dict(),
                        "duracion_ms": duracion,
                        "resumen": [scenario_summary(r) for r in resultados],
                        "escenarios": [r.to_dict() for r in resultados],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            _cabecera()
            for indice, resultado in enumerate(resultados, start=1):
                _imprimir_escenario(resultado, indice)
            _imprimir_resumen(resultados)
            print(f" Tiempo de cálculo: {duracion:.1f} ms")
        return 0
    except NumericalError as error:
        if args.json:
            print(json.dumps({"error": error.to_dict()}, ensure_ascii=False))
        else:
            print(f"ERROR [{error.code}]: {error.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
