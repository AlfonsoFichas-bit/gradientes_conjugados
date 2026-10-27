# Asignación presupuestaria bajo incertidumbre

Simulador académico de **Métodos Numéricos** para la USIE del Consejo de la
Magistratura (La Paz, Bolivia). Resuelve un sistema lineal `A x = b` de orden
`n = 5`, simétrico y estrictamente definido positivo (SPD), mediante
**Cholesky** (referencia directa), **gradientes conjugados (GC)** y
**gradientes conjugados precondicionados (PCG)** con Jacobi y SSOR.

El proyecto separa por completo el cálculo numérico de la interfaz:

- `numerics/` — núcleo en Python puro, sin Django ni librerías externas.
- `simulador/` + `config/` — capa web Django que solo serializa resultados.
- `frontend/` — sitio Vue 3 + TypeScript servido con Inertia.js y Vite.

> **Aviso.** Los montos, rigideces y ajustes objetivos son **ilustrativos** y
> fueron calibrados con fines académicos. No corresponden a cifras oficiales,
> ejecutadas ni proyectadas por el Consejo de la Magistratura.

---

## 1. Modelo matemático

Cada variable `x_i` es el **ajuste neto** (positivo o negativo) sobre la línea
presupuestaria `i`, expresado en millones de bolivianos (MM Bs). El presupuesto
final es `base_i + x_i`.

La matriz se construye por congruencia:

```
A = D^(1/2) R D^(1/2),   R_ij = ρ^|i−j|,   D = diag(d_1, …, d_5)
```

- `d_i > 0` — rigidez de la línea presupuestaria.
- `ρ ∈ (−1, 1)` — interdependencia entre líneas contiguas.
- `b = A x*` — el término independiente se genera a partir de un ajuste objetivo
  conocido `x*`, de modo que la solución exacta esté disponible para verificar
  el software. No es un pronóstico financiero.

### Demostración SPD

1. **Simetría.** `R_ij = ρ^|i−j| = R_ji` y `D^(1/2)` es diagonal, luego
   `Aᵀ = A`.
2. **R es definida positiva.** Su inversa es la matriz tridiagonal

   ```
   R⁻¹ = 1/(1−ρ²) · T
   T_ii = 1 en los extremos, 1+ρ² en el interior
   T_i,i+1 = T_i+1,i = −ρ
   ```

   Para `|ρ| < 1`, `T` es estrictamente diagonalmente dominante con diagonal
   positiva; por el teorema de Gershgorin todos sus autovalores son positivos,
   y también los de `R⁻¹`, por lo que `R` es definida positiva.
3. **Congruencia.** Para todo `x ≠ 0`,

   ```
   xᵀ A x = (D^(1/2) x)ᵀ R (D^(1/2) x) > 0
   ```

   porque `D^(1/2)` es invertible. La congruencia preserva la definición positiva.
4. **Verificación numérica.** El sitio comprueba los pivotes de Cholesky y
   `λ_min(A) > 0` en los tres escenarios (Módulo 3).

### Criterio de parada y métricas

- Parada: `‖r_k‖₂ / ‖b‖₂ < 10⁻⁶` con `tol`, `N_max` y `x₀` configurables.
- El residuo se **recalcula** como `r_k = b − A x_k` en cada iteración.
- Por variable: `E_a = |x*_i − x_i|`, `E_r = E_a / |x*_i|`,
  `E_p = 100 · E_r`.
- Globales: residuo relativo `‖b − Ax‖₂ / ‖b‖₂`, `κ(A)` y `κ(M⁻¹A)`.

`κ(M⁻¹A)` se calcula como `κ(C)` con `C = M^(−1/2) A M^(−1/2)`, matriz
semejante a `M⁻¹A` y simétrica, usando la factorización de Cholesky de `M`.

---

## 2. Escenarios

| Escenario | ρ | Rigideces `d_i` | κ(A) | κ(M⁻¹A) Jacobi | κ(M⁻¹A) SSOR | Iter. GC / Jac. / SSOR |
|---|---|---|---|---|---|---|
| Ideal | 0.30 | 1.00, 1.10, 0.90, 1.20, 1.00 | 2.99 | 2.89 | 1.10 | 5 / 5 / 2 |
| Bajo estrés | 0.75 | 1.00, 1.25, 0.80, 1.40, 0.95 | 23.06 | 21.43 | 2.29 | 5 / 5 / 2 |
| Mal condicionado | 0.98 | 1e−4, 1e−3, 1e−2, 1e−1, 1.0 | 3.09 × 10⁵ | 4.34 × 10² | 25.3 | 6 / 5 / 2 |

Presupuesto base (MM Bs): `[1.80, 1.20, 0.90, 0.70, 0.60]` sobre cinco
categorías de TI: personal y consultoría, hardware e infraestructura, software
y licencias, conectividad y telecomunicaciones, mantenimiento y soporte.

**Dos observaciones que se documentan en lugar de ocultarse:**

- Con `ω = 1` y una matriz AR(1), `M⁻¹A` tiene solo **dos autovalores
  distintos**; por eso PCG-SSOR converge en 2 iteraciones. Es estructural, no
  un error. Cambiar `--omega` altera el espectro y el conteo.
- En aritmética exacta GC converge en a lo sumo `n = 5` pasos. El escenario mal
  condicionado necesita **6** porque el criterio se evalúa con el residuo
  verdadero recalculado y el redondeo domina.

### Editor del Módulo 4

La sección «Simulador» incluye un editor de la matriz `A` y del vector `b`.
Cada cambio se envía con debounce a `POST /api/resolver/`, que llama a
`run_custom` en el núcleo Python: valida dimensión, simetría y definición
positiva, y devuelve el mismo payload que un escenario (Cholesky, GC,
PCG-Jacobi, PCG-SSOR, errores, `κ`). La solución de Cholesky del sistema
editado pasa a ser la referencia de `E_a`, `E_r` y `E_p`, de modo que la tabla
de errores conserva su significado.

- Editar una celda fuera de la diagonal actualiza su simétrica (`A = Aᵀ`).
- `tol`, `N_max`, `x₀` y `ω` son editables; por defecto `x₀ = 0`.
- El borrador persiste en `localStorage` (`usie.editor.v1`) y se restaura al
  recargar; «Restaurar escenario» lo descarta.
- Los errores de dominio (matriz asimétrica, no SPD, dimensión) se responden
  con HTTP 200 y `ok: false`, para que la interfaz los muestre sin llenar la
  consola del navegador de errores de red. Los cuerpos mal formados usan 400,
  los cuerpos excesivos 413 y los fallos inesperados 500.

---

## 3. Puesta en marcha

Requisitos: **Python 3.11+** (probado con 3.14) y **Bun 1.x** (o Node 20+).

```bash
# 1. Dependencias de Python
pip install django inertia-django

# 2. Dependencias del frontend
bun install

# 3. Vite en una terminal
bun run dev

# 4. Django en otra terminal
python manage.py runserver 127.0.0.1:8000
```

Abrir <http://127.0.0.1:8000/>.

### Producción

```bash
bun run build                      # genera static/build/ y su manifest
DJANGO_DEBUG=0 python manage.py collectstatic --noinput
DJANGO_DEBUG=0 python manage.py runserver 0.0.0.0:8000
```

Variables de entorno útiles:

| Variable | Uso |
|---|---|
| `NOMBRE_ESTUDIANTE` | Nombre mostrado en el Módulo 1 |
| `DJANGO_SECRET_KEY` | Clave secreta en producción |
| `DJANGO_DEBUG` | `0` desactiva el modo depuración |
| `DJANGO_ALLOWED_HOSTS` | Lista separada por comas o `*` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS del despliegue |

### Estilos (Tailwind CSS v4)

El sitio usa **Tailwind CSS v4 compilado con Vite** mediante
`@tailwindcss/vite`; no hay CDN. `frontend/tailwind.css` es el punto de entrada:

```css
@import "tailwindcss" source(none);
@source "./**/*.{vue,ts}";
```

`source(none)` desactiva el escaneo automático y `@source` limita la búsqueda a
los archivos del frontend, así el CSS no se contamina con cadenas de `docs/`,
`numerics/` ni de los assets ya compilados. El diseño propio vive en
`frontend/app.css` dentro de `@layer components`, de modo que las utilidades
(`p-8`, `text-xl`, …) pueden sobrescribir las clases semánticas sin
`!important`. `frontend/main.ts` importa primero `tailwind.css` y luego
`app.css`.

En desarrollo Vite inyecta los estilos; en producción Django sirve un único CSS
con hash desde `static/build/assets/`. `bun run build` es obligatorio antes de
desplegar.

---

## 4. Uso del núcleo sin interfaz

```bash
python -m numerics.cli                 # los tres escenarios
python -m numerics.cli --scenario mal --tol 1e-8 --max-iter 300
python -m numerics.cli --json          # salida JSON
python -m numerics.cli --qa            # pruebas funcionales 1–4
```

Como biblioteca:

```python
from numerics import SolverConfig, run_scenario

resultado = run_scenario("ideal", SolverConfig(tol=1e-8, max_iter=200))
print(resultado.metodos["pcg_jacobi"].x)
print(resultado.diagnostico.kappa_A)
```

---

## 5. Pruebas

```bash
python -m unittest discover -s tests -v   # 100 pruebas unitarias del núcleo
python manage.py test simulador            # 29 pruebas de la API web (incluye /salud/)
python -m numerics.cli --qa               # 4 pruebas funcionales
bun run typecheck                         # TypeScript estricto
bun run build                             # build de producción
```

Las cuatro pruebas funcionales exigidas se ejecutan **en el servidor cada vez
que se carga el sitio** y se muestran en el Módulo 9 con el formato
Entrada / Esperado / Obtenido / Conclusión:

1. Carga de los tres escenarios y convergencia de todos los métodos.
2. Rechazo controlado de matrices inválidas (`ASIMETRICA`, `NO_SPD`, `DIM`,
   `NO_NUMERICO`, `NO_FINITO`).
3. Edición de coeficientes con recálculo y verificación de que el sistema sigue
   siendo definido positivo.
4. Comparativa de iteraciones: PCG no debe usar más iteraciones que GC en el
   escenario mal condicionado.

---

## 6. Estructura del repositorio

```
.
├── config/                  # settings, urls, wsgi/asgi de Django
├── docs/
│   ├── Plan.md              # enunciado y rúbrica
│   └── doc-inertiajs-django/
├── frontend/
│   ├── app.css              # sistema visual completo
│   ├── tailwind.css         # entrada de Tailwind v4 (source(none) + @source)
│   ├── main.ts              # arranque de Inertia + Vue
│   ├── types.ts             # contratos TypeScript del payload
│   └── pages/Home.vue       # sitio de una página (Módulos 1–10)
├── numerics/                # núcleo numérico puro
│   ├── linalg/              # Cholesky, LU, autovalores de Jacobi
│   ├── preconditioners/     # Jacobi y SSOR
│   ├── solvers/             # CG y PCG
│   ├── matrix.py            # construcción de A, b y R⁻¹
│   ├── metrics.py           # E_a, E_r, E_p, κ(A), κ(M⁻¹A)
│   ├── scenarios.py         # escenarios y aviso de datos
│   ├── experiment.py        # orquestación y resumen
│   ├── qa.py                # pruebas funcionales 1–4
│   └── cli.py               # interfaz de línea de comandos
├── simulador/               # vistas Django + etiqueta de assets de Vite
├── static/                  # favicon.svg y build/ generado por Vite
├── templates/app.html       # layout de Inertia v3
├── tests/                   # 100 pruebas con unittest
├── manage.py
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 7. Decisiones de diseño

- **Sin NumPy/SciPy.** Todos los algoritmos están implementados con la
  biblioteca estándar para que el proyecto sea verificable y no dependa de
  cajas negras.
- **Núcleo aislado.** `numerics` no importa Django; la capa web solo arma el
  payload. Esto permite probar la matemática desde `unittest` y reutilizarla
  desde la CLI.
- **Errores de dominio.** Las validaciones lanzan `NumericalError` con un
  código estable; nunca se filtra una traza de Python a la interfaz.
- **`math.fsum`.** Los productos internos usan suma compensada para reducir el
  error de redondeo en el escenario mal condicionado.
- **Datos honestos.** El sitio declara en la cabecera, en el pie y en el módulo
  de conclusiones que las cifras son ilustrativas.
- **CSS compilado, no CDN.** Tailwind v4 se compila en el build de Vite y el
  diseño propio queda en `@layer components`, lo que evita depender de un CDN en
  tiempo de ejecución y permite que las utilidades sobrescriban sin `!important`.

---

## 8. Referencias

- Suñagua S., P. (2020). *Método de Gradientes Conjugados Precondicionado.*
  Revista Boliviana de Matemática UMSA, 4, 2–7.
- Golub, G. H., & Van Loan, C. F. (2013). *Matrix Computations* (4th ed.).
  Johns Hopkins University Press.
- Saad, Y. (2003). *Iterative Methods for Sparse Linear Systems* (2nd ed.).
  SIAM.
