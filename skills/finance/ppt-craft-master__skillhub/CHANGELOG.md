# Changelog

## 2.0.0
- Fixed exact page-count bug in `buildOutline`.
- Removed rigid global `layout <= 2` constraint; content suitability now wins.
- Removed silent text truncation as the default overflow strategy.
- Fixed PowerPoint paragraph spacing option naming to `paraSpaceAfterPt`.
- Added explicit overflow policy: `error` by default, `clip` only when requested.
- Raised default minimum generated text size from 8pt to 10pt.
- Reworked QA checker to use JSZip instead of assuming a system `unzip` command.
- Added safe-area, placeholder, small-text, and conservative text-height checks.
- Added package metadata and JSZip dependency.
- Clarified template-first, content-first, and structural-vs-visual QA rules.
