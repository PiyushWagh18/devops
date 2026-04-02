# TaskFlow – Flask Task Manager

A full-stack task management web application built with **Python/Flask**, deployed on **AWS EC2** via a **GitHub Actions CI/CD pipeline** with integrated **DevSecOps security scanning**.

**Live URL:** http://13.62.98.108:5000

---

## Features

- **Full CRUD** – Create, Read, Update, Delete tasks
- **Filtering** – Filter tasks by status and priority
- **Dashboard Charts** – Chart.js bar and doughnut charts for task analytics
- **Input Validation** – Server-side and client-side form validation
- **Security Hardened** – CSRF protection, security headers, CSP, XSS prevention

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.1, Flask-SQLAlchemy |
| Security | Flask-WTF (CSRF), Security Headers, CSP |
| Frontend | Bootstrap 5, Chart.js, Bootstrap Icons |
| Database | SQLite (via SQLAlchemy ORM) |
| Server | Gunicorn (production) |
| CI/CD | GitHub Actions |
| Cloud | AWS EC2 (Amazon Linux 2023, t3.micro, eu-north-1) |
| SAST | Bandit |
| SCA | pip-audit |

---

## Project Structure

```
devops/
├── app/
│   ├── __init__.py        # Flask app factory – security headers, CSRF, error handlers
│   ├── models.py          # SQLAlchemy Task model
│   ├── routes.py          # CRUD route handlers with full input validation
│   ├── static/js/
│   │   ├── dashboard.js   # Chart.js charts (CSP-compliant, no inline scripts)
│   │   └── form.js        # Bootstrap validation + character counters
│   └── templates/
│       ├── base.html      # Navbar, flash messages, SRI CDN links
│       ├── index.html     # Dashboard with stats cards and task table
│       ├── create.html    # Create task form
│       ├── edit.html      # Edit task form
│       ├── view.html      # Task detail view
│       └── errors.html    # Custom 404/500/403 error pages
├── tests/
│   └── test_app.py        # 31 unit tests: CRUD, security headers, CSRF, XSS, injection
├── .github/
│   └── workflows/
│       └── deploy.yml     # 3-stage CI/CD: Test → Security Scan → Deploy
├── .env                   # Local environment variables (never committed)
├── .gitignore
├── requirements.txt
└── run.py
```

---

## CI/CD Pipeline

The GitHub Actions pipeline triggers on every push to `main` and runs three sequential stages:

```
Push to main
     │
     ▼
┌─────────────┐
│  Stage 1    │  Run Unit Tests (pytest)
│   Test      │  ← 31 tests across CRUD, security, CSRF, XSS
└──────┬──────┘
       │ pass
       ▼
┌─────────────────────────┐
│  Stage 2                │  Security Analysis (DevSecOps)
│  Security Scan          │  ← Bandit SAST + pip-audit SCA
│                         │  ← Reports uploaded as pipeline artifacts
└──────────┬──────────────┘
           │ pass
           ▼
┌─────────────────────────┐
│  Stage 3                │  SSH into EC2 → git pull → pip install
│  Deploy to EC2          │  → restart gunicorn
└─────────────────────────┘
```

### Tools Used

| Tool | Purpose | Stage |
|---|---|---|
| **pytest** | Unit & integration testing | Stage 1 |
| **Bandit** | Static Application Security Testing (SAST) | Stage 2 |
| **pip-audit** | Software Composition Analysis – CVEs in deps | Stage 2 |
| **GitHub Actions** | CI/CD automation | All |
| **appleboy/ssh-action** | SSH deploy to EC2 | Stage 3 |

---

## Security Features

### OWASP Top 10 Mitigations

| OWASP | Risk | Mitigation |
|---|---|---|
| A01 | Broken Access Control | HTTP method enforcement (DELETE = POST only) |
| A03 | Injection | SQLAlchemy ORM (parameterised queries), input whitelist |
| A05 | Security Misconfiguration | Security headers, DEBUG=False in production |
| A07 | Auth Failures | Secure session cookies (HttpOnly, SameSite=Lax) |
| A08 | Integrity Failures | SRI on Bootstrap CDN, CSRF tokens on all forms |
| A09 | Logging | Gunicorn access + error logs |
| A10 | XSS | Jinja2 auto-escaping, CSP without unsafe-inline |

### HTTP Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
Content-Security-Policy: default-src 'self'; script-src 'self' cdn.jsdelivr.net; ...
Strict-Transport-Security: max-age=31536000 (production only)
```

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/PiyushWagh18/devops.git
cd devops

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
echo "FLASK_DEBUG=False" >> .env
echo "FLASK_ENV=development" >> .env
echo "DATABASE_URL=sqlite:///app.db" >> .env

# Run locally
python run.py
```

App runs at: http://localhost:5000

---

## Running Tests

```bash
pytest tests/ -v
```

### Test Coverage

| Test Class | Tests | What it covers |
|---|---|---|
| `TestCreate` | 7 | Valid creation, missing title, invalid priority/status, due date |
| `TestRead` | 5 | Index, view, 404, filter by status/priority |
| `TestUpdate` | 4 | Valid edit, missing title, 404 on nonexistent |
| `TestDelete` | 3 | Delete, 404, confirm task gone |
| `TestSecurityHeaders` | 5 | All HTTP security headers, 404 custom page |
| `TestInputSanitization` | 4 | XSS escaping, bad filters, length limits |
| `TestCSRFIntegration` | 2 | CSRF token present in all forms |

---

## EC2 Deployment (One-Time Setup)

```bash
# Provision EC2 (t3.micro, ami-0cc38fb663faa09c2, eu-north-1)
# Security group: inbound TCP 22, 5000, 80

# SSH into instance
ssh -i cloud-key-pair.pem ec2-user@<EC2_PUBLIC_IP>

# Install dependencies
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
sudo pip3 install -r requirements.txt

# Clone and start
git clone https://github.com/PiyushWagh18/devops.git ~/devops
cd ~/devops
gunicorn -w 4 -b 0.0.0.0:5000 run:app --daemon
```

### Required GitHub Actions Secrets

| Secret | Value |
|---|---|
| `EC2_HOST` | Public IP of the EC2 instance |
| `EC2_SSH_KEY` | Contents of `cloud-key-pair.pem` |
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |

---

## CI/CD Demo

To demonstrate the pipeline live:

```bash
# Make a visible change
nano app/templates/base.html  # e.g. change footer text

# Push to trigger pipeline
git add .
git commit -m "demo: update footer for CI/CD demonstration"
git push origin main

# Watch: GitHub → Actions tab → observe 3 stages
# After ~2 min: reload http://13.62.98.108:5000
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key (required in production) | auto-generated (dev) |
| `FLASK_ENV` | `development` or `production` | `development` |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///app.db` |
