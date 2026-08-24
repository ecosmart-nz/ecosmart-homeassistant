# Brand images for the home-assistant/brands pull request

These three files go into the [home-assistant/brands](https://github.com/home-assistant/brands)
repository at:

```
core_integrations/ecosmart/icon.png
core_integrations/ecosmart/icon@2x.png
core_integrations/ecosmart/logo.png
```

`core_integrations/`, not `custom_integrations/` — the brands PR is opened the same day
as the core pull request, for an integration that is being submitted to core.

Regenerate with `scripts/make-brand-images.py` (needs cairosvg, so run it under WSL or
Linux — see the docstring). Verified on write: every file is re-opened and asserted for
exact dimensions, RGBA mode, and an alpha channel that actually reaches both 0 and 255.

## Provenance

| Output | Size | Source | Transform |
|---|---|---|---|
| `icon.png` | 256 × 256 | `ecosmart_website/public/images/brand/mark-256.png` | copied byte-for-byte |
| `icon@2x.png` | 512 × 512 | `ecosmart_website/public/favicon.svg` | rendered at 4096 px, cropped to its ink, scaled once to 444 × 374 and placed at (34, 34) — the same layout `mark-256.png` uses, doubled |
| `logo.png` | 640 × 128 | `ecosmart_website/public/images/brand/lockup-640.png` | copied byte-for-byte |

All three are RGBA with a genuinely transparent background.

## Why the 2× icon comes from the vector

There is no raster copy of the Ecosmart mark larger than 256 px with a transparent
background. Nothing in the brand folder or any of the apps supplies one:

- `mark-256.png` — 256 × 256, transparent. The 1× icon, used as-is.
- `mark-128.png` — 128 × 128. Smaller still.
- `logo-512.png` — 512 × 512 canvas, but the artwork inside it is the **stacked lockup**
  (mark above the word "ecosmart"), not the mark. Ink measures 430 × 212. Using it as
  `icon@2x.png` would put a wordmark in the icon slot while `icon.png` shows the bare
  mark — two different pictures at two zoom levels.
- `synergy-app/assets/icon/app_icon_foreground.png` — 1024 × 1024, but it is a **white**
  bolt for the Android adaptive-icon foreground layer, invisible on a light background.
- Every other 512/1024 app icon is fully opaque with a baked-in background.

Upscaling `mark-256.png` to 512 would invent detail, so that was ruled out. Instead
`favicon.svg` — the mark drawn as vector paths, and the only resolution-independent copy
that exists — is rendered at the size wanted.

That vector was checked against the raster master before being trusted: rendering it at
256 px into the same layout as `mark-256.png` gives an aspect-ratio agreement of **0.34 %**,
a mean absolute RGB difference of **3.09 / 255** and an alpha intersection-over-union of
**0.949** (the remainder is antialiasing at the edges). It is the same drawing.

## What is missing

**`logo@2x.png` is not supplied.** It would need a wordmark lockup of at least
1280 × 256, and the widest master that exists is `lockup-640.png` at 640 × 128. There is
no vector of the wordmark — `favicon.svg` covers the mark only. Producing a 2× logo would
mean upscaling, which would show. It is optional in the brands repo, so the PR goes
without it.

To close that gap, Daryn would need to export from the design source:

- `lockup-1280.png` — the horizontal lockup at 1280 × 256, transparent background, tight
  crop (ink touching all four edges, exactly as `lockup-640.png` is cropped).

Drop it in `ecosmart_website/public/images/brand/`, add it to
`scripts/make-brand-images.py`, and re-run.

## One thing to re-check at PR time

The brands repository states maximum dimensions for `logo.png` in its own README, and
this repo has not verified the current numbers against it. `logo.png` here is 640 × 128,
which is the shipped master at full size. If the brands CI rejects the width, downscale
rather than re-export — the transform is a plain Lanczos resize and loses nothing that
matters:

```python
from PIL import Image
Image.open("logo.png").resize((512, 102), Image.LANCZOS).save("logo.png")
```
