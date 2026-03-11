# Implementation Plan: Enhancements (Document Management & Omni-Search)

This document outlines the changes necessary to implement the requested enhancements: Document Versioning, In-App PDF Preview, and Global Omni-Search.

## User Review Required
Before proceeding to execution, please review if adding a `ProposalDocumentVersion` model fits your desired database schema for versioning, and if a dedicated search results page is acceptable for the Global Omni-Search.

## Proposed Changes

### Core (Search Functionality)
#### [MODIFY] [core/views.py](file:///c:/Users/gerla/revision/rexis/core/views.py)
- Add a new view `global_search(request)` that queries [Proposal](file:///c:/Users/gerla/revision/rexis/proposals/models.py#16-64), [ResearchRecord](file:///c:/Users/gerla/revision/rexis/research/models.py#13-50), [ExtensionRecord](file:///c:/Users/gerla/revision/rexis/extension/models.py#22-69), and `User` models based on the `q` GET parameter.
#### [MODIFY] [rexis/urls.py](file:///c:/Users/gerla/revision/rexis/rexis/urls.py)
- Add routing for the `/search/` endpoint.
#### [MODIFY] [templates/base.html](file:///c:/Users/gerla/revision/rexis/templates/base.html)
- Add a search input field in the top navigation bar.
#### [NEW] `templates/core/search_results.html`
- A new page to display the categorized search results.

---

### Proposals (Document Versioning & Preview)
#### [MODIFY] [proposals/models.py](file:///c:/Users/gerla/revision/rexis/proposals/models.py)
- Create a new model `ProposalDocumentVersion`.
```python
class ProposalDocumentVersion(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='document_versions')
    document = models.FileField(upload_to='proposals/documents/versions/')
    version_number = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # optional: notes about what changed
    version_notes = models.TextField(blank=True)
```
#### [MODIFY] [proposals/views.py](file:///c:/Users/gerla/revision/rexis/proposals/views.py)
- When updating a proposal and a new document is provided, create a new `ProposalDocumentVersion` entry with an incremented version number.
#### [MODIFY] [templates/proposals/proposal_research_detail.html](file:///c:/Users/gerla/revision/rexis/templates/proposals/proposal_research_detail.html) (and similar details)
- Add a "Version History" section showing the previous versions.
- Add a "Preview" button using Alpine.js.
- Add a modal containing a `<canvas>` or `<iframe>` driven by `pdf.js` from a CDN to render the document in-browser without downloading.

## Verification Plan
### Manual Verification
- Upload multiple documents to a proposal to test version incrementation.
- View the versions tab on the detail page to verify the list of historical files.
- Click "Preview" on a PDF file and ensure the modal opens and renders the PDF pages within the browser.
- Type in the search bar in the top navigation and submit, verifying that results from Proposals, Research, and Extensions correctly populate in the search results page.
