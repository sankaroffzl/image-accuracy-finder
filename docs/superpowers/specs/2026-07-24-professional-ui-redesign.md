# Professional UI Redesign — Image Accuracy Finder

## Overview
Redesign the entire frontend with a clean, enterprise-grade blue/white Tailwind CSS theme. All backend logic remains unchanged.

## Design System
- **Primary:** `#2563EB` (blue-600), **Hover:** `#1E40AF` (blue-800)
- **Background:** `#F8FAFC` (slate-50), **Cards:** `#FFFFFF`
- **Text:** `#0F172A` (slate-900) headings, `#475569` (slate-600) body
- **Success:** `#22C55E`, **Warning:** `#EAB308`, **Danger:** `#EF4444`
- **Font:** Inter (system sans-serif fallback)
- **Layout:** 1200px centered container, rounded-xl cards with shadow-sm and border

## Approach
- Add Tailwind v4 Play CDN (`@tailwindcss/browser@4`) to all templates
- Replace existing custom CSS classes with Tailwind utility classes
- Keep a minimal `style.css` for Tailwind-incompatible custom styles (animations, transitions, drag-drop states)
- No build step required (CDN handles everything)

## Pages

### Upload Page (`index.html`)
- Two side-by-side cards (reference + candidates) on desktop, stacked on mobile
- Dashed-border dropzones with hover states
- Blue "Compare All" button
- Header with app title + theme toggle
- Dark mode toggle preserved

### Single Result Page (`results.html`)
- Clean result card with gauge (CSS-based, no canvas)
- Algorithm breakdown grid (SSIM, ORB, Histogram, pHash)
- Color-coded scores (green/yellow/red)

### Batch Results Page (`batch_results.html`)
- Ranked table with gold/silver/bronze rank badges
- Gradient progress bars
- Expandable algorithm breakdown per row
- Pagination (20/page)
- CSV export + New Round buttons
- Top 10 highlighting

## Implementation Plan
1. Add Tailwind CDN + update `style.css` with minimal custom styles
2. Redesign `index.html`
3. Redesign `results.html`
4. Redesign `batch_results.html`
5. Verify all 34 tests still pass
