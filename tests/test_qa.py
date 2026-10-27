"""Pruebas del módulo QA y de la interfaz de línea de comandos."""

from __future__ import annotations

import contextlib
import io
import json
import unittest

from numerics.cli import main
from numerics.qa import run_qa
from numerics.types import SolverConfig


class TestQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.casos = run_qa(SolverConfig(tol=1e-6, max_iter=200))

    def test_cuatro_pruebas(self) -> None:
        self.assertEqual(len(self.casos), 4)
        self.assertEqual([caso.id for caso in self.casos], [1, 2, 3, 4])

    def test_todas_aprobadas(self) -> None:
        for caso in self.casos:
            with self.subTest(prueba=caso.id):
                self.assertTrue(caso.ok, caso.obtenido)
                self.assertTrue(caso.entrada)
                self.assertTrue(caso.esperado)
                self.assertTrue(caso.obtenido)
                self.assertTrue(caso.conclusion)

    def test_prueba_2_reporta_codigos(self) -> None:
        codigos = {caso["codigo"] for caso in self.casos[1].detalle["casos"]}
        self.assertEqual(
            codigos, {"ASIMETRICA", "NO_SPD", "DIM", "NO_NUMERICO", "NO_FINITO"}
        )

    def test_prueba_4_compara_iteraciones(self) -> None:
        detalle = self.casos[3].detalle
        self.assertLessEqual(detalle["iter_jacobi"], detalle["iter_cg"])
        self.assertLessEqual(detalle["iter_ssor"], detalle["iter_cg"])

    def test_serializacion(self) -> None:
        for caso in self.casos:
            json.dumps(caso.to_dict(), ensure_ascii=False)


class TestCLI(unittest.TestCase):
    def _ejecutar(self, argumentos: list[str]) -> tuple[int, str]:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = main(argumentos)
        return codigo, salida.getvalue()

    def test_json_escenario(self) -> None:
        codigo, salida = self._ejecutar(["--json", "--scenario", "ideal"])
        self.assertEqual(codigo, 0)
        datos = json.loads(salida)
        self.assertEqual(len(datos["escenarios"]), 1)
        self.assertEqual(datos["escenarios"][0]["escenario"]["id"], "ideal")
        self.assertIn("resumen", datos)

    def test_json_todos(self) -> None:
        codigo, salida = self._ejecutar(["--json"])
        self.assertEqual(codigo, 0)
        datos = json.loads(salida)
        self.assertEqual(len(datos["escenarios"]), 3)
        self.assertEqual(len(datos["resumen"]), 3)

    def test_qa_json(self) -> None:
        codigo, salida = self._ejecutar(["--qa", "--json"])
        self.assertEqual(codigo, 0)
        datos = json.loads(salida)
        self.assertEqual(datos["total"], 4)
        self.assertEqual(datos["aprobadas"], 4)

    def test_error_configuracion(self) -> None:
        codigo, salida = self._ejecutar(["--json", "--tol", "-1"])
        self.assertEqual(codigo, 2)
        datos = json.loads(salida)
        self.assertEqual(datos["error"]["code"], "TOL")

    def test_error_x0(self) -> None:
        codigo, salida = self._ejecutar(["--json", "--x0", "a,b"])
        self.assertEqual(codigo, 2)
        self.assertEqual(json.loads(salida)["error"]["code"], "X0")

    def test_salida_humana(self) -> None:
        codigo, salida = self._ejecutar(["--scenario", "estres", "--tol", "1e-8"])
        self.assertEqual(codigo, 0)
        self.assertIn("ESCENARIO 1", salida)
        self.assertIn("Bajo estrés financiero", salida)
        self.assertIn("RESUMEN", salida.upper())


if __name__ == "__main__":
    unittest.main()
