# simple-logger Usage

Best practices for integrating @alcyone-labs/simple-logger into any TypeScript application.

## Overview

@alcyone-labs/simple-logger provides:
- Type-safe logging with Zod validation
- Scoped loggers via `child()` method
- Extensible transport system (Console, File, Remote, Pino)
- Metadata merging across logger hierarchy
- Chrome MV3 service worker support via IIFE bundle

## When to Use

| Scenario | Approach |
|----------|----------|
| Backend API service | Configure transports, create file logger, use child loggers per request |
| Frontend component | Component-scoped logger with env context |
| Shared utility library | File-scoped logger with module context, optional remote transport |
| Chrome MV3 Extension | Use IIFE bundle, safe console access, lazy initialization |
| Serverless function | Function-scoped logger with execution context |
| Test utilities | Minimal logger with test context |

## Core Concepts

### Message vs Data

- **message**: Human-readable string describing the event
- **data**: Structured object containing fields for querying/filtering
- **data.metadata**: Tags/labels for categorization (inherited by child loggers)

### Logger Hierarchy

```
Root Logger (configured with transports)
  └─ File Logger (useLogging({ file, module, service }))
      └─ Request/Function Logger (child({ requestId, operation }))
          └─ Operation Logger (child({ action, entity }))
```

### File Scoped Logger Pattern

Always create a logger at the top of each file with contextual metadata:

```typescript
const logger = useLogging({
  file: __filename,
  service: "my-service",
  // Additional file-specific context
});
```

## Decision Tree

```
Need to add logging?
↓
What type of application?
├─ Backend/Service
│  └─ Configure transports → Create file logger → Child per request
├─ Frontend
│  └─ Create component logger → Child per interaction
├─ Chrome MV3 Extension
│  └─ Use IIFE bundle → Safe logger initialization
├─ Shared Library
│  └─ Create file logger → Optional remote transport
└─ Serverless/Lambda
   └─ Create function logger → Include request context
```

## Transport Selection

| Transport | Use When |
|-----------|----------|
| ConsoleTransport | Development, debugging |
| RemoteTransport | Production, centralized logging |
| PinoBridgeTransport | Existing Pino integration |
| Custom ITransport | Platform-specific needs |

## Chrome MV3 Service Worker

Special considerations for MV3 extensions:

```javascript
// Use IIFE bundle in service worker
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');
const { logger, useLogging } = SimpleLogger;

const log = useLogging({ component: 'background' });
log.info({ message: 'SW initialized', data: {} });
```

See `gotchas.md` for MV3-specific limitations and workarounds.

## Metadata Strategy

### Recommended Metadata Fields

```typescript
useLogging({
  file: __filename,                    // Always include
  service: "auth-service",             // Service name
  module: "token-manager",             // Module/subsystem
  // Optional contextual fields
  env: process.env.NODE_ENV,           // Environment
  version: packageJson.version,        // App version
});
```

### Child Logger Fields

```typescript
// Request context
logger.child({
  requestId: uuid(),
  userId: user.id,
  correlationId: headers["x-correlation-id"],
});

// Operation context
operationLogger.child({
  operation: "create",
  entity: "order",
  entityId: order.id,
});
```

## Best Practices Summary

1. **One logger per file** at module level
2. **Always pass `file`** in top-level logger
3. **Use child loggers** for request/function/operation context
4. **Separate message from data** - message for humans, data for machines
5. **Use metadata for tags** - searchable labels in log aggregation
6. **Never log secrets** - passwords, tokens, API keys
7. **Configure transports once** at application entry point
8. **Use typed data** - leverage TypeScript for data structure
9. **Use IIFE bundle for MV3** - ESM may fail in service workers
