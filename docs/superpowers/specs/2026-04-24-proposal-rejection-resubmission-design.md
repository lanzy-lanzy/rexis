# Proposal Rejection and Resubmission Design

## Goal

Add a structured rejection flow for proposals. When an admin rejects a proposal, the admin can mark which requirements are lacking. The faculty author can then resubmit the rejected proposal with upload fields shown only for the missing requirements.

## Approved Approach

Use a checklist-driven resubmission flow.

Admins review a pending proposal, choose `Rejected`, select missing requirements from a checklist, optionally add custom missing requirements, and leave review notes. The proposal becomes rejected and stores the missing requirement list.

Faculty authors see rejected proposals with a clear resubmission panel. The panel lists the admin feedback and shows upload inputs for the missing requirements. After the faculty submits the requested files, the proposal returns to `Pending` so the admin can review it again.

## Requirement Checklist

The fixed checklist should include:

- Proposal Document
- Budget Letter or Budget PDF
- Workplan
- MOA
- Supporting Image or Evidence

The admin can also add custom missing requirements in free text. Custom items should be visible to the faculty during resubmission and should accept an uploaded document.

## Data Model

Add a proposal requirement tracking model tied to `Proposal`.

Each requirement record stores:

- The parent proposal
- Requirement name
- Whether it came from the fixed checklist or a custom admin item
- Optional uploaded file from faculty
- Upload timestamp
- Whether the requirement has been resubmitted

Keep existing proposal fields for the main proposal document, budget PDF, and supporting image. For checklist items that map to those existing fields, uploading during resubmission should update the existing proposal field too. Custom or extra checklist items should store their uploaded files on the requirement record.

## Admin Flow

On the proposal review page:

- Admin can approve or reject the proposal.
- If rejecting, the page displays the missing requirement checklist.
- Rejection requires at least one checked or custom requirement.
- Rejection requires review notes so the faculty has written guidance.
- Submitting rejection stores the checklist, reviewer, review notes, and reviewed timestamp.

## Faculty Flow

On the proposal detail page:

- Rejected proposals show a rejection summary with review notes and missing requirements.
- Faculty authors can resubmit only their own rejected proposals.
- Upload inputs appear only for requirements marked as missing.
- Submitting the resubmission saves uploaded files, marks those requirements as resubmitted, changes proposal status back to `Pending`, clears the prior reviewer timestamp for the new review cycle, and records document versions when the main proposal document changes.

## Permissions

- Only admins can reject proposals and define missing requirements.
- Only the faculty author can resubmit a rejected proposal.
- Non-authors cannot access the resubmission action.
- Pending proposals continue to use the existing edit flow.

## UI Direction

Use the existing Tailwind templates, but make the review screen more explicit:

- Show proposal summary on the left or top.
- Show decision controls clearly: approve or reject.
- Show the checklist only when `Rejected` is selected.
- Use concise labels and helper text around missing documents.

For faculty, keep resubmission inside the proposal detail page so they do not need to guess where to go. The rejected state should feel actionable, with the missing requirement list and upload controls grouped together.

## Testing

Add Django tests for:

- Admin rejection with selected requirements stores checklist entries and sets status to rejected.
- Rejection without missing requirements is invalid.
- Faculty author can resubmit a rejected proposal with requested files.
- Resubmission changes status back to pending and records uploaded requirement files.
- Non-author cannot resubmit someone else's rejected proposal.
