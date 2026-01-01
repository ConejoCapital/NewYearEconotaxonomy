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

```bash
cd src
python run.py
```

### Generar reportes desde resultados existentes

```bash
cd src
python report.py outputs/runs/run_YYYYMMDD_HHMMSS_seed42.parquet outputs/runs/summary_YYYYMMDD_HHMMSS_seed42.csv
```

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

## Extensiones Opcionales

En `params.json` se pueden configurar (actualmente en 0.00):
- `online_sales_fraction_when_closed`: Fracción de ventas online cuando cierra
- `partial_operation_fraction_on_bridge_if_adopted`: Fracción de operación parcial en bridge

## Licencia

Proyecto de investigación académica.

