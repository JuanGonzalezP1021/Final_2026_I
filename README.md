# Call Center Management System

> Plataforma de gestión de fuerza laboral, operaciones y productividad
> para un BPO automotriz.
> Proyecto Final — Programación II.

Aplicación de escritorio para gestionar 2,500+ agentes, registrar
contactos de clientes por teléfono / chat / email, monitorear
productividad, calcular KPIs estándar de la industria y pronosticar
volumen y ocupación.

---

## Tabla de Contenidos

- [Call Center Management System](#call-center-management-system)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Inicio Rápido](#inicio-rápido)
  - [Arquitectura](#arquitectura)
  - [Diagramas de Clases](#diagramas-de-clases)
    - [1. Entidades del Dominio y Repositorios](#1-entidades-del-dominio-y-repositorios)
    - [2. Jerarquía de Excepciones Personalizadas](#2-jerarquía-de-excepciones-personalizadas)
    - [3. Servicio de Notificación (Decorator GoF)](#3-servicio-de-notificación-decorator-gof)
    - [4. Pronóstico (Patrón Strategy)](#4-pronóstico-patrón-strategy)
    - [5. Controladores (Capa de Aplicación)](#5-controladores-capa-de-aplicación)
  - [Modelo de Datos (ER)](#modelo-de-datos-er)
  - [Diagramas de Estado](#diagramas-de-estado)
    - [Ciclo de Vida del Agente (rige BR-02: progresión de tenurity)](#ciclo-de-vida-del-agente-rige-br-02-progresión-de-tenurity)
    - [Ciclo de Vida de un Contacto (por registro)](#ciclo-de-vida-de-un-contacto-por-registro)
    - [Día de Productividad (por agente / día)](#día-de-productividad-por-agente--día)
  - [Diagrama de Secuencia — Registrar Contacto](#diagrama-de-secuencia--registrar-contacto)
  - [Mapa de Procesos (resumen BPMN)](#mapa-de-procesos-resumen-bpmn)
  - [Estructura del Proyecto](#estructura-del-proyecto)
  - [Cómo Ejecutar el Sistema](#cómo-ejecutar-el-sistema)
  - [Pruebas](#pruebas)
  - [Equipo y Responsabilidades](#equipo-y-responsabilidades)
  - [Limitaciones Conocidas](#limitaciones-conocidas)

---

## Inicio Rápido

```bash
# 1. Clonar y entrar al proyecto
git clone <repo-url> && cd call_center_system

# 2. (Opcional) entorno virtual
python -m venv .venv && source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Cargar los CSVs fuente a JSON (ETL única vez)
python scripts/etl_csv_to_json.py \
    --source-dir ./raw_csvs \
    --out-dir ./data

# 5. Lanzar la GUI
python app.py

# 6. Correr las pruebas
python -m pytest tests/ -v
```

---

## Arquitectura

El sistema está organizado en cuatro capas. Las dependencias fluyen
**solo hacia abajo**: presentación depende de aplicación, aplicación
depende de dominio, dominio depende de abstracciones de infraestructura.

```
+----------------------+
|    Presentación      |  tkinter + matplotlib
|    views/, app.py    |
+----------+-----------+
           |
+----------v-----------+
|    Aplicación        |  orquestación de casos de uso
|    controllers/      |
+----+---------+-------+
     |         |
+----v---+ +---v----------+
| Dominio| |  Analítica   |  KPIs + pronosticadores
| models | |  kpis/       |
| rules  | |  forecast/   |
+----+---+ +-------+------+
     |             |
+----v-------------v-----+
|    Infraestructura     |  repo JSON, decorators, logging
|    persistence/        |
|    services/           |
+------------------------+
```

**Patrones aplicados**: MVC, Repository, DTO, Decorator (GoF), Strategy.

---

## Diagramas de Clases

El sistema se divide en cuatro subsistemas cohesivos. Cada diagrama de
abajo se enfoca en uno de ellos; juntos describen todo el código.

### 1. Entidades del Dominio y Repositorios

```mermaid
classDiagram
    class Agent {
        +str agent_id
        +str team_manager
        +str active_date
        +str days_range
        +str tenurity
        +days_in_company() int
        +to_dict() dict
        +from_dict(data)$ Agent
    }

    class Contact {
        +str contact_id
        +str agent_id
        +str date
        +str lob
        +str channel
        +int acw
        +int inbound_tx
        +int outbound_tx
        +int handle_time
        +int hold_time
        +int missed_contacts
        +aht() float
        +total_transactions() int
        +to_dict() dict
    }

    class Productivity {
        +str record_id
        +str agent_id
        +str date
        +int login_duration
        +int busy_duration
        +int available_duration
        +int aux_duration
        +occupancy() float
        +utilization() float
        +aux_ratio() float
        +productivity_score() float
    }

    class JsonRepository {
        <<abstract>>
        -str filepath
        -str key_field
        -Lock _lock
        +find_all(predicate?) list
        +find_by_key(key) dict
        +insert(record) void
        +update(key, record) bool
        +delete(key) bool
    }

    class AgentRepository
    class ContactRepository
    class ProductivityRepository

    JsonRepository <|-- AgentRepository
    JsonRepository <|-- ContactRepository
    JsonRepository <|-- ProductivityRepository

    AgentRepository ..> Agent : persiste
    ContactRepository ..> Contact : persiste
    ProductivityRepository ..> Productivity : persiste

    Contact "muchos" --> "1" Agent : agent_id FK
    Productivity "muchos" --> "1" Agent : agent_id FK
```

### 2. Jerarquía de Excepciones Personalizadas

```mermaid
classDiagram
    class Exception {
        <<built-in>>
    }
    class CallCenterError {
        +str message
        +str code
    }
    class ValidationError {
        +str field
    }
    class NotFoundError
    class DuplicateError
    class BusinessRuleError {
        +str rule_id
    }
    class IntegrityError
    class PersistenceError

    Exception <|-- CallCenterError
    CallCenterError <|-- ValidationError
    CallCenterError <|-- NotFoundError
    CallCenterError <|-- DuplicateError
    CallCenterError <|-- BusinessRuleError
    CallCenterError <|-- IntegrityError
    CallCenterError <|-- PersistenceError
```

### 3. Servicio de Notificación (Decorator GoF)

```mermaid
classDiagram
    class NotificationService {
        <<interface>>
        +notify(operation, entity, payload) dict
    }

    class ConsoleNotification {
        +notify(operation, entity, payload) dict
    }

    class NotificationDecorator {
        <<abstract>>
        -NotificationService _wrapped
        +notify(operation, entity, payload) dict
    }

    class TimestampDecorator {
        +notify(operation, entity, payload) dict
    }

    class EmailNotificationDecorator {
        +notify(operation, entity, payload) dict
        -_send(envelope) void
    }

    class AuditLogDecorator {
        +notify(operation, entity, payload) dict
    }

    NotificationService <|.. ConsoleNotification
    NotificationService <|.. NotificationDecorator
    NotificationDecorator <|-- TimestampDecorator
    NotificationDecorator <|-- EmailNotificationDecorator
    NotificationDecorator <|-- AuditLogDecorator
    NotificationDecorator o-- NotificationService : envuelve
```

La pila canónica de decoradores compuesta por `default_notifier()`:

```
AuditLogDecorator( EmailNotificationDecorator( TimestampDecorator( ConsoleNotification() ) ) )
```

### 4. Pronóstico (Patrón Strategy)

```mermaid
classDiagram
    class Forecaster {
        <<interface>>
        +fit_predict(series, horizon)* ForecastResult
    }

    class ForecastResult {
        +str method
        +int horizon
        +list~float~ predictions
        +float mae
        +list~float~ confidence_low
        +list~float~ confidence_high
    }

    class MovingAverageForecaster {
        -int window
        +fit_predict(series, horizon) ForecastResult
    }

    class LinearRegressionForecaster {
        +fit_predict(series, horizon) ForecastResult
    }

    class ExponentialSmoothingForecaster {
        -float alpha
        +fit_predict(series, horizon) ForecastResult
    }

    Forecaster <|.. MovingAverageForecaster
    Forecaster <|.. LinearRegressionForecaster
    Forecaster <|.. ExponentialSmoothingForecaster
    Forecaster ..> ForecastResult : produce
```

### 5. Controladores (Capa de Aplicación)

```mermaid
classDiagram
    class AgentController {
        -AgentRepository repo
        -NotificationService notifier
        +create(data) Agent
        +read(id) Agent
        +update(id, patch) Agent
        +delete(id) void
        +kpis() dict
        +forecast_established_next_month() dict
    }

    class ContactController {
        -ContactRepository repo
        -AgentRepository agents
        -NotificationService notifier
        +create(data) Contact
        +read(id) Contact
        +update(id, patch) Contact
        +delete(id) void
        +kpis() dict
        +forecast_volume(channel, horizon) dict
    }

    class ProductivityController {
        -ProductivityRepository repo
        -AgentRepository agents
        -NotificationService notifier
        +create(data) Productivity
        +read(id) Productivity
        +update(id, patch) Productivity
        +delete(id) void
        +kpis() dict
        +forecast_occupancy_for_tl(tl, horizon) dict
    }

    AgentController --> AgentRepository
    AgentController --> NotificationService
    AgentController ..> LinearRegressionForecaster : usa

    ContactController --> ContactRepository
    ContactController --> AgentRepository
    ContactController --> NotificationService
    ContactController ..> MovingAverageForecaster : usa
    ContactController ..> LinearRegressionForecaster : usa

    ProductivityController --> ProductivityRepository
    ProductivityController --> AgentRepository
    ProductivityController --> NotificationService
    ProductivityController ..> ExponentialSmoothingForecaster : usa
```

---

## Modelo de Datos (ER)

```mermaid
erDiagram
    AGENT ||--o{ CONTACT          : "atiende"
    AGENT ||--o{ PRODUCTIVITY      : "registra diariamente"
    TEAM_MANAGER ||--o{ AGENT      : "supervisa"

    AGENT {
        string  agent_id PK
        string  team_manager FK
        date    active_date
        string  days_range
        string  tenurity
    }

    CONTACT {
        string  contact_id PK
        string  agent_id FK
        date    date
        string  lob
        string  channel
        int     acw
        int     inbound_tx
        int     outbound_tx
        int     handle_time
        int     hold_time
        int     missed_contacts
    }

    PRODUCTIVITY {
        string  record_id PK
        string  agent_id FK
        date    date
        int     login_duration
        int     busy_duration
        int     available_duration
        int     aux_duration
        int     break_1
        int     break_2
        int     break_3
        int     lunch_duration
        int     meeting_duration
    }

    TEAM_MANAGER {
        string  tl_id PK
    }
```

**Cardinalidades**

| De | A | Regla |
|----|---|-------|
| Agent → Contact | 1 a muchos | Un agente atiende muchos registros de contacto (uno por agente/día/canal/LOB). |
| Agent → Productivity | 1 a muchos | Un registro de productividad por agente por día. |
| Team Manager → Agent | 1 a muchos | Un TL supervisa máximo 15 agentes (BR-01). |

---

## Diagramas de Estado

### Ciclo de Vida del Agente (rige BR-02: progresión de tenurity)

```mermaid
stateDiagram-v2
    [*] --> NewHire : ingreso (active_date)
    NewHire --> EarlyTenure : día 31
    EarlyTenure --> Established : día 90
    Established --> Experienced : día 150
    Experienced --> [*] : separación
    NewHire --> [*] : separación
    EarlyTenure --> [*] : separación
    Established --> [*] : separación

    note right of NewHire
        Días 0-30
        Alta supervisión
    end note
    note right of Experienced
        Días 150+
        Elegible para SME o TL
    end note
```

### Ciclo de Vida de un Contacto (por registro)

```mermaid
stateDiagram-v2
    [*] --> Ofrecido : llamada entrante se enruta al agente
    Ofrecido --> Aceptado : agente contesta
    Ofrecido --> Perdido : tiempo agotado
    Aceptado --> EnEspera : agente pone en espera
    EnEspera --> Aceptado : retoma
    Aceptado --> ACW : termina la conversación
    ACW --> [*] : registro persistido
    Perdido --> [*] : se cuenta en missed_contacts

    note right of ACW
        BR-04 se evalúa aquí:
        AHT vs media+2sigma
    end note
```

### Día de Productividad (por agente / día)

```mermaid
stateDiagram-v2
    [*] --> Login
    Login --> Disponible
    Disponible --> Ocupado : llega contacto
    Ocupado --> Disponible : termina contacto
    Disponible --> Aux : break / reunión / capacitación
    Aux --> Disponible : regresa
    Disponible --> Logout
    Ocupado --> Logout
    Aux --> Logout
    Logout --> [*]

    note right of Aux
        Se contabiliza en:
        break_1/2/3, lunch,
        meeting, training, etc.
    end note
    note right of Ocupado
        Numerador de occupancy
    end note
```

---

## Diagrama de Secuencia — Registrar Contacto

Flujo end-to-end del caso de uso **UC-02: Registrar Contacto**. Muestra
cómo se encadenan validación, reglas de negocio, persistencia,
notificación y el log de auditoría.

```mermaid
sequenceDiagram
    actor U as Supervisor
    participant V as ContactView
    participant CT as ContactController
    participant AR as AgentRepository
    participant KPI as ContactKPICalculator
    participant CR as ContactRepository
    participant N as default_notifier()<br/>(Stack de Decorators)
    participant L as audit.log

    U->>V: llena formulario + click Crear
    V->>CT: create(payload)
    CT->>AR: find_by_key(agent_id)
    AR-->>CT: registro del agente
    alt el agente no existe
        CT-->>V: raise IntegrityError
        V-->>U: diálogo de error
    end

    CT->>CR: find_all() [del día actual]
    CR-->>CT: registros del día
    CT->>CT: assert_tx_volume()   %% BR-05
    CT->>CT: assert_missed_threshold()  %% BR-06

    CT->>KPI: aht_outlier_threshold(channel)
    KPI-->>CT: media + 2sigma
    CT->>CT: validar AHT <= umbral   %% BR-04

    CT->>CR: insert(contact)
    CR-->>CT: ok

    CT->>N: notify('CREATE', 'Contact', payload)
    N->>L: agrega línea JSONL
    N-->>CT: recibo de notificación

    CT-->>V: instancia de Contact
    V-->>U: estado exitoso + refresca tabla
```

---

## Mapa de Procesos (resumen BPMN)

El diagrama BPMN 2.0 completo está en `docs/bpmn_diagram.png`. A
continuación un resumen narrativo de los cuatro casos de uso primarios.

| UC | Nombre | Disparador | Camino principal | Camino de excepción |
|----|--------|------------|------------------|---------------------|
| UC-01 | Onboarding de Agente | Ingreso de nuevo agente | Validar ID → verificar capacidad TL → persistir → notificar | BR-01: TL lleno → reasignar |
| UC-02 | Registrar Contacto | Carga diaria de contactos | Validar FK → revisar volumen/missed → revisar AHT atípico → persistir → notificar | BR-04/05/06 lanza excepción |
| UC-03 | Revisión Diaria de Productividad | Fin de turno | Validar suma de estados → calcular KPIs → marcar si occupancy baja | BR-07/09 lanza excepción |
| UC-04 | Pronóstico de Volumen | Petición del workforce | Agregar por canal → correr MA + LinReg → elegir menor MAE → renderizar gráfica | Serie muy corta → toast de error |

---

## Estructura del Proyecto

```
call_center_system/
├── app.py                       # punto de entrada
├── config.py                    # rutas, umbrales, configuración de email
├── requirements.txt
├── README.md                    # este archivo
├── docs/
│   ├── bpmn_diagram.png
│   ├── class_diagram.png        # exportado del Mermaid de arriba
│   ├── state_diagram.png
│   └── informe_final.docx
├── data/                        # generado por ETL, gitignored
│   ├── roster.json
│   ├── contacts.json
│   ├── productivity.json
│   └── audit.log
├── scripts/
│   └── etl_csv_to_json.py
├── domain/
│   ├── models/      {agent,contact,productivity}.py
│   ├── rules/       {agent,contact,productivity}_rules.py
│   └── exceptions/  custom_exceptions.py
├── infrastructure/
│   ├── persistence/ json_repository.py + 3 repositorios concretos
│   └── services/    notification.py, logger.py
├── analytics/
│   ├── kpis/        {agent,contact,productivity}_kpis.py
│   └── forecast/    base.py, moving_average.py, linear_regression.py,
│                    exp_smoothing.py
├── controllers/     {agent,contact,productivity}_controller.py
├── views/
│   ├── main_view.py
│   ├── {agent,contact,productivity}_view.py
│   └── widgets/     kpi_card.py, forecast_chart.py
└── tests/
    ├── unit/        test_*_model.py, test_forecasters.py, ...
    └── integration/ test_repository_roundtrip.py, test_controller_flow.py
```

---

## Cómo Ejecutar el Sistema

```bash
# Lanzar la GUI
python app.py

# Volver a correr ETL después de refrescar los CSVs
python scripts/etl_csv_to_json.py
```

**Atajos de teclado (cualquier pestaña)**

| Atajo | Acción |
|-------|--------|
| `Ctrl + N` | Nuevo registro |
| `Ctrl + S` | Guardar formulario |
| `Ctrl + F` | Ejecutar pronóstico |
| `F5`       | Refrescar tabla |
| `Delete`   | Eliminar fila seleccionada (con confirmación) |

---

## Pruebas

```bash
# Todas las pruebas, en modo verbose
python -m pytest tests/ -v

# Un archivo específico
python -m pytest tests/unit/test_forecasters.py -v

# Con cobertura (opcional)
pip install pytest-cov
python -m pytest tests/ --cov=domain --cov=analytics --cov-report=term
```

Meta: **50+ pruebas pasando**, con mínimo 10 pruebas unitarias por desarrollador.

---

## Equipo y Responsabilidades

| Desarrollador | Rama | Responsable de |
|---------------|------|----------------|
| Dev 1 | `feature/workforce` | Entidad Agent, BR-01/02/03, KPIs de headcount, pronóstico de tenurity, shell de la GUI |
| Dev 2 | `feature/contacts` | Entidad Contact, BR-04/05/06, KPIs de AHT/missed, pronóstico de volumen |
| Dev 3 | `feature/productivity` + `feature/forecasting` | Entidad Productivity, BR-07/08/09, KPIs de occupancy, los tres pronosticadores |

Ver la sección 14 de la guía de desarrollo PDF para el plan completo de los 42 commits.

---

## Limitaciones Conocidas

- **La persistencia JSON** funciona bien para un proyecto académico pero
  no escala más allá de unos cientos de miles de registros. Para
  producción, cambiar `JsonRepository` por una implementación SQLite o
  PostgreSQL detrás de la misma interfaz.
- **El email está simulado** — el `EmailNotificationDecorator` imprime
  a stdout en lugar de abrir una conexión SMTP. El contrato es el
  mismo; solo cambia el método `_send()`.
- **Los pronosticadores son univariados**. No modelan estacionalidad
  por día de la semana ni patrones específicos por LOB. Holt-Winters
  o SARIMA serían el siguiente paso natural.
- **La GUI es monousuario**. Las ediciones concurrentes entre procesos
  no se coordinan; el lock del archivo solo protege threads dentro del
  mismo proceso.

---
