# External Technology Handbook — Volume 03
## Research, Search, Evidence, Intelligence and Media Rights
**Document ID:** NDX-TECH-HB-V03  
**Version:** 0.1  
**Research date:** 2026-11-04  
**Status:** Research draft — architecture and evaluation guidance, not implementation authorization  
**Parent:** External Technology Handbook Master Map 0.1  
**Scope:** NEXTDECODE Content OS and existing Shorts Studio specialist production engine

---

## 1. Executive decision

NEXTDECODE should treat research as an evidence-production pipeline, not as “search the web and ask an LLM to summarize.”

Core recommendations:
1. Separate discovery from verification. Search results and social posts identify leads; they do not establish truth.
2. Represent claims and evidence explicitly. Preserve source identity, exact URL, publisher/author, publication time, retrieval time, relevant excerpt or locator, source type, confidence and limitations.
3. Preserve provenance through every transformation. A script claim should be traceable to supporting evidence and the source version used when the claim was reviewed.
4. Use source diversity, not result count. Ten copies of one press release are not ten independent sources.
5. Treat trend signals as weak evidence. Search interest, social engagement and news volume are different measurements and do not prove demand, truth or importance.
6. Treat every media asset as a separate rights decision. A search result, API response or “royalty-free” label is not blanket clearance.
7. Block ambiguous rights. If commercial use, adaptation, attribution, territory, personality/privacy, trademark or source authenticity is uncertain, do not put the asset in a publishable package.
8. Keep research and rights findings advisory. Research agents can extract, compare and flag; they cannot certify legal rights, approve content or authorize publishing.

**Recommended direction:** use existing Shorts Studio research and asset-source code as the baseline; preserve claim/evidence/lineage concepts; evaluate Exa as an optional web research API, OpenAlex and Crossref for scholarly metadata, and official APIs/feeds for platform-specific discovery. Do not build a new general-purpose scraper. Retain Wikimedia, Pexels and Pixabay as asset discovery sources only with per-asset rights verification.

---

## 2. Current Shorts Studio baseline

The read-only baseline inventory identifies these existing capabilities and source references:

| Capability | Existing code/document reference | What is evidenced | What remains unknown |
|---|---|---|---|
| Topic discovery | app/research/topics.py, trends.py, selector.py | Discovery and trend-selection paths are documented | Current live sources, exact behavior and provider state |
| Source reading | app/research/desk.py | Source-reading/evidence extraction module is identified | Current extraction quality, freshness and coverage |
| Claim extraction | app/research/claims.py, atomic.py | Claim-oriented modules are identified | Canonical claim schema and runtime evidence |
| Evidence lineage | app/research/lineage.py, app/script/evidence.py | Lineage/evidence paths are identified | Whether lineage is complete and immutable end-to-end |
| Wikimedia asset metadata | app/visuals/stock_fetcher.py | Source code reportedly records licence, author, licence URL and page URL | Verification accuracy, edge cases and actual clearance |
| Visual source integrations | app/visuals/visual_assets.py | References to Wikimedia, Pexels/Pixabay and generation providers | Active configuration, provider order, API status and rights outcomes |

The baseline also reports that topics.py includes Hacker News, arXiv, Reddit RSS, Google Trends RSS, Google News RSS, DuckDuckGo HTML and Bing News RSS paths. These are documented code paths, not proof that each source is currently reachable or permitted for every use.

### Source conflicts and constraints

- Existing provider/source documents have conflicts; SRC-INT-001..006 remain open until reconciled.
- A project environment key or provider name is not evidence of live entitlement or availability.
- Do not use unapproved Google Search scraping or bypass provider access limits. Google's published guidance identifies automated queries to Google Search without express permission as machine-generated traffic that violates policy.
- Do not infer Reddit commercial-use permission from public visibility or historical API access.
- This handbook does not change the existing Shorts Studio architecture or authorize code edits.

---

## 3. Research architecture: from question to defensible claim

### 3.1 Logical pipeline

1. **Question intake:** record the research question, intended decision, audience, date sensitivity and required confidence.
2. **Research plan:** decompose into answerable sub-questions; identify primary, secondary and counter-evidence needs.
3. **Discovery:** query appropriate sources through permitted APIs, feeds, search providers or manual research.
4. **Source triage:** assess authority, proximity to the fact, freshness, independence, incentives and limitations.
5. **Capture:** preserve canonical URL, source metadata, retrieval time and permitted text/excerpts.
6. **Extraction:** identify atomic claims, entities, dates, numbers, quotes and uncertainty.
7. **Verification:** seek corroboration, primary documents, contradictory evidence and original context.
8. **Synthesis:** produce a claim/evidence matrix and separate facts, estimates, interpretation and speculation.
9. **Editorial decision:** decide whether each claim is usable, qualified, rejected or requires human review.
10. **Script integration:** attach claim/evidence references to script statements and retain provenance.
11. **Refresh:** recheck volatile claims before publication and preserve changed-source history.
12. **Archive/retention:** retain only content allowed by source terms and the project's data policy.

### 3.2 Discovery is not verification

A search engine ranks and retrieves documents. It does not guarantee factual accuracy, primary-source status, source independence, page stability, complete context or legal reuse rights. A model-generated summary is a derived interpretation, not a source. Store source references and evidence excerpts separately from generated summaries.

### 3.3 Source quality dimensions

| Dimension | Question |
|---|---|
| Authority | Is the publisher competent and accountable for this subject? |
| Proximity | Is it a primary record, direct participant, independent report or commentary? |
| Evidence | Does it provide documents, data, methods or named sources? |
| Freshness | Is the publication/update date appropriate to the claim? |
| Independence | Is it genuinely independent of other cited sources? |
| Incentives | Does the source have commercial, political or reputational incentives? |
| Specificity | Does it support the exact wording, number, geography and time period? |
| Reproducibility | Can another reviewer locate the same evidence? |
| Contradiction handling | Does the source acknowledge counter-evidence or uncertainty? |

Do not turn this checklist into an unreviewable “truth score.” Keep dimension-level evidence and a human-readable rationale.

---

## 4. Candidate research and discovery technologies

### 4.1 Exa Search and research APIs

**What it is:** A hosted search/research service with web search, page contents/highlights, agent-style research and monitoring products.

**Potential NEXTDECODE fit:** Discover relevant pages for a topic, retrieve selected content, and support research agents with source-linked results. It could reduce the need to build custom search and extraction infrastructure.

**Free/paid reality (official pricing checked 2026-11-04):** Exa advertises a starter tier with $10 monthly credits and a one-time onboarding bonus, with no payment method required according to its pricing page. Paid usage is endpoint-based; the page lists search from $4 per 1,000 requests, contents at $1 per 1,000 pages, agent runs priced by effort, deep search and monitoring as separate billable endpoints. The free allowance and rates can change; record a dated pricing snapshot and measure actual consumption.

**Risks:** Hosted search results and extracted content are subject to provider terms, source-site rights, retention and coverage limits. A citation link does not automatically grant permission to republish page text or media. Agent-style research can create variable usage unless effort and request budgets are bounded.

**Disposition:** EVALUATE for a bounded research discovery benchmark. Do not make it the only source provider or system of record.

### 4.2 OpenAlex

**What it is:** An open scholarly metadata catalogue/API connecting works, authors, sources, institutions and topics.

**Potential fit:** Scientific and technical research discovery, citation/author metadata, topic mapping and finding open-access scholarly works.

**Free/paid reality:** Current OpenAlex documentation says basic API use is free; an API key raises the daily budget and enables cursor paging. Its pricing documentation states a free daily usage budget and pay-as-you-go/annual options above it. Recheck current budget/pricing before production usage.

**Risks:** Scholarly metadata coverage and field quality vary. An OpenAlex record is not the paper's full text and does not prove the paper's conclusions. Verify the original paper, version, corrections, retractions and licence of the actual full text.

**Disposition:** EVALUATE as a structured scholarly metadata source.

### 4.3 Crossref REST API

**What it is:** A public metadata API for DOI-registered scholarly and other research outputs.

**Potential fit:** DOI resolution, bibliographic metadata, publication dates, journal/publisher information and metadata cross-checking.

**Free/paid reality:** Crossref documents public and polite access pools; including a contact email in the mailto parameter is recommended. Metadata Plus is a paid service with higher limits and priority support. Published rate/concurrency limits are pool-dependent and should be read from current documentation/response headers.

**Risks:** Crossref metadata is deposited by members and can be incomplete or inaccurate. A DOI record is not proof of article quality, peer-review rigor, or current validity.

**Disposition:** EVALUATE as a low-cost bibliographic metadata source.

### 4.4 Official feeds, publisher pages and primary documents

**What they are:** RSS/Atom feeds, official press releases, company filings, government datasets, regulator notices, scientific papers and first-party documentation.

**Potential fit:** Primary evidence and source-of-record verification.

**Cost:** Often no API fee for public pages/feeds, but availability, terms, robots policy, rate limits and access conditions vary. Public accessibility is not universal reuse permission.

**Risks:** Official sources can still be selective, self-interested or incomplete. Record who published the document and what the publisher is in a position to know.

**Disposition:** PREFERRED evidence sources where relevant, with independent corroboration for material claims.

### 4.5 Google Trends

**What it is:** Aggregated, anonymized and sampled search-interest data normalized to a 0–100 scale for the selected query, geography and time range.

**Potential fit:** Relative search-interest direction, seasonality, geographic comparison and identifying topics whose search attention is changing.

**Critical limitation:** It is not absolute search volume, a poll, proof of popularity, proof of market demand or proof of causation. Google documents sampling, normalization, privacy noise and limitations for low-volume queries.

**Disposition:** USE AS ONE WEAK SIGNAL in a multi-source trend model. Never present a Trends index as a number of searches or audience size.

### 4.6 Reddit

**What it is:** Community discussion and user-generated content accessible through Reddit interfaces and approved developer services.

**Potential fit:** Qualitative pain points, user vocabulary, objections, emerging conversations and community-level experience.

**Free/paid and commercial-use warning:** Reddit's current help guidance says commercial use of its developer tools/services requires prior permission; its Data API terms reserve the right to charge fees and require separate agreements for commercial purposes or uses outside express permission. Public content is not a blanket commercial data licence.

**Risks:** Sampling bias, coordinated manipulation, bots, reposts, deleted content, personal information, community rules and context collapse. Do not build a durable dataset or train models on user content without applicable permissions.

**Disposition:** LIMITED MANUAL/APPROVED QUALITATIVE SIGNAL only until commercial use, API access and retention terms are explicitly cleared. Do not scrape Reddit.

### 4.7 Google Search and general web scraping

**What it is:** Search engine result pages and website content, accessible through approved interfaces, provider APIs or direct site access where permitted.

**Potential fit:** Broad discovery and finding primary sources.

**Risks:** Google explicitly states automated queries to Google Search without express permission violate its policies/terms. Site-specific terms, robots controls, copyright, rate limits and privacy obligations also apply. Search results are not reusable source content by default.

**Disposition:** Use approved search APIs or authorized access methods. Do not build a Google SERP scraper or a general crawler that ignores source-site restrictions.

---

## 5. Media-source technology comparison

### Wikimedia Commons
A repository of freely licensed and public-domain media contributed by individual creators. Useful for historical images, diagrams, maps and educational visuals. Each file has its own creator, licence and reuse conditions. Some require attribution and a licence link; ShareAlike terms can affect adaptations. Other rights may also apply. **Disposition:** retain as a discovery source, with file-by-file review.

### Pexels
Hosted stock photo/video library and API. Useful for B-roll and supporting visuals. Pexels describes its library as free under its licence. API documentation publishes default limits and asks for prominent Pexels linking and photographer credit when possible. Terms restrict standalone redistribution, competing-library use and bulk/systematic copying. Check the current terms and preserve creator, source page and asset ID. **Disposition:** evaluate/retain for edited B-roll with per-asset provenance.

### Pixabay
Stock media library and API for images and videos under its Content License. API documentation describes free access subject to conditions and a default limit of up to 100 requests per 60 seconds. It asks API users to show where results originate when displaying results. Check the current licence and any restrictions for each intended use. **Disposition:** evaluate/retain with per-asset metadata and review.

### YouTube Data API
Useful for finding source videos, official statements, interviews and demonstrations. Current quota documentation describes a default allocation including 100 search.list calls per day, 100 videos.insert calls per day and a separate 10,000-unit daily bucket for other endpoints, subject to change. The Creative Commons search filter is only a discovery filter; it does not verify every embedded work or third-party right. **Disposition:** use for discovery and metadata, not as blanket permission to reuse video.

### Internet Archive
Useful for historical and archival research. Rights details are often supplied by uploaders, and public access does not prove that commercial reuse is permitted. **Disposition:** research lead only until item-specific provenance and permission are verified.

## 6. Asset review controls

Every media file must be reviewed for its source, creator, applicable licence, intended commercial context, permitted edits, attribution requirements, visible people/brands, third-party content and any stated restrictions. Record the exact source page and the version of the file used. A library listing or API response is not itself proof that the intended use is permitted.

### 6.1 Creative Commons quick guide

| Licence family | Commercial use | Adaptation | Main concern |
|---|---|---|---|
| CC BY | Yes | Yes | Attribution and change notice |
| CC BY-SA | Yes | Yes | Attribution plus ShareAlike on adaptations |
| CC BY-ND | Yes | No derivatives | Editing/adaptation may be prohibited |
| CC BY-NC | No commercial use | Yes | Monetized/commercial use is not permitted |
| CC BY-NC-SA | No commercial use | Yes | Noncommercial plus ShareAlike |
| CC BY-NC-ND | No commercial use | No derivatives | Highly restrictive for video editing |
| CC0 / public domain | Generally broad reuse | Generally yes | Verify status, provenance and other rights |

This is a high-level guide, not legal advice. Follow the exact licence version and legal code, not only a badge or abbreviated label. Creative Commons explains BY, NC, SA and ND conditions. Its guidance notes that applying a CC licence is generally not revocable for existing recipients.

### 6.2 Proposed asset evidence record

Design checklist only; map to accepted Rights, Asset, Artifact and ArtifactVersion contracts before implementation.

| Field group | Evidence to preserve |
|---|---|
| Identity | asset ID, source asset ID, exact file checksum |
| Source | provider, source page URL, original URL, creator, uploader if different |
| Licence | licence name, version, canonical URL, source-page snapshot, retrieval timestamp |
| Attribution | exact credit line, required links, placement requirements, changes statement |
| Permission | written permission reference, grantor, scope, date, expiry and restrictions |
| Context | intended content variant, use purpose, monetization/sponsorship context |
| Depicted elements | people, logos, trademarks, artwork, music and third-party content flags |
| Verification | reviewer, review date, evidence quality, unresolved questions |
| Version lineage | asset checksum, transform history, derivative lineage, final artifact version |
| Decision | review outcome and reason; never infer permission from missing fields |

### 6.3 Proposed review outcomes

Workflow proposal only; do not introduce these as canonical state names without owner approval:
- CLEAR_FOR_DECLARED_USE — evidence supports the specific declared use and conditions are recorded.
- CLEAR_WITH_CONDITIONS — use is possible only if listed conditions are enforced.
- NEEDS_REVIEW — missing or ambiguous evidence; block publishable status.
- RESTRICTED — licence/use restrictions conflict with intended use.
- REJECTED — source/permission is invalid or the use is prohibited.
- EXPIRED_OR_REVOKED — permission window ended or permission was withdrawn where legally effective.

A review decision is purpose- and context-specific. Clearance for one internal research slide does not imply clearance for monetized video.



## Current provider-availability correction — 2026-11-04
Pexels new API-key issuance is currently paused (official help article updated 2026-11-03); API rate-limit increases are also paused (updated 2026-11-02). Do not assume a new project/account can obtain a key. Existing-key status and per-account quota remain separate dashboard checks. See `08_RESEARCH_EVIDENCE_AND_DECISIONS/02_Source_And_Evidence_Log/02_LIVE_PROVIDER_AND_UPSTREAM_REPOSITORY_REEVALUATION_2026-11-04.md` for current provider verification and repository review. Re-check before use.
