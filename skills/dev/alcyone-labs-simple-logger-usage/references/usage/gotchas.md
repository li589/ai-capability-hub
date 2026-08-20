# Gotchas

## Metadata Inheritance Pitfalls

### Child Loggers Merge, Not Replace

```typescript
const parent = useLogging({ file: "parent.ts", service: "api" });
const child = parent.child({ operation: "getUser" });

// Child logs will contain BOTH { file, service } AND { operation }
// NOT just { operation }
```

### Shallow Merge Only

```typescript
const parent = useLogging({ user: { id: 1, name: "Alice" } });
const child = parent.child({ user: { id: 2 } });

// Child logs will have { user: { id: 2 } }
// Original user object is REPLACED, not merged deeply
```

## Empty Metadata Returns Root Logger

```typescript
const logger = useLogging({});

// This creates a child that is actually the root logger
// Any configuration passed to child() is ignored
const child = logger.child({ requestId: "123" });

// Child uses root logger behavior - metadata may not work as expected
```

## ConsoleTransport Output Format

```typescript
const logger = useLogging({ file: "test.ts" });

logger.info({
  message: "Test message",
  data: { value: 42 },
});

// Console output includes message as first arg:
// console.info("Test message", { message: "Test message", data: { value: 42 } })
// Message appears twice - this is expected behavior
```

## RemoteTransport Silent Failures

```typescript
const transport = new RemoteTransport("https://invalid-url.example.com");

// Fetch failures are silently caught
// No error thrown, no console warning
// Check network tab to verify requests

// Solution: Add fallback transport
configureLogger({
  transports: [
    new ConsoleTransport("error"),
    new RemoteTransport(url), // Falls back to console if fails
  ],
});
```

## TypeScript Type Inference

```typescript
// TLog type is inferred from logMessageSchema
const log: TLog = {
  message: "Hello",
  data: { value: 1 }, // data must be object, metadata is optional
};

// This will fail type check:
const bad = { message: "Hello", data: "string" }; // Error: data must be object
```

## Dynamic Metadata in Child Logger

```typescript
const logger = useLogging({ file: __filename });

// Creating child logger with mutable reference
const metadata = { requestId: "" };

const child = logger.child(metadata);

// Later mutation does NOT affect already-created child
metadata.requestId = "123";
console.log(child.requestId); // undefined or original value

// Solution: Create child with actual value
const child2 = logger.child({ requestId: "123" });
```

## Zod Validation Strictness

```typescript
import { logMessageSchema } from "@alcyone-labs/simple-logger";

// Schema requires message to be string
// Schema requires data to be object
// Extra fields in data are allowed

const valid = {
  message: "test",
  data: { customField: true, metadata: { tag: "value" } },
};

// Invalid - missing message:
const invalid1 = { data: { value: 1 } }; // Runtime error

// Invalid - message not string:
const invalid2 = { message: 123, data: {} }; // Runtime error
```

## Multiple ConfigureLogger Calls

```typescript
// First call - sets transports
configureLogger({ transports: [new ConsoleTransport("info")] });

// Second call - REPLACES all transports, does not add
configureLogger({ transports: [new RemoteTransport(url)] });

// First transport is GONE
// Use addTransport() to add without replacing
```

## Global Singleton State

```typescript
// module-a.ts
import { useLogging } from "@alcyone-labs/simple-logger";
const logger = useLogging({ module: "a" });

// module-b.ts
import { useLogging } from "@alcyone-labs/simple-logger";
const logger = useLogging({ module: "b" });

// Both loggers share the same underlying singleton
// Transports configured anywhere apply to all
```

## Environment Variables in Production

```typescript
// Development - works fine
const logger = useLogging({
  file: __filename,
  debug: true,
});

// Production build - __filename may be minified or unavailable
// Consider using process.env.NODE_ENV check
const logger = useLogging({
  file: process.env.NODE_ENV === "development" ? __filename : "prod",
});
```

## Circular References in Data

```typescript
const obj = { name: "circular" };
obj.self = obj;

logger.info({
  message: "Try to log circular",
  data: { obj }, // Will cause JSON.stringify error in transports
});

// Solution: Sanitize before logging
logger.info({
  message: "Try to log circular",
  data: { obj: { name: obj.name, hasCircular: !!obj.self } },
});
```

## File Logger Naming in Bundled Code

```typescript
// Source file
const logger = useLogging({ file: __filename });

// After bundling (Webpack/Rollup/esbuild)
// __filename may become "/src/index.ts" or just "index.ts"
// Consider explicit naming
const logger = useLogging({
  file: "user.controller.ts", // Explicit, reliable
});
```

## Chrome MV3 Service Worker Limitations

### No ESM Imports

```javascript
// ❌ Won't work in MV3 service worker
import { useLogging } from '@alcyone-labs/simple-logger';

// ✅ Use IIFE bundle instead
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');
const { useLogging } = SimpleLogger;
```

### No import.meta.env

```javascript
// ❌ Not available in SW context
const env = import.meta.env.PROD ? 'prod' : 'dev';

// ✅ Use alternative methods
const env = chrome.runtime.getManifest().version;
```

### Console May Be Restricted

```javascript
// Logger handles this gracefully, but be aware:
// - console may not be available during SW startup
// - Some console methods may be missing
// - SafeConsole transport handles missing methods
```

### Service Worker Termination

```javascript
// SW can be terminated at any time
// Don't rely on in-memory logger state
// Logs may be lost if SW terminates mid-operation
// Use RemoteTransport for critical logs
```

### Bundled Dependencies

```javascript
// IIFE bundle includes Zod + all dependencies
// ~125KB minified
// No need to import zod separately
```

## Multiple Package Entry Points

```typescript
// Standard import (works in most cases)
import { useLogging } from "@alcyone-labs/simple-logger";

// IIFE bundle (for MV3, CDN, script tags)
// dist/index.iife.js - exposes global SimpleLogger object

// CommonJS
const { useLogging } = require("@alcyone-labs/simple-logger");

// ESM bundle
dist/index.mjs

// CJS bundle
dist/index.cjs
```
