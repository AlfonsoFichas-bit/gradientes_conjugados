# Guía Integral de Requerimientos: Desafío Académico de Métodos Numéricos

**Asignatura:** Métodos Numéricos  
**Carrera:** Informática – Facultad de Ciencias Puras y Naturales (UMSA)  
**Mención:** Desarrollo de Sistemas  
**Modalidad:** Individual  
**Área de aplicación:** Finanzas  

---

## 1. Parámetros Generales y Restricciones Técnicas

* **Dimensión del sistema:** Mínimo 4 ecuaciones con 4 incógnitas ($n \ge 4$).
* **Tolerancia de parada:** $\|r_k\|_2 / \|b\|_2 < 10^{-6}$.
* **Propiedades obligatorias de la matriz $A$:**
  * Debe ser cuadrada de orden $n \times n$.
  * Debe ser estrictamente simétrica: $A = A^T$.
  * Debe ser estrictamente definida positiva: $x^T A x > 0, \quad \forall x \ne 0$.
  * Se debe incluir demostración formal para los tres escenarios (mediante autovalores estrictamente positivos o el Criterio de Sylvester / menores principales).
* **Consistencia del modelo:**
  * Las variables $x_i$ deben representar magnitudes financieras concretas (activos, presupuestos, flujos, costos, etc.).
  * Los coeficientes $a_{ij}$ y términos independientes $b_i$ deben contar con justificación conceptual de negocio.
  * Los tres escenarios deben mantener las mismas variables y la misma estructura general, modificando de forma justificada los coeficientes numéricos.

---

## 2. Enfoque Específico para la Mención de Desarrollo de Sistemas

* **Caso sugerido por el docente:**  
  * *Simulador de asignación o ajustes presupuestarios de cuatro o más categorías ($n \ge 4$).*  
  *(Nota: Se admiten casos financieros equivalentes siempre que conduzcan rigurosamente a un sistema lineal simétrico y definido positivo).*
* **Énfasis particular y criterios de evaluación técnica de la mención:**
  * **Arquitectura de software:** Diseño desacoplado, modularidad clara entre la capa matemática (algoritmos numéricos) y la capa de presentación/interfaz de usuario.
  * **Componentes web interactivos:** Estructuración de componentes reactivos para manipulación matricial, paneles de control y visualización de resultados.
  * **Validaciones matemáticas de entrada:** Detección y manejo en tiempo real de inconsistencias (e.g., asimetría, matrices no definidas positivas, dimensiones incompatibles, datos vacíos o no numéricos) sin provocar fallos o bloqueos de la aplicación.
  * **Módulo de pruebas funcionales (QA):** Verificación documentada y ejecutable dentro de la interfaz.

---

## 3. Requerimientos Matemáticos y Algorítmicos

### 3.1. Formulación del Sistema Lineal ($Ax = b$)
* Definición y significado financiero explícito de cada una de las variables ($x_1, \dots, x_n$).
* Interpretación económica de los coeficientes $a_{ij}$ (relación, impacto o interdependencia presupuestaria entre categorías).
* Interpretación del vector de términos independientes $b$ (metas de asignación, restricciones de gasto o requerimientos netos).

### 3.2. Solución Numérica de Referencia (Método Directo)
* Implementación de un método directo exacto (Factorización LU, Eliminación Gaussiana o Factorización de Cholesky).
* Esta solución se denominará dentro del sistema como **"Solución numérica de referencia"** (clasificable formalmente como solución exacta) y servirá de base para medir el error de los métodos iterativos.

### 3.3. Algoritmo de Gradientes Conjugados Precondicionado (GCP)
* Se fundamenta en el artículo científico: *Suñagua S., P. (2020), "Método de Gradientes Conjugados Precondicionado"*.
* **Vector inicial:** $x_0 = 0$ (configurable por defecto).
* **Residuo inicial:** $r_0 = b - Ax_0$.
* **Matriz Precondicionadora ($M$):**
  * *Precondicionador de Jacobi (Diagonal):* Por defecto para corregir mal escalamiento en la diagonal principal.
  * *Precondicionador Alternativo (Factorización Incompleta de Cholesky o SSOR):* Aplicable si el mal condicionamiento surge por un fuerte acoplamiento fuera de la diagonal.
* **Ciclo iterativo:**
  1. Resolución del sistema precondicionado: $M z_k = r_k$.
  2. Actualización de direcciones conjugadas $p_k$.
  3. Cálculo del tamaño de paso $\alpha_k$.
  4. Actualización de la aproximación $x_{k+1}$ y del residuo $r_{k+1}$.
  5. Criterio de parada: evaluación del residuo relativo global $\|r_k\|_2 / \|b\|_2 < 10^{-6}$ o límite de iteraciones $N_{max}$.

### 3.4. Algoritmo de Gradientes Conjugados Simple (GC sin precondicionar)
* Debe ejecutarse de manera paralela o comparativa contra el GCP utilizando los mismos datos iniciales, con el único objetivo de contrastar la aceleración en la velocidad de convergencia.

### 3.5. Métricas de Error y Análisis de Condicionamiento
Para cada escenario y por cada variable ($i = 1, \dots, n$):
* **Error Absoluto:**  
  $$E_{a,i} = |x_{ref,i} - x_{GCP,i}|$$
* **Error Relativo:**  
  $$E_{r,i} = \frac{E_{a,i}}{|x_{ref,i}|}$$  
  *(Si $x_{ref,i} = 0$, documentar formalmente que el error relativo no está definido para esa componente).*
* **Error Porcentual:**  
  $$E_{p,i} = E_{r,i} \times 100\%$$
* **Residuo Relativo Global:**  
  $$\frac{\|b - Ax_{GCP}\|_2}{\|b\|_2} \quad (\text{para } \|b\|_2 \ne 0)$$
* **Número de Condición:**  
  * De la matriz original: $\kappa(A) = \|A\| \cdot \|A^{-1}\|$.
  * De la matriz precondicionada: $\kappa(M^{-1}A)$.

---

## 4. Definición de los Tres Escenarios Obligatorios

| Escenario | Descripción Financiera | Modificación Matemática y Comportamiento Esperado |
| :--- | :--- | :--- |
| **1. Ideal** | Situación financiera estable, predecible y equilibrada. | Matriz $A$ bien condicionada con $\kappa(A)$ bajo. Rápida convergencia y alta exactitud de ambos métodos. |
| **2. Bajo Estrés Financiero** | Perturbación del entorno económico (inflación, incremento de costos operativos, variación de tasas de asignación). | Modificación justificada de los valores de $b$ y/o $A$. Análisis del desplazamiento del punto de equilibrio frente a alteraciones en el condicionamiento. |
| **3. Mal Condicionado** | Alto grado de interdependencia entre variables o disparidad severa de escalas presupuestarias. | Matriz $A$ simétrica definida positiva con número de condición elevado ($\kappa(A) \gg 1$). Se evalúa el desempeño del precondicionador ($M$) reduciendo drásticamente las iteraciones requeridas frente a GC simple. |

---

## 5. Estructura y Módulos de la Aplicación Web Interactiva

El producto final es una aplicación web interactiva y dinámica. No se requiere documento escrito ni PDF por separado; toda la información técnica debe presentarse dentro del sitio.

1. **Módulo 1: Inicio**
   * Título oficial del proyecto.
   * Datos del estudiante, carrera y mención académica (*Desarrollo de Sistemas*).
   * Síntesis ejecutiva del caso de asignación presupuestaria.
2. **Módulo 2: Caso de Estudio**
   * Contexto financiero y justificación técnica del modelo.
   * Procedencia y racionalidad de los datos.
3. **Módulo 3: Formulación Matemática**
   * Definición explícita de variables ($n \ge 4$).
   * Presentación del sistema $Ax = b$ e interpretación económica de cada coeficiente.
   * Demostración analítica de simetría y definición positiva de $A$.
4. **Módulo 4: Entrada y Configuración de Datos**
   * Interfaz editable para modificar coeficientes de $A$ y componentes de $b$.
   * Configuración de tolerancia, iteraciones máximas ($N_{max}$), vector inicial $x_0$ y selector del precondicionador ($M$).
   * Controles de ejecución y recálculo instantáneo.
5. **Módulo 5: Selector de Escenarios**
   * Botones de carga rápida preconfigurados para los escenarios: *Ideal*, *Bajo Estrés* y *Mal Condicionado*.
6. **Módulo 6: Solución Numérica de Referencia**
   * Despliegue del vector solución obtenido mediante el método directo (LU, Gauss o Cholesky).
7. **Módulo 7: Comparativa GCP vs. GC Simple**
   * Visualización comparativa de: vectores de solución aproximada, número de iteraciones alcanzadas, norma del residuo final y diagnóstico de convergencia.
8. **Módulo 8: Análisis de Errores y Condicionamiento**
   * Tabla interactiva de errores por componente ($E_a, E_r, E_p$).
   * Comparativa de $\kappa(A)$ frente a $\kappa(M^{-1}A)$.
   * Valor del residuo relativo global.
9. **Módulo 9: Módulo de Pruebas de Software (QA)**
   * Registro y verificación interactiva de casos de prueba del sistema.
10. **Módulo 10: Conclusiones y Referencias**
    * Interpretación técnica, numérica y financiera de los resultados.
    * Cita bibliográfica formal de Suñagua S. (2020) y referencias secundarias.

---

## 6. Tabla Comparativa Obligatoria

La interfaz debe presentar la siguiente matriz de contraste entre escenarios:

| Indicador | Escenario Ideal | Escenario Bajo Estrés | Escenario Mal Condicionado |
| :--- | :--- | :--- | :--- |
| **Solución numérica de referencia** | Vector $[x_1, \dots, x_n]$ | Vector $[x_1, \dots, x_n]$ | Vector $[x_1, \dots, x_n]$ |
| **Solución GCP** | Vector $[x_1, \dots, x_n]$ | Vector $[x_1, \dots, x_n]$ | Vector $[x_1, \dots, x_n]$ |
| **Error absoluto ($E_a$)** | Por variable | Por variable | Por variable |
| **Error porcentual ($E_p$)** | Por variable | Por variable | Por variable |
| **Iteraciones GC (sin precondicionar)** | Número entero | Número entero | Número entero |
| **Iteraciones GCP (precondicionado)** | Número entero | Número entero | Número entero |
| **Número de condición $\kappa(A)$** | Valor escalar | Valor escalar | Valor escalar |
| **Número de condición $\kappa(M^{-1}A)$** | Valor escalar | Valor escalar | Valor escalar |
| **Residuo relativo final GCP** | Valor escalar | Valor escalar | Valor escalar |
| **¿Convergió el algoritmo?** | Sí / No | Sí / No | Sí / No |
| **Interpretación financiera** | Explicación cualitativa | Explicación cualitativa | Explicación cualitativa |

---

## 7. Módulo de Pruebas de Software (QA Obligatorio)

Se debe incorporar una sección visible en la web que documente y ejecute de forma demostrable los siguientes casos de prueba en formato estándar (*Entrada*, *Resultado Esperado*, *Resultado Obtenido*, *Conclusión*):

1. **Prueba 1: Carga de Escenarios**
   * Verificación de la carga íntegra y cálculo sin errores de los tres escenarios predefinidos (Ideal, Estrés, Mal Condicionado).
2. **Prueba 2: Validación de Matriz No Válida**
   * Introducción deliberada de una matriz asimétrica o no definida positiva.
   * Verificación de captura del error mediante mensajes informativos al usuario, evitando fallos o bloqueos de la aplicación.
3. **Prueba 3: Edición Dinámica y Reactividad**
   * Alteración manual de coeficientes en la interfaz para verificar el recálculo automático e instantáneo de la solución de referencia, GCP, errores y métricas.
4. **Prueba 4: Comparativa de Eficiencia del Precondicionamiento**
   * Validación algorítmica de que el método GCP alcance la tolerancia en menor o igual número de iteraciones que el GC simple bajo el escenario mal condicionado.

---

## 8. Criterios de Evaluación y Entregables

### Entregables Oficiales
1. **Enlace público a la aplicación web funcional:** Accesible vía navegador web sin credenciales de acceso, interactiva y con persistencia de cálculos.
2. **Enlace al repositorio de control de versiones:** Repositorio público (GitHub o GitLab) estructurado, con historial secuencial de confirmaciones (*commits*) y archivo `README.md` explicativo que detalle la arquitectura, instalación y ejecución local.

### Rúbrica de Calificación (Total: 100 puntos)

* **Caso financiero y modelado ($n \ge 4$) (15 pts):** Formulación coherente de $Ax = b$, significado de variables y demostración de simetría y definición positiva de $A$.
* **Solución numérica de referencia (15 pts):** Implementación e integración correcta del método directo para los tres escenarios.
* **Implementación del algoritmo GCP (20 pts):** Codificación fiel del algoritmo de Suñagua (2020), cálculo del residuo, precondicionador y contraste con GC simple.
* **Construcción de los tres escenarios (15 pts):** Justificación matemática y de contexto financiero para los escenarios Ideal, Estrés y Mal Condicionado.
* **Análisis de errores y condicionamiento (15 pts):** Cálculo riguroso de errores ($E_a, E_r, E_p$), residuo relativo global y análisis comparativo de $\kappa(A)$ y $\kappa(M^{-1}A)$.
* **Página web interactiva y módulo QA (10 pts):** Usabilidad, reactividad, diseño de interfaz y ejecución del módulo de pruebas de control de calidad.
* **Aporte específico de la mención de Desarrollo (5 pts):** Cumplimiento en arquitectura de componentes, validaciones robustas de entrada y pruebas funcionales de software.
* **Interpretación y conclusiones (5 pts):** Claridad analítica y rigor en las conclusiones técnicas, algorítmicas y financieras.

---

## 9. Referencias Bibliográficas

* Suñagua S., P. (2020). *Método de Gradientes Conjugados Precondicionado*. Revista Boliviana de Matemática UMSA, 04, 2–7.
* Golub, G. H., & Van Loan, C. F. (2013). *Matrix Computations* (4th ed.). Johns Hopkins University Press.
* Saad, Y. (2003). *Iterative Methods for Sparse Linear Systems* (2nd ed.). SIAM.