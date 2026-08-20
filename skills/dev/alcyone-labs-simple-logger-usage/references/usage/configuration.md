# Configuration

## Transport Setup

### Single Transport

```typescript
import { configureLogger, ConsoleTransport } from "@alcyone-labs/simple-logger";

configureLogger({ transports: [new ConsoleTransport("info")] });
```

### Multiple Transports

```typescript
import {
  configureLogger,
  ConsoleTransport,
  RemoteTransport,
} from "@alcyone-labs/simple-logger";

configureLogger({
  transports: [
    new ConsoleTransport("debug"),
    new RemoteTransport("https://logs.example.com/api", "info", {
      "X-API-Key": process.env.LOG_API_KEY,
    }),
  ],
});
```

### Add Transport Later

```typescript
import { addTransport, RemoteTransport } from "@alcyone-labs/simple-logger";

addTransport(new RemoteTransport("https://logs.example.com/ingest"));
```

## Remote Transport with Headers

```typescript
const transport = new RemoteTransport(
  "https://logs.example.com/api/v1/logs",
  "info",
  {
    "Content-Type": "application/json",
    "X-Request-Id": uuid(),
    "Authorization": `Bearer ${process.env.LOG_TOKEN}`,
  }
);
```

## Environment-Based Configuration

```typescript
import { configureLogger, ConsoleTransport, RemoteTransport } from "@alcyone-labs/simple-logger";

const isProduction = process.env.NODE_ENV === "production";

configureLogger({
  transports: isProduction
    ? [new RemoteTransport("https://logs.example.com/api")]
    : [new ConsoleTransport("debug")],
});
```

## Transport Level Configuration

```typescript
// Only log info and above to console in production
new ConsoleTransport("info");

// Log everything in development
new ConsoleTransport("debug");

// Remote only errors
new RemoteTransport(url, "error");
```

## Chrome MV3 Configuration

In Chrome MV3 service workers, use IIFE bundle:

```javascript
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');

// SimpleLogger global is available immediately
const { useLogging, ConsoleTransport } = SimpleLogger;

// Configure transports if needed
SimpleLogger.configureLogger({
  transports: [new ConsoleTransport("debug")]
});

// Create scoped logger
const logger = useLogging({ component: 'background' });
```

**MV3-Specific Notes:**
- IIFE bundle includes all dependencies (no external imports needed)
- Safe console access handles restricted SW contexts
- Lazy initialization prevents startup failures
- No `import.meta.env` available in SW context

## TypeScript Configuration

Ensure `strict` mode is enabled in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "strict": true,
    "esModuleInterop": true
  }
}
```

## Module Resolution

### ESM Projects (type: "module")

```typescript
import { useLogging } from "@alcyone-labs/simple-logger";
```

### CommonJS Projects

```typescript
const { useLogging } = require("@alcyone-labs/simple-logger");
```

### Chrome MV3 Service Worker

```javascript
// Via importScripts (IIFE bundle)
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');
const { useLogging } = SimpleLogger;
```

### Via Script Tag (CDN)

```html
<script src="https://unpkg.com/@alcyone-labs/simple-logger/dist/index.iife.js"></script>
<script>
  const { useLogging } = SimpleLogger;
</script>
```
