# Simulación Económica - Política de Feriados y Días No Laborables (1-2 Enero 2026)

Investigación económica sobre el impacto de las decisiones de operación empresarial durante el feriado del 1 de enero y el día no laborable del 2 de enero de 2026 en Perú.

## Descripción

Este modelo simula las decisiones de empresas peruanas sintéticas frente a dos eventos:

1. **1 de enero de 2026 (Feriado - D.L. 713)**: Las empresas pueden:
   - Cerrar (pago base del feriado: 1x salario)
   - Abrir con descanso sustitutorio (2x salario + costo del descanso futuro)
   - Abrir sin descanso sustitutorio (3x salario - "triple remuneración")

2. **2 de enero de 2026 (Día no laborable / Bridge Day)**: Las empresas pueden:
   - Operar normalmente (1x salario)
   - Adoptar el día no laborable (cerrar con costo de compensación futura)

El modelo genera empresas sintéticas en 5 sectores (lodging, restaurants, retail, transport, manufacturing_b2b) y simula sus decisiones basándose en maximización de utilidades.

## Estructura del Proyecto

```
.
├── data/
│   ├── calendar_2026.csv      # Calendario con tipos de día
│   └── params.json            # Parámetros de la simulación
├── src/
│   ├── generate_firms.py      # Generación de empresas sintéticas
│   ├── demand.py              # Cálculo de demanda y costos por día
│   ├── decisions.py           # Lógica de decisiones empresariales
│   ├── run.py                 # Función principal de simulación
│   └── report.py              # Generación de reportes
├── outputs/
│   └── runs/                  # Resultados de simulaciones
├── README.md
└── requirements.txt
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar simulación completa

Desde la raíz del proyecto:
```bash
python run_simulation.py
```

O desde `src/`:
```bash
cd src
python run.py
```

### Generar visualizaciones y reportes

Después de ejecutar la simulación, puedes generar reportes y gráficos:

```bash
cd src
python -c "
from report import load_results, generate_text_report, plot_decisions_by_sector
import glob
run_files = sorted(glob.glob('../outputs/runs/run_*.parquet'))
summary_files = sorted(glob.glob('../outputs/runs/summary_*.csv'))
if run_files and summary_files:
    firms_df, summary_df = load_results(run_files[-1], summary_files[-1])
    generate_text_report(summary_df, '../outputs/report.txt')
    plot_decisions_by_sector(firms_df, '../outputs/decisions_by_sector.png')
"
```

Esto genera:
- `outputs/report.txt`: Reporte textual con estadísticas agregadas
- `outputs/decisions_by_sector.png`: Gráficos de barras apiladas mostrando decisiones por sector

### Análisis robusto con múltiples seeds y escenarios

Para análisis publicable con replicaciones Monte Carlo y análisis de sensibilidad:

```bash
# Correr 300 seeds por 9 escenarios (2,700 corridas totales)
python scripts/run_many.py --seeds 300

# O ajustar número de empresas para pruebas rápidas
python scripts/run_many.py --seeds 50 --firms 5000
```

Esto genera:
- `outputs/runs_many.parquet`: Datos completos de todas las corridas
- `outputs/summary_many.csv`: Resumen agregado con estadísticas (mean, p10, p50, p90, std) por escenario

**Escenarios incluidos:**
1. `base`: Configuración base
2. `tourism_demand_high`: Demanda turística +20%
3. `tourism_demand_low`: Demanda turística -20%
4. `H_high`: Costos de descanso sustitutorio ×1.5
5. `H_low`: Costos de descanso sustitutorio ×0.5
6. `bridge_attractive`: Bridge más atractivo (demanda +20%, Hcomp -20%)
7. `bridge_costly`: Costos de bridge ×1.5
8. `capacity_high`: Capacidad +20%
9. `capacity_low`: Capacidad -20%

## Especificación del Modelo

### Inputs

- `data/calendar_2026.csv`: Define los tipos de día (holiday, bridge)
- `data/params.json`: Parámetros de la simulación:
  - Número de empresas
  - Distribuciones por sector (salarios, trabajadores, ingresos base)
  - Shocks de demanda y costos por sector y día
  - Multiplicadores de costos laborales legales
  - Factores de costos de política (H, Hcomp)

### Paso 1: Generar empresas sintéticas

Para cada empresa se generan:
- `firm_id`, `sector`
- `W`: Salario diario promedio por trabajador
- `N`: Número de trabajadores
- `R_base`: Ventas base diarias
- `C_base`: Costos no laborales base (C_base = R_base * cost_ratio)
- `K`: Capacidad máxima de ventas (K = R_base * capacity_multiplier)
- `H`: Costo económico del descanso sustitutorio (H = H_factor * N * W)
- `Hcomp`: Costo económico de compensar horas por día no laborable

### Paso 2: Calcular ventas y costos por día

Para cada tipo de día (holiday, bridge):

- **Ventas observadas**: `R_t = min(R_base * (1 + ΔD[sector][day_type]), K)`
- **Costos no laborales**: `C_t = C_base * (1 + ΔC[sector][day_type])`

Donde `ΔD` y `ΔC` son shocks de demanda y costos definidos en `params.json`.

### Paso 3: Decisiones

#### Día 1 (Feriado)

Tres opciones, elegir la de máximo beneficio:

**A) Cerrar:**
```
labor_cost = 1.0 * N * W
profit = 0 - 0 - labor_cost
```

**B) Abrir con descanso sustitutorio:**
```
labor_cost = 2.0 * N * W + H
profit = R_1 - C_1 - labor_cost
```

**C) Abrir sin descanso sustitutorio (3x):**
```
labor_cost = 3.0 * N * W
profit = R_1 - C_1 - labor_cost
```

Si hay empate y `behavioral.holiday_tie_breaker_prefer_sub=true`, se prefiere la opción B.

#### Día 2 (Bridge)

Dos opciones, elegir la de máximo beneficio:

**A) Operar normalmente:**
```
labor_cost = 1.0 * N * W
profit = R_2 - C_2 - labor_cost
```

**B) Adoptar día no laborable:**
```
profit = 0 - 0 - Hcomp
```

### Paso 4: Outputs

Se guardan dos archivos:

1. **`run_YYYYMMDD_HHMMSS_seed{seed}.parquet`**: DataFrame completo con todas las empresas y sus decisiones
2. **`summary_YYYYMMDD_HHMMSS_seed{seed}.csv`**: Resumen agregado por sector y total

Métricas incluidas:
- Tasa de apertura/cierre por sector
- Ventas totales por día y sector
- Costos laborales totales
- Utilidades totales y promedio
- Distribución de decisiones

## Referencias Legales

- **D.L. 713**: Feriados y remuneración por trabajo en feriado
  - https://diariooficial.elperuano.pe/Normas/obtenerDocumento?idNorma=110007

- **SUNAFIL**: Explicación práctica de "triple pago"
  - https://www.gob.pe/institucion/sunafil/noticias/858757-sunafil-quienes-laboren-en-feriado-recibiran-triple-pago-a-fin-de-mes

- **D.S. 042-2025-PCM**: Días no laborables (incluye 2 de enero 2026)
  - https://busquedas.elperuano.pe/dispositivo/NL/2387094-1

## Validaciones

El modelo incluye sanity checks:

1. En el día feriado, ningún costo laboral puede ser menor que `N*W` (pago base)
2. `open_no` siempre tiene costo laboral mayor que `open_sub` (si H no es enorme)
3. Si ΔD = 0 y márgenes son bajos, muchas firmas deberían preferir cerrar

## Resultados del Análisis Robusto

**Análisis completado:** 300 seeds × 9 escenarios = **2,700 corridas** (1.3 minutos de ejecución)

### Resultados Principales (Escenario Base)

Con los parámetros base y 300 replicaciones Monte Carlo:

- **Día Feriado (1 enero)**: 
  - 44.0% cierra (p10-p90: 43.0%-44.0%)
  - 56.0% abre con descanso sustitutorio (p10-p90: 56.0%-57.0%)
  - 0% abre sin descanso sustitutorio (3x)
- **Día Bridge (2 enero)**: 
  - 72.0% opera normalmente
  - 28.0% adopta día no laborable (p10-p90: 27.0%-28.0%)
- **Ventas totales**: S/ 249.6 millones (p10-p90: S/ 246.9-252.2 millones)
- **Profit total**: S/ 26.6 millones (p10-p90: S/ 25.7-27.5 millones)

### Análisis de Sensibilidad por Escenario

**Escenarios más impactantes:**

1. **Capacity High** (+20% capacidad): Profit total **S/ 39.5 millones** (↑48.6% vs base)
2. **Capacity Low** (-20% capacidad): Profit total **S/ 5.9 millones** (↓77.7% vs base)
3. **H Low** (costos descanso -50%): Profit total **S/ 27.4 millones** (↑3.2% vs base)
4. **H High** (costos descanso +50%): Profit total **S/ 25.8 millones** (↓3.0% vs base)

**Tasa de cierre en feriado:**
- Capacity Low: 54.0% (más empresas cierran por restricciones)
- Capacity High: 41.0% (menos empresas cierran, más pueden satisfacer demanda)
- Base: 44.0% (estable)

Los resultados completos se guardan en:
- `outputs/runs_many.parquet`: Datos completos de las 2,700 corridas
- `outputs/summary_many.csv`: Resumen agregado con estadísticas (mean, p10, p50, p90, std) por escenario
- `outputs/scenario_comparison.png`: Gráficos comparativos por escenario

## Extensiones Opcionales

En `params.json` se pueden configurar (actualmente en 0.00):
- `online_sales_fraction_when_closed`: Fracción de ventas online cuando cierra
- `partial_operation_fraction_on_bridge_if_adopted`: Fracción de operación parcial en bridge

## Licencia

Proyecto de investigación académica.

## Repositorio

Código disponible en: https://github.com/ConejoCapital/NewYearEconotaxonomy

