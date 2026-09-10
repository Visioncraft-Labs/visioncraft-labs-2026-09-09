# VisionCraft Labs — approved dark studio direction

This is the private review revision based on the user-supplied static website. The production target remains GitHub → Netlify → visioncraft-labs.com. The Sites deployment is an owner-private review surface, not the primary domain.

## Build and editing

Requires Node 20+ and Python 3.10+. No third-party packages are required for building.

- `npm install` installs the empty dependency manifest.
- `npm run build` generates the 25 pages in `dist`.
- `npm run check` checks page headings, titles, structured data, internal links, anchors and JavaScript syntax.
- `data/projects.json`, `data/services.json`, `data/insights.json` contain reusable content. `scripts/build.py` contains the shared page composition and homepage copy.
- `templates/` preserves the supplied studio, legal, contact and gallery source. Only the appropriate selected sections are used. Edit a source template or the builder; generated HTML will be replaced during the next build.
- `dist/images/` contains the complete media collection. Replace a file while retaining its name, or update its centralized project path. Record changed dimensions in `data/media-dimensions.json` (width, height). No animation changes are required.
- `dist/brand.css` protects the official logo and `dist/experience.css` holds the refinement tokens and responsive styling. `dist/experience.js` owns the progressive interactions.
- To add services or articles, add content using the existing JSON shape. Project media references are centralized near the top of `scripts/build.py`.

## Media provenance and truthful presentation

KarbonKreds: current homepage screenshot captured from https://karbonkreds.com/ on 2026-09-08. Map and context assets retrieved from its existing `karbonkreds-premium` theme. These are website creative assets, not evidence of verified carbon transactions. A contact-page capture exposed visible script output on the live client site, so that image was excluded.

Address12: actual React components from `Address12_10.3.2_TypeScript_Source_With_Tests.zip`, rendered in an isolated screenshot harness with synthetic demonstration data and no guest information. The published site contains the screenshot only, not the private software, credentials, database or runnable admin environment. UI figures are illustrative, not customer outcomes.

Skincare Objects and Daily Ritual are self-initiated mock campaigns, clearly labelled as concepts rather than commissioned client work. All supplied gallery photos/posters and all three MP4 clips are retained.

The AI Lab is a local simulated workflow. It classifies a mock retail website inquiry and prepares a review state. It makes no AI API call and sends no messages. It is not represented as a deployed client engagement.

## Motion and accessibility

The homepage always starts with a populated image. Four project images and a labelled AI concept can be selected. Rotation occurs every six seconds until interaction; a pause control is provided. Image decoding is checked before transitions. All transitions keep a visible populated frame. Desktop pointer tilt, restrained scroll movement, image enlargement and viewport-aware film playback progressively enhance the HTML. Native video controls remain available. Reduced motion disables rotation and automatic playback. Navigation and image dialogs support keyboard operation.

## Contact and analytics

The review form deliberately prepares a mail-app draft; it does not claim server delivery. The visitor must press Send in their mail app. Copyable brief fallback is included. The verified public phone and email are linked. A WhatsApp destination remains unconfigured because a verified company WhatsApp number is still needed. Do not guess one from personal contact history.

The JavaScript prepares dataLayer events for phone, email and project-brief starts. GA4, GTM and Search Console IDs have not been invented or installed. Connect approved IDs before measuring acquisition. Do not label mail-draft creation as a delivered lead.

## SEO and Netlify

`SITE_URL` is the canonical domain. `SITE_MODE=preview` is the default and emits noindex metadata, blocking robots and an empty sitemap. `SITE_MODE=production` enables indexable pages and a 24-URL sitemap, excluding the 404. `netlify.toml` selects production mode only for the production context; branch and deploy previews remain nonindexable.

Nine substantive service pages, four real project case studies, two complete insight articles, unique titles/descriptions, canonical URLs, Organization/WebSite/Breadcrumb/Service/Article structured data and crawlable internal links form the search foundation. `data/keyword-map.json` contains seed search intent targets; search volumes/difficulty and ranking were not measured. No first-page or top-10 ranking is guaranteed. No invented office address, testimonial, metric or result is used.

SEO references: https://developers.google.com/search/docs/fundamentals/seo-starter-guide ; https://developers.google.com/search/docs/appearance/google-images ; https://developers.google.com/search/docs/crawling-indexing/links-crawlable .

Before production: identify the exact Netlify-linked repository, migrate on a review branch, verify build settings and redirects against live URLs, configure the chosen inquiry delivery and analytics, validate domain ownership and submit the production sitemap to Search Console. The connected GitHub account exposes three VisionCraft repositories with the same older Netlify configuration; the current primary-domain binding has not been established. No production branch was changed.

Keep current GitHub/Netlify release available for rollback. Roll back via Netlify's previous successful deployment or revert the reviewed merge. Never replace the main domain merely to make a preview available.

## Media Studio and backend compatibility (September 2026)

All editable media placements now resolve through `data/media.json`; the build no longer overwrites project media edits. Stable placement IDs connect a replacement to the homepage, work, service and case-study views. The official logo remains protected outside this collection. File paths live in the collection, not animation code. `scripts/media.py` validates paths, formats, posters, descriptions and presentation dimensions before generating HTML. Images can become MP4/WebM films without editing layouts. Videos retain posters, native controls, reduced-motion behavior and offscreen pause.

### Review replacements immediately

Open `/admin/`. Select a placement, drop a file (or use the file chooser on mobile), add an accessible description, and save a browser draft. Drafts are stored in IndexedDB on that browser/device. They are **not** server uploads, are not shared between devices, and do not change the website. Export saved changes as `visioncraft-media-update.json` and share that file for application, or apply it to a checkout:

```
python3 scripts/import-media.py /path/to/visioncraft-media-update.json
npm run build
npm run check
```

The importer validates the entire update before modifying the media collection, rejects path traversal, unknown IDs, duplicate entries, oversized or unreferenced assets, and conflicting uploaded filenames. Commit and review the build through the existing preview workflow. The official logo cannot be replaced through this editor. Keep originals: do not delete old assets until no placement or video poster refers to them. Drafts can be lost if browser storage is cleared; export important work.

### Authenticated live editing (prepared, not connected yet)

`/admin/cms.html` contains the Decap CMS GitHub integration, with an editorial draft/review workflow. It remains explicitly disabled in private previews and when the repository is unknown. To activate on the approved Netlify project:

1. Confirm the exact GitHub repository that Netlify deploys; apply this revision to that repository through a reviewed branch.
2. Set `CMS_GITHUB_REPO=owner/repository` and `CMS_GITHUB_BRANCH=main` (or the verified deployment branch).
3. Configure GitHub OAuth for that Netlify project using the official Netlify authentication provider setup. Keep client secrets in Netlify, never in this repository or public configuration. Editor accounts need repository push access.
4. Rebuild on Netlify. Sign in at `/admin/cms.html`, open **Studio media → Images and films**, choose a placement and upload/select a replacement. Update its poster for video, description, caption and crop dimensions. Save a draft, review the deploy preview, then publish when approved.
5. Verify one image and one short film change end to end, including a refresh after deployment. This integration has not been tested against your Netlify account because the linked repository and OAuth configuration are not available here.

GitHub editorial media is stored under `dist/images/uploads`. Direct uploads are limited to 25 MB. Use compressed web-ready films; long/high-resolution video needs a separately configured media service. Decap's GitHub backend does not support Git LFS. CMS client is pinned to Decap 3.8.4 and loaded only in the connected admin; public pages gain no CMS dependency.

### Inquiry submission

The production Netlify context sets `FORM_BACKEND=netlify`. The build emits a named, statically detectable form with `data-netlify`, a honeypot and native POST fallback **only** when `NETLIFY=true`. The frontend submits URL-encoded data, waits for HTTP success, reports errors, prevents duplicate clicks and records a submit event without inquiry details. `/thank-you.html` supports native submissions and is excluded from indexing. Private Sites builds retain the clearly labelled mail-draft behavior; they cannot accidentally claim that a static POST delivered a lead.

Enable Form detection in the Netlify project and configure submission notifications. These account settings and receipt of a real test inquiry remain unverified. Do not describe the form as live until a test appears in Netlify Forms and reaches the configured recipient. Media is Git-backed; inquiries use Netlify Forms; this site does not need a custom database or an unauthenticated upload API.

### Verification and limits

- Build and route checks pass for 26 generated public HTML documents; admin pages are separate and always noindex.
- Four integration tests cover image replacement propagation, image-to-video replacement, rejected imports leaving data unchanged, and Netlify/private build contracts.
- Run `python3 -m unittest discover -s tests -v` after changing media/build/form contracts.
- Live GitHub OAuth, upload persistence through a Netlify deployment, form receipt and email notifications require account-level verification. Static compatibility checks do not prove those external services are connected.
- No primary-domain deployment was performed during this change.

References: https://decapcms.org/docs/github-backend/ · https://decapcms.org/docs/collection-file/ · https://decapcms.org/docs/widgets/file/ · https://docs.netlify.com/manage/forms/setup/

## Social links and film frame update
Social profiles are maintained in `data/socials.json`; phone and WhatsApp destinations are in `data/contact.json`. Clicking the displayed number opens WhatsApp; a separate Call link preserves telephone dialing. Local SVG brand icons come from Simple Icons 15.0.0 (CC0), https://simpleicons.org. Video gallery frames use equal responsive heights and contain-fit footage, independent of media dimensions. Captions align across each row.
