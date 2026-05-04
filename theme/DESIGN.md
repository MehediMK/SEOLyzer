---
name: Precision SEO
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#464555'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#712ae2'
  on-secondary: '#ffffff'
  secondary-container: '#8a4cfc'
  on-secondary-container: '#fffbff'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bbff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5a00c6'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  h1:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  table-data:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-page: 24px
  max-width: 1440px
---

## Brand & Style
The design system is engineered for data-heavy environments where precision and clarity are paramount. The brand personality is **Trustworthy**, **High-Tech**, and **Efficient**, catering to SEO professionals who require rapid insight extraction from complex datasets. 

The aesthetic follows a **Modern Corporate** direction, blending the functional rigor of data-dense utilities with the polished refinement of contemporary SaaS. It prioritizes information density without sacrificing visual breathing room, ensuring that users feel in control of powerful, high-performance software.

## Colors
The color palette is anchored by a deep Indigo primary, signaling stability and professional authority. A vibrant Purple is reserved for high-impact accents, such as "Growth" indicators or "Premium" features, to draw the eye without overwhelming the primary actions. 

Backgrounds utilize a tiered system of neutral whites and very light grays to create subtle contrast between global navigation and workspace areas. Functional colors (Green/Red/Amber) are strictly used for SEO health metrics and trend indicators.

## Typography
This design system utilizes **Inter** exclusively to leverage its exceptional legibility at small sizes and high-resolution screens. 

- **Hierarchy:** Strong contrast between bold headlines and utilitarian body text ensures clear scannability.
- **Tabular Data:** Use `table-data` settings for keyword lists and metric grids. 
- **Labels:** Uppercase labels with slight tracking are used for section headers within sidebars and small metadata tags.

## Layout & Spacing
The layout follows a **Fixed-Fluid hybrid grid**. Sidebars are fixed at 260px, while the main content area expands to fill the remaining space up to a 1440px container.

- **Grid:** A 12-column layout for dashboard views.
- **Rhythm:** An 8px linear scale drives all padding and margins. 
- **Density:** High-density views (like Keyword Explorer) reduce internal cell padding to 8px (`sm`) to maximize the amount of visible data on the initial fold.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** and **Ambient Shadows**. The design avoids heavy drop shadows, opting instead for highly diffused, low-opacity shadows that suggest a subtle lift from the background.

- **Level 1 (Base):** `#F9FAFB` background.
- **Level 2 (Cards/Content):** White surface with a 1px border (`#E5E7EB`) and a soft shadow (0px 1px 3px rgba(0,0,0,0.05)).
- **Level 3 (Modals/Popovers):** White surface with a more pronounced ambient shadow (0px 10px 15px -3px rgba(0,0,0,0.1)).

## Shapes
The shape language is sophisticated and approachable. 
- **Standard UI elements** (Buttons, Inputs) use an 8px radius.
- **Larger containers** (Cards, Data Grids) use a 12px radius.
- **Interactive Tags/Chips** are fully rounded (pill-shaped) to distinguish them from actionable buttons.

## Components
- **Buttons:** Primary buttons use the Indigo fill with white text. Secondary buttons use a subtle gray stroke. State changes (hover/active) should involve a slight darkening of the fill.
- **Data-Dense Tables:** Headers are sticky with a light gray background (`#F3F4F6`). Cells use the `table-data` typography. Implement "Zebra Striping" on hover rather than static rows to keep the interface clean.
- **Input Fields:** 8px rounded corners with a subtle 1px border. On focus, the border transitions to the primary Indigo with a 2px soft outer glow.
- **Elegant Charts:** Use a palette of Indigo, Purple, and Teal. Line charts should use a 2px stroke width with a very light gradient fill below the line.
- **Progress Indicators:** Use thin (4px) bars for "SEO Health" or "Crawling Progress" to maintain a high-tech, precise feel.
- **Audit Cards:** Summary cards with a large numeric metric, a sparkline, and a secondary "Percent Change" indicator.