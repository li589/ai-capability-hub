# Patterns

## Pattern 1: File-Scoped Logger

Always create a logger at the top of each source file.

```typescript
// user.service.ts
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: __filename,
  service: "user-service",
  module: "user-management",
});

export class UserService {
  async getUser(id: string) {
    const opLogger = logger.child({ operation: "getUser", userId: id });

    opLogger.debug({ message: "Fetching user", data: { userId: id } });

    const user = await db.users.findUnique({ where: { id } });

    if (!user) {
      opLogger.warn({ message: "User not found", data: { userId: id } });
      return null;
    }

    opLogger.debug({ message: "User found", data: { userId: id } });
    return user;
  }
}
```

## Pattern 2: Request-Context Logger

Chain child loggers for request-scoped logging.

```typescript
// request-handler.ts
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: __filename,
  service: "api-gateway",
  version: process.env.npm_package_version,
});

async function handleRequest(req: Request): Promise<Response> {
  const requestId = crypto.randomUUID();
  const requestLogger = logger.child({
    requestId,
    method: req.method,
    path: new URL(req.url).pathname,
    timestamp: new Date().toISOString(),
  });

  requestLogger.info({ message: "Request started", data: {} });

  try {
    const result = await processRequest(req);
    requestLogger.info({
      message: "Request completed",
      data: { statusCode: 200 },
    });
    return result;
  } catch (error) {
    requestLogger.error({
      message: "Request failed",
      data: { error: error.message, stack: error.stack },
    });
    return new Response("Internal Error", { status: 500 });
  }
}
```

## Pattern 3: Frontend Component Logger

Scoped logger for UI components with environment awareness.

```typescript
// CheckoutButton.tsx
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: "CheckoutButton.tsx",
  component: "CheckoutButton",
  env: import.meta.env.PROD ? "production" : "development",
});

export function CheckoutButton({ cartId }: { cartId: string }) {
  const buttonLogger = logger.child({
    component: "CheckoutButton",
    cartId,
  });

  const handleClick = async () => {
    buttonLogger.info({
      message: "Checkout button clicked",
      data: { cartId },
    });

    try {
      await api.post("/checkout", { cartId });
      buttonLogger.info({ message: "Checkout initiated", data: { cartId } });
    } catch (error) {
      buttonLogger.error({
        message: "Checkout failed",
        data: { error: error.message, cartId },
      });
    }
  };

  return <button onClick={handleClick}>Checkout</button>;
}
```

## Pattern 4: Shared Utility Logger

Logger for reusable utility functions with optional remote transport.

```typescript
// validation.utils.ts
import { useLogging, addTransport, RemoteTransport } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: __filename,
  module: "validation",
  utility: "email",
});

// Optional: Send validation errors to remote service
if (process.env.REMOTE_LOGGING_ENABLED) {
  addTransport(
    new RemoteTransport("https://logs.example.com/validation", "warn")
  );
}

export function validateEmail(email: string): boolean {
  const validationLogger = logger.child({ function: "validateEmail" });

  const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  validationLogger.debug({
    message: "Email validation",
    data: {
      emailDomain: email.split("@")[1],
      result: isValid,
    },
  });

  return isValid;
}
```

## Pattern 5: Error Boundary Logger

Logger for error handling with full context.

```typescript
// error-boundary.tsx
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: "ErrorBoundary.tsx",
  component: "ErrorBoundary",
});

export class ErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error) {
    const errorLogger = logger.child({
      component: "ErrorBoundary",
      errorType: "render-error",
    });

    errorLogger.error({
      message: "React render error caught",
      data: {
        errorMessage: error.message,
        errorStack: error.stack,
        componentStack: React.captureStackTrace?.(error) || "",
      },
    });

    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

## Pattern 6: Database Transaction Logger

Logger for database operations with transaction context.

```typescript
// database.ts
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({
  file: __filename,
  service: "database",
  module: "transaction",
});

export async function runTransaction<T>(
  fn: (tx: Transaction) => Promise<T>
): Promise<T> {
  const txLogger = logger.child({
    operation: "transaction",
    transactionId: crypto.randomUUID(),
  });

  txLogger.debug({ message: "Starting transaction", data: {} });

  const startTime = Date.now();

  try {
    const result = await db.$transaction(fn, {
      timeout: 5000,
    });

    txLogger.info({
      message: "Transaction committed",
      data: {
        duration: Date.now() - startTime,
        transactionId: txLogger.transactionId,
      },
    });

    return result;
  } catch (error) {
    txLogger.error({
      message: "Transaction failed",
      data: {
        duration: Date.now() - startTime,
        error: error.message,
      },
    });
    throw error;
  }
}
```

## Pattern 7: Chrome MV3 Service Worker Logger

Special pattern for Chrome extension background scripts.

```javascript
// background.js - Chrome MV3 Service Worker
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');

const { useLogging, ConsoleTransport } = SimpleLogger;

// Configure once at startup
SimpleLogger.configureLogger({
  transports: [new ConsoleTransport('debug')]
});

// Create service-scoped logger
const bgLogger = useLogging({ 
  component: 'background',
  version: chrome.runtime.getManifest().version
});

bgLogger.info({ message: 'Service Worker initialized', data: {} });

// Handle messages with request context
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  const requestLogger = bgLogger.child({ 
    requestType: request.type,
    tabId: sender.tab?.id,
    url: sender.tab?.url
  });
  
  requestLogger.debug({ message: 'Received message', data: { request } });
  
  try {
    const result = handleRequest(request);
    requestLogger.info({ message: 'Request handled', data: { success: true } });
    sendResponse({ success: true, data: result });
  } catch (error) {
    requestLogger.error({ 
      message: 'Request failed', 
      data: { error: error.message } 
    });
    sendResponse({ success: false, error: error.message });
  }
  
  return true; // Keep channel open for async
});

// Handle extension events
chrome.action.onClicked.addListener((tab) => {
  bgLogger.info({ message: 'Action clicked', data: { tabId: tab.id } });
});
```

**Key MV3 Considerations:**
- Use IIFE bundle (`index.iife.js`) only
- Safe console access handles restricted contexts
- Lazy initialization prevents startup failures
- All dependencies bundled (no external imports)
- Log at appropriate levels (debug for verbose, info for key events)
