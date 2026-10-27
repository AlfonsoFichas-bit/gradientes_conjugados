export interface VariableError {
  indice: number
  variable: string
  referencia: number
  obtenido: number
  absoluto: number
  relativo: number | null
  porcentual: number | null
  nota: string
}

export interface Metrics {
  metodo: string
  errores: VariableError[]
  residuo_relativo_global: number
  error_absoluto_max: number
  kappa_A: number
  kappa_precondicionada: number
  reduccion_condicion: number
}

export interface SolverResult {
  metodo: string
  x: number[]
  iteraciones: number
  convergido: boolean
  motivo: string
  residuo_relativo: number
  historia: number[]
  tiempo_ms: number
  extra: Record<string, unknown>
}

export interface Diagnostics {
  simetria_max: number
  autovalores: number[]
  autovalor_min: number
  autovalor_max: number
  pivotes_cholesky: number[]
  es_spd_cholesky: boolean
  kappa_A: number
}

export interface ScenarioSpec {
  id: string
  nombre: string
  descripcion: string
  justificacion: string
  rho: number
  rigidez: number[]
  base: number[]
  ajuste_objetivo: number[]
  etiquetas: string[]
  unidad: string
  n: number
}

export interface ScenarioResult {
  escenario: ScenarioSpec
  A: number[][]
  b: number[]
  referencia: SolverResult
  metodos: Record<'cg' | 'pcg_jacobi' | 'pcg_ssor', SolverResult>
  metricas: Record<'cg' | 'pcg_jacobi' | 'pcg_ssor', Metrics>
  diagnostico: Diagnostics
  presupuesto_final: number[]
  parametros: {
    tol: number
    max_iter: number
    x0: number[] | null
    omega: number
  }
}

export interface ScenarioSummary {
  id: string
  nombre: string
  x_referencia: number[]
  x_cg: number[]
  x_pcg_jacobi: number[]
  x_pcg_ssor: number[]
  iter_cg: number
  iter_jacobi: number
  iter_ssor: number
  kappa_A: number
  kappa_jacobi: number
  kappa_ssor: number
  residuo_cg: number
  residuo_jacobi: number
  residuo_ssor: number
  error_max_jacobi: number
  convergieron: Record<'cg' | 'pcg_jacobi' | 'pcg_ssor', boolean>
  presupuesto_base: number[]
  presupuesto_final: number[]
  interpretacion: string
}

export interface ScenarioPayload {
  resultado: ScenarioResult
  resumen: ScenarioSummary
  interpretacion: string
}

export interface ApiError {
  code: string
  message: string
  field: string | null
}

export type ResolverResponse =
  | {
      ok: true
      resultado: ScenarioResult
      resumen: ScenarioSummary
      interpretacion: string
    }
  | { ok: false; error: ApiError }

export interface QACase {
  id: number
  nombre: string
  entrada: string
  esperado: string
  obtenido: string
  conclusion: string
  ok: boolean
  detalle: Record<string, unknown>
}

export interface Procedencia {
  entidad: string
  area: string
  unidad: string
  fuente: string
  racionalidad: string
  verificacion: string
}

export interface HomeProps {
  proyecto: {
    titulo: string
    subtitulo: string
    institucion: string
    estudiante: string
    carrera: string
    facultad: string
    mencion: string
    materia: string
    gestion: string
    dimension: number
  }
  aviso: string
  procedencia: Procedencia
  categorias: string[]
  escenarios: ScenarioPayload[]
  qa: QACase[]
  qa_aprobadas: number
  qa_total: number
  referencias: string[]
}
