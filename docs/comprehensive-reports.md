# Comprehensive Reports

The **Comprehensive Reports** feature gives faculty, administrators, research staff, and extension staff a printable and exportable view of Research & Extension (MIS) records.

## Access

Authenticated users can open the page from the sidebar by selecting **Reports**.

The report is available at:

```text
/reports/
```

PDF export is available at:

```text
/reports/pdf/
```

## Role-Based Scope

The report automatically changes based on the logged-in user's role.

| Role | Report Scope |
| --- | --- |
| Administrator | Institution-wide proposals, research records, extension activities, and narrative reports |
| Faculty | Records authored by the faculty member or records where they are listed as a research or extension participant |
| Research Staff | Research proposals and research records assigned to the staff member |
| Extension Staff | Extension proposals and extension activities assigned to the staff member |

## Report Contents

The report includes:

- Summary cards for proposals, research records, extension activities, and narrative reports
- Proposal status totals
- Research status totals
- Extension status totals
- Proposal table
- Research records table
- Extension activities table
- Narrative reports table

## Filters

Users can refine the report with:

- Search keyword
- Record type
- Status
- Start date
- End date

The same filters apply to the on-screen report, the printable report, and the exported PDF.

## Printing

The **Print** button opens the browser print dialog. The print layout hides the sidebar, top navigation, and filter controls so the printed output focuses on the report content.

## PDF Export

The **Export PDF** button downloads a PDF version of the report. Active filters are preserved in the PDF export link, so the exported document matches the current filtered report.

## Implementation Notes

The feature is implemented through:

- `core/reports.py` for role scoping, filtering, summary data, and PDF generation
- `core/views.py` for the report and PDF views
- `rexis/urls.py` for `/reports/` and `/reports/pdf/`
- `templates/core/comprehensive_reports.html` for the report interface
- `templates/base.html` for the sidebar link
- `core/tests_reports.py` for report access, scoping, filtering, and PDF response tests
