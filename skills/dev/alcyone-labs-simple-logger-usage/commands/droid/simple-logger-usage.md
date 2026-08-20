# simple-logger-usage

## Description

Expert guide for adding structured logging to TypeScript applications using @alcyone-labs/simple-logger.

## Instructions

Load the simple-logger-usage skill and help implement logging patterns based on the request context.

## Workflow

1. Load skill manifest: `{SKILL_PATH}/simple-logger-usage/SKILL.md`
2. Identify task type from request:
   - File/service logging
   - Frontend component logging  
   - Chrome MV3 service worker logging
   - Transport configuration
   - General guidance
3. Read relevant references/usage/ files
4. Generate implementation with:
   - File-scoped logger initialization
   - Appropriate metadata
   - Child logger patterns
   - Transport configuration if needed
5. Include Chrome MV3 guidance when applicable (IIFE bundle)

## Parameters

- **task**: Description of logging task (e.g., "add logging to user service", "configure remote transport")
- **context**: Optional additional context (file path, component name, etc.)
- **target**: Optional target environment (backend, frontend, mv3, shared-library)

## Examples

**Task**: "Add logging to my API service"

**Output**:
```typescript
import { useLogging } from "@alcyone-labs/simple-logger";

const logger = useLogging({ 
  file: __filename, 
  service: "api" 
});

// Use child loggers per request
const requestLogger = logger.child({ requestId });
requestLogger.info({ message: "Request started", data: {} });
```

**Task**: "Chrome extension logging"

**Output**:
```javascript
importScripts('./node_modules/@alcyone-labs/simple-logger/dist/index.iife.js');
const { useLogging } = SimpleLogger;
const logger = useLogging({ component: 'background' });
```
