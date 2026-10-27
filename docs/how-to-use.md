# Portfolio Advisor usage

## Direct browser access on the shared domain

Use <https://shanmukhan.com/#investing> → **Portfolio Advisor**, or open
<https://shanmukhan.com/portfolio-advisor/>. The browser prompts for your existing
RPi Monitor username/password before any Advisor page/assets/WebSocket connection.
Check demo/live mode and data freshness inside; no broker connection or order is
created by opening the page. Apache removes login credentials before proxying.

The public systemd drop-in sets Streamlit's `portfolio-advisor` base path and explicit
HTTPS origin/host checks, retaining CORS/XSRF. Loopback recovery now uses
`http://127.0.0.1:8501/portfolio-advisor/`; its health endpoint is
`/portfolio-advisor/_stcore/health`. The base service installer preserves this drop-in.
Credentials/database remain in the same private `/var/lib` tree. Local development
without this drop-in still uses localhost:8501 at `/`.

After changing monitor credentials, republish the web profile to refresh its minimal
Argon2 identity snapshot. Browser Basic credentials are cached: use a private window
and close it to end that sign-in. No plaintext monitor password/JWT secret is copied.
See [publish, rollback and actual validation](../../agentic-trader/docs/public-browser-access.md).
The earlier SSH-only instructions below describe the service-only baseline.

Local development: install `pip install -e '.[test]'`, copy `.env.example` to a
private `.env`, then run `streamlit run app.py`. Open localhost:8501. Run tests with
`python -m pytest -q`; `requirements.lock` contains portable pinned dependencies
without a workstation editable path.

For the shared Raspberry Pi, follow [the service guide](raspberry-pi.md). It explains
the deploy command, SSH browser access, demo/live distinction, persistent state,
mobile start/stop/restart controls, private session renewal and recovery. Reports
are decision support only; the Kite adapter remains read-only.
