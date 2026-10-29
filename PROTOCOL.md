# PROTOCOL.md — Reverse Engineering Urja Meter Ops

## 1. Overview & Exploration
- **Target Portal**: `https://urja-ops.flockenergy.tech`
- **Authentication**: Form-based session authentication (`username` and `password`).
- **Target Audience / Legacy Use**: Field operations teams looking up meter serials, phases, and parent Distribution Transformers (DTs).

## 2. Authentication Mechanism
- **Login Endpoint**: `POST /login`
- **Credentials Used**:
  - `username`: `operator@urja.local`
  - `password`: `urja-ops-2026`
- **Session Handling**: 
  - On valid credentials, the server responds with an HTTP status `302 Found` (or `200 OK`) and returns a `Set-Cookie` header containing a session token.
  - Subsequent requests to protected routes (`/meters`, `/meters?page=n`) require passing this session cookie in the `Cookie` request header.

## 3. Data Endpoints & Structure
- **Meters Listing**: `GET /meters?page={N}`
- **Rendering Model**: Server-rendered HTML tables (no native REST or JSON API was provided).
- **Extracted Fields**:
  - `meter`: Alphanumeric meter code (e.g., `MTR-XXXXX`).
  - `serial`: Hardware serial number.
  - `make`: Manufacturer (e.g., `HPL`, `L&T`, `Genus`, `Schneider`).
  - `phase`: Electrical phase layout (`Single` or `Three`).
  - `status`: Deployment state (`Installed`, `Faulty`, `Decommissioned`).
  - `dt`: Upstream Distribution Transformer identifier.

## 4. Network Hierarchy
- Meters do not sit in isolation; they are logically grouped under **Distribution Transformers (DTs)**.
- Reconstructing this hierarchy allows downstream engineering services to query:
  - All meters belonging to a specific transformer node.
  - Health/fault ratios at the transformer level.

## 5. Quirks, Edge Cases & Surprises
- **Rate-Limiting / Sequential Scrape Delay**: Scraping across 20+ pages over HTTP sequentially introduces latency (100–300ms per round trip).
- **Solution / Architectural Decision**: Rather than proxying live scraper round-trips for every incoming API client request, we ingest data into an embedded local SQLite storage layer via `/api/v1/sync`. Subsequent queries resolve in sub-millisecond time.