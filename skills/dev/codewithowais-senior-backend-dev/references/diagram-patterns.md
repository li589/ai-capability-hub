# Diagram Patterns Reference

Use these Mermaid diagram patterns when producing architecture artifacts.

---

## 1. System Overview (Flowchart)

Use for showing service boundaries and data flow.

```mermaid
flowchart LR
    Client([Client App]) --> Gateway[API Gateway]
    Gateway --> AuthSvc[Auth Service]
    Gateway --> UserSvc[User Service]
    Gateway --> OrderSvc[Order Service]
    UserSvc --> UserDB[(PostgreSQL)]
    OrderSvc --> OrderDB[(PostgreSQL)]
    OrderSvc --> Cache[(Redis)]
    OrderSvc --> Queue[[Message Queue]]
    Queue --> NotifSvc[Notification Service]
```

**When to use:** High-level system topology, service maps, deployment views.

---

## 2. Request Flow (Sequence Diagram)

Use for showing step-by-step interactions between components.

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as Auth Service
    participant S as Order Service
    participant D as Database

    C->>G: POST /orders
    G->>A: Validate JWT
    A-->>G: Token valid
    G->>S: Create order
    S->>D: BEGIN TRANSACTION
    S->>D: INSERT order
    S->>D: UPDATE inventory
    S->>D: COMMIT
    S-->>G: 201 Created
    G-->>C: 201 Created + order body
```

**When to use:** API call flows, auth flows, multi-step processes, debugging
interaction problems.

---

## 3. Entity Relationships (ER Diagram)

Use for database schema visualization.

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER {
        uuid id PK
        string email UK
        string password_hash
        timestamp created_at
        timestamp updated_at
    }
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        uuid id PK
        uuid user_id FK
        enum status
        decimal total
        timestamp created_at
    }
    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price
    }
    PRODUCT ||--o{ ORDER_ITEM : "appears in"
    PRODUCT {
        uuid id PK
        string name
        decimal price
        int stock
    }
```

**When to use:** Schema design, migration planning, data model discussions.

---

## 4. State Machine

Use for modeling entity lifecycle.

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Pending: submit()
    Pending --> Processing: payment_confirmed()
    Pending --> Cancelled: cancel()
    Processing --> Shipped: ship()
    Processing --> Cancelled: cancel()
    Shipped --> Delivered: deliver()
    Shipped --> Returned: return_requested()
    Delivered --> Returned: return_requested()
    Returned --> Refunded: refund_processed()
    Cancelled --> [*]
    Delivered --> [*]
    Refunded --> [*]
```

**When to use:** Order workflows, user account states, approval processes,
any entity with a lifecycle.

---

## 5. Deployment / Infrastructure

```mermaid
flowchart TB
    subgraph Cloud["AWS / GCP / Azure"]
        subgraph LB["Load Balancer"]
            ALB[Application LB]
        end
        subgraph App["App Tier - Auto-scaling"]
            A1[Instance 1]
            A2[Instance 2]
            A3[Instance N]
        end
        subgraph Data["Data Tier"]
            Primary[(Primary DB)]
            Replica[(Read Replica)]
            Redis[(Redis Cluster)]
        end
        subgraph Async["Async Processing"]
            Queue[[SQS / RabbitMQ]]
            Worker[Worker Fleet]
        end
    end
    ALB --> A1 & A2 & A3
    A1 & A2 & A3 --> Primary
    A1 & A2 & A3 --> Replica
    A1 & A2 & A3 --> Redis
    A1 & A2 & A3 --> Queue
    Queue --> Worker
    Worker --> Primary
```

**When to use:** Infrastructure discussions, scaling plans, cloud architecture.

---

## 6. C4 Context Diagram

Use for showing system context and external integrations.

```mermaid
flowchart TB
    User([End User]) --> WebApp[Web Application]
    Admin([Admin]) --> AdminPanel[Admin Dashboard]
    WebApp --> API[Backend API]
    AdminPanel --> API
    API --> DB[(Database)]
    API --> Cache[(Redis)]
    API --> Email[Email Service\nSendGrid]
    API --> Payment[Payment Gateway\nStripe]
    API --> Storage[File Storage\nS3]
```

**When to use:** Stakeholder presentations, system boundaries, external
dependency mapping.

---

## Tips

- Keep diagrams focused on ONE concern. Split into multiple diagrams rather
  than cramming everything into one.
- Label arrows with the protocol or action (`HTTP`, `gRPC`, `publish`, `query`).
- Use subgraphs to group related components.
- Color-code by concern when helpful: `style NodeName fill:#f96,stroke:#333`.
- For complex systems, start with a C4 Context diagram, then zoom into
  specific areas with flowcharts or sequence diagrams.
