"""Los tres escenarios obligatorios y la procedencia de los datos.

Las cifras son **ilustrativas**: se calibraron para que el sistema tenga la
estructura matemática exigida (simétrico, definido positivo, ``n = 5``) y para
que los tres escenarios exhiban el comportamiento esperado. No son cifras
oficiales del Consejo de la Magistratura.
"""

from __future__ import annotations

from .types import ScenarioSpec

AVISO_DATOS = (
    "Los montos base, rigideces y ajustes objetivos son ilustrativos y fueron "
    "calibrados con fines académicos. No corresponden a cifras oficiales, "
    "ejecutadas ni proyectadas por el Consejo de la Magistratura."
)

PROCEDENCIA = {
    "entidad": "USIE — Consejo de la Magistratura (La Paz, Bolivia)",
    "area": "Finanzas y presupuesto de tecnologías de la información",
    "unidad": "millones de bolivianos (MM Bs)",
    "fuente": (
        "Estructura de categorías tomada de un presupuesto institucional típico "
        "de TI (personal, hardware, software, conectividad y soporte). Los valores "
        "numéricos se calibraron de forma deliberada para el experimento numérico."
    ),
    "racionalidad": (
        "Cada variable x_i representa el ajuste neto (positivo o negativo) sobre "
        "la línea presupuestaria i. El sistema Ax = b relaciona esos ajustes con "
        "el requerimiento neto b: la rigidez d_i mide cuánto resiste una línea a "
        "moverse y rho mide la interdependencia entre líneas contiguas."
    ),
    "verificacion": (
        "El vector b se obtiene como b = A·x* a partir de un ajuste objetivo x* "
        "conocido. Así la solución exacta queda disponible para verificar los "
        "métodos (verificación de software, no pronóstico financiero)."
    ),
}

CATEGORIAS = [
    "Personal y consultoría TI",
    "Hardware e infraestructura",
    "Software y licencias",
    "Conectividad y telecomunicaciones",
    "Mantenimiento y soporte técnico",
]

BASE = [1.80, 1.20, 0.90, 0.70, 0.60]

IDEAL = ScenarioSpec(
    id="ideal",
    nombre="Ideal",
    descripcion=(
        "Entorno financiero estable: inflación contenida, asignaciones "
        "previsibles y baja interdependencia entre categorías."
    ),
    justificacion=(
        "rho = 0,30 indica que un ajuste en una línea apenas se transmite a las "
        "siguientes. Las rigideces (0,90 a 1,20) son cercanas entre sí, de modo "
        "que ninguna categoría domina el sistema. Se espera kappa(A) bajo y "
        "convergencia rápida de ambos métodos."
    ),
    rho=0.30,
    rigidez=[1.00, 1.10, 0.90, 1.20, 1.00],
    base=list(BASE),
    ajuste_objetivo=[-0.18, 0.06, -0.09, 0.07, 0.03],
    etiquetas=list(CATEGORIAS),
)

ESTRES = ScenarioSpec(
    id="estres",
    nombre="Bajo estrés financiero",
    descripcion=(
        "Choque inflacionario y aumento de costos operativos: las categorías "
        "acopladas deben ajustarse en bloque y el punto de equilibrio se desplaza."
    ),
    justificacion=(
        "rho = 0,75 eleva la correlación entre líneas contiguas (compras y "
        "contratos se renegocian juntos). Las rigideces se dispersan (0,80 a "
        "1,40) porque hardware y conectividad absorben el mayor impacto de "
        "precios. kappa(A) sube a un valor moderado sin perder la estructura."
    ),
    rho=0.75,
    rigidez=[1.00, 1.25, 0.80, 1.40, 0.95],
    base=list(BASE),
    ajuste_objetivo=[-0.45, 0.12, -0.18, 0.14, 0.06],
    etiquetas=list(CATEGORIAS),
)

MAL_CONDICIONADO = ScenarioSpec(
    id="mal",
    nombre="Mal condicionado",
    descripcion=(
        "Interdependencia extrema y escalas presupuestarias muy dispares: una "
        "línea concentra el gasto mientras otras son marginales."
    ),
    justificacion=(
        "rho = 0,98 hace que todas las categorías se muevan casi como una sola, "
        "y las rigideces abarcan cuatro órdenes de magnitud (1e-4 a 1,0). La "
        "matriz sigue siendo D.P. por congruencia con una matriz de correlación, "
        "pero kappa(A) es del orden de 1e5; aquí el precondicionador es decisivo."
    ),
    rho=0.98,
    rigidez=[1e-4, 1e-3, 1e-2, 1e-1, 1.0],
    base=list(BASE),
    ajuste_objetivo=[-0.40, 0.15, -0.35, 0.20, 0.08],
    etiquetas=list(CATEGORIAS),
)

SCENARIOS: tuple[ScenarioSpec, ...] = (IDEAL, ESTRES, MAL_CONDICIONADO)
SCENARIOS_POR_ID = {escenario.id: escenario for escenario in SCENARIOS}

_ALIAS = {
    "ideal": "ideal",
    "estres": "estres",
    "estrés": "estres",
    "bajo estres": "estres",
    "bajo estrés": "estres",
    "mal": "mal",
    "mal condicionado": "mal",
    "malcondicionado": "mal",
}


def get_scenario(identificador: str) -> ScenarioSpec:
    """Busca un escenario por id o alias (``"estrés"``, ``"mal condicionado"``)."""
    clave = (identificador or "").strip().lower()
    clave = _ALIAS.get(clave, clave)
    if clave not in SCENARIOS_POR_ID:
        disponibles = ", ".join(SCENARIOS_POR_ID)
        from .types import NumericalError

        raise NumericalError(
            "ESCENARIO",
            f"Escenario desconocido: {identificador!r}. Disponibles: {disponibles}.",
            "escenario",
        )
    return SCENARIOS_POR_ID[clave]
