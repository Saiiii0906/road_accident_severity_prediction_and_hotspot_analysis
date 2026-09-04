# Vantage Frontend Design System

This document outlines the design tokens, visual language, component patterns, typography, and accessibility principles of the **Vantage** interface.

---

## 1. Brand Identity & Visual Philosophy

Vantage employs a high-density, technical aesthetic engineered for transport analysts, dispatchers, and safety engineers. The interface emphasizes high data legibility, structured evidence hierarchies, and unambiguous risk communication.

- **Brand Name:** Vantage
- **Tagline:** AI-Powered Road Safety & Traffic Intelligence
- **Primary Visual Tone:** Clean slate surfaces, subtle borders, high-contrast typography, and purposeful semantic risk accents.

---

## 2. Color Palette & Theme Tokens

Vantage is built with **Tailwind CSS v4** utilizing custom CSS variables defined in `frontend/src/styles.css`. It supports persistent **Dark** and **Light** modes via `use-theme.tsx`.

### Surface & Neutral Tones

| Token | Dark Mode Value | Light Mode Value | Usage |
| --- | --- | --- | --- |
| `--background` | `hsl(222, 47%, 11%)` | `hsl(0, 0%, 100%)` | Main application background |
| `--card` | `hsl(217, 33%, 17%)` | `hsl(0, 0%, 98%)` | Panel and metric container surfaces |
| `--border` | `hsl(217, 20%, 25%)` | `hsl(220, 13%, 91%)` | Subtle card dividers and table borders |
| `--text-primary` | `hsl(210, 40%, 98%)` | `hsl(222, 47%, 11%)` | Primary headlines and high-contrast text |
| `--text-muted` | `hsl(215, 20%, 65%)` | `hsl(215, 16%, 47%)` | Field labels, captions, and secondary metadata |

### Semantic Risk Indicators

To ensure immediate recognition across maps, charts, and summary cards, risk tiers are mapped to consistent color tokens:

| Risk Tier | Tailwind Classes | Hex Equivalent | Semantic Meaning |
| --- | --- | --- | --- |
| **Low** | `text-emerald-400 bg-emerald-950/40 border-emerald-800/50` | `#10B981` | Standard conditions, baseline topological risk. |
| **Moderate** | `text-amber-400 bg-amber-950/40 border-amber-800/50` | `#F59E0B` | Elevated attention recommended, moderate delays. |
| **High** | `text-orange-400 bg-orange-950/40 border-orange-800/50` | `#F97316` | Disproportionate collision concentration or high GNN risk. |
| **Critical** | `text-rose-400 bg-rose-950/40 border-rose-800/50` | `#F43F5E` | Active lane closure, freezing hazard, or severe bottleneck. |

### Data Availability Indicators

Used across telemetry and subsystem cards to indicate upstream data status:

- **`available`:** Emerald badge / dot (`bg-emerald-500`)
- **`partial`:** Amber badge / dot (`bg-amber-500`)
- **`unavailable` / `out_of_bounds`:** Slate/Rose badge (`bg-slate-700` or `bg-rose-500`)

---

## 3. Typography

- **Primary Sans-Serif:** Inter, system-ui, `-apple-system`, BlinkMacSystemFont, `sans-serif`. Used for all UI chrome, body copy, headings, and data labels.
- **Monospace:** `ui-monospace`, SFMono-Regular, Menlo, Monaco, Consolas, `monospace`. Used for geographic coordinates, road segment identifiers, timestamps, and raw JSON payloads.

### Type Scale Hierarchy

- **Page Titles:** `text-2xl font-bold tracking-tight text-text-primary`
- **Section Headers:** `text-lg font-semibold text-text-primary`
- **Card Subheadings:** `text-sm font-medium text-text-muted`
- **Body Text:** `text-sm leading-relaxed text-text-secondary`
- **Captions & Metadata:** `text-xs text-text-muted`

---

## 4. Reusable UI Components

The UI library in `frontend/src/components/ui/` is built on headless **Radix UI** primitives styled with Tailwind:

### Buttons (`button.tsx`)

- `variant="default"`: Solid primary action button.
- `variant="outline"`: Bordered secondary action button.
- `variant="ghost"`: Icon button with subtle hover background (used in navbar controls).
- `variant="destructive"`: Alert or cancellation actions.

### Cards & Panels (`card.tsx`)

- Modular container with `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, and `CardFooter`.
- Renders rounded corners (`rounded-xl`), subtle borders (`border border-border`), and dark slate background fills.

### Metric Tiles (`metric-tile.tsx`)

- Specialized dashboard element for displaying key figures (e.g. Total Distance, Historical Clusters Matched, Max GNN Risk).
- Pairs an icon, a large metric value, and a small contextual interpretation label.

---

## 5. Responsive Design & Layout Principles

- **Fluid Grid System:** Layouts utilize responsive Tailwind grids:
  - Mobile ($<768\text{px}$): Single-column stack.
  - Tablet ($768\text{px} \dots 1024\text{px}$): Two-column layout.
  - Desktop ($>1024\text{px}$): Multi-column grid with sticky lateral panels.
- **Mobile Navigation Drawer:** On viewports $<768\text{px}$, the sidebar collapses into a slide-out navigation sheet controlled by the hamburger trigger in `AppNavbar`.

---

## 6. Accessibility Considerations

1. **Headless Radix Primitives:** Form elements, dropdowns, and modals automatically maintain correct ARIA roles, focus traps, and keyboard navigation.
2. **Color Contrast:** Text and background token pairings exceed WCAG AA contrast ratios ($>4.5:1$ for body copy).
3. **Reduced Motion:** Interactive transitions honor the user's `prefers-reduced-motion` system preference.
