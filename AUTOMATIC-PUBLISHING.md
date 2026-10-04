# Media descriptions and automatic Netlify publishing

The existing Netlify site is linked to `Visioncraft-Labs/visioncraft-labs-2026-09-09`, branch `main`. Its `netlify.toml` runs `npm run build`. Git updates to that production branch are the publishing source; uploading a folder to Netlify is unnecessary.

Edit a media description once in `data/media.json`. The existing build inserts it into every use of that media item. `alt` supplies meaningful image alternative text or a video's accessible name. An optional `description` supplies a fuller text alternative for silent motion. Video descriptions are linked with `aria-describedby` and supplied as browser fallback text. Decorative icons intentionally keep empty alt attributes because their containing links already have accessible names.

Every Netlify build validates the media collection and all generated HTML. Missing image alt attributes, blank portfolio-image descriptions, unnamed videos, and missing linked video descriptions fail the build before publication. The GitHub workflow runs the same checks and compatibility tests on pushes and pull requests.

When introducing a genuinely new image or film, provide its factual description once. The build propagates it automatically; it does not invent visual details from a filename. Existing descriptions remain stable until the actual asset content changes.

This change does not replace the live site's design with the separate ivory/sage preview. It strengthens the production repository's existing media and build pipeline. Descriptive text improves accessibility and helps search engines understand the page; no description or publishing workflow guarantees a search ranking.
