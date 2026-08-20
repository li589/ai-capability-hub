# TanStack Start Dockerfile Guide

Reference guide for creating Dockerfiles for TanStack Start applications with haloy.

Complete example: [haloydev/examples/tanstack-start-postgres](https://github.com/haloydev/examples/tree/main/tanstack-start-postgres)

## Project Detection

TanStack Start projects have these indicators:
- `@tanstack/react-start` in package.json dependencies
- `vite.config.ts` with `tanstackStart()` plugin
- `src/routes/` directory with file-based routing

## Critical Configuration

### package.json Requirements

The project MUST have:
```json
{
  "type": "module",
  "scripts": {
    "build": "vite build",
    "start": "node .output/server/index.mjs"
  }
}
```

**Important:** The `"type": "module"` field is crucial. Without it, Node.js treats files as CommonJS instead of ES modules, causing errors like `"This package is ESM only but it was tried to load by require"`.

### vite.config.ts Requirements

TanStack Start needs a Vite config that wires in the Start plugin and Nitro. A minimal working config is:

```typescript
import { defineConfig } from "vite";
import { nitro } from "nitro/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";

export default defineConfig({
  server: {
    port: 3000,
  },
  plugins: [
    tsConfigPaths(),
    tanstackStart(),
    nitro(),
    viteReact(),
  ],
  nitro: {},
});
```

Nitro is the server engine for TanStack Start. The default Node preset works with haloy, so an empty `nitro: {}` config is sufficient.

### Build Output

TanStack Start uses Nitro as its server engine. The build output goes to `.output/` directory:
- `.output/server/index.mjs` - Server entry point
- `.output/public/` - Static assets

## Dockerfile

**Note:** Verify current Node.js version in `references/base-images.md` before using. The examples below use Node 24 (LTS) but check for the latest stable version.

```dockerfile
FROM node:24-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
COPY . /app
WORKDIR /app

FROM base AS prod-deps
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile

FROM base AS build
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN pnpm run build

FROM base
COPY --from=prod-deps /app/node_modules /app/node_modules
COPY --from=build /app/.output /app/.output

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["pnpm", "start"]
```

If the app listens on a port other than 3000, update the HEALTHCHECK URL to match the actual port.

### Dockerfile Explanation

1. **Base stage**: Sets up pnpm via corepack (Node 24 includes corepack)
2. **prod-deps stage**: Installs only production dependencies with cache mount
3. **build stage**: Full install and build
4. **Final stage**: Combines production deps with build output

### Package Manager Variations

For npm projects, replace pnpm commands:
```dockerfile
FROM node:24-slim AS base
COPY . /app
WORKDIR /app

FROM base AS prod-deps
RUN npm ci --omit=dev

FROM base AS build
RUN npm ci
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

FROM base
COPY --from=prod-deps /app/node_modules /app/node_modules
COPY --from=build /app/.output /app/.output

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["npm", "start"]
```

## Health Check Route

TanStack Start apps should include a health check route at `src/routes/health.tsx`:

```tsx
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/health")({
  server: {
    handlers: {
      GET: async () => {
        return Response.json({ status: "ok" });
      },
    },
  },
});
```

This endpoint responds without querying the database, ensuring the container can be marked healthy quickly.

## .dockerignore

```
node_modules
.git
.gitignore
*.md
.output
.vinxi
.DS_Store
.env
.env.*
```

## haloy.yaml Configuration

To create a `haloy.yaml` configuration file for your TanStack Start app, either:
- Run the `/haloy-config` skill for guided configuration generation
- Check the [haloy documentation](https://haloy.dev/docs) for configuration options

## Database Connection Pattern

When using PostgreSQL with haloy, the database hostname changes between environments:

```typescript
// src/db/database-url.ts
export function getDatabaseUrl() {
  const postgresUser = process.env.POSTGRES_USER;
  if (!postgresUser) {
    throw new Error("POSTGRES_USER environment variable not found");
  }

  const postgresPassword = process.env.POSTGRES_PASSWORD;
  if (!postgresPassword) {
    throw new Error("POSTGRES_PASSWORD environment variable not found");
  }

  const postgresDb = process.env.POSTGRES_DB;
  if (!postgresDb) {
    throw new Error("POSTGRES_DB environment variable not found");
  }

  // In production, use the service name 'postgres' as the host
  // In development, connect to localhost
  const host = process.env.NODE_ENV === "production" ? "postgres" : "localhost";

  return `postgres://${postgresUser}:${postgresPassword}@${host}:5432/${postgresDb}`;
}
```

## Deployment Steps

1. Deploy the database first (if using one):
   ```bash
   haloy deploy -t postgres
   ```

2. Push database schema via tunnel:
   ```bash
   # Terminal 1
   haloy tunnel 5432 -t postgres

   # Terminal 2
   pnpm db:push
   ```

3. Deploy the application:
   ```bash
   haloy deploy -t app
   ```
