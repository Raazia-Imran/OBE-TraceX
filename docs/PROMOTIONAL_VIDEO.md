# Promotional film and opening animation

`OBE-TraceX-Promo-60s.mp4` is a 60-second portrait social-media film: 1080 × 1920 pixels, 24 fps, H.264 video, stereo AAC audio and web-friendly fast-start metadata. Eight animated scenes explain the assessment process. The instrumental score is composed and synthesized by the included renderer; no commercial music track, student record or external video footage is used. This is a project showcase, not a claim of production deployment or verified accuracy for a full historical group.

The main visual source is `media-src/render_promo.py`. It requires Python, Pillow, NumPy and FFmpeg in an offline media environment. The website itself does not require NumPy or FFmpeg. Run from the repository root and provide a private output directory. The renderer writes the MP4, its original WAV score and preview frames. Generated media is delivered separately instead of being committed to Git.

`media-src/make_wordmark.py` creates the self-drawing OBE-TraceX wordmark from URW Base35 Z003 italic letterforms. Typography uses installed URW Base35 and Open Sans fonts; these are not a custom font or a registered trademark. The generated wordmark is included as SVG paths and animated with CSS. Replay is available on the login page. Sign-in remains immediately usable, and reduced-motion preferences suppress the drawing animation.

Public process copy refers to the system, linked sheets and the master workbook. It avoids implying that the public viewer owns the project or spreadsheet. Account-specific labels such as My profile remain appropriate to the signed-in account.
