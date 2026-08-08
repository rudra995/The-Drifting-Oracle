# Design System: Editorial Intelligence

## 1. Overview & Creative North Star
**The Creative North Star: "The Precision Lens"**

This design system moves away from the "generic SaaS dashboard" archetype. Instead, it embraces an **Editorial Intelligence** aesthetic—a style that combines the high-density information requirements of financial software with the sophisticated, airy hierarchy of modern broadsheet typography. 

In "Drifting Oracle," we treat data not as a series of boxes, but as a narrative. We break the rigid grid through **Intentional Asymmetry**: using large, bold Manrope headlines to anchor the eye, while Inter-based data sets flow beneath them. The layout relies on "Negative Space as Structure," using breathing room and tonal shifts rather than lines to define the boundaries of complex machine learning insights.

---

## 2. Colors & Surface Philosophy
The palette is rooted in a foundation of slate and deep ocean blues to project authority and calm in high-stakes monitoring environments.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1x1 solid borders to separate sections. We define architecture through color logic:
- **Primary Layout:** Use `surface` (`#f7f9fb`) as the base.
- **Sectioning:** Define major areas by transitioning to `surface-container-low` (`#f0f4f7`).
- **Nesting:** To highlight a specific module within a section, use `surface-container-lowest` (`#ffffff`) to create a "lifted" effect through tonal contrast alone.

### Glass & Gradient Soul
To avoid a flat, sterile feel, apply these signature treatments:
- **The Oracle Glow:** Primary CTAs and critical ML drift status cards should utilize a subtle linear gradient from `primary` (`#545f73`) to `primary-container` (`#d8e3fb`) at a 135° angle.
- **Floating Intelligence:** Overlays and dropdowns must use a "Glassmorphism" effect: `surface_container_low` at 80% opacity with a `24px` backdrop blur. This ensures the dashboard feels like a unified, layered environment rather than a collection of disparate parts.

---

## 3. Typography
We use a dual-font strategy to balance character with extreme legibility.

- **The Anchor (Manrope):** Reserved for `display` and `headline` roles. Its geometric nature provides a modern, high-end editorial feel. It signals "Executive Summary."
- **The Engine (Inter):** Used for `title`, `body`, and `label` roles. Inter is chosen for its exceptional readability in dense data tables and technical ML metrics.

**Hierarchy as Brand:** 
Large `display-sm` headers (Manrope, Semi-Bold) should be used to title major sections (e.g., "Feature Drift Analysis"), contrasted immediately by `label-md` (Inter, All-Caps, Monospaced-style tracking) to provide technical metadata. This contrast communicates both "Vision" and "Detail."

---

## 4. Elevation & Depth
Depth in this system is organic, mimicking natural light rather than digital shadows.

### The Layering Principle
Stacking tiers is the primary method of elevation:
1. **Background:** `surface`
2. **Main Workspace:** `surface-container`
3. **Interactive Cards:** `surface-container-lowest` (This creates a natural "pop" against the gray-blue background).

### Ambient Shadows & Ghost Borders
- **Shadows:** When a card requires a floating state (e.g., a hovered KPI card), use a shadow with a 32px blur, 0px offset, and 6% opacity of the `on-surface` color.
- **The Ghost Border:** For high-density tables where cell separation is vital, use the `outline-variant` (`#a9b4b9`) at **10% opacity**. It should be felt, not seen.

---

## 5. Components

### KPI Cards & ML Metrics
- **Structure:** Forbid divider lines. Use `surface-container-highest` for the metric value and `surface-container-low` for the trend Sparkline.
- **Status Indicators:** Use `tertiary` (`#006592`) for neutral data and `error` (`#9f403d`) for critical drift alerts. Icons should be paired with `error_container` backgrounds at 20% opacity.

### High-Density Data Tables
- **Header:** `surface-container-high` with `label-md` typography.
- **Rows:** Alternating `surface` and `surface-container-low` backgrounds. No borders.
- **Interactivity:** Hover states must use `primary_container` at 30% opacity to highlight the active row without obscuring text.

### Interactive Charts (Recharts Style)
- **Grid Lines:** Use `outline-variant` at 15% opacity.
- **Tooltip:** Apply the "Glassmorphism" rule—`surface-container-lowest` at 90% opacity with a soft `8px` rounded corner (`lg`).
- **Data Traces:** Use `tertiary` for the primary data line and `primary_fixed_dim` for historical baselines.

### Form Elements & Inputs
- **Field Styling:** Fields should not be "boxes" but "surfaces." Use `surface-container-highest` with a bottom-only `outline` of 2px that animates to `primary` on focus.
- **Buttons:** Primary buttons use the "Oracle Glow" gradient. Tertiary buttons are text-only with `label-md` styling, gaining a subtle `surface-variant` background on hover.

---

## 6. Do's and Don'ts

### Do:
- **Embrace White Space:** Give charts 40px of internal padding. Data density requires room to breathe to remain "trustworthy."
- **Use Tonal Stepping:** Use `surface-dim` for inactive sidebar states to create a clear hierarchy between the navigation and the stage.
- **Type-Heavy Hierarchy:** Let the font size do the work. A `display-sm` headline is more effective than a bold background color.

### Don't:
- **No 100% Black:** Never use `#000000`. Use `on-surface` (`#2a3439`) for text to maintain a sophisticated, slate-toned softness.
- **No Sharp Corners:** Avoid the `none` roundedness scale. Enterprise-grade doesn't mean "aggressive." Use `md` (0.375rem) as the standard for all data containers.
- **No "Default" Shadows:** Never use standard CSS drop shadows. If it looks like a template, it has failed. Follow the Ambient Shadow rule.