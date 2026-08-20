---
name: simple-logger-usage
description: Best practices for using simple-logger in TypeScript applications
references:
  - usage
install_source: official
install_method: download
skill_id: official_0hDZ4sNd
enabled_at: 1787231625732
version: 1.0.0
name_zh: Simple使用
---

# simple-logger-usage

Expert guide for adding structured logging to any TypeScript application using @alcyone-labs/simple-logger.

## When to Apply

- Adding logging to new or existing TypeScript project
- Need consistent logging across files (frontend/backend/services)
- Want typed logs with metadata/data separation
- Need scoped loggers per file/module
- Building Chrome MV3 extensions with service workers

## Golden Rules

- Create file-scoped logger at top of each file using `useLogging`
- Pass contextual metadata (service, file, component, requestId)
- Separate `message` (human-readable) from `data` (structured)
- Use `data.metadata` for tags/labels, `data.*` for structured fields
- Never pass secrets/passwords in logs
- Child loggers inherit parent metadata via chaining
- Use IIFE bundle for Chrome MV3 service workers

## Workflow Decision Tree

```
Request: Add logging to [target]
↓
What type of target?
├─ Single file → Create file logger with module context
│  └─ logger = useLogging({ file: __filename, module: "auth-utils" })
│  └─ Add child loggers per function if needed
│
├─ Backend service → Configure transports first
│  └─ configureLogger({ transports: [new RemoteTransport(...)] })
│  └─ Create service logger with file context
│  └─ Add child loggers per request
│
├─ Frontend component → Create component-scoped logger
│  └─ logger = useLogging({ component: "LoginForm" })
│  └─ Add child loggers per interaction
│
├─ Chrome MV3 Extension → Use IIFE bundle
│  └─ importScripts('./node_modules/.../index.iife.js')
│  └─ const { logger } = SimpleLogger
│  └─ Safe for service worker context
│
└─ Shared library → File-scoped with optional remote transport
   └─ Minimal context to avoid conflicts
```

## Examples

### Backend Service File

**Input:** `user.controller.ts` needs logging

**Output:**
```typescript
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({ service: "user-api", file: "user.controller.ts" });

export async function createUser(req: Request) {
  const requestLogger = logger.child({ requestId: crypto.randomUUID() });

  requestLogger.info({
    message: "Creating new user",
    data: { email: req.body.email },
  });

  try {
    const user = await db.createUser(req.body);
    requestLogger.info({
      message: "User created successfully",
      data: { userId: user.id },
    });
    return user;
  } catch (error) {
    requestLogger.error({
      message: "Failed to create user",
      data: { error: error.message },
    });
    throw error;
  }
}
```

### Frontend Component

**Input:** `CheckoutForm.tsx` needs interaction logging

**Output:**
```typescript
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  component: "CheckoutForm",
  env: import.meta.env.PROD ? "production" : "development",
});

export function CheckoutForm() {
  const formLogger = logger.child({ formId: "checkout" });

  const handleSubmit = async (data: FormData) => {
    formLogger.info({
      message: "Checkout form submitted",
      data: { timestamp: Date.now() },
    });

    try {
      await api.post("/checkout", data);
      formLogger.info({ message: "Checkout successful", data: {} });
    } catch (error) {
      formLogger.error({
        message: "Checkout failed",
        data: { error: error.message },
      });
    }
  };

  return <form onSubmit={handleSubmit}>{/* ... */}</form>;
}
```

### Chrome MV3 Service Worker

**Input:** `background.js` in Chrome extension needs logging

**Output:**
```javascript
// background.js - Chrome MV3 Service Worker
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');

const { logger, useLogging } = SimpleLogger;

// Create scoped logger for background
const bgLogger = useLogging({ component: 'background' });

bgLogger.info({ message: 'Service Worker initialized', data: {} });

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  const requestLogger = bgLogger.child({ 
    requestType: request.type,
    tabId: sender.tab?.id 
  });
  
  requestLogger.debug({ message: 'Received message', data: { request } });
  
  // Handle message...
  
  sendResponse({ success: true });
  return true;
});
```

### Multiple Log Levels

**Input:** Cache service needs different log levels per operation

**Output:**
```typescript
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({ file: "cache.service.ts", service: "cache" });

export class CacheService {
  private cache = new Map();

  async get<T>(key: string): Promise<T | null> {
    const cacheLogger = logger.child({ operation: "get", key });

    if (!this.cache.has(key)) {
      cacheLogger.debug({ message: "Cache miss", data: { key } });
      return null;
    }

    const entry = this.cache.get(key);

    if (Date.now() > entry.expiresAt) {
      cacheLogger.warn({
        message: "Cache entry expired",
        data: { key, expiredAt: entry.expiresAt },
      });
      this.cache.delete(key);
      return null;
    }

    cacheLogger.debug({ message: "Cache hit", data: { key } });
    return entry.value;
  }
}
```

## References

- **references/usage/README.md**: Overview, decision tree, best practices
- **references/usage/api.md**: Complete API signatures and types
- **references/usage/configuration.md**: Transport setup, environment config
- **references/usage/patterns.md**: 6 common implementation patterns
- **references/usage/gotchas.md**: 10+ pitfalls and workarounds
