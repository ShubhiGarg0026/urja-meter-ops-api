# Flock Energy — Urja Meter Ops API Gateway & Modern Client

A robust, production-ready REST API service, local analytical query layer, and interactive operations dashboard built on top of the legacy Urja Meter Ops portal[cite: 1, 2, 3].

---

## 📌 Architecture Overview

1. **Proxy & API Service (`FastAPI`)**: Exposes structured, documented REST endpoints conforming to OpenAPI 3.x standards.
2. **Reverse Scraper Engine (`httpx` + `BeautifulSoup`)**: Manages session-based authentication, cookies, and table parsing from the legacy portal[cite: 1].
3. **High-Speed Query Layer (`SQLite`)**: Indexes records locally so consumers can filter by `status`, `make`, and `phase` with sub-millisecond response times.
4. **Operations Dashboard (`/dashboard`)**: A modern Tailwind CSS interface featuring fleet statistics, health breakdown, and network hierarchy metrics[cite: 3].

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- Windows, macOS, or Linux

### 2. Setup Environment
```bash
# Clone the repository
git clone [https://github.com/](https://github.com/)<your-username>/urja-meter-ops-api.git
cd urja-meter-ops-api

# Create and activate virtual environment
python -m venv myenv

# Windows:
.\myenv\Scripts\activate
# macOS/Linux:
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt
