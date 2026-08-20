# Brand Profile

The profile contains approved public facts and presentation rules. It is data, not an implementation mode.

## Minimal schema

```json
{
  "brand": {
    "name": "BRAND_NAME",
    "site": "https://example.com",
    "language": "zh-CN",
    "tone": ["professional", "restrained"],
    "public_facts": ["APPROVED_PUBLIC_FACT"],
    "forbidden_context": ["INTERNAL_CONTEXT_PATTERN"]
  },
  "visual": {
    "logo": "PORTABLE_LOGO_PATH",
    "primary_color": "#00B38A",
    "cover_style": "editorial",
    "cover_ratios": ["2.35:1", "1:1"]
  },
  "products": [
    {
      "name": "PRODUCT_NAME",
      "promise": "USER_VISIBLE_RESULT",
      "url": "https://example.com/product"
    }
  ],
  "blocks": {
    "endcap": true,
    "product_intro": true,
    "copyable_assets": "optional"
  }
}
```

## Rules

- Treat only `public_facts`, product promises, names, URLs, and approved design fields as publishable.
- Treat `forbidden_context` as a final-output exclusion list, never as copy.
- Keep product promises outcome-led; do not invent metrics, customers, awards, integrations, or capabilities.
- Resolve relative asset paths against the profile location.
- Profiles may reference private local assets, but committed examples must use placeholders.
