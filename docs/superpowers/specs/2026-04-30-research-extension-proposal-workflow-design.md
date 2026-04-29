# Research and Extension Proposal Workflow Design

## Goal

Update the proposal workflow so every faculty proposal is reviewed by Research and Extension Staff before the administrator can make the final approval decision. The Research Staff and Extension Staff roles will be merged into one role named `Research & Extension Staff`.

The workflow must also allow Research and Extension Staff to submit a proposal on behalf of a faculty member while keeping the faculty member as the proposal owner.

## Approved Approach

Use a two-stage approval workflow with separate project progress tracking.

Proposal approval status should answer where the proposal is in the approval process:

- `PENDING_RECOMMENDATION`: waiting for Research and Extension Staff review.
- `RECOMMENDED_APPROVAL`: staff recommends admin approval.
- `RECOMMENDED_REVISION`: staff requests revision or resubmission.
- `APPROVED`: admin gave final approval.
- `REJECTED`: admin gave final rejection.

Project progress should answer what happened after admin approval:

- `ONGOING`
- `PRESENTED`
- `COMPLETED`

Approval status and project progress must stay separate so reports can distinguish proposal decisions from project outcomes.

## Role Model

Replace the separate `Research Staff` and `Extension Staff` roles with one merged role:

- `Research & Extension Staff`

Existing users with either old staff role should be treated as the new merged role after migration. The app should show one staff dashboard and one staff permission path for proposal recommendation work.

Faculty departments remain:

- `SOCJE`
- `SAFES`
- `STE`
- `SCS`

## Proposal Ownership

Proposal records should track both the owner and the actual submitter:

- `faculty_author`: the faculty member the proposal belongs to.
- `submitted_by`: the user who created the proposal record.
- `submitted_on_behalf`: true when Research and Extension Staff submitted for a faculty member.

When faculty submits directly, `faculty_author` and `submitted_by` are the same user, and `submitted_on_behalf` is false.

When Research and Extension Staff submits on behalf of faculty, staff must select a faculty author from a dropdown. The proposal appears under the selected faculty member's records, while the detail page still shows which staff user submitted it.

## Approval Workflow

The approved workflow is:

1. Faculty submits a proposal, or Research and Extension Staff submits on behalf of faculty.
2. Proposal starts as `PENDING_RECOMMENDATION`.
3. Research and Extension Staff reviews the proposal first.
4. Staff either recommends admin approval or requests revision.
5. Admin can only approve or reject proposals with `RECOMMENDED_APPROVAL`.
6. Admin gives the final decision: `APPROVED` or `REJECTED`.

If staff requests revision, the proposal uses `RECOMMENDED_REVISION` and returns to the faculty author for resubmission. After resubmission, it returns to `PENDING_RECOMMENDATION`, not directly to admin.

## Staff Recommendation Data

The proposal should store the staff recommendation decision and audit details:

- `recommended_by`
- `recommended_at`
- `recommendation_notes`

Recommendation notes are required when staff requests revision. They are optional but useful when staff recommends admin approval.

Existing admin review fields remain:

- `reviewed_by`
- `reviewed_at`
- `review_notes`

Admin review notes remain required when rejecting.

## Screens

### Proposal Form

Faculty sees the normal proposal submission form. The proposal starts in `PENDING_RECOMMENDATION`.

Research and Extension Staff also sees the proposal form, with an added required faculty dropdown labeled as submitting on behalf of faculty. Staff can select only users with the faculty role.

### Proposal List

The list should support the new approval status filters.

Faculty sees proposals they own, including proposals submitted on their behalf.

Research and Extension Staff sees proposals awaiting recommendation and can also view proposals they submitted on behalf of faculty.

Admin sees all proposals for awareness, but the primary review action appears only for proposals that have been recommended for admin approval.

### Proposal Detail

The detail page should show:

- Faculty author.
- Actual submitter.
- Whether it was submitted on behalf of faculty.
- Staff recommendation status, recommender, date, and notes.
- Admin final decision details, reviewer, date, and notes.
- Project progress status after approval.

### Staff Recommendation Page

Research and Extension Staff gets a dedicated recommendation page.

Allowed actions:

- Recommend for admin approval.
- Request revision or resubmission.

Staff cannot make the final admin approval decision.

### Admin Review Page

Admin review remains the final decision screen.

Admin can only approve or reject if the proposal status is `RECOMMENDED_APPROVAL`. Attempts to review a proposal still waiting for staff recommendation should be blocked with a clear message.

### Staff Dashboard

The merged staff dashboard should show:

- Pending staff recommendations.
- Recommended proposals waiting for admin.
- Ongoing approved projects.
- Presented projects.
- Completed projects.

The existing separate research and extension dashboard concepts can be consolidated into this one staff dashboard.

## Permissions

- Faculty can submit, view, edit while allowed, and resubmit their own proposals.
- Faculty can view proposals submitted on their behalf.
- Research and Extension Staff can submit proposals on behalf of faculty.
- Research and Extension Staff can recommend approval or request revision before admin review.
- Admin can view all proposals.
- Admin can only final-review proposals after staff recommends admin approval.
- Resubmitted proposals return to staff review, not directly to admin review.

## Reporting

Reports should be updated so approval status and project progress can be filtered independently.

Recommended report filters:

- Approval status: pending recommendation, recommended approval, recommended revision, approved, rejected.
- Project progress: ongoing, presented, completed.
- Department: SOCJE, SAFES, STE, SCS.
- Submitter: faculty direct submission or staff on behalf of faculty.

## Testing

Add Django tests for:

- Faculty submission starts as `PENDING_RECOMMENDATION`.
- Research and Extension Staff can submit on behalf of a selected faculty member.
- Staff submission stores both `faculty_author` and `submitted_by`.
- Admin review is blocked before staff recommendation.
- Staff can recommend approval and route the proposal to admin review.
- Staff can request revision and require notes.
- Faculty resubmission returns the proposal to `PENDING_RECOMMENDATION`.
- Admin can approve or reject only after staff recommendation.
- Project progress can be set to `ONGOING`, `PRESENTED`, or `COMPLETED` only after admin approval.

## Out of Scope

- Changing the faculty department list beyond SOCJE, SAFES, STE, and SCS.
- Adding a multi-person recommendation committee.
- Reworking document preview or version history beyond whatever is needed to keep resubmission compatible with the new workflow.
- Building new analytics charts.
