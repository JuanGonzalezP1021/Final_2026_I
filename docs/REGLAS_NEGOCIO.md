# Reglas de Negocio del Sistema

> Documento de referencia de todas las reglas de negocio (BR) del
> Call Center Management System. Cada regla tiene un identificador
> único, un dueño, una justificación operacional, su implementación
> en código y su prueba unitaria asociada.

---

## Resumen

El sistema implementa **9 reglas de negocio** distribuidas en 3 áreas
de dominio. Cada regla se evidencia desde el mapa de procesos (BPMN) y
se valida en código antes de persistir cualquier cambio.

| ID | Área | Dueño | Tipo | Acción ante violación |
|----|------|-------|------|------------------------|
| BR-01 | Workforce | Dev 1 (Juan David) | Bloqueante | `BusinessRuleError` |
| BR-02 | Workforce | Dev 1 (Juan David) | Derivación | Calcula valor correcto |
| BR-03 | Workforce | Dev 1 (Juan David) | Bloqueante | `BusinessRuleError` |
| BR-04 | Contact Ops | Dev 2 (Luna) | Bloqueante (outlier) | `BusinessRuleError` |
| BR-05 | Contact Ops | Dev 2 (Luna) | Bloqueante (sanity) | `BusinessRuleError` |
| BR-06 | Contact Ops | Dev 2 (Luna) | Bloqueante (SLA) | `BusinessRuleError` |
| BR-07 | Productivity | Dev 3 (Lorena) | Bloqueante (integridad) | `BusinessRuleError` |
| BR-08 | Productivity | Dev 3 (Lorena) | Informativa | Marca `review_flags` |
| BR-09 | Productivity | Dev 3 (Lorena) | Bloqueante | `BusinessRuleError` |

**Tipos de regla:**
- **Bloqueante**: Lanza `BusinessRuleError` y aborta la operación.
- **Derivación**: Calcula automáticamente un valor a partir de otros.
- **Informativa**: No bloquea; agrega un flag al registro para revisión posterior.

---

## Área 1: Workforce Management (Dev 1 — Juan David)

### BR-01 · Capacidad máxima de Team Leader

**Descripción**
Un Team Leader (TL) no puede tener asignados más de **15 agentes directos**.

**Justificación de negocio**
El span of control de la industria de BPO para operaciones de voz/chat
se sitúa entre 8 y 15 agentes por supervisor. Pasar de 15 degrada la
calidad del coaching, aumenta el tiempo de respuesta a escalaciones y
correlaciona con mayor attrition.

**Disparador**
- Al crear un nuevo agente (`AgentController.create`)
- Al cambiar el `team_manager` de un agente existente (`update`)

**Implementación**
- Archivo: `domain/rules/agent_rules.py`
- Función: `assert_tl_capacity(team_manager, current_count)`
- Umbral: `config.MAX_AGENTS_PER_TL = 15`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-01',
    f'TL {team_manager} already has {current_count} agents (max 15)')
```

**Test asociado**
- Archivo: `tests/unit/test_agent_rules.py`
- Test: `test_tl_capacity_at_limit_raises`

**Trazabilidad BPMN**
Decisión "¿TL tiene capacidad?" en el subproceso UC-01 Onboarding de Agente.

---

### BR-02 · Derivación de tenurity desde fecha de ingreso

**Descripción**
El campo `tenurity` y `days_range` de un agente se calculan
automáticamente a partir de la diferencia entre la fecha actual y
`active_date`, según los siguientes buckets:

| Días en empresa | Tenurity | Days range |
|-----------------|----------|------------|
| 0 – 30 | New Hire | `0-30` |
| 31 – 89 | Early Tenure | `31-89` |
| 90 – 149 | Established | `90-149` |
| 150 + | Experienced | `150+` |

**Justificación de negocio**
Mantener `tenurity` derivado evita inconsistencias por edición manual
y permite que un agente progrese automáticamente entre buckets al
pasar el tiempo. Es la base para reportes de attrition y para el
forecast de personal en cada bucket.

**Disparador**
- Al crear un agente si no se proveen `tenurity` o `days_range`
- En batch al regenerar reportes (no expuesto en GUI)

**Implementación**
- Archivo: `domain/rules/agent_rules.py`
- Función: `derive_tenurity(active_date_iso, ref)`

**Test asociado**
- Archivo: `tests/unit/test_agent_rules.py`
- Test: `test_tenurity_buckets` (verifica los 7 puntos frontera 0/30/31/89/90/149/150)

**Trazabilidad BPMN**
Actividad "Calcular tenurity inicial" en UC-01 Onboarding de Agente.

---

### BR-03 · Protección contra desactivación con actividad reciente

**Descripción**
Un agente **no puede ser eliminado** del sistema si tiene contactos o
registros de productividad en los últimos **7 días**.

**Justificación de negocio**
Eliminar a un agente con actividad reciente rompe la integridad
referencial de los reportes operacionales (AHT histórico,
contribución del agente al SLA del LOB). Forzar un período de gracia
evita la pérdida silenciosa de datos.

**Disparador**
- Al ejecutar `AgentController.delete(agent_id)`

**Implementación**
- Archivo: `domain/rules/agent_rules.py`
- Función: `assert_can_deactivate(agent_id, has_recent_activity)`
- El controller consulta `ContactRepository` y `ProductivityRepository`
  filtrando por `date >= hoy - 7 días`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-03',
    f'agent {agent_id} has activity in last 7 days')
```

**Test asociado**
- Archivo: `tests/unit/test_agent_rules.py`
- Test: `test_can_deactivate_blocked`

**Trazabilidad BPMN**
Decisión "¿Agente tiene actividad reciente?" en UC-01 (camino de eliminación).

---

## Área 2: Contact Operations (Dev 2 — Luna)

### BR-04 · Detección de AHT atípico por canal

**Descripción**
Un registro de contacto cuyo AHT sea mayor a **media + 2 desviaciones
estándar** de la población de su canal (Phone, Chat o Email) se
considera atípico y se rechaza.

**Justificación de negocio**
AHT extremos suelen ser errores de captura (agente olvidó cerrar el
caso, conexión colgada que quedó contando) o casos genuinamente
excepcionales que deben revisarse manualmente antes de afectar los
promedios operacionales. Bajo distribución normal, mean + 2σ cubre
~97.7% de los casos legítimos, dejando el 2.3% restante para
revisión.

**Justificación estadística**
Si AHT por canal aproxima una distribución normal con media μ y
desviación σ, entonces:
- P(X ≤ μ + 2σ) ≈ 0.977
- P(X > μ + 2σ) ≈ 0.023 → candidatos a revisión

La regla se activa solo cuando hay **≥ 30 registros** en el canal,
para que la estimación de σ sea estable.

**Disparador**
- Al ejecutar `ContactController.create(data)`

**Implementación**
- Archivo: `domain/rules/contact_rules.py`
- Función: `assert_aht_in_range(contact_aht, channel_population_aht)`
- KPI auxiliar: `ContactKPICalculator.aht_outlier_threshold(channel)`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-04',
    f'AHT {contact_aht:.0f}s exceeds mean+2sigma ({upper:.0f}s)')
```

**Test asociado**
- Archivo: `tests/unit/test_contact_kpis.py`
- Tests: `test_aht_outlier_threshold`, `test_aht_below_threshold_ok`

**Trazabilidad BPMN**
Decisión "¿AHT dentro de rango?" en UC-02 Registrar Contacto.

---

### BR-05 · Límite de transacciones diarias por agente

**Descripción**
Un agente no puede registrar más de **200 transacciones**
(inbound + outbound) en un mismo día.

**Justificación de negocio**
200 transacciones en un turno de 8 horas implicaría un AHT promedio
de ≤ 144 segundos sostenido, lo cual es operacionalmente imposible
en cualquier canal del BPO. Cualquier valor por encima es síntoma de
un error de carga (archivo duplicado, parser que dobló filas).

**Disparador**
- Al ejecutar `ContactController.create(data)` o `update`
- Suma transacciones existentes del día + las nuevas

**Implementación**
- Archivo: `domain/rules/contact_rules.py`
- Función: `assert_tx_volume(daily_tx_so_far, new_tx)`
- Umbral: `config.MAX_CONTACTS_PER_AGENT_DAY = 200`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-05',
    f'daily transactions {total} exceed max 200')
```

**Test asociado**
- Archivo: `tests/unit/test_contact_kpis.py`
- Test: `test_tx_volume_cap_raises`

**Trazabilidad BPMN**
Decisión "¿Volumen diario ≤ 200?" en UC-02 Registrar Contacto.

---

### BR-06 · Umbral de SLA por contactos perdidos

**Descripción**
Si un agente acumula **5 o más contactos perdidos** (`missed_contacts`)
en un mismo día, el siguiente intento de registrar un contacto lanza
una alerta de incumplimiento de SLA.

**Justificación de negocio**
El SLA típico de respuesta para soporte automotriz de marca está en
≥ 95% de contactos atendidos. Con 5 missed en un día, un agente que
maneja 50 contactos cae a 90%, debajo del SLA contractual. Disparar
la alerta a tiempo permite reasignar carga al resto del equipo.

**Disparador**
- Al ejecutar `ContactController.create(data)`
- Suma `missed_contacts` existentes del día + el nuevo registro

**Implementación**
- Archivo: `domain/rules/contact_rules.py`
- Función: `assert_missed_threshold(daily_missed)`
- Umbral: `config.MISSED_THRESHOLD_PER_DAY = 5`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-06',
    f'missed contacts {daily_missed} reached SLA breach threshold')
```

**Test asociado**
- Archivo: `tests/unit/test_contact_kpis.py`
- Tests: `test_missed_threshold_triggers`, `test_missed_threshold_below_ok`

**Trazabilidad BPMN**
Decisión "¿Contactos perdidos < 5?" en UC-02 (rama de alerta de SLA).

---

## Área 3: Productivity Analytics (Dev 3 — Lorena)

### BR-07 · Integridad de la suma de estados de tiempo

**Descripción**
La suma de todas las duraciones de estado (aux, breaks, lunch,
meeting, training, busy, available, etc.) **no puede exceder**
`login_duration`.

**Justificación de negocio**
Un agente solo puede estar en un estado a la vez. La suma de tiempos
en cada estado debe coincidir exactamente con el tiempo logueado.
Si la suma excede el login, hay un error en el sistema de
reporting (estados solapados, duplicación, etc.) y los KPIs de
ocupación se vuelven inválidos (occupancy > 100%).

**Disparador**
- Al ejecutar `ProductivityController.create(data)` o `update`

**Implementación**
- Archivo: `domain/rules/productivity_rules.py`
- Función: `assert_state_sum(record)`
- Suma los 13 campos de estado y compara contra `login_duration`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-07',
    f'states sum {total}s > login {login_duration}s')
```

**Test asociado**
- Archivo: `tests/unit/test_productivity_rules.py`
- Tests: `test_state_sum_ok`, `test_state_sum_overflow`

**Trazabilidad BPMN**
Decisión "¿Σ estados ≤ login?" en UC-03 Revisión Diaria de Productividad.

---

### BR-08 · Flag de revisión por baja ocupación o alto AUX

**Descripción**
Regla **no bloqueante**. Un registro de productividad se marca con
`review_flags` si cumple alguna de estas condiciones:

- `occupancy < 40%` → flag `LOW_OCCUPANCY`
- `aux_ratio > 30%` → flag `HIGH_AUX`

El registro se persiste de todos modos.

**Justificación de negocio**
Ocupación por debajo del 40% sugiere sobre-staffing o un agente con
poca asignación de contactos. AUX por encima del 30% indica que más
de un tercio del turno se va en estados no-productivos (training,
reuniones, problemas técnicos). Ninguna es un error de dato — son
realidades operacionales — pero ambas requieren revisión del WFM
para decidir intervención (reasignar volumen, agendar coaching).

A diferencia de las demás reglas, esta **no bloquea** porque marcar
forzosamente como error frenaría operaciones legítimas (por ejemplo,
un día con training corporativo).

**Disparador**
- Al ejecutar `ProductivityController.create(data)` o `update`

**Implementación**
- Archivo: `domain/rules/productivity_rules.py`
- Función: `flag_for_review(record) -> list[str]`
- Umbrales:
  - `config.MIN_OCCUPANCY = 0.40`
  - `config.MAX_AUX_RATIO = 0.30`

**Resultado**
```python
record['review_flags'] = ['LOW_OCCUPANCY (30%)', 'HIGH_AUX (35%)']
```

**Test asociado**
- Archivo: `tests/unit/test_productivity_rules.py`
- Tests: `test_flag_low_occupancy`, `test_flag_high_aux`

**Trazabilidad BPMN**
Actividad "Marcar para revisión" en UC-03, sin rama de bloqueo.

---

### BR-09 · Tope de duración de sesión

**Descripción**
`login_duration` no puede exceder **12 horas (43,200 segundos)**.

**Justificación de negocio**
La normativa laboral colombiana (Código Sustantivo del Trabajo,
art. 161) establece una jornada máxima ordinaria de 8 horas, con
posibilidad de extensión hasta máximo 10 horas con horas extra.
Un registro con > 12 horas de login indica:
- Agente olvidó cerrar sesión (overnight)
- Error de cálculo en el sistema de tracking
- Posible violación de la jornada legal a investigar

Bloquear este caso evita que datos corruptos entren al sistema y
contamine los KPIs de ocupación.

**Disparador**
- Al ejecutar `ProductivityController.create(data)` o `update`

**Implementación**
- Archivo: `domain/rules/productivity_rules.py`
- Función: `assert_login_duration(login_seconds)`
- Umbral: `config.MAX_LOGIN_DURATION_SEC = 43_200`

**Excepción lanzada**
```python
raise BusinessRuleError('BR-09',
    f'login {login_seconds}s exceeds max 43200s')
```

**Test asociado**
- Archivo: `tests/unit/test_productivity_rules.py`
- Tests: `test_login_cap_ok`, `test_login_cap_exceeded`

**Trazabilidad BPMN**
Decisión "¿Login ≤ 12h?" en UC-03 Revisión Diaria de Productividad.

---

## Cobertura por desarrollador (cumple requisito 5 de la rúbrica)

| Desarrollador | Reglas implementadas | Tests por regla |
|---------------|----------------------|------------------|
| **Juan David** (Workforce) | BR-01, BR-02, BR-03 | 6+ tests |
| **Luna** (Contacts) | BR-04, BR-05, BR-06 | 6+ tests |
| **Lorena** (Productivity) | BR-07, BR-08, BR-09 | 6+ tests |

> El criterio del profesor pide **mínimo 1 regla por integrante**;
> el sistema entrega **3 reglas por integrante** (9 totales), cada una
> evidenciada en el BPMN y respaldada por pruebas unitarias.

---

## Configuración centralizada de umbrales

Todos los umbrales viven en `config.py`. Para ajustar una regla solo
hay que modificar la constante correspondiente; el código de negocio
las lee en cada evaluación.

```python
# config.py — fragmento relevante

MAX_AGENTS_PER_TL          = 15        # BR-01
MAX_CONTACTS_PER_AGENT_DAY = 200       # BR-05
MISSED_THRESHOLD_PER_DAY   = 5         # BR-06
MAX_LOGIN_DURATION_SEC     = 43_200    # BR-09 (12 horas)
MIN_OCCUPANCY              = 0.40      # BR-08
MAX_AUX_RATIO              = 0.30      # BR-08
```

---

*Última actualización: documento generado en la entrega final del proyecto.*
