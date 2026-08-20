# UI Taste Guard Rules

## Always Apply — For Any Web/UI Code Generation

### Detect and Use Existing Design System

Before writing any UI code:
1. Check for design system: components.json (shadcn), package.json (antd/mui), src/components/ui/
2. Import from the design system — never recreate primitives
3. Use project's color tokens, spacing scale, and typography
4. Match existing border-radius, shadow, and animation patterns

### Forbidden Anti-Patterns

NEVER use these in non-landing-page contexts:
- Purple-blue gradients (`from-purple-600 to-blue-600`)
- Glassmorphism on functional elements (`backdrop-blur-xl bg-white/10`)
- Decorative blobs or floating colored circles
- `text-6xl` or larger for app/tool/dashboard pages
- Card-in-card nesting (3+ levels)
- Fake dashboard with placeholder data
- `rounded-2xl` or `rounded-3xl` on everything
- Marketing hero layout for settings/tools/admin pages

### All States Must Be Handled

Every interactive component must account for:
- **Loading**: Skeleton, spinner, or progress
- **Empty**: Helpful message with action CTA
- **Error**: Clear message + recovery action
- **Disabled**: Visible disabled appearance
- **Hover**: Subtle feedback on interactive elements
- **Focus**: Visible focus ring for keyboard navigation

### Mobile Compatibility

- Test layout mentally at 375px width
- No text overflow (use truncate, max-width)
- No button content squishing (adequate padding)
- Forms must be usable on mobile

### SaaS/Tool/Admin Page Layout

- Compact, information-dense
- Clear hierarchy: title → actions → content
- Tables for data, not decorative cards
- Functional labels, not marketing copy
- Forms with persistent labels above inputs
