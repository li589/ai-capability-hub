# Release Checklist

## Authorization

- User confirms ownership or explicit permission.
- No private, paywalled, authenticated, login, payment, account, or admin flows are mirrored unless the user owns them and explicitly requests internal use.
- External third-party links remain external.
- Brand usage, public display, ICP, public-security filing, and copyright obligations are handled by the user.

## Output Integrity

Check:

```bash
python3 -m json.tool output/example/original/quality_report.json | sed -n '1,160p'
```

Require:

- `ready_for_release=true`.
- Page success rate meets `quality_policy.min_page_success_rate`.
- Resource success rate meets `quality_policy.min_resource_success_rate`.
- No unresolved internal links beyond policy.
- No residual same-domain remote static resources.

## Browser Checks

Preview locally and inspect:

- Home page.
- A deep content page.
- A subdomain page if included.
- A page with images.
- A page with CSS/JS-heavy layout.

In browser DevTools, check:

- Network has no same-domain missing CSS, JS, image, font, video, or document resources.
- Console has no rendering-blocking errors.
- Internal navigation stays inside the mirrored host mapping.

## Deployment Checks

Before enabling public access:

- DNS points to the deployment server.
- Nginx config is generated and reviewed.
- `nginx -t` passes.
- HTTPS certificate is installed.
- Required ICP and public-security filing information is displayed when applicable.
- Access controls are configured if the mirror is private or invitation-only.
