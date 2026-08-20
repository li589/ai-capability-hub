# Anti-Pattern Catalog

## Visual Anti-Patterns (Code Patterns to Avoid)

### 1. The "AI Gradient Hero"

**Bad:**
```tsx
<div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-500 to-indigo-700 flex items-center justify-center">
  <h1 className="text-6xl font-bold text-white text-center">
    Revolutionize Your Workflow
  </h1>
</div>
```

**Good (SaaS app page):**
```tsx
<div className="px-6 py-4 border-b">
  <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
  <p className="text-sm text-gray-500 mt-1">Manage your account preferences</p>
</div>
```

### 2. The "Glassmorphism Everything"

**Bad:**
```tsx
<div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-8 shadow-2xl">
  <div className="backdrop-blur-lg bg-white/5 rounded-2xl p-6">
    Content here
  </div>
</div>
```

**Good:**
```tsx
<Card className="border">
  <CardHeader>
    <CardTitle>Notifications</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

### 3. The "Decorative Blob"

**Bad:**
```tsx
<div className="relative">
  <div className="absolute -top-20 -right-20 w-96 h-96 bg-purple-400 rounded-full blur-3xl opacity-30" />
  <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-400 rounded-full blur-3xl opacity-20" />
  <div className="relative z-10">Content</div>
</div>
```

**Good:**
```tsx
<div className="px-6 py-8">
  Content
</div>
```

### 4. The "Card Inception"

**Bad:**
```tsx
<Card>
  <CardContent>
    <Card>
      <CardContent>
        <Card>
          <CardContent>Nested 3 levels deep</CardContent>
        </Card>
      </CardContent>
    </Card>
  </CardContent>
</Card>
```

**Good:**
```tsx
<div className="space-y-4">
  <section>
    <h2 className="text-lg font-medium mb-3">Section Title</h2>
    <div className="border rounded-md divide-y">
      <div className="p-4">Item 1</div>
      <div className="p-4">Item 2</div>
    </div>
  </section>
</div>
```

### 5. The "Fake Dashboard"

**Bad:**
```tsx
<div className="grid grid-cols-3 gap-6">
  <Card><CardContent><p className="text-4xl font-bold text-purple-600">2,847</p><p>Active Users</p></CardContent></Card>
  <Card><CardContent><p className="text-4xl font-bold text-blue-600">$12.5K</p><p>Revenue</p></CardContent></Card>
  <Card><CardContent><p className="text-4xl font-bold text-green-600">98.5%</p><p>Uptime</p></CardContent></Card>
</div>
```

**Good (real data or honest empty state):**
```tsx
<div className="grid grid-cols-3 gap-4">
  <Card>
    <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Users</CardTitle></CardHeader>
    <CardContent>
      {data ? <p className="text-2xl font-semibold">{data.activeUsers}</p> : <Skeleton className="h-8 w-20" />}
    </CardContent>
  </Card>
  {/* ... */}
</div>
```

### 6. The "All Rounded Everything"

**Bad:**
```tsx
<div className="rounded-3xl">
  <button className="rounded-2xl">Click</button>
  <input className="rounded-xl" />
  <Card className="rounded-2xl" />
</div>
```

**Good (consistent radius):**
```tsx
<div className="rounded-lg">
  <Button>Click</Button>      {/* inherits rounded-md from shadcn */}
  <Input />                    {/* inherits rounded-md from shadcn */}
  <Card />                     {/* inherits rounded-lg from shadcn */}
</div>
```

### 7. The "No States Handled"

**Bad:**
```tsx
function UserList() {
  const { data, isLoading, error } = useUsers();
  return (
    <div>
      {data.map(user => <UserRow key={user.id} user={user} />)}
    </div>
  );
}
```

**Good:**
```tsx
function UserList() {
  const { data, isLoading, error } = useUsers();

  if (isLoading) return <UserListSkeleton />;
  if (error) return <ErrorState message={error.message} onRetry={refetch} />;
  if (!data?.length) return <EmptyState icon={Users} title="No users yet" action={<Button>Add User</Button>} />;

  return (
    <div className="divide-y">
      {data.map(user => <UserRow key={user.id} user={user} />)}
    </div>
  );
}
```

### 8. The "Mobile Text Overflow"

**Bad:**
```tsx
<td className="whitespace-nowrap">{user.longEmailAddress@example.com}</td>
<button className="px-8 py-4 text-lg">Very Long Button Label Text</button>
```

**Good:**
```tsx
<td className="truncate max-w-[200px]" title={user.email}>{user.email}</td>
<Button className="w-full sm:w-auto">{t('submit')}</Button>
```

## State Checklist Template

For every interactive component, verify:

```
Component: [name]
- [ ] Default state renders correctly
- [ ] Loading state (skeleton/spinner)
- [ ] Empty state (helpful message + CTA)
- [ ] Error state (message + recovery)
- [ ] Disabled state (visible, not just hidden)
- [ ] Hover state (subtle feedback)
- [ ] Focus state (visible focus ring)
- [ ] Active/pressed state
- [ ] Mobile at 375px (no overflow, no squishing)
- [ ] Dark mode (if project supports it)
```
