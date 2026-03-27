---
name: revealjs-presentation
version: 1.0.0
description: Generate a polished, self-contained Reveal.js HTML presentation from structured content. Use this skill whenever the user asks to "make a presentation", "create slides", "build a Reveal.js deck", "turn this into a presentation", or when another skill (like shortcut-demo-planner) needs to produce a slide deck. Output is a single .html file that opens in any browser with no dependencies or installation required. Supports speaker notes, theming, and section grouping.
---

# Reveal.js Presentation Skill

Generates a beautiful, self-contained Reveal.js `.html` file loaded entirely
from CDN — no installation needed, opens in any browser.

---

## Input

Expect either:
- A structured outline passed directly (e.g. from shortcut-demo-planner)
- A freeform description of what the slides should contain

Generate immediately for concrete requests. Clarify only if the content is genuinely unclear (e.g. the audience is unknown, the scope doesn't make sense, or key topics are missing).

---

## Output

A single self-contained HTML file using Reveal.js from CDN, written directly to the output path (see Delivery section).

---

## Template

Use this base structure and fill in slides:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{TITLE}}</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/reveal.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/theme/{{THEME}}.min.css" /><!-- Default: moon -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" />
  <style>
    /* Custom overrides go here */
    .reveal h1, .reveal h2 { text-transform: none; }
    .reveal .slides section { text-align: left; }
    .reveal ul { display: block; }
    .tag {
      display: inline-block;
      background: rgba(255,255,255,0.15);
      border-radius: 4px;
      padding: 2px 10px;
      font-size: 0.6em;
      margin: 2px;
      vertical-align: middle;
    }
    .flow {
      font-family: monospace;
      font-size: 0.7em;
      background: rgba(0,0,0,0.35);
      border-radius: 8px;
      padding: 14px 18px;
      line-height: 1.7;
      white-space: pre;
    }
  </style>
</head>
<body>
<div class="reveal">
  <div class="slides">

    <!-- SLIDES GO HERE -->

  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/reveal.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/plugin/notes/notes.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/plugin/highlight/highlight.min.js"></script>
<script>
  Reveal.initialize({
    hash: true,
    width: 1600,
    height: 900,
    margin: 0.04,
    transition: 'slide',
    backgroundTransition: 'fade',
    plugins: [ RevealNotes, RevealHighlight ]
  });
</script>
</body>
</html>
```

> **Why `width: 1600, height: 900`?** Reveal.js defaults to 960px wide. On typical laptop viewports (~1500px+) this causes content to scale *up* (~1.6×), making everything too large. Setting 1600×900 forces a scale-down instead, so text and layout stay proportional without needing to zoom out.

---

## Slide Patterns

### Title slide
```html
<section data-background-gradient="linear-gradient(135deg, #1a1a2e, #16213e)">
  <h1 style="color:#fff;">{{PRESENTATION TITLE}}</h1>
  <p style="color:#aaa;">{{Subtitle or date}}</p>
</section>
```

### Section divider
```html
<section data-background-color="#0f3460">
  <h2 style="color:#e94560;">{{Section Name}}</h2>
</section>
```

### Story / feature slide
```html
<section>
  <h2>{{Story Title}}</h2>
  <p>{{One-sentence summary}}</p>
  <ul>
    <li>{{Key point}}</li>
    <li>{{Key point}}</li>
  </ul>
  <aside class="notes">
    {{Speaker notes: what to say, what to demo, what to watch out for}}
  </aside>
</section>
```

### Monospace flow / ASCII diagram
Use the `.flow` CSS class for step-by-step flows, data pipelines, or ASCII diagrams:
```html
<div class="flow">Step 1 → Step 2
  → detail
Step 3 → outcome</div>
```
Keep `.flow` blocks concise. If a flow has more than ~10 lines, reduce `font-size` inline: `style="font-size:0.58em; line-height:1.6;"`. Blank lines between steps add height fast — omit them if the slide is dense.

### Summary / what's next slide
```html
<section data-background-gradient="linear-gradient(135deg, #1a1a2e, #16213e)">
  <h2 style="color:#fff;">What's next</h2>
  <ul style="color:#ccc;">
    <li>{{Next item}}</li>
  </ul>
</section>
```

---

## Theme Selection

Pick a theme that fits the content tone:

| Theme     | Best for |
|-----------|----------|
| `moon`    | Dark, elegant, technical |
| `night`   | Dark, high contrast |
| `black`   | Minimal dark |
| `white`   | Clean light |
| `league`  | Bold, dramatic |
| `sky`     | Light, friendly |

Default to `moon` for technical/dev content.

---

## Design Principles

- **Dark opening and closing slides**, lighter content slides ("sandwich")
- **One idea per slide** — don't cram bullets
- **Speaker notes on every story slide** — what to say, what to click, what to highlight. Section dividers and summary/closing slides do not require notes unless there is something specific to say.
- **Section dividers** between thematic groups
- Use the `.tag` CSS class for labels, epics, or story types
- Avoid walls of text — if a description is long, distil to 2–3 bullet points

---

## Layout — preventing overflow

Reveal.js scales slide content to fit the viewport. Dense slides can overflow if the unscaled content is taller than 900px. Apply these fixes in order:

1. **Reduce `.flow` block font size** — start at `font-size:0.65em`, go to `0.58em` if needed. Also set `line-height:1.6` and remove blank lines between steps.
2. **Reduce `p` and `ul` font sizes** — `0.75em` for supporting text, `0.65em` for secondary detail.
3. **Tighten margins** — reduce `margin-bottom` on headings and paragraphs (`0.4em`–`0.6em`).
4. **Split the slide** — if content still overflows after font reduction, split into two slides. Two clear slides beat one cramped one.

Never shrink below `0.55em` — text becomes unreadable in presentation conditions.

---

## Delivery

1. Write the full HTML directly to the output path specified by the user (or `/mnt/user-data/outputs/presentation.html` if unspecified)
2. **Verify layout**: open the file in a browser (or use the preview tool if available) and screenshot each content-heavy slide at 100% zoom. Fix any overflow before handing off — apply the layout fixes above.
3. Tell the user: open in browser, use arrow keys to navigate, `S` for speaker notes

Note: CDN links are pinned to Reveal.js 4.6.1 intentionally for stability.
