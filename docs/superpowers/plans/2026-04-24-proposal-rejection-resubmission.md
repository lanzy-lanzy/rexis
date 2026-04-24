# Proposal Rejection Resubmission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build checklist-based proposal rejection so admins can request missing requirements and faculty can upload only those requirements during resubmission.

**Architecture:** Add a `ProposalRequirement` model as child state for rejected proposals. Keep the existing proposal document, budget, and image fields as canonical fields for known mapped uploads, while storing every resubmission file on its requirement record for auditability.

**Tech Stack:** Django 4.2, Django forms, function-based views, Django template/Tailwind UI, SQLite in development, Django `TestCase`.

---

## File Structure

- Modify `proposals/models.py`: add requirement constants and `ProposalRequirement`.
- Modify `proposals/forms.py`: add rejection checklist validation and dynamic resubmission form.
- Modify `proposals/views.py`: store rejection requirements and add resubmission endpoint.
- Modify `proposals/urls.py`: add `proposal_resubmit`.
- Modify `templates/proposals/proposal_review.html`: show reject checklist conditionally.
- Modify `templates/proposals/proposal_detail.html`: show rejected proposal resubmission panel.
- Modify `proposals/tests.py`: add behavior tests for rejection and resubmission.
- Create `proposals/migrations/0004_proposalrequirement.py`: schema migration.

### Task 1: Failing Tests

**Files:**
- Modify: `proposals/tests.py`

- [ ] **Step 1: Write failing tests**

Add tests for admin rejection, invalid rejection, faculty resubmission, and non-author protection using Django `Client` requests and `SimpleUploadedFile`.

- [ ] **Step 2: Run tests to verify failure**

Run: `python manage.py test proposals`

Expected: failures caused by missing `ProposalRequirement`, missing form fields, and missing resubmission URL.

### Task 2: Requirement Model

**Files:**
- Modify: `proposals/models.py`
- Create: `proposals/migrations/0004_proposalrequirement.py`

- [ ] **Step 1: Implement model**

Add a child model with fields: `proposal`, `requirement_key`, `label`, `is_custom`, `uploaded_file`, `uploaded_at`, `is_resubmitted`, `created_at`, `updated_at`.

- [ ] **Step 2: Create migration**

Run: `python manage.py makemigrations proposals`

- [ ] **Step 3: Run tests**

Run: `python manage.py test proposals`

Expected: model import errors gone; form/view failures remain.

### Task 3: Forms

**Files:**
- Modify: `proposals/forms.py`

- [ ] **Step 1: Implement rejection form validation**

Extend `ProposalReviewForm` with a fixed checklist and custom requirements textarea. If status is rejected, require review notes and at least one missing requirement.

- [ ] **Step 2: Implement dynamic resubmission form**

Add `ProposalResubmissionForm` that receives requirement records and creates one file field per unresolved requirement.

- [ ] **Step 3: Run tests**

Run: `python manage.py test proposals`

Expected: form validation failures gone; missing view persistence may remain.

### Task 4: Views and URLs

**Files:**
- Modify: `proposals/views.py`
- Modify: `proposals/urls.py`

- [ ] **Step 1: Store missing requirements on rejection**

When an admin rejects, replace unresolved requirement records with the selected checklist/custom items, save reviewer metadata, and keep approval behavior unchanged.

- [ ] **Step 2: Add faculty resubmission view**

Allow only the faculty author to post uploads for rejected proposals. Save requirement files, update mapped proposal fields, create document versions for main proposal document uploads, and move status back to pending.

- [ ] **Step 3: Run tests**

Run: `python manage.py test proposals`

Expected: behavior tests pass except template rendering issues.

### Task 5: Templates

**Files:**
- Modify: `templates/proposals/proposal_review.html`
- Modify: `templates/proposals/proposal_detail.html`

- [ ] **Step 1: Redesign admin review page**

Add a clear approve/reject selector, notes field, and missing requirement checklist that appears when `Rejected` is selected.

- [ ] **Step 2: Add faculty rejected-state panel**

Show review notes, missing requirements, current uploaded status, and upload inputs for unresolved requirements.

- [ ] **Step 3: Run tests**

Run: `python manage.py test proposals`

Expected: all proposal tests pass.

### Task 6: Final Verification

**Files:**
- No file edits expected.

- [ ] **Step 1: Apply migrations locally**

Run: `python manage.py migrate`

- [ ] **Step 2: Run proposal tests**

Run: `python manage.py test proposals`

- [ ] **Step 3: Run project checks**

Run: `python manage.py check`

Expected: zero failures and no system check issues.
