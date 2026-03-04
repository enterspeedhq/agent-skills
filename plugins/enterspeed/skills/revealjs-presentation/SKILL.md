---
name: revealjs-presentation
description: >
  Generate a polished, self-contained Reveal.js HTML presentation from structured
  content. Use this skill whenever the user asks to "make a presentation", "create
  slides", "build a Reveal.js deck", "turn this into a presentation", or when
  another skill (like shortcut-demo-planner) needs to produce a slide deck.
  Output is a single .html file that opens in any browser with no dependencies
  or installation required. Supports speaker notes, theming, and section grouping.
---

# Reveal.js Presentation Skill

Generates a beautiful, self-contained Reveal.js `.html` file loaded entirely
from CDN — no installation needed, opens in any browser.

---

## Input

Expect either:
- A structured outline passed directly (e.g. from shortcut-demo-planner)
- A freeform description of what the slides should contain

Always clarify before generating if the content is ambiguous.

---

## Output

A single `/tmp/presentation.html` file using Reveal.js from CDN.

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
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.6.1/theme/{{THEME}}.min.css" />
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
    transition: 'slide',
    backgroundTransition: 'fade',
    plugins: [ RevealNotes, RevealHighlight ]
  });
</script>
</body>
</html>
```

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
- **Speaker notes on every story slide** — what to say, what to click, what to highlight
- **Section dividers** between thematic groups
- Use the `.tag` CSS class for labels, epics, or story types
- Avoid walls of text — if a description is long, distil to 2–3 bullet points

---

## Delivery

1. Write the full HTML to `/tmp/presentation.html`
2. Copy to `/mnt/user-data/outputs/presentation.html`
3. Use `present_files` to share it with the user
4. Tell the user: open in browser, use arrow keys to navigate, `S` for speaker notes
