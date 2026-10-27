"""Pruebas de integración del núcleo numérico y de los escenarios calibrados."""

from __future__ import annotations

import json
import unittest

from numerics.experiment import (
    analyze,
    run_all,
    run_custom,
    run_scenario,
    scenario_summary,
)
from numerics.matrix import build_A, build_b
from numerics.norms import matvec, max_abs_diff
from numerics.scenarios import AVISO_DATOS, SCENARIOS, get_scenario
from numerics.types import NumericalError, SolverConfig


class TestEscenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resultados = run_all(SolverConfig(tol=1e-6, max_iter=200))

    def test_tres_escenarios(self) -> None:
        self.assertEqual([r.escenario.id for r in self.resultados], ["ideal", "estres", "mal"])

    def test_todos_convergen(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                self.assertTrue(resultado.referencia.convergido)
                self.assertLess(resultado.referencia.residuo_relativo, 1e-10)
                for metodo in resultado.metodos.values():
                    self.assertTrue(metodo.convergido, metodo.metodo)
                    self.assertLess(metodo.residuo_relativo, 1e-6)

    def test_diagnostico_spd(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                diag = resultado.diagnostico
                self.assertLess(diag.simetria_max, 1e-15)
                self.assertGreater(diag.autovalor_min, 0.0)
                self.assertTrue(diag.es_spd_cholesky)
                self.assertTrue(all(p > 0.0 for p in diag.pivotes_cholesky))
                self.assertAlmostEqual(
                    diag.kappa_A, diag.autovalor_max / diag.autovalor_min, places=6
                )

    def test_calibracion_aprobada(self) -> None:
        esperado = {
            "ideal": (2.99, 2.89, 1.10, 5, 5, 2),
            "estres": (23.06, 21.43, 2.29, 5, 5, 2),
            "mal": (3.09e5, 433.8, 25.25, 6, 5, 2),
        }
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                k_a, k_j, k_s, it_cg, it_j, it_s = esperado[resultado.escenario.id]
                resumen = scenario_summary(resultado)
                self.assertAlmostEqual(resumen["kappa_A"] / k_a, 1.0, places=2)
                self.assertAlmostEqual(resumen["kappa_jacobi"] / k_j, 1.0, places=2)
                self.assertAlmostEqual(resumen["kappa_ssor"] / k_s, 1.0, places=2)
                self.assertEqual(resumen["iter_cg"], it_cg)
                self.assertEqual(resumen["iter_jacobi"], it_j)
                self.assertEqual(resumen["iter_ssor"], it_s)

    def test_b_es_la_imagen_del_ajuste_objetivo(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                esperado = matvec(resultado.A, resultado.escenario.ajuste_objetivo)
                self.assertLess(max_abs_diff([esperado], [resultado.b]), 1e-14)

    def test_presupuesto_final(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                self.assertEqual(len(resultado.presupuesto_final), resultado.escenario.n)
                for base, ajuste, final in zip(
                    resultado.escenario.base,
                    resultado.metodos["pcg_jacobi"].x,
                    resultado.presupuesto_final,
                ):
                    self.assertAlmostEqual(base + ajuste, final, places=12)

    def test_metricas_por_metodo(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                self.assertEqual(set(resultado.metricas), {"cg", "pcg_jacobi", "pcg_ssor"})
                for metrica in resultado.metricas.values():
                    self.assertEqual(len(metrica.errores), 5)
                    self.assertLess(metrica.residuo_relativo_global, 1e-6)

    def test_serializacion_json(self) -> None:
        for resultado in self.resultados:
            with self.subTest(escenario=resultado.escenario.id):
                texto = json.dumps(resultado.to_dict(), ensure_ascii=False)
                self.assertGreater(len(texto), 100)
                self.assertIn(resultado.escenario.id, texto)

    def test_resumen(self) -> None:
        resumen = scenario_summary(self.resultados[0])
        claves = {
            "id",
            "x_referencia",
            "x_cg",
            "x_pcg_jacobi",
            "x_pcg_ssor",
            "iter_cg",
            "iter_jacobi",
            "iter_ssor",
            "kappa_A",
            "kappa_jacobi",
            "kappa_ssor",
            "residuo_jacobi",
            "convergieron",
            "presupuesto_final",
            "interpretacion",
        }
        self.assertTrue(claves.issubset(resumen))
        self.assertTrue(resumen["interpretacion"])


class TestEscenarioIndividual(unittest.TestCase):
    def test_alias_con_acento(self) -> None:
        spec = get_scenario("estrés")
        self.assertEqual(spec.id, "estres")

    def test_run_scenario_por_objeto(self) -> None:
        spec = get_scenario("ideal")
        resultado = run_scenario(spec, SolverConfig())
        self.assertEqual(resultado.escenario.id, "ideal")

    def test_escenario_desconocido(self) -> None:
        with self.assertRaises(Exception):
            get_scenario("inexistente")

    def test_aviso_de_datos(self) -> None:
        self.assertIn("ilustrativos", AVISO_DATOS)
        self.assertTrue(all(spec.n == 5 for spec in SCENARIOS))


class TestSistemaPersonalizado(unittest.TestCase):
    def test_analyze_genera_escenario_sintetico(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        b = [1.0, 2.0]
        resultado = analyze(A, b, config=SolverConfig(tol=1e-12, max_iter=50))
        self.assertEqual(resultado.escenario.id, "personalizado")
        self.assertEqual(resultado.escenario.n, 2)
        self.assertTrue(resultado.referencia.convergido)
        self.assertTrue(resultado.metodos["cg"].convergido)
        self.assertAlmostEqual(resultado.presupuesto_final[0], resultado.referencia.x[0])

    def test_analyze_acepta_base(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        b = [1.0, 2.0]
        resultado = analyze(A, b, base=[10.0, 20.0], config=SolverConfig())
        self.assertAlmostEqual(resultado.presupuesto_final[0], 10.0 + resultado.metodos["pcg_jacobi"].x[0])

    def test_no_muta_el_escenario_original(self) -> None:
        spec = get_scenario("ideal")
        base_original = list(spec.base)
        A = build_A(spec.rigidez, spec.rho)
        b = build_b(A, spec.ajuste_objetivo)
        analyze(A, b, spec=spec, base=[9.0] * 5)
        self.assertEqual(spec.base, base_original)


class TestSistemaEditado(unittest.TestCase):
    """``run_custom`` alimenta el editor de coeficientes del Módulo 4."""

    def setUp(self) -> None:
        self.base = get_scenario("ideal")
        self.A = build_A(self.base.rigidez, self.base.rho)
        self.b = build_b(self.A, self.base.ajuste_objetivo)

    def test_conserva_categorias_y_presupuesto_base(self) -> None:
        resultado = run_custom(self.A, self.b, self.base)
        self.assertEqual(resultado.escenario.id, "personalizado")
        self.assertIn("editado", resultado.escenario.nombre)
        self.assertEqual(resultado.escenario.base, self.base.base)
        self.assertEqual(resultado.escenario.etiquetas, self.base.etiquetas)
        self.assertEqual(resultado.escenario.unidad, self.base.unidad)
        self.assertEqual(resultado.escenario.rigidez, [self.A[i][i] for i in range(5)])

    def test_ajuste_objetivo_es_la_referencia_directa(self) -> None:
        resultado = run_custom(self.A, self.b, self.base)
        self.assertEqual(resultado.escenario.ajuste_objetivo, resultado.referencia.x)
        for metrica in resultado.metricas.values():
            self.assertEqual(len(metrica.errores), 5)
            self.assertEqual(metrica.errores[0].variable, self.base.etiquetas[0])

    def test_presupuesto_final_parte_de_la_base(self) -> None:
        resultado = run_custom(self.A, self.b, self.base)
        for base_i, x_i, final_i in zip(
            self.base.base, resultado.metodos["pcg_jacobi"].x, resultado.presupuesto_final
        ):
            self.assertAlmostEqual(final_i, base_i + x_i)

    def test_rechaza_dimension_distinta(self) -> None:
        A = [[4.0, 1.0], [1.0, 3.0]]
        with self.assertRaises(NumericalError) as ctx:
            run_custom(A, [1.0, 2.0], self.base)
        self.assertEqual(ctx.exception.code, "DIM")

    def test_rechaza_matriz_asimetrica(self) -> None:
        A = [list(fila) for fila in self.A]
        A[0][1] += 0.5
        with self.assertRaises(NumericalError) as ctx:
            run_custom(A, self.b, self.base)
        self.assertEqual(ctx.exception.code, "ASIMETRICA")

    def test_rechaza_sistema_no_spd(self) -> None:
        A = [list(fila) for fila in self.A]
        A[0][0] = -1.0
        with self.assertRaises(NumericalError) as ctx:
            run_custom(A, self.b, self.base)
        self.assertEqual(ctx.exception.code, "NO_SPD")


if __name__ == "__main__":
    unittest.main()
