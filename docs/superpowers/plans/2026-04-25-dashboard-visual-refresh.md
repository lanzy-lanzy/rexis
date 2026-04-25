# Dashboard Visual Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a formal, modern, Executive Clean visual refresh for the Admin, Faculty, Extension Staff, and Research Staff dashboards.

**Architecture:** Keep the existing Django view functions, context variables, URLs, and base layout. Add lightweight dashboard smoke tests, then update the four role dashboard templates with a shared Executive Clean visual language: dark dashboard header band, polished metric cards, restrained panels, readable tables/lists, and consistent badges.

**Tech Stack:** Django 4.2 templates, Django `TestCase` and test client, Tailwind CSS utility classes already loaded in `templates/base.html`.

---

## File Structure

- Modify `portal/tests.py`: add role dashboard render tests that fail until the refreshed layout markers exist.
- Modify `templates/portal/admin_dashboard.html`: admin overview metrics, recent proposals, and compact quick actions.
- Modify `templates/portal/faculty_dashboard.html`: faculty summary metrics and proposals table.
- Modify `templates/portal/extension_dashboard.html`: extension activity metrics and activities table.
- Modify `templates/portal/research_dashboard.html`: research metrics, projects panel, and abstracts action panel.

### Task 1: Dashboard Render Tests

**Files:**
- Modify: `portal/tests.py`

- [ ] **Step 1: Write failing tests**

Replace `portal/tests.py` with:

```python
from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser, UserRole


class DashboardVisualRefreshTests(TestCase):
    def make_user(self, username, role):
        return CustomUser.objects.create_user(
            username=username,
            password='password123',
            role=role,
        )

    def assert_dashboard_shell(self, user, expected_heading):
        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-dashboard-shell')
        self.assertContains(response, expected_heading)
        self.assertContains(response, 'Operational summary')
        self.assertContains(response, 'metric-card')

    def test_admin_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('admin-user', UserRole.ADMIN)

        self.assert_dashboard_shell(user, 'Admin Workspace')

    def test_faculty_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('faculty-user', UserRole.FACULTY)

        self.assert_dashboard_shell(user, 'Faculty Workspace')

    def test_research_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('research-user', UserRole.RESEARCH_STAFF)

        self.assert_dashboard_shell(user, 'Research Workspace')

    def test_extension_dashboard_uses_formal_operations_layout(self):
        user = self.make_user('extension-user', UserRole.EXTENSION_STAFF)

        self.assert_dashboard_shell(user, 'Extension Workspace')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test portal`

Expected: tests fail because dashboard responses do not yet contain `data-dashboard-shell`, role workspace headings, and `Operational summary`.

- [ ] **Step 3: Commit failing tests**

Run:

```bash
git add portal/tests.py
git commit -m "test: cover refreshed dashboard layout markers"
```

### Task 2: Admin Dashboard Template

**Files:**
- Modify: `templates/portal/admin_dashboard.html`

- [ ] **Step 1: Replace admin template with operations-dense layout**

Use this structure in `templates/portal/admin_dashboard.html`:

```django
{% extends 'base.html' %}

{% block page_title %}Overview{% endblock %}
{% block page_title_mobile %}Admin Dashboard{% endblock %}

{% block content %}
<section data-dashboard-shell data-dashboard-variant="executive-clean" class="space-y-6">
    <div class="overflow-hidden rounded-lg border border-slate-800 bg-slate-950 shadow-soft">
        <div class="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
                <p class="text-xs font-semibold uppercase tracking-widest text-blue-200">Operational summary</p>
                <h1 class="mt-1 text-2xl font-bold tracking-tight text-white">Admin Workspace</h1>
                <p class="mt-1 max-w-2xl text-sm text-slate-300">Monitor proposals, research, extension activities, and user activity from a refined institutional overview.</p>
            </div>
            <div class="flex flex-wrap gap-2">
                <a href="{% url 'proposal_list' %}?status=PENDING" class="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30">Review Pending</a>
                <a href="{% url 'user_management' %}" class="inline-flex items-center rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500/40">Manage Users</a>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <!-- metric cards keep existing context variables: total_proposals, pending_proposals, total_research, ongoing_research, total_extension, ongoing_extension, total_users, faculty_count -->
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <!-- recent proposals panel spans two columns, compact actions panel uses one column -->
    </div>
</section>
{% endblock %}
```

Add four `.metric-card` panels in the metric grid: proposals with `{{ total_proposals }}` and `{{ pending_proposals }}`, research with `{{ total_research }}` and `{{ ongoing_research }}`, extension with `{{ total_extension }}` and `{{ ongoing_extension }}`, and users with `{{ total_users }}` and `{{ faculty_count }}`. Preserve the existing recent proposals loop, status badge logic, empty state, and quick action URLs.

- [ ] **Step 2: Run focused tests**

Run: `python manage.py test portal.DashboardVisualRefreshTests.test_admin_dashboard_uses_formal_operations_layout`

Expected: admin dashboard test passes or fails only because other dashboard templates are not updated yet.

### Task 3: Faculty Dashboard Template

**Files:**
- Modify: `templates/portal/faculty_dashboard.html`

- [ ] **Step 1: Replace faculty template with operations-dense layout**

Create a `data-dashboard-shell` section with heading `Faculty Workspace`, subtitle `Operational summary`, a primary `Submit Proposal` action, four `.metric-card` panels for total, pending, approved, and rejected proposals, and the existing proposal table.

Keep these existing values and links:

```django
{{ total_proposals }}
{{ pending_proposals }}
{{ approved_proposals }}
{{ rejected_proposals }}
{% url 'proposal_create' %}
{% url 'proposal_detail' proposal.pk %}
```

- [ ] **Step 2: Run focused tests**

Run: `python manage.py test portal.DashboardVisualRefreshTests.test_faculty_dashboard_uses_formal_operations_layout`

Expected: faculty dashboard test passes.

### Task 4: Extension Dashboard Template

**Files:**
- Modify: `templates/portal/extension_dashboard.html`

- [ ] **Step 1: Replace extension template with operations-dense layout**

Create a `data-dashboard-shell` section with heading `Extension Workspace`, subtitle `Operational summary`, a primary `New Activity` action, four `.metric-card` panels for total activities, planning, ongoing, and completed, and the existing extension activities table.

Keep these existing values and links:

```django
{{ total_extension }}
{{ planning_extension }}
{{ ongoing_extension }}
{{ completed_extension }}
{% url 'extension_create' %}
{% url 'extension_detail' ext.pk %}
```

- [ ] **Step 2: Run focused tests**

Run: `python manage.py test portal.DashboardVisualRefreshTests.test_extension_dashboard_uses_formal_operations_layout`

Expected: extension dashboard test passes.

### Task 5: Research Dashboard Template

**Files:**
- Modify: `templates/portal/research_dashboard.html`

- [ ] **Step 1: Replace research template with operations-dense layout**

Create a `data-dashboard-shell` section with heading `Research Workspace`, subtitle `Operational summary`, a primary `Add Research` action, four `.metric-card` panels for total research, ongoing, published, and approved proposals, then preserve the research projects loop and faculty abstracts link.

Keep these existing values and links:

```django
{{ total_research }}
{{ ongoing_research }}
{{ published_research }}
{{ approved_proposals }}
{% url 'research_create' %}
{% url 'research_detail' research.pk %}
{% url 'faculty_abstracts' %}
```

If `research_detail` is not currently used in the template, keep the row non-clickable and do not invent a new URL.

- [ ] **Step 2: Run focused tests**

Run: `python manage.py test portal.DashboardVisualRefreshTests.test_research_dashboard_uses_formal_operations_layout`

Expected: research dashboard test passes.

### Task 6: Full Verification

**Files:**
- Verify: all modified files

- [ ] **Step 1: Run dashboard tests**

Run: `python manage.py test portal`

Expected: all four dashboard visual refresh tests pass.

- [ ] **Step 2: Run Django system check**

Run: `python manage.py check`

Expected: `System check identified no issues`.

- [ ] **Step 3: Review changed files**

Run: `git diff -- portal/tests.py templates/portal/admin_dashboard.html templates/portal/faculty_dashboard.html templates/portal/extension_dashboard.html templates/portal/research_dashboard.html`

Expected: only dashboard tests and dashboard template visual refresh changes appear.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add portal/tests.py templates/portal/admin_dashboard.html templates/portal/faculty_dashboard.html templates/portal/extension_dashboard.html templates/portal/research_dashboard.html docs/superpowers/plans/2026-04-25-dashboard-visual-refresh.md
git commit -m "style: refresh role dashboards"
```
