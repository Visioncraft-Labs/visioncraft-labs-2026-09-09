# Global service SEO and automatic trend updates

The production source is this repository's `main` branch. Netlify builds and publishes changes automatically; manual uploads are unnecessary.

## Stable service content

`data/keyword-map.json` now supplies the nine service pages' titles, descriptions and introductory copy. These are global, commercially relevant phrases grounded in the studio's existing services, not measured rankings or keyword-volume claims. The homepage and service directory also target global clients. Core titles stay stable between trend checks. Google does not use a meta-keywords tag for ranking, so none is added.

## Daily search-trend refresh

`.github/workflows/search-trends.yml` runs daily at approximately 07:17 UTC, manually through Actions, and when its source configuration changes on `main`. GitHub may delay scheduled runs. It fetches the public Google Trends RSS feeds for the US, UK, Canada and Australia. These are sampled markets, not worldwide coverage or Search Console measurements. Feed traffic is not the website's ranking or keyword search volume.

`data/trend-topics.json` contains approved phrases tied to services already offered. Only complete approved phrase matches qualify. Ambiguous single terms and unrelated news are discarded. `scripts/refresh_trends.py` requires all four feeds to be valid before it replaces `data/seo-trends.json` atomically. A source failure leaves the last successful file untouched and fails the workflow; logs remain in GitHub Actions. No API key or new service subscription is needed.

The build can add a small **In focus** area to the homepage and service directory using approved labels and existing service links. External query text and external URLs never become page copy. Observations older than seven days are omitted at build time. Successful refreshes with no relevant matches publish an empty selection, so the block disappears. No match is invented to fill a space. The initial check found no eligible service trends.

Before committing a snapshot, the workflow builds the production site and runs all tests. Only the validated trend and opportunity JSON snapshots are committed. Git push is not forced: a concurrent change safely aborts publication, and the next daily run tries again. Netlify's connected repository deploys the resulting commit. GitHub's bot commits do not start other GitHub Actions workflows; this workflow performs validation itself. The updated check time records feed monitoring, not a fabricated content-publication date.

## Crawl protections

`scripts/check_seo.py` runs on every build. Production pages must be indexable, have correct canonicals and unique titles/descriptions, and appear in the sitemap. The public robots.txt permits crawling. Admin screens, 404 responses and thank-you pages remain excluded intentionally. Private deployment previews remain noindex to avoid duplicate copies competing with the public domain.

The live audit on 2026-10-04 checked all 24 pre-update sitemap URLs: HTTP 200, indexing allowed, matching canonicals and no restrictive HTTP robots headers. A Googlebot User-Agent also received HTTP 200. These checks cover site configuration and accessibility, not guaranteed indexing, external search-engine behavior or ranking. Search Console access is needed to measure actual impressions, queries and positions.

## Local verification

```sh
SITE_MODE=production npm run build
python3 -m unittest discover -s tests
python3 scripts/refresh_trends.py
```

New service phrases should be reviewed against actual offered capabilities before being added to the catalog. The automation updates relevant topics; it does not generate thin articles or continually rewrite the brand's core messaging.

## Etsy and freelance project discovery

The focused `/etsy-seller-services` page offers existing branding, listing imagery and digital creative capabilities to Etsy sellers. It is linked from the homepage, service directory and footer. It does not imply an existing Etsy account or Etsy client history. The contact form includes an Etsy project option. Netlify form detection was enabled for the existing site so the next deployment can register the production inquiry form; submissions can be reviewed in Netlify Forms. Notifications require separate account configuration. No trial inquiry was submitted.

`/admin/opportunities.html` contains recent public project briefs with Etsy matches first, text filtering and direct links to the original requests. `scripts/opportunities.py` fetches eight public Freelancer searches (Etsy, web design, branding, Blender, UI UX, AI automation, product photography and video editing) and rejects private, closed, stale or unrelated records. Project data is escaped before display, and links are constructed from validated IDs. Up to100 current matches are shown. Each source is checked completely before an atomic snapshot replacement.

The same daily workflow updates `data/opportunities.json`. Trend and opportunity fetches run independently: a successful source can publish while the other preserves its last-good snapshot. A failed source is explicitly reported as a workflow failure after validation/publication. No three-hour refresh or automatic renewal is configured. There is no automatic bidding, outreach or paid account action.

The dashboard is noindex under the existing `/admin/*` rules, **not access protected**. It contains public project data only. It also links to Upwork, PeoplePerHour, Contra, Fiverr,99designs, Behance, Dribbble, LinkedIn and Etsy. Account-only messages, matched briefs and applications remain on those platforms. Upwork discontinued public RSS in2024; use its supported saved searches and alerts. Etsy is a storefront for creative deliverables and buyer orders, not a public freelance job feed. No platform accounts were connected or invented.

Sources: [Etsy creative service policy](https://www.etsy.com/legal/policy/services/242665313101), [Upwork RSS deprecation](https://support.upwork.com/hc/en-us/articles/52052528243731-RSS-deprecation), [Freelancer Etsy requests](https://www.freelancer.com/jobs/etsy/).
