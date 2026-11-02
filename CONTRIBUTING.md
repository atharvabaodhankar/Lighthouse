# Contributing to Lighthouse

Thank you for your interest in contributing to **Lighthouse**! Lighthouse is a production-grade Home DNS Shield and Traffic Intelligence companion platform built on FastAPI, Pi-hole v6, Nginx DNS-over-TLS (DoT), and Terraform.

Whether you are fixing a bug, expanding documentation, adding support for a new client platform, or polishing the user interface, we welcome your contributions.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Environment Setup](#development-environment-setup)
3. [Repository Architecture](#repository-architecture)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Submitting a Pull Request](#submitting-a-pull-request)
8. [Reporting Issues & Security Disclosures](#reporting-issues--security-disclosures)

---

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for all contributors. Please treat everyone with respect, constructive criticism, and professional courtesy.

---

## Development Environment Setup

### Prerequisites

- **Python**: `>= 3.11`
- **Docker & Docker Compose** (optional for local mock mode, required for container testing)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/lighthouse.git
cd lighthouse
```

### 2. Configure Virtual Environment

```bash
# On Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the sample environment file:

```bash
cp .env.example .env
```

Default settings allow the dashboard to run in mock mode when a live Pi-hole v6 server is not detected:
- `HOST=0.0.0.0`
- `PORT=8000`
- `MOCK_MODE=false` (auto-falls back to simulated telemetry if connection fails)

### 5. Launch Development Server

```bash
python run.py
# or using Makefile:
make dev
```

Visit [http://localhost:8000](http://localhost:8000) in your browser.

---

## Repository Architecture

Lighthouse enforces a clear separation between frontend views, REST controllers, external engine clients, and cloud infrastructure:

```
Lighthouse/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions automated test & build pipeline
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── notion.css       # Production Notion & Linear design system stylesheet
│   │   └── js/
│   │       └── app.js           # Client-side SPA controller & Chart.js engine
│   ├── templates/
│   │   └── index.html           # Notion-styled single-page application shell
│   ├── config.py                # Pydantic v2 application settings & environment parser
│   ├── main.py                  # FastAPI application routes & REST endpoints
│   ├── pihole_client.py         # Async Pi-hole v6 REST client with automatic mock fallback
│   └── telegram.py              # Telegram bot alerting & Markdown report formatter
├── docs/                        # Comprehensive technical documentation
│   ├── ARCHITECTURE.md          # Topology, FTL engine, Nginx DoT, and container design
│   ├── SETUP_GUIDE.md           # Client setup: Android DoT, iOS, Router DHCP, Windows, Linux
│   ├── API.md                   # REST API documentation with request/response schemas
│   ├── SECURITY.md              # Threat model, open resolver defense, and firewall rules
│   └── DEPLOYMENT.md            # Terraform provisioning, EC2 bootstrap, SSL automation
├── scripts/
│   ├── prepare_deployment.py    # Cloud-init packer & terraform.tfvars builder
│   └── verify_dns.py            # Diagnostic script testing DoT 853, DNS 53, and REST API
├── tests/
│   └── test_api.py              # Automated test suite (FastAPI TestClient + unittest)
├── Dockerfile                   # Dashboard container specification
├── docker-compose.dashboard.yml # Multi-container local stack definition
├── main.tf                      # Terraform AWS infrastructure (EC2, EIP, SG, AMI)
├── Makefile                     # Standard developer commands
├── pyproject.toml               # Project packaging metadata & tool configurations
├── requirements.txt             # Locked Python runtime dependencies
└── run.py                       # CLI application launcher
```

---

## Development Workflow

1. **Create a topic branch**:
   ```bash
   git checkout -b feat/add-query-export
   ```
2. **Follow Semantic Commit Messages**:
   We follow the [Conventional Commits](https://www.conventionalcommits.org/) convention:
   - `feat:` A new user-facing feature or enhancement
   - `fix:` A bug fix in API, UI, or infrastructure
   - `docs:` Documentation additions or revisions
   - `style:` Code style formatting (spaces, semicolons) without logic change
   - `refactor:` Code reorganization that neither fixes a bug nor adds a feature
   - `perf:` Performance improvements
   - `test:` Adding or correcting automated tests
   - `chore:` Dependency bumps, CI updates, configuration tweaks

---

## Coding Standards

### Python Guidelines

- **PEP 8**: Strict adherence to PEP 8 standards. Max line length: 100 characters.
- **Async First**: Use async/await for network I/O (`httpx.AsyncClient`).
- **Type Annotations**: Use Python typing hints (`typing.Optional`, `typing.Dict`, `typing.List`) on all public function signatures.
- **Defensive Error Handling**: External connections to Pi-hole or Telegram must fail gracefully without terminating the web worker.

### Frontend Guidelines (Notion & Linear Design System)

- **Palette Integrity**: Use standard CSS custom properties defined in `app/static/css/notion.css` (`--bg-canvas`, `--surface`, `--ink-primary`, `--accent-sky`, `--border-subtle`).
- **No AI Slop**: Avoid artificial neon glows, excessive purple gradients, or unconstrained rounded corners. Maintain quiet, calm, high-density productivity ergonomics.
- **Accessibility**: Ensure keyboard navigable tabs, accessible color contrasts, and responsive layout behavior across mobile (< 768px) and desktop (> 1024px) viewports.

---

## Testing Guidelines

All pull requests must pass the existing automated test suite before merging.

### Running Tests Locally

```bash
python -m unittest discover tests -v
# or
make test
```

### Adding New Tests

Add new test cases to `tests/test_api.py` or create a new `tests/test_*.py` file:
- Verify both the success path and edge cases (e.g., empty strings, invalid filter values, network timeouts).
- Never weaken or skip existing assertions to make a new feature pass.

---

## Submitting a Pull Request

1. Push your branch to GitHub:
   ```bash
   git push origin feat/add-query-export
   ```
2. Open a Pull Request against the `main` branch.
3. Complete the PR template with:
   - A summary of the change and rationale.
   - Screenshots/recordings if modifying the UI.
   - Verification record (commands executed, unit test output).
4. Ensure all CI checks pass.

---

## Reporting Issues & Security Disclosures

- **Bug Reports & Feature Requests**: Submit an issue via GitHub Issues with detailed replication steps, OS version, and browser/client information.
- **Security Vulnerabilities**: For vulnerabilities affecting public DNS exposure or authentication bypasses, please email security disclosures privately to the repository maintainers rather than filing a public issue.
