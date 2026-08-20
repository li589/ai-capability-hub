# Request-Response Hooks

This reference captures the HTTP request lifecycle hooks described in Litestar's lifecycle-hooks documentation.

## Hook Stages

- `before_request`: runs immediately before the route handler function is called.
- `after_request`: runs after the route handler returns and the response object has been resolved.
- `after_response`: runs after the response has been returned by the server.

## `before_request`

Contract:

- First parameter is `Request`.
- Return `None` to continue normally.
- Return any response-compatible value to bypass the route handler.

Typical uses:

- Populate `request.state` for downstream handler use.
- Enforce lightweight transport-level gates.
- Return an early response when request conditions fail.

Design notes:

- Treat a non-`None` return as a real control-flow branch, not a convenience shortcut.
- Keep short-circuit responses consistent with the API's error contract.
- Prefer handler or dependency validation when the logic is really endpoint-specific rather than cross-cutting.

## `after_request`

Contract:

- First parameter is `Response`.
- Must return a `Response`.

Typical uses:

- Add or normalize headers.
- Wrap or transform text/content responses into a different response shape.
- Apply response-object adjustments after handler execution.

Design notes:

- You may return the same response or a replacement response.
- Keep response replacement deliberate because it changes the handler's outward contract.
- If the concern is lower-level ASGI message mutation instead of response-object handling, move to middleware or `before_send` in app setup.

## `after_response`

Contract:

- First parameter is `Request`.
- Returns `None`.

Typical uses:

- Increment counters.
- Emit audit or analytics side effects.
- Notify third-party systems after the client response is already complete.

Design notes:

- The response is already sent, so current-response mutation is impossible.
- Use it for post-processing only.
- Failures here should be observable, but the hook should not assume it can recover the user-facing response.

## Layered Precedence

- Hooks can be declared on the application, router, controller, and handler layers.
- If the same hook exists on multiple layers, the closest layer to the handler wins.
- This is override precedence, not composition.

Implication:

- Do not split one concern across multiple layers expecting all hook implementations to execute.
- Put the authoritative hook at the narrowest layer that should own the behavior.

## Testing Focus

- Test at least one request that follows normal flow.
- Test at least one request that short-circuits in `before_request`.
- Test that `after_request` returns the expected response object shape.
- Test that `after_response` side effects happen after the response and do not leak into the returned payload.
- Test layer overrides explicitly when app/router/controller/handler combinations are involved.
