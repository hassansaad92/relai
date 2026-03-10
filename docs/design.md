# Design Themes

Color palette sets for the RelAI app. Pick a theme and apply its hex values to the CSS variables throughout `index.html`.

---

## Otis Theme *(current)*

Inspired by Otis elevator branding — deep navy authority with a bold pink-red accent.

| Role                  | Hex       | RGB              |
|-----------------------|-----------|------------------|
| Primary (dark)        | `#041e42` | (4, 30, 66)      |
| Accent                | `#f6DC776` | (246, 82, 117)   |
| Background            | `#ffffff` | (255, 255, 255)  |
| Surface border        | `#f0f0f0` | (240, 240, 240)  |
| Body text             | `#333333` | (51, 51, 51)     |

**Usage pattern:**
- Sidebar background → Primary
- Nav active border, buttons, status badges → Accent
- Card/modal background → Background
- Card borders, inputs → Surface border
- Skills tags → Primary on white text

---

## Outer Sunset

Warm coastal fog meets Pacific blue — muted steel tones with a golden highlight.

| Role                  | Hex       | RGB              |
|-----------------------|-----------|------------------|
| Primary (dark)        | `#2b69ac` | (43, 105, 172)   |
| Secondary (mid)       | `#3e5a85` | (62, 90, 133)    |
| Accent (gold)         | `#f2c46d` | (242, 196, 109)  |
| Surface / light       | `#c5cdda` | (197, 205, 218)  |
| Highlight blue        | `#9abdd9` | (154, 189, 217)  |

**Usage pattern (suggested):**
- Sidebar background → Secondary
- Nav active border, accent elements → Accent (gold)
- Skills tags → Primary
- Card borders, muted surfaces → Surface / light
- Hover states, subtle highlights → Highlight blue
