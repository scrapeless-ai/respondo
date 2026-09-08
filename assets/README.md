# Artwork provenance

## Scrapeless product identity

The repository is presented as **Respondo by Scrapeless** for the
`scrapeless-ai/respondo` publication target. The README opens with a unified
**Scrapeless Respondo** raster banner, with charcoal, white and restrained teal
styling. Its accessible image heading supplies the product name and tagline
without repeating a separate logo/title stack. The exact official SVG wordmark
remains available below as the authoritative source. The older rainbow feature illustration is
retained for source-history continuity but no longer displayed in the README.
Brand marks remain their owners' property; the existing code license and notice
are unchanged. These assets do not establish a support SLA or publication status.

- `scrapeless-logo.svg`: official vector wordmark extracted from the header of
  https://www.scrapeless.com/en on 2026-09-07. Its path geometry and teal colors
  are unchanged. The `--grey-12` theme variable is resolved to `#171717` for
  standalone use on a light background.
- `scrapeless-respondo-banner.png`: current README hero, generated with the
  built-in image tool on 2026-09-08 using the prior banner as the redesign target
  and a browser-rendered official SVG as the logo reference. It unifies the
  Scrapeless and Respondo names and illustrates HTML to JSON/CSV transformation.
  A second, targeted generation requested a flatter logo. The raster mark remains
  reference-generated, not a pixel-exact reproduction of the official geometry;
  use `scrapeless-logo.svg` whenever exact vector fidelity is required.
  The full prompts are recorded in [banner-prompt.md](banner-prompt.md).
- `respondo-scrapeless-banner.png`: generated with the built-in image generation
  tool using a rendered reference of that official wordmark. Visually checked
  for readable Respondo/Scrapeless branding, tagline, and feature line. The logo
  in the raster banner is reference-based; the SVG above preserves the official
  source geometry. This previous design is preserved but no longer displayed in
  the README. The original generated output was preserved outside the repo.
- `banner-dark.svg`, `features.svg`, `social-preview.svg`: retained from the
  supplied source archive. The README now uses the new banner and a text-based
  feature table. The banner's light canvas remains legible in both themes.

## Previous banner prompt

Use case: ads-marketing. Asset type: GitHub README banner for the Respondo Python library, a finished wide landscape raster graphic, approximately 3:1 aspect ratio, high resolution. Input image 1 is an official Scrapeless logo reference, not a screenshot to reproduce. Preserve that exact black-and-teal circular wave emblem and lowercase scrapeless wordmark, with their real shapes, proportions and lettering. Ignore the browser scrollbar in the reference. Design a refined developer-tool banner on a clean warm-white/ivory background, restrained teal and deep charcoal accents. Place the authentic Scrapeless logo modestly at upper left with generous clear space. Main hero title below it, large and exceptionally readable: "Respondo". Subtitle exactly: "Parse the web. Shape the data." Smaller footer line exactly: "Python · Zero dependencies · CLI included". On the right, create a beautiful restrained dimensional illustration of an HTML document transforming into organized JSON data: three floating thin ivory panels, teal edges, subtle soft shadows, delicate connecting lines, a few readable curly braces and simple ordered data rows. Avoid dense code or random text. Plenty of breathing room, polished editorial typography, precise alignment, premium software brand aesthetic. No purple, no neon, no busy background, no unnecessary badges, no invented logos, no extra words, no watermarks. The authentic Scrapeless logo and Respondo title must both be prominent and fully visible with safe margins.
