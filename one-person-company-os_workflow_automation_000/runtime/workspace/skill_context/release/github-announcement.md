# GitHub Announcement

I upgraded `one-person-company-os` again.

The previous release made the project easier to understand.
This release makes the artifact system look and behave like real deliverables instead of placeholder management.

The main gaps were:

- generated artifacts still carried too much placeholder and status-marker semantics
- the workspace still exposed document-spec language instead of final-document language
- file names looked like workflow state rather than real deliverables

This release fixes that.

This release includes:

- final-named DOCX deliverables without `[待生成]` and `[已生成]`
- a new deliverable map and deliverable directory overview inside the workspace
- document maturity tracked inside the file content instead of the file name
- updated release validation for the new final-document model
