# Contributing to Zerodha Portfolio Advisor

Thank you for your interest in contributing! This project is a read-only, discipline-enforcing equity portfolio advisor tailored for Indian markets (NSE) and Zerodha Kite Connect.

---

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/portfolio-advisor.git
   cd portfolio-advisor
   ```

2. **Create and activate a virtual environment (Python >= 3.10):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up local environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Generate local sample demo data:**
   ```bash
   python scripts/generate_sample_data.py
   ```

6. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

---

## 🧪 Testing

We use `pytest` for unit testing. All tests must pass before submitting a pull request:

```bash
pytest -v
```

To run with coverage:
```bash
pytest --cov=advisor tests/
```

---

## 📐 Code Style & Conventions

- Follow **PEP 8** style guidelines.
- Always include **type annotations** for public functions and classes.
- Write informative **docstrings** following Google or Sphinx format for all modules, classes, and functions.
- Avoid committing secrets or live credentials to `.env` or repository history.
- Ensure all queries touching SQLite use parameterized placeholders `?` to prevent SQL injection.
- Ensure any user-facing HTML interpolated in Streamlit uses `html.escape()` or sanitized wrappers.

---

## 🔒 Security Policy

- This advisor operates strictly in **READ-ONLY** mode. No automated order placement or capital movement methods should ever be added to `advisor.broker.KiteReadOnly`.
- If you discover a security vulnerability, please do NOT open a public issue. Report it privately to the maintainers.
