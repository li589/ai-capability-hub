---
name: presentation
description: Interactive slide presentation with horizontal narrative slides, optional vertical detail stacks, staged fragments, keyboard navigation, overview, fullscreen, and deep links. Use for talks, pitches, demos, lessons, and guided walkthroughs.
category: communication
---

Use this when the user wants a slide deck, presentation, pitch, lesson, demo,
or guided walkthrough. Generate a real interactive presentation, not a long
page divided into card-shaped sections.

Do not use this recipe for a dashboard, reference document, or report that the
user should scan freely. Use a normal scrollable Canvas for those outputs.

## Authoring Model

Use only these presentation components, imported from `qoder/canvas`:

- `Presentation` owns navigation, controls, progress, keyboard and touch input,
  overview, fullscreen, speaker notes, and URL state.
- `PresentationSlide` is one horizontal narrative step.
- `PresentationStack` groups a short vertical branch of related slides.
- `PresentationFragment` reveals supporting content within the active slide.

Keep the public surface simple. Compose slide content from normal Canvas
primitives or native JSX, but let `Presentation` own presentation behavior.

Never import `reveal.js`, `@revealjs/react`, a Reveal theme, or Reveal CSS.
Never hand-write previous/next buttons, progress bars, slide counters, keyboard
listeners, touch gestures, fullscreen calls, overview state, or hash routing.

## Recommended Story Shape

Prefer 5-9 horizontal steps. A useful default is:

```text
+-------------+     +-------------+     +-------------+
| 1. Title    | --> | 2. Context  | --> | 3. Claim    |
+-------------+     +-------------+     +-------------+
                                                |
                                                v
                                         +-------------+
                                         | 4. Evidence |
                                         +-------------+
                                                |
                                      vertical details
                                                |
                                                v
                                         +-------------+
                                         | 4.1 Detail  |
                                         +-------------+

+-------------+     +-------------+     +-------------+
| 7. Close    | <-- | 6. Decision | <-- | 5. Demo     |
+-------------+     +-------------+     +-------------+
```

Horizontal navigation carries the main story. Use a vertical stack only when
the audience can understand the main story without opening every detail slide.
Keep each stack to 2-3 slides and avoid nested stacks.

## Slide Layout

Design for a 16:9 stage. Each slide should make one claim and usually contain:

```text
+------------------------------------------------------------------+
| Short slide title                                                |
| One-sentence claim or context                                    |
|                                                                  |
| +---------------------------+  +-------------------------------+ |
| | Primary visual, example,  |  | 2-4 supporting points,       | |
| | diagram, or evidence      |  | comparison, or callout       | |
| +---------------------------+  +-------------------------------+ |
|                                                                  |
| Optional source or takeaway                                      |
+------------------------------------------------------------------+
```

Rules:

- Put one primary idea on each slide.
- Keep titles short enough to fit on one line.
- Prefer one strong visual, diagram, code example, or comparison over many
  small cards.
- Use 2-4 supporting points, not dense prose.
- Keep critical content inside the center of the stage so controls and narrow
  host frames do not cover it.
- Use stable sizes and wrapping. Do not shrink text with viewport units.
- Use the user's language for visible text. Keep code, file paths, commands,
  URLs, and identifiers unchanged.

## Core Canvas TSX Pattern

```tsx
import {
  Card,
  CardBody,
  Grid,
  H1,
  H2,
  Presentation,
  PresentationFragment,
  PresentationSlide,
  PresentationStack,
  Stack,
  Text,
  useHostTheme,
} from "qoder/canvas";

export default function Canvas() {
  const { tokens } = useHostTheme();
  return (
    <Presentation
      defaultSlide={0}
      keyboard
      controls
      progress
      slideNumber
      thumbnails
      overview
      fullscreen
      speakerNotes
      deepLink
      touch
      loop={false}
      transition="slide"
      aspectRatio="16 / 9"
      height="min(760px, calc(100vh - 48px))"
      aria-label="Product launch presentation"
    >
      <PresentationSlide
        id="opening"
        title="A clear opening claim"
        thumbnail={<strong>A clear opening claim</strong>}
        notes="State the audience problem before showing the solution."
        background={{
          color: tokens.bg.elevated,
          pattern: "aurora",
          accent: tokens.chart.blue,
          accentSecondary: tokens.chart.purple,
        }}
      >
        <Stack gap={20} align="center">
          <H1>A clear opening claim</H1>
          <Text tone="secondary">One sentence that gives the audience a reason to continue.</Text>
        </Stack>
      </PresentationSlide>

      <PresentationSlide id="evidence" title="Evidence">
        <Stack gap={20}>
          <H2>Show the evidence before the detail</H2>
          <Grid columns="repeat(2, minmax(0, 1fr))" gap={16}>
            <Card><CardBody>Primary evidence</CardBody></Card>
            <Card><CardBody>Why it matters</CardBody></Card>
          </Grid>
          <PresentationFragment index={0} effect="fade">
            <Text>Reveal the takeaway after the audience has seen the evidence.</Text>
          </PresentationFragment>
        </Stack>
      </PresentationSlide>

      <PresentationStack>
        <PresentationSlide id="workflow" title="Workflow">
          <H2>Explain the main workflow</H2>
        </PresentationSlide>
        <PresentationSlide id="workflow-detail" title="Workflow detail">
          <H2>Keep optional detail in the vertical branch</H2>
        </PresentationSlide>
      </PresentationStack>

      <PresentationSlide id="close" title="Decision">
        <Stack gap={16} align="center">
          <H2>End with one decision or next step</H2>
          <PresentationFragment index={0} effect="fade">
            <Text>Make the requested action explicit.</Text>
          </PresentationFragment>
        </Stack>
      </PresentationSlide>
    </Presentation>
  );
}
```

## Keyboard and Interaction

- Keyboard navigation is focus-scoped. The user should focus the presentation
  before using slide shortcuts. Do not install document-level key handlers.
- Left and Right move through the horizontal story. Up and Down move inside a
  vertical stack. Home and End jump to the deck boundaries.
- Space advances the current fragment sequence before it advances the slide.
- Overview and fullscreen shortcuts are owned by `Presentation`; do not shadow
  them with slide-level handlers.
- Escape should leave a transient mode such as overview or fullscreen before it
  affects the surrounding Canvas.
- Inputs, textareas, selects, editable content, and nested keyboard-operable
  components must keep their own keys. Do not add navigation logic around them.
- Keep `loop={false}` for talks and decision decks. Enable looping only for a
  kiosk or unattended repeating presentation.

## Fragments

Use fragments to control attention, not to animate every element.

- Reveal a conclusion after its evidence, a diagram annotation after the base
  diagram, or the next step in a short process.
- Use integer `index` values for an intentional order. Fragments with the same
  index should appear together.
- Keep fragment sequences short, usually 1-4 steps per slide.
- Do not hide the slide title, essential context, source attribution, or the
  only way to navigate inside a fragment.
- Prefer `effect="fade"` unless motion carries meaning.
- The next action should reveal a pending fragment before leaving the slide;
  the previous action should hide fragments in reverse order.

## Overview, Fullscreen, Notes, and Deep Links

- Give every slide a concise `title`. Overview uses titles to make destinations
  understandable; the visible heading may repeat that title.
- Give every slide a unique, stable, URL-safe `id`. Keep the same ID when slides
  are reordered so existing deep links remain useful.
- Set `deepLink` on `Presentation`; do not read or write `window.location.hash`,
  `history`, or URL query parameters from slide content.
- Treat deep links as entry points, not as the primary narrative. A linked slide
  must still make sense when opened without the previous slide.
- Let `Presentation` request and leave fullscreen. Do not call the Fullscreen
  API directly or force global page overflow styles.
- Slides must remain readable when fullscreen is unavailable or denied by the
  host.
- Put short presenter-only cues in the slide `notes` prop. Do not render notes
  as hidden DOM inside the visible slide.
- Overview thumbnails should remain recognizable at a glance. Avoid slides that
  differ only through fragments or tiny body text.

## Thumbnail Rail

Set `thumbnails` on `Presentation` to make a Slides-like preview rail available.
The rail starts closed so opening the Canvas directly in a browser still feels
like playback, not an editor. The toolbar control or `T` shortcut opens it.

- The rail uses each slide's background, title, and short static summary by
  default. Clicking a preview navigates directly to that slide.
- Use `defaultThumbnailsOpen` only for an explicit authoring or review surface.
  Keep the playback default (`false`) for shared links and browser presentation.
- Add a lightweight `thumbnail` node to `PresentationSlide` only when a more
  recognizable preview materially helps. Keep it decorative and compact.
- Never place inputs, buttons, IDs, data loading, timers, or other stateful
  components inside `thumbnail`; it renders separately from the live slide.
- Up and Down move through the rail when a thumbnail has focus. Home and End
  jump to its first and last entries.
- Opening overview or entering fullscreen closes the rail automatically so the
  primary slide remains the focus.
- Keep stable `title` and `id` values because they label preview destinations
  for keyboard and assistive-technology users.

## Backgrounds

Use backgrounds to separate narrative phases and create depth without hiding
the slide content. Keep the `background` API declarative:

- Use `pattern: "aurora"` for title, vision, and closing slides.
- Use `pattern: "spotlight"` to focus attention on one claim or visual.
- Use `pattern: "grid"` for architecture, workflow, and technical slides.
- Use `pattern: "dots"` for supporting evidence or a lighter transition slide.
- Set `color`, `accent`, and `accentSecondary` from `useHostTheme().tokens`.
- Use `image` for a full-bleed image URL. Add a readable `gradient` layer above
  it when text needs contrast.
- Do not use a different loud background on every slide. Reuse 2-3 related
  treatments across the deck so the story still feels coherent.

## Validation

After writing the Canvas:

1. Require the host Canvas TypeScript check to report no errors.
2. Preview the real presentation, not only the SDK build.
3. Focus the stage and verify horizontal navigation, vertical stacks, Home,
   End, Space, and reverse navigation.
4. Verify that fragments appear before slide changes and disappear in reverse.
5. Verify overview selection, fullscreen entry and exit, and stable deep links
   after reload.
6. Verify that typing or using arrows inside an input or interactive child does
   not change slides.
7. When `thumbnails` is enabled, verify that playback starts with the rail
   closed, then open it from the toolbar and navigate by click and keyboard.
8. Check the first, densest, stacked, and final slides at the normal host size,
   fullscreen size, and a narrow Canvas width.
9. Confirm that no manual navigation, Reveal dependency, global listener, or
   global page style was added.
