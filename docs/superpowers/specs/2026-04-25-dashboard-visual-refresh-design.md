# Dashboard Visual Refresh Design

## Goal

Refresh the Admin, Faculty, Extension Staff, and Research Staff dashboards so they feel formal, modern, and efficient for daily academic operations. The selected visual direction is "Operations Dense": compact, clean, data-forward, and restrained.

## Scope

Update these Django templates:

- `templates/portal/admin_dashboard.html`
- `templates/portal/faculty_dashboard.html`
- `templates/portal/extension_dashboard.html`
- `templates/portal/research_dashboard.html`

The work should preserve the existing Django view context and URL names. No model, database, authentication, or routing changes are required.

## Visual Direction

Use a professional administrative interface style:

- White and very light slate surfaces.
- Thin borders and subtle shadows.
- Compact cards with stable spacing and smaller radius than the current rounded dashboard cards.
- Minimal hover motion; no rotating or playful card animation.
- Clear status color semantics: amber for pending/planning, blue for ongoing, emerald for approved/completed, red for rejected/cancelled, violet only where it adds category distinction.
- Dense but readable tables and lists for scanning.

The design should avoid decorative gradient-heavy panels and oversized UI. It should look like a serious institutional management system.

## Shared Dashboard Pattern

Each dashboard should use the same structural language:

1. Header band inside the content area with role name, short operational summary, and primary action when relevant.
2. Compact metric grid with icon, label, value, and optional subtext.
3. Main work panel containing the user's relevant records.
4. Consistent table/list styling, status badges, empty states, and action buttons.

The existing base layout and sidebar remain intact. Changes should be concentrated in the dashboard templates.

## Role-Specific Design

### Admin

Admin should show a broad institutional overview:

- Metric cards for proposals, research projects, extension activities, and users.
- Recent proposals as the primary review panel.
- Quick actions as compact buttons rather than large decorative tiles.
- Preserve existing links to create proposals, manage users, review pending proposals, and add research.

### Faculty

Faculty should focus on submission status and next action:

- Metric cards for total proposals, pending, approved, and rejected if available.
- A primary action to submit a new proposal.
- My proposals table remains the central content area.
- Keep proposal title, type, status, date submitted, and view action.

### Extension Staff

Extension should focus on activity management:

- Metric cards for total activities, planning, ongoing, and completed where context supports it.
- A primary action to create a new activity.
- My extension activities table remains the central content area.
- Keep activity title, type, status, beneficiaries, and view action.

### Research Staff

Research should focus on research progress and available approved proposals:

- Metric cards for total research, ongoing, published, and approved proposals.
- My research projects as a compact list or table-like panel.
- Faculty abstracts/approved proposal access as a secondary action panel.
- Keep add research and browse faculty proposals actions.

## Interaction

Buttons and links should remain accessible, keyboard-focusable, and visually consistent. Status badges should retain text labels and not rely on color alone. Tables should remain horizontally scrollable on small screens.

## Testing

Verification should include:

- Django template syntax check via `python manage.py check`.
- Manual browser review of all four dashboard templates if login/test users are available.
- Responsive inspection for desktop and mobile widths, with special attention to table overflow, card wrapping, and text clipping.

## Out of Scope

- Changing dashboard data queries.
- Adding charts or JavaScript dashboards.
- Redesigning the entire base layout or sidebar.
- Changing permissions, role routing, or notification behavior.
