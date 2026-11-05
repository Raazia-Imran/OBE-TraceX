# Baseline inspection

Inspected the seven newly uploaded workflow exports, uploaded FYDP_Master_Database.xlsx, Rameen's FYDP_STRATEGY, and supplied original D1–D7 documents. Original workflow/workbook files were read only; their working copies were not rewritten.

## Verified observations

- All seven exported workflows have `active: false` in the supplied files. This is export metadata, not a claim about the running localhost instance.
- Workflow inputs: D1_Averaged_QEC, D2_S1_Progress, D3_Averaged_QEC, D4_S2_Progress, D5_Averaged_QEC, D6_Averaged_QEC, and ` D7_CONSOLIDATED_GRADING` (leading space).
- Workflows 1, 3, 5, 6 and 7 have If nodes for release checkboxes. Workflows 2/4 use direct response paths.
- All seven Convert to File nodes use `operation: toText` and `.html` filenames. Genuine automatic PDF bytes are not produced by these nodes.
- The supplied templates contain QEC references and a four-member group summary table. D1–D6 include additional rubric pages that must be retained.
- Workflow 4 scales Intellectual Contribution by .16 and the other four criteria by .08, matching the supplied D4 maxima.
- The workbook D7 formula instead averages all five D4 percentages and multiplies by .48. Unequal criterion weights are therefore lost.
- For 50% on the first four D4 criteria and 0% timely submission: correct D4 is 20/48; the equal-weight formula gives 19.2. For 75% on those criteria and 0% timely submission: correct D4 is 30; the equal-weight formula gives 28.8.
- Successful all-maximum historical cases can hide that discrepancy. Preserve the reported historical success and add uneven weighting regression cases.
- Individual report layouts differ from the official QEC forms and still contain references. Removal remains a separate tested n8n change, as requested by the user.
- The repository was empty and public when inspected. Raw workflow exports include account bindings and recipients; these are not published in this repository. Private student workbook data is also excluded.
- With the user's explicit remote-access authorization, a read-only GET to the laptop's `http://localhost:5678/healthz` returned HTTP 200. No n8n workflow was imported, changed, executed or deleted.

## Form inspection limit

The supplied screenshots show D1–D6 form titles and multiple copies. The common Forms home URL does not identify the six canonical forms or establish current account access. Response column structures can be inspected from the workbook, but form settings and active destinations remain to be verified from their actual editor/preview URLs.
