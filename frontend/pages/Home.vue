<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { ApiError, HomeProps, ResolverResponse, ScenarioPayload } from '../types'

const props = defineProps<HomeProps>()

const activoId = ref<string>(props.escenarios[0]?.resultado.escenario.id ?? 'ideal')
const escenarioBase = computed<ScenarioPayload | undefined>(
  () =>
    props.escenarios.find((e) => e.resultado.escenario.id === activoId.value) ??
    props.escenarios[0],
)
const personalizado = ref<ScenarioPayload | null>(null)
const activo = computed<ScenarioPayload | undefined>(
  () => personalizado.value ?? escenarioBase.value,
)
const editado = computed(() => personalizado.value !== null)

const CLAVES = ['cg', 'pcg_jacobi', 'pcg_ssor'] as const
type Clave = (typeof CLAVES)[number]

const nombresMetodo: Record<Clave, string> = {
  cg: 'GC simple',
  pcg_jacobi: 'PCG-Jacobi',
  pcg_ssor: 'PCG-SSOR',
}

const coloresMetodo: Record<Clave, string> = {
  cg: '#27272a',
  pcg_jacobi: '#71717a',
  pcg_ssor: '#1d5fbf',
}

function num(valor: number | null | undefined, decimales = 4): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  return valor.toLocaleString('es-BO', {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  })
}

function compacto(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  if (valor === 0) return '0'
  const absoluto = Math.abs(valor)
  if (absoluto >= 1e4 || absoluto < 1e-3) return valor.toExponential(2)
  if (absoluto >= 100) return valor.toFixed(0)
  if (absoluto >= 10) return valor.toFixed(1)
  return valor.toFixed(2)
}

function cientifico(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  if (valor === 0) return '0'
  return valor.toExponential(2)
}

function porcentaje(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  if (valor === 0) return '0 %'
  if (Math.abs(valor) < 0.01) return `${valor.toExponential(1)} %`
  return `${valor.toFixed(2)} %`
}

function matriz(valor: number): string {
  if (valor === 0) return '0'
  const absoluto = Math.abs(valor)
  if (absoluto < 1e-3) return valor.toExponential(1)
  return valor.toFixed(3)
}

const filasVariables = computed(() => {
  const e = activo.value
  if (!e) return []
  const r = e.resultado
  return props.categorias.map((nombre, i) => {
    const error = r.metricas.pcg_jacobi.errores[i]
    return {
      nombre,
      base: r.escenario.base[i],
      referencia: r.referencia.x[i],
      cg: r.metodos.cg.x[i],
      pcg: r.metodos.pcg_jacobi.x[i],
      final: r.presupuesto_final[i],
      ea: error?.absoluto ?? 0,
      er: error?.relativo ?? null,
      ep: error?.porcentual ?? null,
    }
  })
})

const metodosFilas = computed(() => {
  const e = activo.value
  if (!e) return []
  return CLAVES.map((clave) => {
    const metodo = e.resultado.metodos[clave]
    const metrica = e.resultado.metricas[clave]
    return {
      clave,
      nombre: nombresMetodo[clave],
      color: coloresMetodo[clave],
      iteraciones: metodo.iteraciones,
      residuo: metodo.residuo_relativo,
      kappa: metrica.kappa_precondicionada,
      error: metrica.error_absoluto_max,
      convergido: metodo.convergido,
      motivo: metodo.motivo,
    }
  })
})

const historias = computed(() =>
  metodosFilas.value.map((fila) => ({
    nombre: fila.nombre,
    color: fila.color,
    datos: activo.value?.resultado.metodos[fila.clave].historia ?? [],
  })),
)

const maxLen = computed(() =>
  Math.max(...historias.value.map((h) => h.datos.length), 2),
)

const rangoGrafica = computed(() => {
  const valores = historias.value
    .flatMap((h) => h.datos)
    .map((v) => Math.log10(Math.max(v, 1e-18)))
  const minimo = Math.max(-18, Math.min(-2, Math.floor(Math.min(...valores))))
  return { min: minimo, max: 0 }
})

const ANCHO = 560
const ALTO = 150
const MARGEN = 12

function xGrafica(indice: number): number {
  return MARGEN + (indice / (maxLen.value - 1)) * (ANCHO - 2 * MARGEN)
}

function yGrafica(valor: number): number {
  const log = Math.log10(Math.max(valor, 1e-18))
  const { min, max } = rangoGrafica.value
  return ALTO - MARGEN - ((log - min) / (max - min)) * (ALTO - 2 * MARGEN)
}

function puntosGrafica(datos: number[]): string {
  return datos.map((valor, i) => `${xGrafica(i).toFixed(2)},${yGrafica(valor).toFixed(2)}`).join(' ')
}

const grilla = computed(() => {
  const { min } = rangoGrafica.value
  const paso = min <= -12 ? 4 : min <= -6 ? 2 : 1
  const marcas: { y: number; etiqueta: string }[] = []
  for (let exponente = 0; exponente >= min; exponente -= paso) {
    marcas.push({ y: yGrafica(10 ** exponente), etiqueta: `10^${exponente}` })
  }
  const ultima = marcas[marcas.length - 1]
  if (!ultima || ultima.etiqueta !== `10^${min}`) {
    marcas.push({ y: yGrafica(10 ** min), etiqueta: `10^${min}` })
  }
  return marcas
})

const escalaBarras = computed(() => {
  const valores = filasVariables.value.flatMap((f) => [f.base, f.final])
  return Math.max(...valores, 0.0001)
})

function anchoBarra(valor: number): string {
  return `${Math.max(0, Math.min(100, (valor / escalaBarras.value) * 100))}%`
}

const qaAprobadas = computed(() => props.qa.filter((caso) => caso.ok).length)
const qaTotal = computed(() => props.qa.length)

/* -------------------------------------------------------------------------
 * Módulo 4 · editor de coeficientes con recálculo en el servidor
 * ---------------------------------------------------------------------- */

interface Borrador {
  version: 1
  escenarioId: string
  A: string[][]
  b: string[]
  x0?: string[]
  tol: number
  maxIter: number
  omega: number
}

const CLAVE_BORRADOR = 'usie.editor.v1'
const DIMENSION = props.proyecto.dimension

const editorA = ref<string[][]>([])
const editorB = ref<string[]>([])
const editorX0 = ref<string[]>([])
const tol = ref<number>(1e-6)
const maxIter = ref<number>(200)
const omega = ref<number>(1)
const estadoEditor = ref<'inactivo' | 'calculando' | 'listo' | 'error'>('inactivo')
const errorEditor = ref<ApiError | null>(null)
const calculando = computed(() => estadoEditor.value === 'calculando')

let temporizador: number | undefined
let controlador: AbortController | null = null
let solicitud = 0

const etiquetasCortas = computed(() =>
  props.categorias.map((nombre) => nombre.split(/ (?:y|e) /)[0]),
)

function textoNumero(valor: number): string {
  if (!Number.isFinite(valor) || valor === 0) return '0'
  return Number(valor.toPrecision(12)).toString()
}

function aNumero(texto: string): number | null {
  const limpio = texto.trim().replace(/\s/g, '').replace(',', '.').replace('−', '-')
  if (!limpio) return null
  const valor = Number(limpio)
  return Number.isFinite(valor) ? valor : null
}

function cargarDesdeEscenario(payload: ScenarioPayload): void {
  editorA.value = payload.resultado.A.map((fila) => fila.map(textoNumero))
  editorB.value = payload.resultado.b.map(textoNumero)
  editorX0.value = (payload.resultado.parametros.x0 ?? Array(DIMENSION).fill(0)).map(
    textoNumero,
  )
  tol.value = payload.resultado.parametros.tol
  maxIter.value = payload.resultado.parametros.max_iter
  omega.value = payload.resultado.parametros.omega
}

function sistemaActual(): { A: number[][]; b: number[]; x0: number[] } | null {
  if (editorA.value.length !== DIMENSION || editorB.value.length !== DIMENSION) return null
  if (editorX0.value.length !== DIMENSION) return null
  const A: number[][] = []
  for (const fila of editorA.value) {
    if (fila.length !== DIMENSION) return null
    const convertida: number[] = []
    for (const celda of fila) {
      const valor = aNumero(celda)
      if (valor === null) return null
      convertida.push(valor)
    }
    A.push(convertida)
  }
  const b: number[] = []
  for (const celda of editorB.value) {
    const valor = aNumero(celda)
    if (valor === null) return null
    b.push(valor)
  }
  const x0: number[] = []
  for (const celda of editorX0.value) {
    const valor = aNumero(celda)
    if (valor === null) return null
    x0.push(valor)
  }
  return { A, b, x0 }
}

function configuracionValida(): boolean {
  return (
    Number.isFinite(tol.value) &&
    tol.value > 0 &&
    Number.isInteger(maxIter.value) &&
    maxIter.value >= 1 &&
    Number.isFinite(omega.value) &&
    omega.value > 0 &&
    omega.value < 2
  )
}

function csrfToken(): string {
  const coincidencia = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return coincidencia ? decodeURIComponent(coincidencia[1]) : ''
}

function guardarBorrador(): void {
  const borrador: Borrador = {
    version: 1,
    escenarioId: activoId.value,
    A: editorA.value.map((fila) => [...fila]),
    b: [...editorB.value],
    x0: [...editorX0.value],
    tol: tol.value,
    maxIter: maxIter.value,
    omega: omega.value,
  }
  try {
    window.localStorage.setItem(CLAVE_BORRADOR, JSON.stringify(borrador))
  } catch {
    /* almacenamiento no disponible */
  }
}

function borrarBorrador(): void {
  try {
    window.localStorage.removeItem(CLAVE_BORRADOR)
  } catch {
    /* almacenamiento no disponible */
  }
}

function esBorrador(valor: unknown): valor is Borrador {
  if (!valor || typeof valor !== 'object') return false
  const b = valor as Partial<Borrador>
  return (
    b.version === 1 &&
    typeof b.escenarioId === 'string' &&
    props.escenarios.some((e) => e.resultado.escenario.id === b.escenarioId) &&
    Array.isArray(b.A) &&
    b.A.length === DIMENSION &&
    b.A.every(
      (fila) =>
        Array.isArray(fila) &&
        fila.length === DIMENSION &&
        fila.every((celda) => typeof celda === 'string'),
    ) &&
    Array.isArray(b.b) &&
    b.b.length === DIMENSION &&
    b.b.every((celda) => typeof celda === 'string') &&
    (b.x0 === undefined ||
      (Array.isArray(b.x0) &&
        b.x0.length === DIMENSION &&
        b.x0.every((celda) => typeof celda === 'string'))) &&
    typeof b.tol === 'number' &&
    Number.isFinite(b.tol) &&
    b.tol > 0 &&
    typeof b.maxIter === 'number' &&
    Number.isInteger(b.maxIter) &&
    b.maxIter >= 1 &&
    typeof b.omega === 'number' &&
    Number.isFinite(b.omega) &&
    b.omega > 0 &&
    b.omega < 2
  )
}

async function recalcular(): Promise<void> {
  const sistema = sistemaActual()
  if (!sistema || !escenarioBase.value) return

  window.clearTimeout(temporizador)
  controlador?.abort()
  controlador = new AbortController()
  const id = ++solicitud
  estadoEditor.value = 'calculando'

  try {
    const respuesta = await fetch('/api/resolver/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'same-origin',
      signal: controlador.signal,
      body: JSON.stringify({
        escenario_id: escenarioBase.value.resultado.escenario.id,
        A: sistema.A,
        b: sistema.b,
        x0: sistema.x0,
        tol: tol.value,
        max_iter: maxIter.value,
        omega: omega.value,
      }),
    })
    const datos = (await respuesta.json()) as ResolverResponse
    if (id !== solicitud) return

    if (!respuesta.ok || !datos.ok) {
      estadoEditor.value = 'error'
      errorEditor.value = datos.ok
        ? {
            code: `HTTP_${respuesta.status}`,
            message: 'El servidor rechazó la solicitud.',
            field: null,
          }
        : datos.error
      return
    }

    personalizado.value = {
      resultado: datos.resultado,
      resumen: datos.resumen,
      interpretacion: datos.interpretacion,
    }
    estadoEditor.value = 'listo'
    errorEditor.value = null
    guardarBorrador()
  } catch (excepcion) {
    if (id !== solicitud || (excepcion as Error).name === 'AbortError') return
    estadoEditor.value = 'error'
    errorEditor.value = {
      code: 'RED',
      message: 'No se pudo contactar al servidor. Revise la conexión e intente de nuevo.',
      field: null,
    }
  }
}

function programar(): void {
  window.clearTimeout(temporizador)
  controlador?.abort()
  solicitud += 1

  if (!sistemaActual()) {
    estadoEditor.value = 'error'
    errorEditor.value = {
      code: 'ENTRADA',
      message: 'Complete A, b y x₀ con números válidos.',
      field: null,
    }
    return
  }
  if (!configuracionValida()) {
    estadoEditor.value = 'error'
    errorEditor.value = {
      code: 'CONFIG',
      message: 'Use una tolerancia positiva, N máx. entero y 0 < ω < 2.',
      field: null,
    }
    return
  }

  estadoEditor.value = 'calculando'
  errorEditor.value = null
  temporizador = window.setTimeout(() => {
    void recalcular()
  }, 450)
}

function alEditarA(i: number, j: number): void {
  if (i !== j) editorA.value[j][i] = editorA.value[i][j]
  programar()
}

function seleccionar(id: string): void {
  const payload = props.escenarios.find((e) => e.resultado.escenario.id === id)
  if (!payload) return
  if (id === activoId.value && !personalizado.value) return

  activoId.value = id
  personalizado.value = null
  errorEditor.value = null
  estadoEditor.value = 'inactivo'
  window.clearTimeout(temporizador)
  controlador?.abort()
  solicitud += 1
  borrarBorrador()
  cargarDesdeEscenario(payload)
}

function restaurar(): void {
  if (!escenarioBase.value) return
  personalizado.value = null
  errorEditor.value = null
  estadoEditor.value = 'inactivo'
  window.clearTimeout(temporizador)
  controlador?.abort()
  solicitud += 1
  borrarBorrador()
  cargarDesdeEscenario(escenarioBase.value)
}

onMounted(() => {
  const base = escenarioBase.value
  if (!base) return

  let restaurado = false
  try {
    const bruto = window.localStorage.getItem(CLAVE_BORRADOR)
    if (bruto) {
      const borrador: unknown = JSON.parse(bruto)
      if (esBorrador(borrador)) {
        activoId.value = borrador.escenarioId
        editorA.value = borrador.A.map((fila) => [...fila])
        editorB.value = [...borrador.b]
        editorX0.value = borrador.x0
          ? [...borrador.x0]
          : Array(DIMENSION).fill('0')
        tol.value = borrador.tol
        maxIter.value = borrador.maxIter
        omega.value = borrador.omega
        restaurado = true
      } else {
        borrarBorrador()
      }
    }
  } catch {
    borrarBorrador()
  }

  if (restaurado) {
    void recalcular()
  } else {
    cargarDesdeEscenario(base)
  }
})

onBeforeUnmount(() => {
  window.clearTimeout(temporizador)
  controlador?.abort()
})
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div class="topbar-inner">
        <a class="brand" href="#inicio" aria-label="Ir al inicio">
          <span class="brand-mark">Ax=b</span>
          <span class="brand-text">
            Simulador presupuestario
            <small>USIE · Consejo de la Magistratura</small>
          </span>
        </a>
        <nav class="nav" aria-label="Secciones del sitio">
          <a href="#caso">Caso</a>
          <a href="#modelo">Modelo</a>
          <a href="#simulador">Simulador</a>
          <a href="#qa">QA</a>
          <a href="#conclusiones">Conclusiones</a>
        </nav>
      </div>
    </header>

    <main>
      <section id="inicio" class="hero">
        <div class="hero-copy">
          <div class="meta-tag">Módulo 1 · {{ proyecto.materia }} {{ proyecto.gestion }}</div>
          <h1>{{ proyecto.titulo }}</h1>
          <p class="lead">{{ proyecto.subtitulo }}</p>
          <dl class="hero-meta">
            <div>
              <dt>Estudiante</dt>
              <dd>{{ proyecto.estudiante }}</dd>
            </div>
            <div>
              <dt>Carrera</dt>
              <dd>{{ proyecto.carrera }}</dd>
            </div>
            <div>
              <dt>Mención</dt>
              <dd>{{ proyecto.mencion }}</dd>
            </div>
            <div>
              <dt>Dimensión</dt>
              <dd>n = {{ proyecto.dimension }}</dd>
            </div>
          </dl>
          <div class="hero-actions">
            <a class="btn primary" href="#simulador">Abrir simulador</a>
            <a class="btn ghost" href="#qa">Ver pruebas QA</a>
          </div>
        </div>
        <aside class="hero-panel" aria-label="Resumen del sistema">
          <p class="panel-label">Sistema en estudio</p>
          <p class="equation">A x = b</p>
          <ul class="fact-list">
            <li><strong>A</strong> simétrica y definida positiva</li>
            <li><strong>n</strong> = 5 categorías de TI</li>
            <li><strong>M</strong> Jacobi y SSOR</li>
            <li><strong>tol</strong> = 10<sup>-6</sup></li>
          </ul>
          <p class="panel-foot">Cholesky como referencia directa</p>
        </aside>
      </section>

      <div class="notice" role="note">
        <strong>Datos ilustrativos.</strong> {{ aviso }}
      </div>

      <section id="caso" class="section">
        <header class="section-head">
          <div class="meta-tag">Módulo 2 · Caso de estudio</div>
          <h2>Ajustar cinco líneas de TI sin perder el equilibrio</h2>
          <p class="section-lead">
            La USIE necesita decidir cómo redistribuir su presupuesto tecnológico cuando cambia
            el entorno. Cada variable es un ajuste neto sobre una línea: un valor negativo
            recorta, uno positivo refuerza. El sistema lineal traduce esos ajustes en un
            requerimiento neto compatible con la rigidez de cada categoría.
          </p>
        </header>
        <div class="grid three">
          <article class="card">
            <h3>Contexto financiero</h3>
            <p>{{ procedencia.entidad }}.</p>
            <p class="muted">{{ procedencia.area }}</p>
            <p class="muted">Unidad de trabajo: {{ procedencia.unidad }}.</p>
          </article>
          <article class="card">
            <h3>Procedencia de los datos</h3>
            <p>{{ procedencia.fuente }}</p>
            <p class="muted">
              Las cifras se calibraron para que el experimento numérico sea reproducible.
            </p>
          </article>
          <article class="card">
            <h3>Racionalidad del modelo</h3>
            <p>{{ procedencia.racionalidad }}</p>
          </article>
        </div>
        <div class="callout">
          <strong>Cómo leer el experimento.</strong> {{ procedencia.verificacion }}
        </div>
      </section>

      <section id="modelo" class="section">
        <header class="section-head">
          <div class="meta-tag">Módulo 3 · Formulación matemática</div>
          <h2>Un sistema SPD con estructura económica</h2>
          <p class="section-lead">
            La matriz no se elige al azar: se construye como una matriz de correlación AR(1)
            escalada por la rigidez de cada línea presupuestaria. Eso garantiza simetría y
            definición positiva por construcción.
          </p>
        </header>

        <div class="grid two">
          <article class="card">
            <h3>Variables del sistema</h3>
            <ol class="variable-list">
              <li v-for="(categoria, i) in categorias" :key="categoria">
                <span class="var">x<sub>{{ i + 1 }}</sub></span>
                <span>{{ categoria }}</span>
              </li>
            </ol>
            <p class="muted">
              x<sub>i</sub> es el ajuste neto en {{ procedencia.unidad }}. El presupuesto
              final se calcula como base<sub>i</sub> + x<sub>i</sub>.
            </p>
          </article>

          <article class="card">
            <h3>Coeficientes e interpretación</h3>
            <p class="formula">A = D<sup>1/2</sup> R D<sup>1/2</sup></p>
            <p class="formula small">R<sub>ij</sub> = ρ<sup>|i−j|</sup> &nbsp;·&nbsp;
              a<sub>ij</sub> = √(d<sub>i</sub> d<sub>j</sub>) ρ<sup>|i−j|</sup></p>
            <ul class="plain-list">
              <li><strong>d<sub>i</sub></strong>: rigidez presupuestaria de la línea i.</li>
              <li><strong>ρ</strong>: interdependencia entre líneas contiguas.</li>
              <li><strong>b</strong>: requerimiento neto; se calcula como b = A x*.</li>
            </ul>
            <p class="muted">
              Un ρ alto implica que mover una categoría obliga a mover las vecinas. Una
              dispersión grande de d<sub>i</sub> produce mal condicionamiento.
            </p>
          </article>
        </div>

        <article class="card proof">
          <h3>Demostración de simetría y definición positiva</h3>
          <div class="proof-grid">
            <div>
              <h4>1 · Simetría</h4>
              <p>
                R<sub>ij</sub> = ρ<sup>|i−j|</sup> = R<sub>ji</sub> y D<sup>1/2</sup> es
                diagonal, por lo que A<sup>T</sup> = A.
              </p>
            </div>
            <div>
              <h4>2 · R es definida positiva</h4>
              <p>
                R<sup>−1</sup> es tridiagonal, con diagonal 1 en los extremos y 1 + ρ² en el
                interior, y fuera de la diagonal −ρ, dividida por 1 − ρ². Para |ρ| &lt; 1 es
                estrictamente diagonalmente dominante con diagonal positiva; por Gershgorin
                sus autovalores son reales y positivos.
              </p>
            </div>
            <div>
              <h4>3 · Congruencia</h4>
              <p>
                Para todo x ≠ 0, x<sup>T</sup>Ax = (D<sup>1/2</sup>x)<sup>T</sup>R(D<sup>1/2</sup>x)
                &gt; 0. La congruencia con D<sup>1/2</sup> invertible preserva la definición
                positiva.
              </p>
            </div>
            <div>
              <h4>4 · Verificación numérica</h4>
              <p>
                El criterio de Sylvester se comprueba con los pivotes de Cholesky y con los
                autovalores:
              </p>
              <ul class="mini-list">
                <li v-for="esc in escenarios" :key="esc.resultado.escenario.id">
                  {{ esc.resultado.escenario.nombre }}:
                  λ<sub>min</sub> = {{ cientifico(esc.resultado.diagnostico.autovalor_min) }} &gt; 0
                </li>
              </ul>
            </div>
          </div>
        </article>
      </section>

      <section id="simulador" class="section">
        <header class="section-head">
          <div class="meta-tag">Módulos 4–8 · Simulador y análisis</div>
          <h2>Tres escenarios, un mismo sistema</h2>
          <p class="section-lead">
            Seleccione un escenario para comparar la solución de referencia de Cholesky con
            GC simple, PCG-Jacobi y PCG-SSOR. En el Módulo 4 puede editar los coeficientes de
            A y las componentes de b: cada cambio se recalcula en el servidor con el mismo
            núcleo numérico y actualiza errores, residuos y condicionamiento.
          </p>
        </header>

        <div class="scenario-tabs" role="tablist" aria-label="Escenarios">
          <button
            v-for="esc in escenarios"
            :key="esc.resultado.escenario.id"
            type="button"
            role="tab"
            :aria-selected="activoId === esc.resultado.escenario.id"
            :class="{ active: activoId === esc.resultado.escenario.id }"
            @click="seleccionar(esc.resultado.escenario.id)"
          >
            <span>{{ esc.resultado.escenario.nombre }}</span>
            <small>κ(A) = {{ compacto(esc.resultado.diagnostico.kappa_A) }}</small>
          </button>
        </div>

        <article class="card editor-card" id="editor">
          <div class="card-head">
            <h3>Entrada y configuración de datos</h3>
            <span class="subtle-badge">Módulo 4</span>
          </div>
          <p class="hint">
            Edite los coeficientes de <strong>A</strong> y las componentes de
            <strong>b</strong> del escenario
            <strong>{{ escenarioBase?.resultado.escenario.nombre }}</strong>. Al modificar una
            celda fuera de la diagonal se actualiza su simétrica para conservar
            A = A<sup>T</sup>. Los cálculos se ejecutan en el servidor con el núcleo
            <code>numerics</code>, no en JavaScript.
          </p>

          <div class="editor-grid">
            <div class="editor-block">
              <p class="editor-title">Matriz A ({{ DIMENSION }} × {{ DIMENSION }})</p>
              <div class="table-wrap matrix-editor-wrap">
                <table class="matrix-editor">
                  <thead>
                    <tr>
                      <th scope="col"><span class="visually-hidden">Fila / columna</span></th>
                      <th v-for="(_, j) in editorA" :key="`col-${j}`" scope="col">
                        {{ j + 1 }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(fila, i) in editorA" :key="`fila-${i}`">
                      <th scope="row">{{ i + 1 }}</th>
                      <td v-for="(_, j) in fila" :key="`a-${i}-${j}`" :class="{ diag: i === j }">
                        <input
                          v-model="editorA[i][j]"
                          type="text"
                          inputmode="decimal"
                          autocomplete="off"
                          spellcheck="false"
                          :aria-label="`Coeficiente a ${i + 1}, ${j + 1}`"
                          @input="alEditarA(i, j)"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="hint">La diagonal se resalta. Edición simétrica automática.</p>
            </div>

            <div class="editor-block">
              <p class="editor-title">Vector b</p>
              <div class="b-editor">
                <label v-for="(_, i) in editorB" :key="`b-${i}`" class="b-field">
                  <span class="b-label">
                    <b>{{ i + 1 }}</b> {{ etiquetasCortas[i] }}
                  </span>
                  <input
                    v-model="editorB[i]"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    spellcheck="false"
                    :aria-label="`Componente b ${i + 1}`"
                    @input="programar"
                  />
                </label>
              </div>

              <p class="editor-title config-title">Vector inicial x₀</p>
              <div class="x0-editor">
                <label v-for="(_, i) in editorX0" :key="`x0-${i}`">
                  <span>{{ i + 1 }}</span>
                  <input
                    v-model="editorX0[i]"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    spellcheck="false"
                    :aria-label="`Componente x0 ${i + 1}`"
                    @input="programar"
                  />
                </label>
              </div>

              <p class="editor-title config-title">Parámetros del criterio</p>
              <div class="editor-config">
                <label>
                  <span>Tolerancia</span>
                  <select v-model.number="tol" @change="programar">
                    <option :value="1e-4">1 × 10⁻⁴</option>
                    <option :value="1e-6">1 × 10⁻⁶</option>
                    <option :value="1e-8">1 × 10⁻⁸</option>
                  </select>
                </label>
                <label>
                  <span>N<sub>máx</sub></span>
                  <input
                    v-model.number="maxIter"
                    type="number"
                    min="1"
                    max="2000"
                    step="1"
                    @change="programar"
                  />
                </label>
                <label>
                  <span>ω SSOR</span>
                  <input
                    v-model.number="omega"
                    type="number"
                    min="0.1"
                    max="1.9"
                    step="0.1"
                    @change="programar"
                  />
                </label>
              </div>
              <p class="hint">
                El criterio de parada es ‖r<sub>k</sub>‖₂ / ‖b‖₂ &lt; tol. Use
                x₀ = 0 para reproducir el escenario original.
              </p>
            </div>
          </div>

          <div class="editor-actions">
            <button class="btn primary" type="button" :disabled="calculando" @click="recalcular">
              {{ calculando ? 'Calculando…' : 'Recalcular ahora' }}
            </button>
            <button class="btn ghost" type="button" @click="restaurar">
              Restaurar escenario
            </button>
            <p v-if="calculando" class="editor-status muted" role="status">
              Recalculando con el núcleo numérico…
            </p>
            <p v-else-if="errorEditor" class="editor-status error" role="alert">
              <strong>{{ errorEditor.code }}</strong> · {{ errorEditor.message }}
              <template v-if="personalizado">
                Se muestran los resultados de la última edición válida.
              </template>
            </p>
            <p v-else-if="personalizado" class="editor-status ok" role="status">
              Sistema SPD verificado · κ(A) =
              {{ compacto(personalizado.resultado.diagnostico.kappa_A) }} ·
              {{ personalizado.resultado.metodos.cg.iteraciones }} iter. GC /
              {{ personalizado.resultado.metodos.pcg_ssor.iteraciones }} iter. PCG-SSOR.
            </p>
            <p v-else class="editor-status muted">
              Edite un coeficiente para recalcular el sistema.
            </p>
          </div>
        </article>

        <div v-if="editado" class="edit-banner">
          <span class="status ok">Sistema editado</span>
          <p>
            Los resultados siguientes corresponden a los coeficientes ingresados, no al
            escenario {{ escenarioBase?.resultado.escenario.nombre }}.
          </p>
          <button class="btn ghost small" type="button" @click="restaurar">
            Volver al escenario
          </button>
        </div>

        <template v-if="activo">
          <div class="scenario-brief card">
            <div>
              <h3>{{ activo.resultado.escenario.nombre }}</h3>
              <p>{{ activo.resultado.escenario.descripcion }}</p>
              <p class="muted">{{ activo.resultado.escenario.justificacion }}</p>
            </div>
            <dl class="chips">
              <div v-if="!editado"><dt>ρ</dt><dd>{{ num(activo.resultado.escenario.rho, 2) }}</dd></div>
              <div v-else><dt>Modo</dt><dd>Editado</dd></div>
              <div><dt>n</dt><dd>{{ activo.resultado.escenario.n }}</dd></div>
              <div><dt>Unidad</dt><dd>{{ activo.resultado.escenario.unidad }}</dd></div>
              <div><dt>ω SSOR</dt><dd>{{ num(activo.resultado.parametros.omega, 1) }}</dd></div>
            </dl>
          </div>

          <div class="stat-row">
            <article class="stat">
              <p class="stat-label">κ(A)</p>
              <p class="stat-value">{{ compacto(activo.resultado.diagnostico.kappa_A) }}</p>
              <p class="stat-foot">condicionamiento original</p>
            </article>
            <article class="stat">
              <p class="stat-label">κ(M<sup>−1</sup>A) SSOR</p>
              <p class="stat-value">{{ compacto(activo.resumen.kappa_ssor) }}</p>
              <p class="stat-foot">
                reducción ×{{ compacto(
                  activo.resultado.diagnostico.kappa_A / activo.resumen.kappa_ssor,
                ) }}
              </p>
            </article>
            <article class="stat">
              <p class="stat-label">Iteraciones</p>
              <p class="stat-value">
                {{ activo.resumen.iter_cg }}
                <span class="arrow">→</span>
                {{ activo.resumen.iter_ssor }}
              </p>
              <p class="stat-foot">GC simple → PCG-SSOR</p>
            </article>
            <article class="stat">
              <p class="stat-label">Residuo PCG-Jacobi</p>
              <p class="stat-value small">{{ cientifico(activo.resumen.residuo_jacobi) }}</p>
              <p class="stat-foot">‖r‖₂ / ‖b‖₂ &lt; 10<sup>−6</sup></p>
            </article>
          </div>

          <div class="sim-grid">
            <div class="sim-main">
              <article class="card">
                <div class="card-head">
                  <h3>Solución y presupuesto final</h3>
                  <span class="subtle-badge">Módulo 6 · 8</span>
                </div>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Categoría</th>
                        <th class="num">Base</th>
                        <th class="num">x ref.</th>
                        <th class="num">x PCG</th>
                        <th class="num">Final</th>
                        <th class="num">E<sub>a</sub></th>
                        <th class="num">E<sub>r</sub></th>
                        <th class="num">E<sub>p</sub></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="fila in filasVariables" :key="fila.nombre">
                        <td>{{ fila.nombre }}</td>
                        <td class="num">{{ num(fila.base, 2) }}</td>
                        <td class="num">{{ num(fila.referencia, 4) }}</td>
                        <td class="num">{{ num(fila.pcg, 4) }}</td>
                        <td class="num strong">{{ num(fila.final, 2) }}</td>
                        <td class="num">{{ cientifico(fila.ea) }}</td>
                        <td class="num">{{ cientifico(fila.er) }}</td>
                        <td class="num">{{ porcentaje(fila.ep) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p class="hint">
                  E<sub>a</sub> = |x ref. − x PCG|; E<sub>r</sub> = E<sub>a</sub> / |x ref.|;
                  E<sub>p</sub> = 100 · E<sub>r</sub>. Montos en {{ activo.resultado.escenario.unidad }}.
                </p>
              </article>

              <article class="card">
                <div class="card-head">
                  <h3>Comparativa de métodos</h3>
                  <span class="subtle-badge">Módulo 7</span>
                </div>
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Método</th>
                        <th class="num">Iteraciones</th>
                        <th class="num">Residuo rel.</th>
                        <th class="num">κ(M<sup>−1</sup>A)</th>
                        <th class="num">Error máx.</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="fila in metodosFilas" :key="fila.clave">
                        <td>
                          <span class="dot" :style="{ background: fila.color }"></span>
                          {{ fila.nombre }}
                        </td>
                        <td class="num">{{ fila.iteraciones }}</td>
                        <td class="num">{{ cientifico(fila.residuo) }}</td>
                        <td class="num">{{ compacto(fila.kappa) }}</td>
                        <td class="num">{{ cientifico(fila.error) }}</td>
                        <td>
                          <span class="status" :class="fila.convergido ? 'ok' : 'bad'">
                            {{ fila.convergido ? 'Convergió' : 'No convergió' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p class="hint">
                  Método de referencia: {{ activo.resultado.referencia.metodo }} (factorización
                  directa, residuo {{ cientifico(activo.resultado.referencia.residuo_relativo) }}).
                  Tolerancia: {{ cientifico(activo.resultado.parametros.tol) }};
                  N<sub>máx</sub> = {{ activo.resultado.parametros.max_iter }}.
                </p>
              </article>

              <article class="card">
                <div class="card-head">
                  <h3>Presupuesto base vs. propuesta</h3>
                  <span class="subtle-badge">Módulo 8</span>
                </div>
                <div class="bars">
                  <div v-for="fila in filasVariables" :key="fila.nombre" class="bar-row">
                    <span class="bar-label">{{ fila.nombre }}</span>
                    <div class="bar-track">
                      <span class="bar base" :style="{ width: anchoBarra(fila.base) }"></span>
                      <span class="bar final" :style="{ width: anchoBarra(fila.final) }"></span>
                    </div>
                    <span class="bar-value">{{ num(fila.final, 2) }}</span>
                  </div>
                </div>
                <div class="legend-bar">
                  <span><i class="swatch base"></i> Base</span>
                  <span><i class="swatch final"></i> Final (PCG-Jacobi)</span>
                </div>
              </article>
            </div>

            <aside class="sim-side">
              <article class="card">
                <h3>Diagnóstico espectral</h3>
                <dl class="kv">
                  <div>
                    <dt>λ<sub>min</sub>(A)</dt>
                    <dd>{{ cientifico(activo.resultado.diagnostico.autovalor_min) }}</dd>
                  </div>
                  <div>
                    <dt>λ<sub>max</sub>(A)</dt>
                    <dd>{{ compacto(activo.resultado.diagnostico.autovalor_max) }}</dd>
                  </div>
                  <div>
                    <dt>κ(A)</dt>
                    <dd>{{ compacto(activo.resultado.diagnostico.kappa_A) }}</dd>
                  </div>
                  <div>
                    <dt>Pivotes &gt; 0</dt>
                    <dd>{{ activo.resultado.diagnostico.es_spd_cholesky ? 'Sí' : 'No' }}</dd>
                  </div>
                  <div>
                    <dt>Simetría máx.</dt>
                    <dd>{{ cientifico(activo.resultado.diagnostico.simetria_max) }}</dd>
                  </div>
                  <div>
                    <dt>Error máx. PCG</dt>
                    <dd>{{ cientifico(activo.resumen.error_max_jacobi) }}</dd>
                  </div>
                </dl>
              </article>

              <article class="card">
                <h3>Matriz A</h3>
                <div class="table-wrap">
                  <table class="matrix">
                    <tbody>
                      <tr v-for="(fila, i) in activo.resultado.A" :key="i">
                        <td
                          v-for="(valor, j) in fila"
                          :key="j"
                          :class="{ diag: i === j }"
                        >
                          {{ matriz(valor) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p class="hint">A = D<sup>1/2</sup> R D<sup>1/2</sup>; se resalta la diagonal.</p>
              </article>

              <article class="card">
                <h3>Historia de convergencia</h3>
                <svg
                  class="chart"
                  :viewBox="`0 0 ${ANCHO} ${ALTO}`"
                  role="img"
                  aria-label="Residuo relativo por iteración en escala logarítmica"
                >
                  <line
                    v-for="marca in grilla"
                    :key="marca.etiqueta"
                    :x1="MARGEN"
                    :x2="ANCHO - MARGEN"
                    :y1="marca.y"
                    :y2="marca.y"
                    class="grid-line"
                  />
                  <text
                    v-for="marca in grilla"
                    :key="`t-${marca.etiqueta}`"
                    :x="ANCHO - MARGEN"
                    :y="marca.y - 3"
                    class="grid-label"
                    text-anchor="end"
                  >
                    {{ marca.etiqueta }}
                  </text>
                  <polyline
                    v-for="historia in historias"
                    :key="historia.nombre"
                    :points="puntosGrafica(historia.datos)"
                    :stroke="historia.color"
                    class="serie"
                  />
                </svg>
                <ul class="legend">
                  <li v-for="historia in historias" :key="historia.nombre">
                    <span class="dot" :style="{ background: historia.color }"></span>
                    {{ historia.nombre }}
                  </li>
                </ul>
                <p class="hint">Escala logarítmica de ‖r<sub>k</sub>‖₂ / ‖b‖₂.</p>
              </article>
            </aside>
          </div>

          <div class="grid two">
            <div class="callout">
              <strong>¿Por qué PCG-SSOR converge en 2 iteraciones?</strong>
              Con ω = 1 y una matriz AR(1), el operador M<sup>−1</sup>A tiene solo dos
              autovalores distintos; el gradiente conjugado lo resuelve en dos pasos. No es un
              error del método. Cambiar ω altera el espectro y el conteo (la CLI acepta
              <code>--omega</code>).
            </div>
            <div class="callout">
              <strong>El límite de n = 5.</strong>
              En aritmética exacta, GC converge en a lo sumo n pasos. Aquí el escenario mal
              condicionado necesita 6 porque el criterio se evalúa con el residuo verdadero
              recalculado y el redondeo domina. Se documenta en lugar de ocultarse.
            </div>
          </div>

          <article class="card interpretation">
            <h3>Interpretación financiera</h3>
            <p>{{ activo.interpretacion }}</p>
            <p class="muted">
              <template v-if="editado">
                Referencia x = [{{ activo.resultado.escenario.ajuste_objetivo.map((v) => num(v, 2)).join(', ') }}]
                obtenida con Cholesky para el sistema editado; los errores de los métodos
                iterativos se miden contra este vector.
              </template>
              <template v-else>
                Ajuste objetivo x* = [{{ activo.resultado.escenario.ajuste_objetivo.map((v) => num(v, 2)).join(', ') }}].
                La solución numérica reproduce ese vector; el valor de x* es una calibración
                académica, no un pronóstico.
              </template>
            </p>
          </article>
        </template>
      </section>

      <section id="qa" class="section">
        <header class="section-head">
          <div class="meta-tag">Módulo 9 · Pruebas de software</div>
          <h2>QA ejecutable dentro del sitio</h2>
          <p class="section-lead">
            Las cuatro pruebas obligatorias se ejecutan en el servidor cada vez que se carga
            la página. El resultado que se muestra proviene del núcleo numérico real, no de
            datos escritos a mano.
          </p>
          <p class="qa-score">
            <span class="status" :class="qaAprobadas === qaTotal ? 'ok' : 'bad'">
              {{ qaAprobadas }}/{{ qaTotal }} pruebas aprobadas
            </span>
          </p>
        </header>

        <div class="qa-grid">
          <article
            v-for="caso in qa"
            :key="caso.id"
            class="card qa-card"
            :class="{ failed: !caso.ok }"
          >
            <div class="qa-head">
              <span class="qa-id">Prueba {{ caso.id }}</span>
              <span class="status" :class="caso.ok ? 'ok' : 'bad'">
                {{ caso.ok ? 'OK' : 'Fallo' }}
              </span>
            </div>
            <h3>{{ caso.nombre }}</h3>
            <dl class="qa-detail">
              <div><dt>Entrada</dt><dd>{{ caso.entrada }}</dd></div>
              <div><dt>Esperado</dt><dd>{{ caso.esperado }}</dd></div>
              <div><dt>Obtenido</dt><dd>{{ caso.obtenido }}</dd></div>
              <div><dt>Conclusión</dt><dd>{{ caso.conclusion }}</dd></div>
            </dl>
          </article>
        </div>
      </section>

      <section id="conclusiones" class="section">
        <header class="section-head">
          <div class="meta-tag">Módulo 10 · Conclusiones y referencias</div>
          <h2>Qué muestran los números</h2>
        </header>

        <div class="grid three">
          <article class="card">
            <h3>Lectura técnica</h3>
            <p>
              La matemática vive en un paquete Python sin dependencias de Django; la capa web
              solo serializa resultados. Esa separación permite probar el núcleo con
              <code>unittest</code> y reutilizarlo desde la CLI o desde Inertia sin duplicar
              fórmulas.
            </p>
          </article>
          <article class="card">
            <h3>Lectura numérica</h3>
            <p>
              El condicionamiento explica el esfuerzo iterativo. En el escenario ideal
              κ(A) ≈ 3 y ambos métodos convergen en pocos pasos. En el mal condicionado
              κ(A) ≈ 3,1 × 10<sup>5</sup>: Jacobi baja a 4,3 × 10<sup>2</sup> y SSOR a 25,
              con la misma tolerancia.
            </p>
          </article>
          <article class="card">
            <h3>Lectura financiera</h3>
            <p>
              Los recortes se concentran en consultoría y software, mientras hardware,
              conectividad y soporte se refuerzan. Cuanto mayor es la interdependencia, más
              debe leerse el ajuste como un paquete y no como decisiones aisladas.
            </p>
          </article>
        </div>

        <div class="grid two">
          <article class="card">
            <h3>Limitaciones declaradas</h3>
            <ul class="plain-list">
              <li>n = 5 acota la comparación de iteraciones; el análisis se apoya en κ y en la historia de convergencia.</li>
              <li>Los montos y rigideces son ilustrativos y calibrados, no cifras oficiales.</li>
              <li>x* se usa para construir b y verificar el software; no es un pronóstico financiero.</li>
              <li>El escenario mal condicionado requiere 6 iteraciones de GC por redondeo, no por fallo del algoritmo.</li>
            </ul>
          </article>
        </div>
      </section>
    </main>

    <footer class="footer">
      <p>{{ proyecto.institucion }} · {{ proyecto.facultad }}</p>
      <p>{{ proyecto.materia }} · Mención {{ proyecto.mencion }} · {{ proyecto.gestion }}</p>
      <p class="muted">Sitio académico. Los datos presupuestarios son ilustrativos.</p>
    </footer>
  </div>
</template>
