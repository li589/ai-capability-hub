# API Reference

## Exports

```typescript
// Main hook
export const useLogging = (metadata?: Record<string, any>): ILogger;

// Configuration
export const configureLogger = (options: { transports?: ITransport[] }): void;
export const addTransport = (transport: ITransport): void;

// Types
export { logMessageSchema, type TLog, type TLogLevel, type ITransport, type ILogger };

// Transports
export { ConsoleTransport, RemoteTransport, PinoBridgeTransport };
```

## useLogging

```typescript
useLogging(metadata?: Record<string, any>): ILogger
```

Returns a logger instance. If metadata provided, returns child logger with bound metadata.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| metadata | `Record<string, any>` | No | Metadata to merge into all log messages |

### Returns

`ILogger` instance with `info`, `debug`, `warn`, `error` methods.

### Usage

```typescript
// Global logger (no metadata)
const logger = useLogging();

// Scoped logger (with metadata)
const fileLogger = useLogging({ file: __filename, service: "api" });

// Child logger (inherits parent metadata)
const requestLogger = fileLogger.child({ requestId: uuid() });
```

## ILogger Interface

```typescript
interface ILogger {
  info(data: TLog): void;
  debug(data: TLog): void;
  warn(data: TLog): void;
  error(data: TLog): void;
  child(metadata: Record<string, any>): ILogger;
}
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| info | `(data: TLog) => void` | Log info level message |
| debug | `(data: TLog) => void` | Log debug level message |
| warn | `(data: TLog) => void` | Log warning level message |
| error | `(data: TLog) => void` | Log error level message |
| child | `(metadata) => ILogger` | Create child logger with bound metadata |

## ITransport Interface

```typescript
interface ITransport {
  level?: TLogLevel;
  info(data: TLog): void;
  debug(data: TLog): void;
  warn(data: TLog): void;
  error(data: TLog): void;
}
```

## TLog Type

```typescript
type TLog = {
  message: string;
  data: {
    metadata?: Record<string, any>;
    [key: string]: any;
  };
};
```

## TLogLevel Type

```typescript
type TLogLevel = "debug" | "info" | "warn" | "error";
```

## configureLogger

```typescript
configureLogger(options: { transports?: ITransport[] }): void
```

Replaces all active transports with provided transports.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| options.transports | `ITransport[]` | No | Array of transports to use |

### Usage

```typescript
import { configureLogger, ConsoleTransport, RemoteTransport } from "@alcyone-labs/simple-logger";

configureLogger({
  transports: [
    new ConsoleTransport("debug"),
    new RemoteTransport("https://logs.example.com/api"),
  ],
});
```

## addTransport

```typescript
addTransport(transport: ITransport): void
```

Adds a transport to the existing list of active transports.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| transport | `ITransport` | Yes | Transport instance to add |

### Usage

```typescript
import { addTransport, ConsoleTransport } from "@alcyone-labs/simple-logger";

addTransport(new ConsoleTransport("info"));
```

## Transport Classes

### ConsoleTransport

```typescript
class ConsoleTransport implements ITransport {
  constructor(level?: TLogLevel);
}
```

### RemoteTransport

```typescript
class RemoteTransport implements ITransport {
  constructor(url: string, level?: TLogLevel, headers?: Record<string, string>);
}
```

### PinoBridgeTransport

```typescript
class PinoBridgeTransport implements ITransport {
  constructor(pinoInstance: any, level?: TLogLevel);
}
```

## Chrome MV3 IIFE Bundle

When using in Chrome MV3 service workers via IIFE:

```javascript
// Global SimpleLogger object is available
const { 
  logger,           // Pre-configured root logger
  useLogging,       // Hook function
  ConsoleTransport, // Transport class
  RemoteTransport,  // Transport class
  configureLogger,  // Config function
  addTransport      // Add transport function
} = SimpleLogger;
```

**Note:** IIFE bundle has all dependencies bundled, including Zod validation.
