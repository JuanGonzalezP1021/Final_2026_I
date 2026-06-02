# Mapa de Procesos — BPMN 2.0

> Diagrama de procesos del Call Center Management System usando notación
> BPMN 2.0 representada en Mermaid. Muestra los 4 casos de uso primarios
> y marca explícitamente las 9 reglas de negocio (BR-01 a BR-09).

---

## Vista general del sistema

```mermaid
flowchart LR
    Start([Inicio]) --> UC1[UC-01<br/>Onboarding<br/>Agente]
    Start --> UC2[UC-02<br/>Registrar<br/>Contacto]
    Start --> UC3[UC-03<br/>Productividad<br/>Diaria]
    Start --> UC4[UC-04<br/>Forecast]
    UC1 --> End([Fin])
    UC2 --> End
    UC3 --> End
    UC4 --> End

    style UC1 fill:#a8dadc,stroke:#1d3557,stroke-width:2px
    style UC2 fill:#f1c0a8,stroke:#1d3557,stroke-width:2px
    style UC3 fill:#cdb4db,stroke:#1d3557,stroke-width:2px
    style UC4 fill:#ffe5a8,stroke:#1d3557,stroke-width:2px
```

---

## UC-01 — Onboarding de Agente

Reglas evaluadas: **BR-01, BR-02, BR-03**

```mermaid
flowchart TD
    Start([Inicio: Nuevo agente]) --> Input[/Capturar datos:<br/>agent_id, team_manager,<br/>active_date/]
    Input --> Validate{¿Datos válidos?<br/>formato ID, fecha ISO, TL prefix}
    Validate -->|No| ErrV[ValidationError]
    ErrV --> End1([Fin])

    Validate -->|Si| BR02[BR-02:<br/>Derivar tenurity y<br/>days_range desde<br/>active_date]
    BR02 --> CheckTL{BR-01:<br/>¿TL tiene < 15<br/>agentes?}
    CheckTL -->|No| ErrBR1[BusinessRuleError<br/>BR-01: TL lleno]
    ErrBR1 --> End1

    CheckTL -->|Si| Persist[Persistir en<br/>roster.json]
    Persist --> Notify[EmailService:<br/>notificar CREATE]
    Notify --> Audit[Audit log:<br/>JSONL entry]
    Audit --> Success([Fin: Agente creado])

    style BR02 fill:#90ee90,stroke:#2d6a4f,stroke-width:2px
    style CheckTL fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style ErrBR1 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style ErrV fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

**Camino alterno: Eliminar agente (evalúa BR-03)**

```mermaid
flowchart TD
    Start([Inicio: Eliminar agente]) --> Find{¿Agente existe?}
    Find -->|No| ErrNF[NotFoundError]
    ErrNF --> End1([Fin])

    Find -->|Si| CheckAct{BR-03:<br/>¿Tiene actividad<br/>en ultimos 7 dias?}
    CheckAct -->|Si| ErrBR3[BusinessRuleError<br/>BR-03: agente activo]
    ErrBR3 --> End1

    CheckAct -->|No| Delete[Eliminar de<br/>roster.json]
    Delete --> Notify[EmailService:<br/>notificar DELETE]
    Notify --> Success([Fin: Agente eliminado])

    style CheckAct fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style ErrBR3 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

---

## UC-02 — Registrar Contacto

Reglas evaluadas: **BR-04, BR-05, BR-06**

```mermaid
flowchart TD
    Start([Inicio: Nuevo contacto]) --> Input[/Capturar datos:<br/>agent_id, fecha, canal,<br/>AHT, inbound/outbound,<br/>missed/]
    Input --> ValidateFK{¿Agent existe<br/>en roster?}
    ValidateFK -->|No| ErrInt[IntegrityError]
    ErrInt --> End1([Fin])

    ValidateFK -->|Si| ValidateData{¿Validaciones<br/>de dominio OK?<br/>canal en enum,<br/>valores no-negativos}
    ValidateData -->|No| ErrV[ValidationError]
    ErrV --> End1

    ValidateData -->|Si| BR05{BR-05:<br/>¿Volumen diario<br/>+ nuevo ≤ 200?}
    BR05 -->|No| ErrBR5[BusinessRuleError<br/>BR-05: exceso volumen]
    ErrBR5 --> End1

    BR05 -->|Si| BR06{BR-06:<br/>¿Missed acumulado<br/>+ nuevo < 5?}
    BR06 -->|No| ErrBR6[BusinessRuleError<br/>BR-06: SLA breach]
    ErrBR6 --> End1

    BR06 -->|Si| BR04{BR-04:<br/>¿AHT ≤ media + 2σ<br/>del canal?}
    BR04 -->|No| ErrBR4[BusinessRuleError<br/>BR-04: AHT atipico]
    ErrBR4 --> End1

    BR04 -->|Si| Persist[Persistir en<br/>contacts.json]
    Persist --> Notify[EmailService:<br/>notificar CREATE]
    Notify --> Audit[Audit log:<br/>JSONL entry]
    Audit --> Success([Fin: Contacto registrado])

    style BR05 fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style BR06 fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style BR04 fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style ErrBR5 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style ErrBR6 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style ErrBR4 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

---

## UC-03 — Productividad Diaria

Reglas evaluadas: **BR-07, BR-08, BR-09**

```mermaid
flowchart TD
    Start([Inicio: Registro<br/>de productividad]) --> Input[/Capturar 14 duraciones:<br/>aux, breaks, lunch,<br/>busy, available, login,<br/>etc./]
    Input --> ValidateFK{¿Agent existe<br/>en roster?}
    ValidateFK -->|No| ErrInt[IntegrityError]
    ErrInt --> End1([Fin])

    ValidateFK -->|Si| BR09{BR-09:<br/>¿login_duration<br/>≤ 43200s 12h?}
    BR09 -->|No| ErrBR9[BusinessRuleError<br/>BR-09: jornada excedida]
    ErrBR9 --> End1

    BR09 -->|Si| BR07{BR-07:<br/>¿Σ estados<br/>≤ login?}
    BR07 -->|No| ErrBR7[BusinessRuleError<br/>BR-07: estados solapados]
    ErrBR7 --> End1

    BR07 -->|Si| Compute[Calcular KPIs:<br/>occupancy, utilization,<br/>aux_ratio, score]
    Compute --> BR08[BR-08:<br/>Evaluar flags de revision<br/>LOW_OCCUPANCY si occ < 40%<br/>HIGH_AUX si aux > 30%]
    BR08 --> Persist[Persistir en<br/>productivity.json<br/>con review_flags]
    Persist --> Notify[EmailService:<br/>notificar CREATE]
    Notify --> Audit[Audit log:<br/>JSONL entry]
    Audit --> Success([Fin: Productividad registrada])

    style BR09 fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style BR07 fill:#fff3cd,stroke:#bc6c25,stroke-width:2px
    style BR08 fill:#cfe2ff,stroke:#0d6efd,stroke-width:2px
    style ErrBR9 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style ErrBR7 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

> Nota: BR-08 (en azul) es **informativa, no bloqueante**. El registro se persiste igual, pero queda marcado.

---

## UC-04 — Forecast de Volumen / Ocupación

Sin reglas de negocio asociadas — es un caso de uso de analítica pura.

```mermaid
flowchart TD
    Start([Inicio: Workforce<br/>solicita forecast]) --> Select[/Seleccionar:<br/>canal o TL<br/>+ horizonte/]
    Select --> Aggregate[Agregar serie<br/>diaria desde<br/>contacts/productivity.json]
    Aggregate --> Check{¿Serie tiene<br/>≥ 5 puntos?}
    Check -->|No| ErrSh[Error: serie<br/>muy corta]
    ErrSh --> End1([Fin])

    Check -->|Si| RunAll[Correr los 3<br/>forecasters:<br/>MA-7, LinReg, ExpSmooth]
    RunAll --> Compare[Comparar MAE<br/>in-sample de cada uno]
    Compare --> Pick[Elegir forecaster<br/>con menor MAE]
    Pick --> Render[Renderizar grafica:<br/>historia + prediccion<br/>+ banda 95% CI]
    Render --> Success([Fin: Forecast mostrado])

    style RunAll fill:#e0e1dd,stroke:#415a77,stroke-width:2px
    style Pick fill:#a8dadc,stroke:#1d3557,stroke-width:2px
```

---

## Trazabilidad de reglas en los procesos

Tabla cruzada que verifica que cada regla aparece explícita en al menos un proceso BPMN:

| Regla | Proceso | Tipo de nodo | Dueño |
|-------|---------|--------------|-------|
| BR-01 | UC-01 | Gateway (rombo) | Juan David |
| BR-02 | UC-01 | Activity (rectángulo) | Juan David |
| BR-03 | UC-01 (eliminar) | Gateway | Juan David |
| BR-04 | UC-02 | Gateway | Luna |
| BR-05 | UC-02 | Gateway | Luna |
| BR-06 | UC-02 | Gateway | Luna |
| BR-07 | UC-03 | Gateway | Lorena |
| BR-08 | UC-03 | Activity (no bloqueante) | Lorena |
| BR-09 | UC-03 | Gateway | Lorena |

---

## Convenciones del diagrama

- **Rombos amarillos** (`BR-XX`) — Decisiones que aplican una regla de negocio bloqueante
- **Cajas verdes** — Actividades de derivación automática
- **Cajas azules** — Reglas informativas (no bloquean el flujo)
- **Cajas rojas** — Estados de error (lanzan excepción)
- **Cajas grises/aqua** — Procesamiento técnico (cálculos, persistencia)

---

*Diagramas BPMN en Mermaid — generados para la entrega final.*
