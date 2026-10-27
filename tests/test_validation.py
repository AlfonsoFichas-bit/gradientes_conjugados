"""Pruebas de las validaciones de entrada."""

from __future__ import annotations

import unittest

from numerics.matrix import build_A, build_b
from numerics.scenarios import get_scenario
from numerics.types import NumericalError, ScenarioSpec, SolverConfig
from numerics.validation import (
    validate_config,
    validate_matrix,
    validate_scenario,
    validate_system,
    validate_vector,
)


class TestValidacionMatriz(unittest.TestCase):
    def test_matriz_valida(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        self.assertIsNone(validate_matrix(A))

    def test_vacia(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([])
        self.assertEqual(ctx.exception.code, "VACIO")

    def test_no_cuadrada(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        self.assertEqual(ctx.exception.code, "DIM")

    def test_asimetrica(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[2.0, 1.0], [0.0, 2.0]])
        self.assertEqual(ctx.exception.code, "ASIMETRICA")

    def test_no_definida_positiva(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[1.0, 2.0], [2.0, 1.0]])
        self.assertEqual(ctx.exception.code, "NO_SPD")

    def test_no_numerica(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[2.0, "a"], ["a", 2.0]])  # type: ignore[list-item]
        self.assertEqual(ctx.exception.code, "NO_NUMERICO")

    def test_nan_e_infinito(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[2.0, 0.0], [0.0, float("nan")]])
        self.assertEqual(ctx.exception.code, "NO_FINITO")
        with self.assertRaises(NumericalError) as ctx2:
            validate_matrix([[2.0, 0.0], [0.0, float("inf")]])
        self.assertEqual(ctx2.exception.code, "NO_FINITO")

    def test_bool_no_es_numero(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_matrix([[2.0, 0.0], [0.0, True]])
        self.assertEqual(ctx.exception.code, "NO_NUMERICO")


class TestValidacionSistema(unittest.TestCase):
    def test_sistema_valido(self) -> None:
        spec = get_scenario("ideal")
        A = build_A(spec.rigidez, spec.rho)
        b = build_b(A, spec.ajuste_objetivo)
        self.assertIsNone(validate_system(A, b))

    def test_dimension_b(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_system([[2.0, 0.0], [0.0, 2.0]], [1.0])
        self.assertEqual(ctx.exception.code, "DIM")

    def test_b_nulo(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_system([[2.0, 0.0], [0.0, 2.0]], [0.0, 0.0])
        self.assertEqual(ctx.exception.code, "B_CERO")

    def test_b_no_numerico(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_system([[2.0, 0.0], [0.0, 2.0]], [1.0, None])  # type: ignore[list-item]
        self.assertEqual(ctx.exception.code, "NO_NUMERICO")

    def test_vector_dimension(self) -> None:
        with self.assertRaises(NumericalError):
            validate_vector([1.0, 2.0], 3, "b")


class TestValidacionConfig(unittest.TestCase):
    def test_valida(self) -> None:
        self.assertIsNone(validate_config(SolverConfig(), 5))
        self.assertIsNone(
            validate_config(
                SolverConfig(tol=1e-8, max_iter=10, x0=[0.0] * 5, omega=1.5), 5
            )
        )

    def test_tolerancia(self) -> None:
        for tol in (0.0, -1e-6, float("nan")):
            with self.subTest(tol=tol):
                with self.assertRaises(NumericalError) as ctx:
                    validate_config(SolverConfig(tol=tol), 5)
                self.assertEqual(ctx.exception.code, "TOL")

    def test_max_iter(self) -> None:
        for valor in (0, -3, 1.5):  # type: ignore[arg-type]
            with self.subTest(valor=valor):
                with self.assertRaises(NumericalError) as ctx:
                    validate_config(SolverConfig(max_iter=valor), 5)  # type: ignore[arg-type]
                self.assertEqual(ctx.exception.code, "MAX_ITER")

    def test_x0(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            validate_config(SolverConfig(x0=[0.0, 0.0]), 5)
        self.assertEqual(ctx.exception.code, "X0_DIM")

    def test_omega(self) -> None:
        for omega in (0.0, 2.0, -1.0, float("inf")):
            with self.subTest(omega=omega):
                with self.assertRaises(NumericalError) as ctx:
                    validate_config(SolverConfig(omega=omega), 5)
                self.assertEqual(ctx.exception.code, "OMEGA")


class TestConstruccion(unittest.TestCase):
    def test_rho_fuera_de_rango(self) -> None:
        for rho in (-1.0, 1.0, 2.0, float("nan")):
            with self.subTest(rho=rho):
                with self.assertRaises(NumericalError) as ctx:
                    build_A([1.0, 1.0], rho)
                self.assertEqual(ctx.exception.code, "RHO")

    def test_rigidez_no_positiva(self) -> None:
        for valor in (0.0, -1.0, float("nan")):
            with self.subTest(valor=valor):
                with self.assertRaises(NumericalError) as ctx:
                    build_A([1.0, valor], 0.5)
                self.assertEqual(ctx.exception.code, "RIGIDEZ")

    def test_dimension_minima(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            build_A([1.0], 0.5)
        self.assertEqual(ctx.exception.code, "DIM")


class TestValidacionEscenario(unittest.TestCase):
    def test_escenario_valido(self) -> None:
        for spec in (get_scenario("ideal"), get_scenario("estres"), get_scenario("mal")):
            self.assertIsNone(validate_scenario(spec))

    def test_etiquetas_incompletas(self) -> None:
        spec = get_scenario("ideal")
        malo = ScenarioSpec(
            id=spec.id,
            nombre=spec.nombre,
            descripcion=spec.descripcion,
            justificacion=spec.justificacion,
            rho=spec.rho,
            rigidez=spec.rigidez,
            base=spec.base,
            ajuste_objetivo=spec.ajuste_objetivo,
            etiquetas=spec.etiquetas[:2],
        )
        with self.assertRaises(NumericalError) as ctx:
            validate_scenario(malo)
        self.assertEqual(ctx.exception.code, "DIM")

    def test_presupuesto_base_negativo(self) -> None:
        spec = get_scenario("ideal")
        malo = ScenarioSpec(
            id="x",
            nombre="x",
            descripcion="x",
            justificacion="x",
            rho=0.5,
            rigidez=[1.0] * 5,
            base=[-1.0, 1.0, 1.0, 1.0, 1.0],
            ajuste_objetivo=[0.1] * 5,
            etiquetas=[f"x{i}" for i in range(5)],
        )
        with self.assertRaises(NumericalError) as ctx:
            validate_scenario(malo)
        self.assertEqual(ctx.exception.code, "BASE")


if __name__ == "__main__":
    unittest.main()
