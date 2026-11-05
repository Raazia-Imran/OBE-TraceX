# Walkthrough, preferences and profiles

On the login page, choose **Watch the 36-second story**. This opens a self-hosted, silent animated explanation with captions, six chapters, a seek bar, pause, restart and a direct sign-in link. It is optional and does not delay login. It is an interactive SVG/CSS animation, not an MP4 recording or externally embedded video. The original Trace Prism artwork adapts the project's X logo; no SVGator character or paid asset is copied. Reduced-motion settings suppress floating effects. Switching to another browser tab pauses playback.

The branded request indicator appears during submitted forms, including Google reads. It represents an actual pending request; no artificial 30-second loading delay is added.

The initial cookie notice offers **Essential only** or **Enable preferences**. Only the latter allows remembering that the introduction has been seen. Both choices are equally functional for sign-in. Cookie settings can be reopened, and withdrawing preferences removes the stored introduction flag. No analytics or advertising scripts were added. Privacy text describes the local trial; NED must confirm the deployment contact and retention policy before production.

Both Coordinator and HOD have **My profile**. They can edit first/last name, contact email, and a profile photo, or remove the photo. Changing contact email requires the current password. Email is not a verified identity, sign-in method or recovery channel. The assigned username and access role cannot be changed by profile requests. Password changes use the existing Account security page.

Photos are limited to 2 MB and 16 megapixels, decoded as still JPEG/PNG/WebP, cropped to 256 pixels square, and freshly encoded to JPEG to discard embedded metadata and appended content. They are stored with the account in SQLite/PostgreSQL and served through an authenticated endpoint. There is no public media folder to configure. Database backups now also contain account photos. Profile updates are recorded in the audit history using field names, not passwords or photo data.

After pulling this update on a fresh installation:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
```

## Faculty test workbook

The supplied historical reference is a different, single-sheet layout from the live Google master workbook. It contains 10 students across three groups. Its final totals equal the sum of separately reported stage marks. Five stages use ROUND to a whole mark; Final Report uses CEILING to a whole mark. Rounding only the overall raw sum differs for nine students. This is a reference finding, not authorization to change the tested source formulas.

`tools/review_faculty_workbook.py` reads that specific historical layout, checks reported stage sums and creates a private expected-results JSON plus a roster CSV. It never changes the workbook, enters Google Forms, imports grades or approves results. Student data and reference outputs must remain outside Git. Compare actual replay results against these expected marks before claiming end-to-end accuracy. Reconcile any difference in rounding with the Coordinator before modifying the live grading policy.
