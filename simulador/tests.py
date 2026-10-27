"""Pruebas de la capa web: endpoint de recálculo del Módulo 4."""

from __future__ import annotations

import json
from unittest import mock

from django.test import Client, SimpleTestCase

from numerics import build_A, build_b, get_scenario

URL = "/api/resolver/"


class ResolverApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.spec = get_scenario("ideal")
        self.A = build_A(self.spec.rigidez, self.spec.rho)
        self.b = build_b(self.A, self.spec.ajuste_objetivo)

    def post(self, payload: object):
        return self.client.post(
            URL, data=json.dumps(payload), content_type="application/json"
        )

    def cuerpo(self, **cambios: object) -> dict:
        datos: dict = {"escenario_id": "ideal", "A": self.A, "b": self.b}
        datos.update(cambios)
        return datos

    def test_recalcula_un_sistema_valido(self) -> None:
        respuesta = self.post(self.cuerpo())
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertTrue(datos["ok"])
        resultado = datos["resultado"]
        self.assertEqual(resultado["escenario"]["id"], "personalizado")
        self.assertEqual(resultado["escenario"]["base"], self.spec.base)
        self.assertEqual(set(resultado["metodos"]), {"cg", "pcg_jacobi", "pcg_ssor"})
        self.assertTrue(resultado["diagnostico"]["es_spd_cholesky"])
        self.assertGreaterEqual(resultado["metodos"]["cg"]["iteraciones"], 1)
        self.assertIn("κ(A)", datos["interpretacion"])
        self.assertIn("iter_cg", datos["resumen"])

    def test_acepta_configuracion_personalizada(self) -> None:
        respuesta = self.post(self.cuerpo(tol=1e-9, max_iter=300, omega=1.2))
        self.assertEqual(respuesta.status_code, 200)
        parametros = respuesta.json()["resultado"]["parametros"]
        self.assertEqual(parametros["tol"], 1e-9)
        self.assertEqual(parametros["max_iter"], 300)
        self.assertEqual(parametros["omega"], 1.2)

    def test_rechaza_matriz_asimetrica(self) -> None:
        A = [list(fila) for fila in self.A]
        A[0][1] += 0.5
        error = self.post(self.cuerpo(A=A)).json()["error"]
        self.assertEqual(error["code"], "ASIMETRICA")
        self.assertEqual(error["field"], "A")

    def test_rechaza_matriz_no_spd(self) -> None:
        A = [list(fila) for fila in self.A]
        A[0][0] = -1.0
        self.assertEqual(
            self.post(self.cuerpo(A=A)).json()["error"]["code"], "NO_SPD"
        )

    def test_rechaza_dimension_distinta(self) -> None:
        self.assertEqual(
            self.post(
                self.cuerpo(A=[[4.0, 1.0], [1.0, 3.0]], b=[1.0, 2.0])
            ).json()["error"]["code"],
            "DIM",
        )

    def test_rechaza_vector_b_incompatible(self) -> None:
        self.assertEqual(
            self.post(self.cuerpo(b=[1.0, 2.0])).json()["error"]["code"], "DIM"
        )

    def test_rechaza_escenario_desconocido(self) -> None:
        self.assertEqual(
            self.post(self.cuerpo(escenario_id="inexistente")).json()["error"]["code"],
            "ESCENARIO",
        )

    def test_rechaza_tolerancia_invalida(self) -> None:
        self.assertEqual(
            self.post(self.cuerpo(tol=0)).json()["error"]["code"], "TOL"
        )

    def test_rechaza_omega_fuera_de_rango(self) -> None:
        self.assertEqual(
            self.post(self.cuerpo(omega=2.5)).json()["error"]["code"], "OMEGA"
        )

    def test_fallo_interno_no_filtra_la_traza(self) -> None:
        with mock.patch("simulador.views.run_custom", side_effect=RuntimeError("boom")):
            with self.assertLogs("simulador.views", level="ERROR"):
                respuesta = self.post(self.cuerpo())
        self.assertEqual(respuesta.status_code, 500)
        cuerpo = respuesta.json()
        self.assertFalse(cuerpo["ok"])
        error = cuerpo["error"]
        self.assertEqual(error["code"], "INTERNO")
        self.assertEqual(error["field"], None)
        texto = respuesta.content.decode()
        self.assertNotIn("boom", texto)
        self.assertNotIn("Traceback", texto)

    def test_acepta_content_type_distinto_de_json(self) -> None:
        # Contrato actual: el cuerpo se procesa igual aunque el Content-Type no
        # sea application/json. Endurecer a 415 es una decisión aparte, no de
        # este cambio de verificación.
        respuesta = self.client.post(
            URL, data=json.dumps(self.cuerpo()), content_type="text/plain"
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["ok"])

    def test_rechaza_max_iter_no_entero(self) -> None:
        self.assertEqual(
            self.post(self.cuerpo(max_iter=2.5)).json()["error"]["code"], "CONFIG"
        )

    def test_rechaza_componentes_no_numericas(self) -> None:
        with self.subTest(campo="A"):
            A = [list(fila) for fila in self.A]
            A[0][0] = "x"
            error = self.post(self.cuerpo(A=A)).json()["error"]
            self.assertEqual(error["code"], "NO_NUMERICO")
            self.assertEqual(error["field"], "A")
        with self.subTest(campo="b"):
            error = self.post(
                self.cuerpo(b=["x"] + list(self.b)[1:])
            ).json()["error"]
            self.assertEqual(error["code"], "NO_NUMERICO")
            self.assertEqual(error["field"], "b")

    def test_rechaza_forma_invalida(self) -> None:
        with self.subTest(caso="A no cuadrada"):
            A = [list(fila) for fila in self.A]
            A[0].append(0.0)
            error = self.post(self.cuerpo(A=A)).json()["error"]
            self.assertEqual(error["code"], "DIM")
            self.assertEqual(error["field"], "A")
        with self.subTest(caso="A no es lista"):
            error = self.post(self.cuerpo(A="no es lista")).json()["error"]
            self.assertEqual(error["code"], "DIM")
            self.assertEqual(error["field"], "A")
        with self.subTest(caso="A ausente"):
            datos = self.cuerpo()
            datos.pop("A")
            error = self.post(datos).json()["error"]
            self.assertEqual(error["code"], "DIM")
            self.assertEqual(error["field"], "A")
        with self.subTest(caso="b ausente"):
            datos = self.cuerpo()
            datos.pop("b")
            error = self.post(datos).json()["error"]
            self.assertEqual(error["code"], "DIM")
            self.assertEqual(error["field"], "A")

    def test_rechaza_parametros_de_texto(self) -> None:
        for clave in ("tol", "max_iter", "omega"):
            with self.subTest(parametro=clave):
                error = self.post(self.cuerpo(**{clave: "abc"})).json()["error"]
                self.assertEqual(error["code"], "CONFIG")
                self.assertEqual(error["field"], clave)

    def test_seleccion_de_escenario(self) -> None:
        error = self.post(self.cuerpo(escenario_id=5)).json()["error"]
        self.assertEqual(error["code"], "ESCENARIO")

        datos = self.cuerpo()
        datos.pop("escenario_id")
        respuesta = self.post(datos).json()
        self.assertTrue(respuesta["ok"])
        self.assertEqual(
            respuesta["resultado"]["escenario"]["base"], self.spec.base
        )

    def test_errores_de_dominio_no_usan_4xx(self) -> None:
        A = [list(fila) for fila in self.A]
        A[0][1] += 0.5
        respuesta = self.post(self.cuerpo(A=A))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])
        self.assertEqual(respuesta.json()["error"]["code"], "ASIMETRICA")

    def test_acepta_vector_inicial(self) -> None:
        x0 = [0.1, -0.2, 0.3, -0.4, 0.5]
        datos = self.post(self.cuerpo(x0=x0)).json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["resultado"]["parametros"]["x0"], x0)

    def test_x0_igual_a_la_solucion_converge_de_inmediato(self) -> None:
        x_ref = self.post(self.cuerpo()).json()["resultado"]["referencia"]["x"]
        datos = self.post(self.cuerpo(x0=x_ref)).json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["resultado"]["metodos"]["cg"]["iteraciones"], 0)
        self.assertTrue(datos["resultado"]["metodos"]["cg"]["convergido"])

    def test_rechaza_x0_de_dimension_incorrecta(self) -> None:
        error = self.post(self.cuerpo(x0=[0.0, 0.0])).json()["error"]
        self.assertEqual(error["code"], "X0_DIM")
        self.assertEqual(error["field"], "x0")

    def test_rechaza_x0_que_no_es_lista(self) -> None:
        error = self.post(self.cuerpo(x0="0,0,0,0,0")).json()["error"]
        self.assertEqual(error["code"], "X0_DIM")

    def test_rechaza_x0_no_numerico(self) -> None:
        error = self.post(self.cuerpo(x0=[0, 0, 0, 0, "x"])).json()["error"]
        self.assertEqual(error["code"], "X0_DIM")

    def test_rechaza_json_invalido(self) -> None:
        respuesta = self.client.post(URL, data="{", content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"]["code"], "JSON")

    def test_rechaza_cuerpo_demasiado_grande(self) -> None:
        respuesta = self.client.post(
            URL, data="x" * 65_000, content_type="application/json"
        )
        self.assertEqual(respuesta.status_code, 413)

    def test_get_no_permitido(self) -> None:
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_home_establece_la_cookie_csrf(self) -> None:
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("csrftoken", respuesta.cookies)

    def test_csrf_obligatorio(self) -> None:
        cliente = Client(enforce_csrf_checks=True)
        sin_token = cliente.post(
            URL, data=json.dumps(self.cuerpo()), content_type="application/json"
        )
        self.assertEqual(sin_token.status_code, 403)

        cliente.get("/")
        token = cliente.cookies["csrftoken"].value
        con_token = cliente.post(
            URL,
            data=json.dumps(self.cuerpo()),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(con_token.status_code, 200)


class SaludApiTests(SimpleTestCase):
    def test_salud_ok(self) -> None:
        respuesta = self.client.get("/salud/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"].split(";")[0], "application/json")
        datos = respuesta.json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["nucleo"], "numerics")

    def test_salud_no_acepta_post(self) -> None:
        respuesta = self.client.post("/salud/")
        self.assertEqual(respuesta.status_code, 405)
