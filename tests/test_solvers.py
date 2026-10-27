"""Pruebas de los solvers iterativos y los precondicionadores."""

from __future__ import annotations

import unittest

from numerics.linalg import cholesky, lu_factor, lu_solve
from numerics.matrix import build_A, build_b
from numerics.norms import matvec, norm2
from numerics.preconditioners import (
    JacobiPreconditioner,
    SSORPreconditioner,
    build_preconditioner,
)
from numerics.scenarios import get_scenario
from numerics.solvers import cg, pcg
from numerics.types import NumericalError, SolverConfig


class TestCG(unittest.TestCase):
    def setUp(self) -> None:
        spec = get_scenario("ideal")
        self.A = build_A(spec.rigidez, spec.rho)
        self.b = build_b(self.A, spec.ajuste_objetivo)
        self.x_objetivo = spec.ajuste_objetivo

    def test_converge_y_cumple_tolerancia(self) -> None:
        resultado = cg(self.A, self.b, SolverConfig(tol=1e-10, max_iter=50))
        self.assertTrue(resultado.convergido)
        self.assertLess(resultado.residuo_relativo, 1e-10)
        self.assertLessEqual(len(resultado.historia), resultado.iteraciones + 1)
        for obtenido, esperado in zip(resultado.x, self.x_objetivo):
            self.assertAlmostEqual(obtenido, esperado, places=8)

    def test_historia_es_decreciente(self) -> None:
        resultado = cg(self.A, self.b, SolverConfig(tol=1e-12, max_iter=50))
        historia = resultado.historia
        self.assertGreater(historia[0], 0.0)
        for anterior, siguiente in zip(historia, historia[1:]):
            self.assertLessEqual(siguiente, anterior + 1e-14)

    def test_residuo_reportado_es_verdadero(self) -> None:
        resultado = cg(self.A, self.b)
        r = [bi - ai for bi, ai in zip(self.b, matvec(self.A, resultado.x))]
        self.assertAlmostEqual(norm2(r) / norm2(self.b), resultado.residuo_relativo, places=14)

    def test_respeta_max_iter(self) -> None:
        resultado = cg(self.A, self.b, SolverConfig(tol=1e-18, max_iter=1))
        self.assertFalse(resultado.convergido)
        self.assertEqual(resultado.iteraciones, 1)
        self.assertIn("N_max", resultado.motivo)

    def test_vector_inicial_configurable(self) -> None:
        x0 = [0.1, -0.2, 0.05, 0.0, 0.03]
        resultado = cg(self.A, self.b, SolverConfig(tol=1e-10, max_iter=50, x0=x0))
        self.assertTrue(resultado.convergido)
        self.assertAlmostEqual(resultado.x[0], self.x_objetivo[0], places=8)

    def test_x0_de_dimension_incorrecta(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            cg(self.A, self.b, SolverConfig(x0=[0.0, 0.0]))
        self.assertEqual(ctx.exception.code, "X0_DIM")

    def test_b_nulo(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            cg(self.A, [0.0] * len(self.A))
        self.assertEqual(ctx.exception.code, "B_CERO")


class TestPreconditioners(unittest.TestCase):
    def setUp(self) -> None:
        spec = get_scenario("mal")
        self.A = build_A(spec.rigidez, spec.rho)
        self.b = build_b(self.A, spec.ajuste_objetivo)

    def test_jacobi_es_diagonal(self) -> None:
        M = JacobiPreconditioner(self.A)
        r = [1.0, 2.0, 3.0, 4.0, 5.0]
        z = M.apply(r)
        for i, valor in enumerate(z):
            self.assertAlmostEqual(valor, r[i] / self.A[i][i], places=14)
        matriz = M.matrix()
        self.assertEqual(matriz[0][1], 0.0)

    def test_ssor_apply_equivale_a_resolver_m(self) -> None:
        r = [0.7, -1.2, 0.3, 1.5, -0.4]
        for omega in (0.5, 0.8, 1.0, 1.3, 1.7):
            with self.subTest(omega=omega):
                M = SSORPreconditioner(self.A, omega)
                z = M.apply(r)
                LU, perm = lu_factor(M.matrix())
                z_explicito = lu_solve(LU, perm, r)
                for a, b in zip(z, z_explicito):
                    self.assertLessEqual(abs(a - b), 1e-10 * max(1.0, abs(b)))

    def test_ssor_matrix_es_simetrica_y_definida_positiva(self) -> None:
        for omega in (0.5, 1.0, 1.5):
            M = SSORPreconditioner(self.A, omega)
            matriz = M.matrix()
            self.assertLess(abs(matriz[0][1] - matriz[1][0]), 1e-15)
            cholesky(matriz)  # no debe lanzar

    def test_omega_invalido(self) -> None:
        for omega in (0.0, -0.5, 2.0, 3.0):
            with self.subTest(omega=omega):
                with self.assertRaises(NumericalError) as ctx:
                    SSORPreconditioner(self.A, omega)
                self.assertEqual(ctx.exception.code, "OMEGA")

    def test_fabrica(self) -> None:
        self.assertIsInstance(build_preconditioner("jacobi", self.A), JacobiPreconditioner)
        self.assertIsInstance(build_preconditioner("SSOR", self.A, 0.9), SSORPreconditioner)
        with self.assertRaises(NumericalError):
            build_preconditioner("ilu", self.A)


class TestPCG(unittest.TestCase):
    def setUp(self) -> None:
        spec = get_scenario("mal")
        self.A = build_A(spec.rigidez, spec.rho)
        self.b = build_b(self.A, spec.ajuste_objetivo)
        self.x_objetivo = spec.ajuste_objetivo

    def test_pcg_jacobi_converge(self) -> None:
        resultado = pcg(self.A, self.b, JacobiPreconditioner(self.A), SolverConfig(tol=1e-10))
        self.assertTrue(resultado.convergido)
        self.assertLess(resultado.residuo_relativo, 1e-10)

    def test_pcg_ssor_converge(self) -> None:
        resultado = pcg(
            self.A, self.b, SSORPreconditioner(self.A, 1.0), SolverConfig(tol=1e-10)
        )
        self.assertTrue(resultado.convergido)
        self.assertLess(resultado.residuo_relativo, 1e-10)
        for obtenido, esperado in zip(resultado.x, self.x_objetivo):
            self.assertAlmostEqual(obtenido, esperado, places=8)

    def test_precondicionado_no_usa_mas_iteraciones(self) -> None:
        config = SolverConfig(tol=1e-6)
        simple = cg(self.A, self.b, config)
        jacobi = pcg(self.A, self.b, JacobiPreconditioner(self.A), config)
        ssor = pcg(self.A, self.b, SSORPreconditioner(self.A, 1.0), config)
        self.assertLessEqual(jacobi.iteraciones, simple.iteraciones)
        self.assertLessEqual(ssor.iteraciones, simple.iteraciones)

    def test_pcg_sin_precondicionador(self) -> None:
        with self.assertRaises(NumericalError):
            pcg(self.A, self.b, None)  # type: ignore[arg-type]

    def test_metodo_reportado(self) -> None:
        resultado = pcg(self.A, self.b, JacobiPreconditioner(self.A))
        self.assertEqual(resultado.metodo, "PCG-Jacobi")
        self.assertEqual(resultado.extra["precondicionador"], "Jacobi")


if __name__ == "__main__":
    unittest.main()
