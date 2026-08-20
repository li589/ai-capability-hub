# Context Mapping Examples

## Example 1: React + Next.js Project

### Task: "Add a settings page to the existing app"

### Step 1: Repo Map

```
REPO MAP — my-saas-app
───────────────────────
Stack: TypeScript, Next.js 14, React 18, shadcn/ui, Tailwind CSS
Entry: src/app/layout.tsx
Structure:
  src/app/
    (dashboard)/    — Protected dashboard routes (3 pages)
    (auth)/         — Login/Register pages
    api/            — API routes (5 files)
    layout.tsx      — Root layout with providers
  src/components/
    ui/             — shadcn/ui primitives (Button, Input, Card, etc.)
    layout/         — Header, Sidebar, Footer
    forms/          — Shared form components
  src/lib/
    utils.ts        — cn() helper, formatDate, etc.
    auth.ts         — Auth utilities
    db.ts           — Prisma client
  src/hooks/        — Custom React hooks (3 files)
Key configs: package.json, tsconfig.json, tailwind.config.ts, components.json
Relevant to task: src/app/(dashboard)/, src/components/ui/, src/components/layout/
```

### Step 2: Targeted Reading Plan

```
Files to read (in priority order):
1. src/app/(dashboard)/layout.tsx     — Understand dashboard layout structure
2. src/components/layout/Sidebar.tsx  — Where to add settings nav link
3. src/components/ui/ (index)         — Available shadcn components
4. src/app/layout.tsx                 — Root layout providers
5. package.json                       — Confirm dependencies
```

### Step 3: Context Ledger After Reading

```
CONTEXT LEDGER — Task: Add settings page
────────────────────────────────────────
File                                | Purpose              | Key Facts                          | Relevance
────────────────────────────────────┼──────────────────────┼────────────────────────────────────┼──────────
src/app/(dashboard)/layout.tsx      | Dashboard wrapper    | Has Sidebar + main content area    | HIGH
src/components/layout/Sidebar.tsx   | Navigation           | Uses NavLink component, items[]    | HIGH
src/components/ui/button.tsx        | UI primitive         | shadcn Button with variants        | MEDIUM
src/components/ui/input.tsx         | UI primitive         | shadcn Input                       | MEDIUM
src/components/ui/card.tsx          | UI primitive         | Card, CardHeader, CardContent      | MEDIUM
src/components/ui/select.tsx        | UI primitive         | shadcn Select component            | MEDIUM
src/app/layout.tsx                  | Root layout          | ThemeProvider, AuthProvider        | MEDIUM
package.json                        | Dependencies         | Next 14.1, React 18.2, shadcn     | HIGH
src/lib/utils.ts                    | Helpers              | cn() from clsx + tailwind-merge   | MEDIUM
tailwind.config.ts                  | Theme config         | Custom colors: brand-* palette     | HIGH
components.json                     | shadcn config        | Style: default, baseColor: slate   | HIGH
src/hooks/use-auth.ts               | Auth hook            | useAuth() returns user, logout     | MEDIUM
```

### Step 4: Why NOT to Read Everything

```
SKIPPED (with reason):
- src/app/(auth)/* — Not relevant to settings page
- src/app/api/* — Settings page is UI only; API can be added later
- src/components/forms/* — Will use shadcn primitives directly
- src/hooks/use-debounce.ts — Not needed for basic settings form
- node_modules/* — Never read dependencies directly
```

## Example 2: Exceeding Limits with Justification

```
CONTEXT LIMIT OVERRIDE:
Default limit: 30 files
Current count: 28 files read
Need 7 more files because:
  - Settings page has 4 tabs (Profile, Security, Notifications, Billing)
  - Each tab needs to match existing UI patterns
  - Must read existing tab implementations to maintain consistency
  - This is a quality-critical feature; context quality > token savings

Files to add:
  29. src/app/(dashboard)/profile/page.tsx     — Tab pattern reference
  30. src/app/(dashboard)/billing/page.tsx     — Tab pattern reference
  31. src/components/forms/ProfileForm.tsx     — Form pattern reference
  32. src/components/forms/SecurityForm.tsx    — Form pattern reference
  33. src/lib/validators/profile.ts            — Validation pattern
  34. src/lib/api/settings.ts                  — Existing API patterns
  35. src/types/settings.ts                    — Type definitions
```

## Example 3: Context Compression

Before compression (verbose):
```
[Full contents of Sidebar.tsx - 150 lines]
[Full contents of Header.tsx - 80 lines]
[Full contents of Footer.tsx - 40 lines]
```

After compression:
```
## Layout Components Summary
- Sidebar.tsx: Vertical nav with NavLink[] items array, collapsible sections,
  active state via usePathname(). Export: <Sidebar />
- Header.tsx: Top bar with breadcrumbs, user avatar dropdown, theme toggle.
  Export: <Header />
- Footer.tsx: Copyright + version. Export: <Footer />
- All use shadcn/ui primitives + Tailwind classes
- Sidebar width: w-64, collapsible to w-16
```
