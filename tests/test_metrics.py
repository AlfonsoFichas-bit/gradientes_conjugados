"""Pruebas de errores por variable y números de condición."""

from __future__ import annotations

import unittest

from numerics.matrix import build_A, build_b
from numerics.metrics import (
    build_metrics,
    global_relative_residual,
    kappa,
    kappa_preconditioned,
    variable_errors,
)
from numerics.preconditioners import JacobiPreconditioner, SSORPreconditioner
from numerics.scenarios import get_scenario


class TestErroresPorVariable(unittest.TestCase):
    def test_calculo_basico(self) -> None:
        errores = variable_errors([1.0, 0.0, -2.0], [1.5, 0.1, -1.0], ["a", "b", "c"])
        self.assertEqual(len(errores), 3)
        self.assertAlmostEqual(errores[0].absoluto, 0.5)
        self.assertAlmostEqual(errores[0].relativo, 0.5)
        self.assertAlmostEqual(errores[0].porcentual, 50.0)
        self.assertAlmostEqual(errores[2].absoluto, 1.0)
        self.assertAlmostEqual(errores[2].porcentual, 50.0)

    def test_referencia_cero(self) -> None:
        errores = variable_errors([0.0, 2.0], [0.3, 2.1])
        self.assertIsNone(errores[0].relativo)
        self.assertIsNone(errores[0].porcentual)
        self.assertIn("no definido", errores[0].nota)
        self.assertAlmostEqual(errores[1].relativo, 0.05)

    def test_dimensiones_distintas(self) -> None:
        with self.assertRaises(Exception):
            variable_errors([1.0], [1.0, 2.0])

    def test_etiquetas_por_defecto(self) -> None:
        errores = variable_errors([1.0, 2.0], [1.0, 2.0])
        self.assertEqual([e.variable for e in errores], ["x_1", "x_2"])


class TestResiduo(unittest.TestCase):
    def test_sistema_exacto(self) -> None:
        A = [[2.0, 0.0], [0.0, 4.0]]
        x = [3.0, -1.0]
        b = [6.0, -4.0]
        self.assertAlmostEqual(global_relative_residual(A, x, b), 0.0)

    def test_residuo_conocido(self) -> None:
        A = [[1.0, 0.0], [0.0, 1.0]]
        x = [1.0, 1.0]
        b = [2.0, 0.0]
        # r = b - x = [1, -1], ||r|| = sqrt(2), ||b|| = 2
        self.assertAlmostEqual(global_relative_residual(A, x, b), (2.0**0.5) / 2.0)


class TestCondicionamiento(unittest.TestCase):
    def test_kappa_diagonal(self) -> None:
        self.assertAlmostEqual(kappa([[1.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 100.0]]), 100.0)

    def test_kappa_no_spd(self) -> None:
        with self.assertRaises(Exception):
            kappa([[1.0, 2.0], [2.0, 1.0]])

    def test_precondicionador_identidad(self) -> None:
        spec = get_scenario("estres")
        A = build_A(spec.rigidez, spec.rho)
        identidad = [[1.0 if i == j else 0.0 for j in range(5)] for i in range(5)]
        self.assertAlmostEqual(
            kappa_preconditioned(A, identidad), kappa(A), places=10
        )
        self.assertAlmostEqual(kappa_preconditioned(A, None), kappa(A), places=10)

    def test_jacobi_elimina_escalamiento_diagonal(self) -> None:
        A = [[1.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 100.0]]
        self.assertAlmostEqual(kappa_preconditioned(A, JacobiPreconditioner(A)), 1.0, places=10)

    def test_escenario_mal_condicionado(self) -> None:
        spec = get_scenario("mal")
        A = build_A(spec.rigidez, spec.rho)
        k_a = kappa(A)
        k_jacobi = kappa_preconditioned(A, JacobiPreconditioner(A))
        k_ssor = kappa_preconditioned(A, SSORPreconditioner(A, 1.0))
        self.assertGreater(k_a, 1e5)
        self.assertLess(k_jacobi, k_a)
        self.assertLess(k_ssor, k_jacobi)


class TestMetrics(unittest.TestCase):
    def test_build_metrics(self) -> None:
        spec = get_scenario("ideal")
        A = build_A(spec.rigidez, spec.rho)
        b = build_b(A, spec.ajuste_objetivo)
        x = list(spec.ajuste_objetivo)
        metrica = build_metrics("PCG-Jacobi", x, x, A, b, JacobiPreconditioner(A), spec.etiquetas)
        self.assertEqual(metrica.metodo, "PCG-Jacobi")
        self.assertEqual(len(metrica.errores), 5)
        self.assertAlmostEqual(metrica.residuo_relativo_global, 0.0, places=14)
        self.assertAlmostEqual(metrica.error_absoluto_max, 0.0, places=14)
        self.assertGreaterEqual(metrica.reduccion_condicion, 1.0)


if __name__ == "__main__":
    unittest.main()
