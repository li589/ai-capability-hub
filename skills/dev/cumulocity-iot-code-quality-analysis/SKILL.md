---
name: code-quality-analysis
description: |
  Analyze Angular / Cumulocity Web SDK code for anti-patterns, bugs, and quality issues.
  Use when reviewing components, services, or modules for code quality, maintainability,
  performance, and correctness. Covers TypeScript best practices, Angular idioms, C8Y SDK
  usage patterns, and project-specific conventions. Triggers: code review, anti-pattern,
  quality check, refactor suggestion, style guide, bug analysis.
version: 1.0.0
category: code-quality
triggers:
  - code review
  - anti-pattern
  - quality
  - refactor
  - analyze code
  - code smell
  - best practices
  - bug analysis
  - style guide
tags:
  - angular
  - typescript
  - cumulocity
  - code-quality
  - anti-patterns
install_source: official
install_method: download
skill_id: official_rXL8Nurn
enabled_at: 1787231776554
name_zh: 代码分析
---

# Code Quality Analysis Skill

## Overview

This skill performs comprehensive code quality analysis on Angular + Cumulocity Web SDK
codebases. It combines guidance from:

1. **TypeScript best practices** — load the `mastering-typescript` skill (from https://github.com/SpillwaveSolutions/mastering-typescript-skill/tree/main/mastering-typescript)
2. **Angular documentation** — fetch `https://angular.dev/assets/context/llms-full.txt`
3. **Cumulocity Codex** — use the `mcp_c8y-docs_*` MCP tools to retrieve component and API references

---

## How to Run an Analysis

### Step 1 — Gather Reference Material

Before analyzing any file, load the following resources in parallel:

1. Read [`skills/mastering-typescript/SKILL.md`](https://github.com/SpillwaveSolutions/mastering-typescript-skill/tree/main/mastering-typescript)
2. Fetch `https://angular.dev/assets/context/llms-full.txt` (use the `fetch_webpage` tool)
3. Call `mcp_c8y-docs_get-codex-structure` to get the full Codex map
4. Call `mcp_c8y-docs_query-codex` with queries relevant to the features used in the
   file under review (e.g. `["css utility classes spacing", "color tokens", "widgets lazy loading"]`)
5. Read `skills/c8y-client-api/SKILL.md` for C8Y SDK usage validation

### Step 2 — Identify Files to Analyze

If no specific file was provided, search for:
- All `*.component.ts` files
- All `*.service.ts` files  
- All `*.module.ts` files
- All `*.component.html` files

### Step 3 — Analyze Each File

Run each check below against the target file(s). For every finding:

- State the **file path and line number**
- State which **anti-pattern** was found
- Show the **problematic snippet**
- Provide a **corrected / recommended** version

---

## Anti-Patterns Catalogue

### AP-01 · `*ngIf` instead of `@if` (Angular Control Flow)

**Rule:** Never use the structural directive `*ngIf`. Use the built-in `@if / @else` block
syntax introduced in Angular 17+.

**Also applies to:** `*ngFor` → `@for`, `*ngSwitch` → `@switch`.

```html
<!-- BAD -->
<div *ngIf="loading">Loading…</div>
<li *ngFor="let item of items">{{ item.name }}</li>

<!-- GOOD -->
@if (loading) {
  <div>Loading…</div>
}
@for (item of items; track item.id) {
  <li>{{ item.name }}</li>
}
```

---

### AP-02 · Too Much Logic Inside Components

**Rule:** Components are responsible for the *view* only. Business logic, data
transformation, and orchestration belong in dedicated services.

**Signals of violation:**
- Methods longer than ~20 lines inside a component
- Complex data mapping or aggregation inside a component
- Direct HTTP/SDK calls made from inside a component class (not delegated to a service)
- Multiple levels of nested async/await inside lifecycle hooks

**Refactor pattern:** Extract logic into an `@Injectable()` service. The component calls
the service and binds the result.

---

### AP-03 · Using `any` Everywhere

**Rule:** Explicit `any` is forbidden except at genuine boundaries (e.g. 3rd-party library
interop with no types). Prefer `unknown`, proper interfaces, or generic type parameters.

**Detection:**
- Property typed as `: any`
- Cast with `as any`
- Function parameter typed `: any`

**Fix examples:**
```typescript
// BAD
function process(data: any): any { … }

// GOOD
function process<T extends Record<string, unknown>>(data: T): ProcessedResult { … }
```

Cross-reference the **mastering-typescript** skill (section "Type Guards and Narrowing") for
patterns that eliminate the need for `any`.

---

### AP-04 · Ignoring OnPush Change Detection

**Rule:** Every component that does not mutate shared mutable state should use
`ChangeDetectionStrategy.OnPush`. Default change detection causes unnecessary re-renders
across the entire component tree.

```typescript
// BAD
@Component({ selector: 'app-sensor', templateUrl: '…' })
export class SensorComponent { … }

// GOOD
@Component({
  selector: 'app-sensor',
  templateUrl: '…',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SensorComponent { … }
```

**Note:** With `OnPush`, use `async` pipe or `markForCheck()` / signals to trigger updates.

---

### AP-05 · Missing `trackBy` / `track` in Loops

**Rule:** Every `@for` loop (or legacy `*ngFor`) that renders a list of objects **must**
specify a track expression so Angular can diff items by identity rather than re-rendering
the entire list.

```html
<!-- BAD -->
@for (sensor of sensors) {
  <app-sensor [sensor]="sensor" />
}

<!-- GOOD -->
@for (sensor of sensors; track sensor.id) {
  <app-sensor [sensor]="sensor" />
}
```

---

### AP-06 · Non-Standalone Components (NgModule / `standalone: false`)

**Rule:** All newly created components, directives, and pipes must be standalone
(`standalone: true`). Do not create new NgModules for features. Existing NgModules can
be kept only when wrapping third-party code that requires it. `standalone: false` should
never appear in new code.

```typescript
// BAD
@Component({ selector: 'app-foo', templateUrl: '…', standalone: false })
export class FooComponent { … }

// GOOD
@Component({ selector: 'app-foo', templateUrl: '…', standalone: true, imports: [CommonModule] })
export class FooComponent { … }
```

---

### AP-07 · Overusing RxJS When a Simple Value Works

**Rule:** Do not create an `Observable` or `Subject` just to hold a synchronous or
non-reactive value. Use plain variables, `signal()`, or `computed()` instead.

**Signals of violation:**
- `BehaviorSubject<boolean>(false)` used as a simple flag with no subscribers outside
  the same class
- `Subject` that is immediately `.next()`-ed once and never reused
- Wrapping a one-shot `Promise` result in an `Observable` without a good reason

```typescript
// BAD — isLoading is never observed reactively outside this class
private isLoading$ = new BehaviorSubject<boolean>(false);

// GOOD
isLoading = signal(false);
```

---

### AP-08 · Heavy Logic / Method Calls in Templates

**Rule:** Angular templates re-evaluate every expression on each change-detection cycle.
Method calls in templates are called every cycle, even if their inputs have not changed.

**Signals of violation:**
- `{{ formatDate(item.timestamp) }}` — function call in interpolation
- `[class]="getClass(item)"` — function call in binding
- `*ngIf="shouldShow(item)"` / `@if (shouldShow(item))` — function call in condition

**Fix:** Move transformation logic to a **pure Pipe** or pre-compute in the component
class (e.g. derived `signal()` or `computed()`).

```typescript
// BAD (template): {{ formatValue(measurement) }}

// GOOD — create a pipe
@Pipe({ name: 'formatValue', pure: true, standalone: true })
export class FormatValuePipe implements PipeTransform {
  transform(measurement: IMeasurement): string { … }
}
```

---

### AP-09 · Subscribing Without Unsubscribing

**Rule:** Any `Observable.subscribe()` call made inside a component or service that is
not `providedIn: 'root'` must be cleaned up to avoid memory leaks.

**Preferred patterns (in order):**
1. Use the `async` pipe in the template — Angular unsubscribes automatically
2. Use `takeUntilDestroyed(this.destroyRef)` (Angular 16+)
3. Collect in a `Subscription` and call `subscription.unsubscribe()` in `ngOnDestroy`

```typescript
// BAD
ngOnInit(): void {
  this.service.data$.subscribe(d => this.data = d);
}

// GOOD
private destroyRef = inject(DestroyRef);

ngOnInit(): void {
  this.service.data$
    .pipe(takeUntilDestroyed(this.destroyRef))
    .subscribe(d => this.data = d);
}
```

---

### AP-10 · Using `FetchClient` for Calls Covered by `@c8y/client`

**Rule:** Never use Angular's `HttpClient` or `FetchClient` for Cumulocity REST API calls
that are already wrapped by a service in `@c8y/client`. Only ok if used for microservice queries (baseUrl contains `/service`).

Consult the `c8y-client-api` skill (`skills/c8y-client-api/SKILL.md`) for the full list
of covered domains: inventory, alarms, events, measurements, operations, binary, users, …

```typescript
// BAD — HttpClient used for inventory
constructor(private http: HttpClient) {}
getDevice(id: string) {
  return this.http.get(`/inventory/managedObjects/${id}`);
}

// GOOD — use the typed SDK service
constructor(private inventory: InventoryService) {}
async getDevice(id: string) {
  const { data } = await this.inventory.detail(id);
  return data;
}
```

**Exception:** Raw HTTP is acceptable only for external APIs or endpoints not covered by
`@c8y/client`.

---

### AP-11 · Eager-Loading Widget / Plugin Modules

**Rule:** Widget plugin modules that are registered via the C8Y hook mechanism must use
**lazy loading** so they are only downloaded when needed. Implies configuring components as standalone: true.

- Use `loadComponent` instead of `component`
- Use `loadConfigComponent` instead of `configComponent`

```typescript
// BAD
{
  component: MyWidgetComponent,
  configComponent: MyWidgetConfigComponent,
}

// GOOD
{
  loadComponent: () => import('./my-widget/my-widget.component').then(m => m.MyWidgetComponent),
  loadConfigComponent: () => import('./my-widget/my-widget-config.component').then(m => m.MyWidgetConfigComponent),
}
```

---

### AP-12 · Heavy Custom Styles / Hard-Coded Colors

**Rule:** Do not introduce custom CSS/LESS rules for spacing, typography, or color when
the Cumulocity Design System already provides utility classes or CSS custom properties.
Hard-coded hex/rgb color values break tenant branding.

**Action:** Before writing any custom style, query the Codex:
```
mcp_c8y-docs_query-codex(["css utility classes spacing padding margin", "color tokens design system", "typography font size"])
```

**Signals of violation:**
- Inline styles in templates
- LESS rules that set `margin`, `padding`, or `font-size` with raw pixel values when a
  utility class exists
- Hard-coded hex/rgb/hsl color values (e.g. `color: #1776BF`, `background: rgb(23,118,191)`)
- Overriding `--c8y-*` design tokens with fixed values

**Fix:** Use the Cumulocity utility classes (`m-t-8`, `p-l-16`, `text-muted`, etc.) or
CSS custom properties (`var(--c8y-brand-primary)`) documented in the Codex.

---

### AP-13 · Repetitive Code — Missing Utilities or Shared Components

**Rule:** If the same logical block or template pattern appears more than twice across
different files, extract it into:
- A shared **util service** (for logic)
- A shared **component** in `src/modules/shared/` (for templates)
- A shared **pure pipe** (for value transformations)

**Signals of violation:**
- The same `filter + map` chain repeated in multiple services
- Copy-pasted loading-state or error-handling boilerplate across components
- Identical table/list template fragments in more than one component

---

### AP-14 · Model Interfaces Defined Inside Components

**Rule:** Do not define TypeScript interfaces or types inside a component, directive, or
service file if those types are also used by other files. Define them in a dedicated
model file (e.g. `src/models/sensor.model.ts` or adjacent `*.model.ts`).

```typescript
// BAD — inside sensor-list.component.ts
export interface SensorFilter { type: string; active: boolean; }

// GOOD — src/models/sensor-filter.model.ts
export interface SensorFilter { type: string; active: boolean; }
```

---

### AP-15 · Every Service Decorated with `providedIn: 'root'`

**Rule:** Only services that genuinely need application-wide singleton state should use
`providedIn: 'root'`. If a service is tightly coupled to a single component (e.g. it
holds local UI state), remove `providedIn` and provide it in the component's `providers`
array instead — this also ensures it is destroyed along with the component.

```typescript
// BAD — global singleton for a component-local concern
@Injectable({ providedIn: 'root' })
export class SensorTableStateService { … }

// GOOD — provided by the component that owns it
@Injectable()
export class SensorTableStateService { … }

@Component({
  …
  providers: [SensorTableStateService],
})
export class SensorTableComponent { … }
```

---

### AP-16 · Long Async Tasks Inside Components

**Rule:** Components are tied to the Angular view lifecycle and can be destroyed at any
time. Do not perform long-running async operations (polling loops, large data fetches,
chained network requests) directly inside a component.

**Fix:** Delegate long-running work to a root-level service that is not bound to a
component's lifetime. The component subscribes to the service's output observable or
signal and unsubscribes cleanly on destroy (see AP-09).

```typescript
// BAD — long poll inside a component
ngOnInit(): void {
  this.pollFirmwareStatus(); // may run forever if component is destroyed mid-flight
}

// GOOD — root service drives the async work
@Injectable({ providedIn: 'root' })
export class FirmwareStatusService {
  readonly status$ = timer(0, 5000).pipe(
    switchMap(() => this.fetchStatus()),
    shareReplay(1),
  );
}
```

---

### AP-17 · Untyped / Unguarded Access to `IManagedObject` Extra Attributes

**Rule:** `IManagedObject` is a generic model with an open index signature (`[key: string]: any`).
Any fragment or custom attribute on are not guaranteed to be present or correctly shaped at
runtime. Every access to a non-standard `IManagedObject` property **must** be guarded with a
type predicate function or a Zod schema so that the code is both type-safe and validated at
runtime.

Reference: https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates

**Signals of violation:**
- Direct property access without narrowing: `device['c8y_Hardware'].serialNumber`
- Cast with `as MyDeviceType` without runtime validation
- Optional-chaining without a type guard when the shape is non-trivial: `(obj as any)?.nested?.prop`

**Fix — Type Predicate:**
```typescript
// BAD
function getSerialNumber(mo: IManagedObject): string {
  return mo['c8y_Hardware'].serialNumber; // no guarantee the fragment or field exists
}

// GOOD — define the expected shape and a type predicate
interface C8yHardware {
  model: string;
  revision: string;
  serialNumber: string;
}

interface DeviceWithHardware extends IManagedObject {
  c8y_Hardware: C8yHardware;
}

function hasHardwareInfo(mo: IManagedObject): mo is DeviceWithHardware {
  const hw = (mo as DeviceWithHardware).c8y_Hardware;
  return (
    typeof hw === 'object' &&
    hw !== null &&
    typeof hw.serialNumber === 'string'
  );
}

// Usage
if (hasHardwareInfo(device)) {
  // device.c8y_Hardware is now fully typed and validated
  return device.c8y_Hardware.serialNumber;
}
```

**Fix — Zod Schema (preferred for complex/nested shapes):**
```typescript
import { z } from 'zod';

const C8yHardwareSchema = z.object({
  model: z.string(),
  revision: z.string(),
  serialNumber: z.string(),
});

// Parse at the boundary (e.g. when receiving the MO from the API)
const parseHardwareInfo = (mo: IManagedObject) => C8yHardwareSchema.safeParse(mo['c8y_Hardware']);

const result = parseHardwareInfo(device);
if (result.success) {
  const { model, revision, serialNumber } = result.data; // fully typed
}
```

Cross-reference the **mastering-typescript** skill (section "Zod Validation") for
schema composition patterns.

---

### AP-18 · Missing Localization (`| translate`)

**Rule:** Every user-visible string in a template **must** be piped through `| translate`
so it can be localized via the `.po` translation files. Hard-coded English strings in
templates are not translatable and will break non-English deployments.

**Also applies to:**
- Strings passed to `AlertService`, `ModalService`, toast notifications, etc. — use
  `TranslateService.instant()` or pass keys.
- Dynamic strings assembled in TypeScript — construct the string key and translate it,
  do not concatenate translated fragments.

**Signals of violation:**
- `<span>Loading…</span>` — no `| translate`
- `[placeholder]="'Enter a value'"` — hard-coded string in binding
- `title="Device details"` — hard-coded HTML attribute
- `this.alertService.add({ text: 'Saved successfully' })` — un-translated string

**Fix:**
```html
<!-- BAD -->
<button>Save</button>
<span>No devices found.</span>

<!-- GOOD -->
<button>{{ 'Save' | translate }}</button>
<span>{{ 'No devices found.' | translate }}</span>
```

```typescript
// BAD
this.alert.add({ text: 'Operation failed', type: 'danger' });

// GOOD
this.alert.add({ text: this.translate.instant('Operation failed'), type: 'danger' });
```

**After adding a new key, add translations to every `.po` file** in `src/locales/`
(`de.po`, `fr.po`, `es.po`, `it.po`, `ja_JP.po`, `ko.po`, `pt_BR.po`, `ru.po`, `zh_CN.po`).
At minimum, copy the English string as a placeholder so the build does not produce
empty translation entries.

---

### AP-19 · Secrets, Credentials, and Tenant URLs Committed to Source Control

**Severity: High (Security)**

**Rule:** No passwords, API keys, bearer tokens, or tenant-specific URLs must ever be
committed to source control. This includes:

- Passwords or tokens in `package.json` scripts (e.g. `--user admin:password`)
- Tenant URLs hard-coded in `package.json` proxy/server configs (e.g. `https://mytenant.cumulocity.com`)
- API keys or secrets in any `*.ts`, `*.json`, or `*.env` file that is tracked by git
- `.env` files containing real credentials that are not in `.gitignore`

**Signals of violation:**
- `package.json` `scripts` containing `--user`, `--password`, `--bearer`, or credential-looking strings
- `package.json` devProxy / c8ycli server config with a hard-coded `https://<tenant>.cumulocity.com` URL (tenant-specific; should live in a local env file)
- Any `*.env` or `.env.*` file tracked by git that contains non-example values
- Secrets or tokens in comments (`// token: eyJhbGc…`)

**Fix:**
```jsonc
// BAD — package.json
{
  "scripts": {
    "start": "c8ycli server --user admin:mypassword123 https://mytenant.eu-latest.cumulocity.com"
  }
}

// GOOD — package.json references an env var or local config file
{
  "scripts": {
    "start": "c8ycli server"  // tenant + credentials read from .env (gitignored)
  }
}
```

```bash
# .gitignore — ensure these are always excluded
.env
.env.local
.env.*.local
*.credentials.json
```

**Action items when this pattern is found:**
1. Remove the secret from the file immediately.
2. Add the relevant file pattern to `.gitignore`.
3. Rotate any credential that was committed (assume it is compromised).
4. Use environment variables or a local-only `.env` file (excluded from git) for
   tenant URLs and credentials.

---

### AP-20 · Using Deprecated `HOOK_*` Injection Tokens Instead of Hook Functions

**Rule:** The uppercase `HOOK_*` injection token pattern (e.g. `HOOK_TABS`, `HOOK_ROUTE`,
`HOOK_ACTION_BAR`, `HOOK_COMPONENTS`) is deprecated. Use the equivalent **hook function**
from `@c8y/ngx-components` instead. Hook functions are tree-shakeable, produce cleaner
provider arrays, and are the officially supported API going forward.

**Also applies to:** Using `hookComponent` to register a **widget** — widgets must use
`hookWidget` instead. This distinction matters because `hookWidget` registers the
component in the widget gallery and wires up additional widget-specific configuration.

**Mapping:**

| Deprecated token | Replacement function | Import path |
|---|---|---|
| `HOOK_TABS` | `hookTab` | `@c8y/ngx-components` |
| `HOOK_ROUTE` | `hookRoute` | `@c8y/ngx-components` |
| `HOOK_ACTION_BAR` | `hookActionBar` | `@c8y/ngx-components` |
| `HOOK_COMPONENTS` | `hookWidget` | `@c8y/ngx-components` |
| `hookComponent({…})` for a widget | `hookWidget({…})` | `@c8y/ngx-components` |

**Note:** Custom project-level `InjectionToken`s named `HOOK_*` (defined with `new InjectionToken(…)`) are not affected — only tokens imported from `@c8y/ngx-components`.

```typescript
// BAD — deprecated token-based pattern
import { HOOK_TABS, HOOK_ACTION_BAR } from '@c8y/ngx-components';

providers: [
  { provide: HOOK_TABS, useClass: MyTabFactory, multi: true },
  { provide: HOOK_ACTION_BAR, useClass: MyActionFactory, multi: true },
]

// GOOD — hook function pattern
import { hookTab, hookActionBar } from '@c8y/ngx-components';

providers: [
  hookTab(MyTabFactory),
  hookActionBar(MyActionFactory),
]
```

```typescript
// BAD — hookComponent used for a widget registration
import { hookComponent } from '@c8y/ngx-components';

providers: [
  hookComponent({
    id: 'my-widget',
    label: 'My Widget',
    component: MyWidgetComponent,
  }),
]

// GOOD — hookWidget for widget gallery registration
import { hookWidget } from '@c8y/ngx-components';

providers: [
  hookWidget({
    id: 'my-widget',
    label: 'My Widget',
    component: MyWidgetComponent,
  }),
]
```

---

### AP-21 · Public Methods and Properties Not Used in Templates

**Rule:** Every `public` method or property on a component must be referenced in its
template (HTML). All other methods/properties must be `private` (or `protected`
if used by subclasses).

**Signals of violation:**
- `public method(): void { … }` that is never called in the template
- `public isLoading = false;` that is never read in the template (should be `private`)
- Helper methods visible as `public` because they were not explicitly marked `private`

**Detection strategy:**
- Search the template (`.component.html`) for references to each method/property name
- If not found, the method/property should be `private`
- Use IDE symbol search to verify; if the IDE shows zero template references, mark it `private`

```typescript
// BAD — public method never called from the template
@Component({ … })
export class SensorComponent {
  public title = 'Sensors';
  public formatValue(val: number): string { return val.toFixed(2); }  // template uses the pipe instead
  public calculateThreshold(): number { … }  // internal logic, not in template
}

// GOOD — only public if used in template; otherwise private
@Component({ … })
export class SensorComponent {
  public title = 'Sensors';  // referenced in template: {{ title }}
  private formatValue(val: number): string { … }  // not in template; use a pipe instead or call from a template-bound method
  private calculateThreshold(): number { … }  // internal helper, never called from template
  
  // Template-bound event handler — public because it's called from template (click)="onUpdate()"
  public onUpdate(): void { … }
}
```

```html
<!-- Corresponding template -->
<h1>{{ title }}</h1>
<button (click)="onUpdate()">Update</button>
```

**Refactoring guide:**

1. **Method called from template** (event handler, `| async`, interpolation) → keep `public`
2. **Method used only internally by other methods** → mark `private`
3. **Property bound in template** (interpolation, property binding) → keep `public`
4. **Property for internal state** (not in template) → mark `private`

---

### AP-22 · Overriding Private APIs from @c8y/ngx-components

**Severity: High (Technical Debt)**

**Rule:** Do not access or override private methods, properties, or internal APIs from
`@c8y/ngx-components`, `@c8y/client`, or any other third-party library. Private APIs are
not guaranteed to remain stable across patch versions and can break your code without
notice.

**Exception:** If extending a component or service from `@c8y/ngx-components` genuinely
requires accessing a private member, this is **only acceptable as a last resort** when:
- The public API does not provide a way to achieve the requirement
- An issue has been filed with Cumulocity requesting the feature as public
- The override is clearly documented with `// TODO:` and `assert()` to detect
  future breakage

**Signals of violation:**
- Accessing a property prefixed with `_` (e.g. `this._internalState`, `component._cache`)
- Calling methods that are not documented in the public API
- Casting to `any` to bypass TypeScript's access checks for private members
- Using `Object.defineProperty()` or reflection to access/modify private state
- Overriding a `private` or `protected` method from a parent class without documented justification

**Code patterns to avoid:**
```typescript
// BAD — accessing private property
export class MyDetailsComponent extends DetailsComponent {
  ngOnInit(): void {
    this._internalData = { … };  // DetailsComponent._internalData is private
  }
}

// BAD — casting to any to bypass type safety
const cache = (this.service as any)._cache;  // _cache is private

// BAD — no documentation about fragility
export class MyComponent extends BaseTabsComponent {
  override protected getSelectedTabIndex(): number {
    return this._selectedIndex;  // relying on internal property
  }
}
```

**Correct pattern — document, assert, and plan to remove:**

```typescript
export class MyDetailsComponent extends DetailsComponent {
  // TODO: Extract this logic to public API in @c8y/ngx-components
  // Issue: https://github.com/SoftwareAG/cumulocity-app-builder/issues/XXXXX
  // Risk: This overrides private method '_initializeForm()'. Patch upgrades may break this.
  override protected _initializeForm(): void {
    super._initializeForm();
    
    // Assert that the internal structure hasn't changed
    console.assert(
      typeof (this as any)._formBuilder === 'function',
      'Expected private _formBuilder method to exist on DetailsComponent'
    );
    
    // Custom initialization
    this._applyCustomValidation();
  }

  private _applyCustomValidation(): void { … }
}
```

**Why this matters:**

1. **Fragility:** Private APIs can change in any version (major, minor, or patch) without
   backward-compatibility guarantees. Your code becomes brittle across upgrades.
2. **Maintenance burden:** Every time `@c8y/ngx-components` is upgraded, the team must
   review and test overridden private methods to ensure they still work.
3. **Technical debt:** Overriding private APIs is a sign that the library's public API is
   insufficient; this should be escalated as a feature request rather than worked around.
4. **Coupling:** Tight coupling to implementation details makes refactoring the library
   difficult and ties down future development.

**Action items:**

1. **File an issue** with Cumulocity requesting the required feature as part of the
   public API, including use case and version context.
2. **Document the override** with a `// TODO:` comment including:
   - The reason for the override
   - Link to the feature request issue
   - Warning about upgrade risk
3. **Add runtime assertions** (like `console.assert()`) to catch breaking changes early
4. **Plan a removal strategy** — track when the public API is added, then remove the
   override in the next major version bump

**Checking for violations:**

- Search for property/method names starting with `_` (underscore)
- Look for `as any` casts combined with property access
- Check for `Object.defineProperty()`, `Object.getOwnPropertyDescriptor()`, or reflection APIs
- Review `override` keywords on `protected` or `private` methods in extended classes

---

## Output Format

For each file analyzed, produce a structured report:

```
## Analysis: <file path>

### Summary
<one-paragraph summary>

### Findings

| # | Anti-Pattern | Severity | Line(s) |
|---|---|---|---|
| 1 | AP-06 Non-Standalone Component | High | 12 |
| 2 | AP-09 Missing Unsubscribe | Medium | 45–52 |

### Details

#### Finding 1 — AP-06 Non-Standalone Component (line 12)
**Code:**
```ts
// problematic snippet
```
**Recommendation:**
```ts
// fixed snippet
```
```

### Severity Levels
- **High** — likely bug, memory leak, or security concern
- **Medium** — maintainability or performance problem
- **Low** — style / convention violation

---

## Contextual Cross-References

When the analysis involves:
- **TypeScript types / generics** → consult [mastering-typescript](https://github.com/SpillwaveSolutions/mastering-typescript-skill/tree/main/mastering-typescript)
- **Angular lifecycle / control flow / change detection** → fetch `https://angular.dev/assets/context/llms-full.txt`
- **Angular style guide and conventions** → reference the version-specific style guide: `https://vMAJOR.angular.dev/style-guide` (e.g., `https://v20.angular.dev/style-guide` for Angular 20, `https://v19.angular.dev/style-guide` for Angular 19, or `https://angular.dev/style-guide` for the latest version)
- **CSS utilities, design tokens, component APIs** → call `mcp_c8y-docs_query-codex` with relevant keywords
- **C8Y REST API wrappers** → consult `skills/c8y-client-api/SKILL.md`
