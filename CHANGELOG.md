# Changelog

## 2026-10-25 — shared-domain browser profile

- Added public-profile usage for the Investing link, HTTPS base path, monitor-password
  browser authentication, WebSocket proxy and explicit Streamlit origin/host checks.
- Shared publishing keeps CORS/XSRF enabled, removes Basic credentials before proxying,
  preserves existing data/config and supports configuration-only rollback. The base
  installer retains the public drop-in and prefixed health check.
- Infrastructure/navigation/auth checks live in rpi-setup; deployed evidence and
  synthetic/real acceptance limits are in the shared browser runbook.

## 2026-10-25 — Raspberry Pi service support

- Added `ADVISOR_ENV_FILE` for persistent private credentials across root-owned code
  releases; local project `.env` remains the default. UI and CLI renewal share it.
- Removed the absolute workstation editable install from `requirements.lock`.
- Shared Agentic Trader installer provisions loopback:8501, persistent SQLite/config,
  systemd boot/restart policy and RPi Monitor allowlist/polkit integration.
- Added real-process configuration, persisted-ledger, renewal and portability checks.
  See [usage and deployment evidence](docs/raspberry-pi.md); simulated data is separate
  from broker, handset and power-loss acceptance.


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- GitHub Actions CI workflow for Python 3.10 through 3.13 (`.github/workflows/test.yml`).
- `requirements.lock` pinning tested package dependencies.
- `.python-version` file specifying Python 3.13.
- `CONTRIBUTING.md` developer guide.
- `parse_kite_holdings()` shared parser in `advisor.broker` to eliminate duplicate holding extraction logic across modules.
- Strict symbol and date format validation in `advisor.storage` (`validate_symbol`, `validate_date`).
- Comprehensive type hints and docstrings across `advisor.storage`, `advisor.broker`, `advisor.data`, and `advisor.cli`.
- Fully structured CLI with PEP 8 compliance, `--compact` flag, and proper Unix exit codes in `advisor.cli`.

### Security
- Re-enabled Streamlit XSRF and CORS protections (`enableXsrfProtection = true`, `enableCORS = true`).
- Enforced parameterized queries and validated symbol sanitization across storage inputs.

### Changed
- Replaced raw `print()` calls in data loading, broker, and sync routines with Python's standard `logging` library.
- Refactored `scripts/enrich_user_portfolio.py` to use `advisor.storage.connect()` and respect the `ADVISOR_DB` environment configuration with proper database connection lifecycle management.
- Reused `parse_kite_holdings()` in `scripts/login.py` and `advisor.data`.
