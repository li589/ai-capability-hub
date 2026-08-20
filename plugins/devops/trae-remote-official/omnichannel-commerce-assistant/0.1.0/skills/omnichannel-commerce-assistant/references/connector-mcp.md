# Optional connectors and MCP

Load this reference only when the user explicitly asks about direct platform access, connectors, MCP, or automatic retrieval.

## Default behavior

- Treat every connector as optional and unavailable until it is visible in the runtime.
- Prefer read-only retrieval.
- Ask which account, store, marketplace/site, date range, and dataset are in scope.
- Request only the permissions required for the stated decision.
- Never claim that an account is connected or data was retrieved without visible evidence.

## Fastest path

1. Use an existing approved connector if it exposes the required read operation.
2. Otherwise continue with public evidence or labeled uncertainty. Mention a platform export, spreadsheet, screenshot, or authorized browser inspection as an optional next step without interrupting the task.
3. Discuss custom MCP/API setup only for recurring retrieval or advanced integration needs.

Do not make connector setup a prerequisite for a one-off diagnosis that a CSV/XLSX export can support.

## Safety

Keep credentials out of chat and files. Do not ask users to paste secrets. Do not mutate listings, prices, ads, orders, messages, inventory, or account settings without explicit authorization and a supported runtime action.

Read `connector-platforms.md` only when the user asks to configure a named platform connection.
