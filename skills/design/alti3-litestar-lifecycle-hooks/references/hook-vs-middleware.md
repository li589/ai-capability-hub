# Hook vs Middleware

Use this reference when deciding whether the concern belongs in Litestar lifecycle hooks or middleware.

## Prefer Lifecycle Hooks When

- You need a `Request` or `Response` object, not raw ASGI `scope/receive/send`.
- The concern is tied to handler execution timing such as pre-handler gating, post-handler response mutation, or post-send side effects.
- The work is lightweight and HTTP-handler focused.
- You want a layered override where the closest handler layer wins.

## Prefer Middleware When

- You need raw ASGI wrapping around the application pipeline.
- The concern must apply across broader route sets as a formal wrapper.
- You need built-in middleware capabilities such as CORS, CSRF, compression, sessions, rate limiting, or allowed hosts.
- The behavior must account for more than handler response-object mutation.
- The concern may need `http`, `websocket`, or `lifespan` scope awareness.

## Exception and Routing Boundary Notes

- Middleware still applies to responses produced by exception handlers for route-handler or dependency exceptions.
- Litestar router-generated `NotFoundException` and `MethodNotAllowedException` occur before the middleware stack is called.
- Lifecycle hooks are even narrower than middleware: if no route handler lifecycle is reached, hook logic will not run.

## Practical Heuristics

- Need to short-circuit based on `Request` data before the handler? Use `before_request`.
- Need to replace or mutate the resolved `Response`? Use `after_request`.
- Need metrics or external notifications after send? Use `after_response`.
- Need to wrap every matching request as ASGI flow, choose order, or use a built-in wrapper? Use middleware.
- Need `before_send`, `after_exception`, or app construction interception? Use `litestar-app-setup`, not this skill.

## Smell Checks

- If the code is reaching for `scope`, `receive`, or `send`, it is probably middleware.
- If the code only cares about `Request` or `Response`, hooks are usually the simpler fit.
- If the concern is startup/shutdown or lifespan ownership, neither hooks nor middleware is the right first tool.
