# Radar visual kit

These assets support the report's curatorial framework. They are optional runtime-compatible
starting points, not a template or alternate report system.

- `radar-interactions.css` provides token-based focus, selection, and reduced-motion behavior.
- `radar-interactions.js` coordinates chapter anchors and signal selection with one state key.
- `icons/radar-icons.svg` contains optional unified line icons.
- `styles.json` is the authoritative six-style inventory and fixed framework pairing.
- `layout-guides/*.svg` contains six original one-to-one lightweight composition and palette guides.
  Inspect only the randomly selected guide for proportions, hierarchy, whitespace, and a
  maximum-three-color direction.
- `dynamic-ui-companions/manifest.json` pairs every random style with one compact companion identity.
- `dynamic-ui-companions/*.svg` contains six lightweight composition guides for adapting the
  built-in Dynamic UI material without replacing its code, tokens, theme, fallback, or interaction.

When copying the CSS or JavaScript into an `html-report` output, place it in the runtime's report-local
`assets/` directory, preserve the `_shared/` structure, and adapt selectors to the report's real
evidence. Do not add cards, navigation, or motion solely because the asset supports them.

All layout and companion guides are internal design references, not report content. Never copy,
embed, trace, or ship them in a delivered report or widget. They contain no source screenshots or
third-party artwork. No
wireframe, moodboard, framework study, screenshot, placeholder chart, or internal design commentary
may appear in a delivered report.
