# Contexts

<details>
<summary>
Architectural Context Overview
</summary>

```mermaid
flowchart LR

    subgraph UserSpace[User Space]
        U[User]
    end

    subgraph ClientLayer[Client Layer]
        W[WebUI Client<br/>~OpenWebUI~]
        C[CLI Client<br/>~Continue CLI~]
    end

    subgraph Orchestration[Model Orchestration]
        O[Ollama Server<br/>Model Runtime]
    end

    subgraph Tooling[Tool Servers]
        A[FastAPI Server<br/>~Primary Tool Server~]:::servers
        M[FastMCP Server<br/>~MCP Wrapper<br/>Depends on FastAPI~]:::servers
        DB[~PostgreSQL~]
    end

    subgraph External[External Integrations]
        D[Driver API]
        H[Webhook Endpoint]
    end

    %% User entry
    U --> W
    U --> C

    %% Clients to orchestrator
    W --> O
    C --> O

    %% Orchestrator to tool servers
    O --> W
    O --> C

    %% Client routing
    W --> A
    C --> M

    %% Dependency direction
    M --> A

    %% Tool server interactions
    A --> DB
    M --> DB
    A --> D
    D --> A
    H --> A

    classDef servers fill:#fea,stroke:#333,stroke-width:4px;
```

</details>

<details>
<summary>
Usage Contexts : CLI + WebUI Agent Tool
</summary>

```mermaid

---
config:
  theme: redux-color
---

sequenceDiagram
    actor User as User
    participant Client as Client Interface<br/>~WebUI or CLI~
    participant Orchestrator as Ollama Model Orchestrator
    participant FastAPI as FastAPI Server<br/>~Primary OpenAPI Tool Server~
    participant FastMCP as FastMCP Server<br/>~MCP Wrapper Depends on FastAPI~
    participant DB as PostgreSQL
    participant DriverAPI as External Driver API
    participant Webhook as Webhook Endpoint

    Note over FastAPI, FastMCP: FastAPI is the defined server.<br/>FastMCP wraps.

    User->>Client: Provide prompt requiring tool use
    Client->>Orchestrator: Send prompt + tool metadata
    Orchestrator-->>Client: Model decides to call tool

    alt Tool call triggered
        %% Client routing logic
        alt Client = OpenWebUI
            Client->>FastAPI: OpenAPI tool request
        else Client = Continue CLI
            Client->>FastMCP: Native MCP tool request
            FastMCP->>FastAPI: Delegates to underlying FastAPI tool
        end

        FastAPI->>DB: Log request ~optional~

        %% External API
        FastAPI->>DriverAPI: External API call ~if required~
        DriverAPI-->>FastAPI: Payload

        alt Async webhook
            Webhook->>FastAPI: Webhook callback
            FastAPI-->>Webhook: 200 OK
        end

        FastAPI->>DB: Log events

        %% Return path
        alt Client = OpenWebUI
            FastAPI-->>Client: Tool result
        else Client = Continue CLI
            FastAPI-->>FastMCP: Tool result
            FastMCP-->>Client: MCP tool result
        end

        Client->>Orchestrator: Provide tool output to model
        Orchestrator-->>Client: Final model response
    end

    Client-->>User: Display final output
```

</details>