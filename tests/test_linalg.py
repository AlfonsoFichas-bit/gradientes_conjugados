"""Pruebas de factorizaciones, autovalores y operaciones básicas."""

from __future__ import annotations

import math
import unittest

from numerics.linalg import (
    cholesky,
    cholesky_solve,
    inverse_from_cholesky,
    jacobi_eigenvalues,
    lu_factor,
    lu_solve,
)
from numerics.matrix import ar1_precision, build_A, build_b
from numerics.norms import dot, matvec, max_abs_diff, norm2, transpose
from numerics.scenarios import SCENARIOS
from numerics.types import NotPositiveDefiniteError, NumericalError


def _reconstruir(L: list[list[float]]) -> list[list[float]]:
    n = len(L)
    return [
        [math.fsum(L[i][k] * L[j][k] for k in range(n)) for j in range(n)]
        for i in range(n)
    ]


class TestNorms(unittest.TestCase):
    def test_dot_y_norma(self) -> None:
        self.assertAlmostEqual(dot([1.0, 2.0, 3.0], [4.0, -5.0, 6.0]), 12.0)
        self.assertAlmostEqual(norm2([3.0, 4.0]), 5.0)
        self.assertEqual(norm2([0.0, 0.0]), 0.0)

    def test_matvec_y_transpuesta(self) -> None:
        A = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(matvec(A, [1.0, 1.0]), [3.0, 7.0])
        self.assertEqual(transpose(A), [[1.0, 3.0], [2.0, 4.0]])

    def test_max_abs_diff(self) -> None:
        A = [[1.0, 2.0], [3.0, 4.0]]
        B = [[1.0, 2.5], [3.0, 3.5]]
        self.assertAlmostEqual(max_abs_diff(A, B), 0.5)


class TestCholesky(unittest.TestCase):
    def test_reconstruye_matriz(self) -> None:
        A = [[4.0, 2.0, 1.0], [2.0, 5.0, 3.0], [1.0, 3.0, 6.0]]
        L = cholesky(A)
        self.assertLess(max_abs_diff(_reconstruir(L), A), 1e-13)
        self.assertTrue(all(L[i][j] == 0.0 for i in range(3) for j in range(i + 1, 3)))

    def test_solucion_conocida(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        b = [1.0, 2.0]
        x = cholesky_solve(cholesky(A), b)
        self.assertLess(max_abs_diff([matvec(A, x)], [b]), 1e-14)
        self.assertAlmostEqual(x[0], 1.0 / 11.0, places=14)
        self.assertAlmostEqual(x[1], 7.0 / 11.0, places=14)

    def test_inversa(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        inv = inverse_from_cholesky(cholesky(A))
        producto = [[math.fsum(A[i][k] * inv[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        self.assertLess(max_abs_diff(producto, [[1.0, 0.0], [0.0, 1.0]]), 1e-13)

    def test_rechaza_no_definida_positiva(self) -> None:
        with self.assertRaises(NotPositiveDefiniteError) as ctx:
            cholesky([[1.0, 2.0], [2.0, 1.0]])
        self.assertEqual(ctx.exception.code, "NO_SPD")

    def test_rechaza_no_cuadrada(self) -> None:
        with self.assertRaises(NumericalError):
            cholesky([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])


class TestLU(unittest.TestCase):
    def test_coincide_con_cholesky_en_escenarios(self) -> None:
        for spec in SCENARIOS:
            A = build_A(spec.rigidez, spec.rho)
            b = build_b(A, spec.ajuste_objetivo)
            x_chol = cholesky_solve(cholesky(A), b)
            LU, perm = lu_factor(A)
            x_lu = lu_solve(LU, perm, b)
            self.assertLess(max_abs_diff([x_chol], [x_lu]), 1e-12, spec.id)

    def test_pivoteo_parcial(self) -> None:
        A = [[0.0, 2.0], [1.0, 3.0]]
        b = [4.0, 5.0]
        LU, perm = lu_factor(A)
        x = lu_solve(LU, perm, b)
        self.assertAlmostEqual(x[0], -1.0, places=12)
        self.assertAlmostEqual(x[1], 2.0, places=12)

    def test_matriz_singular(self) -> None:
        with self.assertRaises(NumericalError) as ctx:
            lu_factor([[1.0, 2.0], [2.0, 4.0]])
        self.assertEqual(ctx.exception.code, "SINGULAR")


class TestJacobiEigenvalues(unittest.TestCase):
    def test_matriz_diagonal(self) -> None:
        valores = jacobi_eigenvalues([[3.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 2.0]])
        self.assertEqual(valores, [1.0, 2.0, 3.0])

    def test_caso_2x2(self) -> None:
        valores = jacobi_eigenvalues([[1.0, 1.0], [1.0, 2.0]])
        self.assertAlmostEqual(valores[0], (3.0 - math.sqrt(5.0)) / 2.0, places=12)
        self.assertAlmostEqual(valores[1], (3.0 + math.sqrt(5.0)) / 2.0, places=12)

    def test_ar1_es_spd_y_su_inversa_es_tridiagonal(self) -> None:
        n = 6
        rho = 0.62
        R = build_A([1.0] * n, rho)
        valores = jacobi_eigenvalues(R)
        self.assertGreater(valores[0], 0.0)

        inversa = inverse_from_cholesky(cholesky(R))
        precision = ar1_precision(n, rho)
        self.assertLess(max_abs_diff(inversa, precision), 1e-11)

        # Dominancia diagonal estricta de R^-1: garantiza D.P.
        for i in range(n):
            fuera = math.fsum(abs(precision[i][j]) for j in range(n) if j != i)
            self.assertLess(fuera, precision[i][i])


if __name__ == "__main__":
    unittest.main()
