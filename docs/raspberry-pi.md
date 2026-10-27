# Raspberry Pi service

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

Deploy from sibling Agentic Trader:

```sh
cd ../agentic-trader
bash deployment/rpi/deploy.sh lipi@192.168.1.13 ../portfolio-advisor
ssh -N -L 8501:127.0.0.1:8501 lipi@192.168.1.13
```

Open <http://127.0.0.1:8501>. The systemd unit `portfolio-advisor.service` is enabled
at boot, runs as its own unprivileged user and binds only loopback:8501. RPi Monitor
reads `portfolio-advisor` from its server allowlist; refresh the mobile Services
view. Active means process liveness, not valid broker data. Stop/Restart
interrupt browser work; Start reopens saved state. No mobile rebuild is needed.
No public route or standalone dashboard login is added: use SSH access control.

Root-owned code lives at `/opt/portfolio-advisor/releases/RELEASE`, selected by
`/opt/portfolio-advisor/current`. State survives code updates under
`/var/lib/portfolio-advisor`: `data/advisor.sqlite3` and `config/.env` (private).
The unit sets `ADVISOR_ENV_FILE=/var/lib/portfolio-advisor/config/.env`; app,
configuration loader, import UI and login helper use that file. When the variable
is absent/empty, local usage still loads project `.env`. Never put a second `.env`
in the release directory. Credential saves use the writable state directory so
python-dotenv's atomic file replacement works with systemd's read-only code policy.

Fresh installs use `ADVISOR_MODE=demo`, no Kite credentials and shipped sample CSVs.
Local holdings/purchase databases and `.env` are excluded from deployment. Demo
portfolio/recommendations are synthetic, not proof of broker/device acceptance.
Use the existing Import Data/login flow over the SSH tunnel for explicit live
configuration; manual CLI renewal uses `ADVISOR_ENV_FILE` and `python -m scripts.login`
from the current release as the service user. Do not pass secrets as arguments.
Restart after manual file edits. Expired/live failures may fall back to cached/demo
inputs; inspect displayed mode/freshness before using reports. No orders are placed.

```sh
ssh lipi@192.168.1.13 'systemctl is-active portfolio-advisor; curl -fsS http://127.0.0.1:8501/_stcore/health'
ssh lipi@192.168.1.13 'sudo journalctl -u portfolio-advisor -n 50 --no-pager'
```

Updates preserve private config/database and prepare locked dependencies before
stopping services. The lockfile contains dependency pins only; its old absolute
Mac editable path was removed. Release manifests hash tracked source, including
working-tree edits. Untracked new source is excluded until tracked. Health failure
restores previous code/units, retaining financial state. Repeated failures require
fixing the cause and `sudo systemctl reset-failed portfolio-advisor` before restart.
Backups/releases are not automatically pruned. SQLite monetary columns still use
REAL; no accounting migration is implied. Do not overwrite a financial database
with an old backup without a separate reviewed integrity/accounting recovery.

See the [shared deployment runbook](../../agentic-trader/docs/raspberry-pi.md) for
exact installer behavior, backup paths, monitor/polkit rollback and dated device
evidence. Local tests include separate-process config/storage persistence,
independent SQLite inspection, private-file credential renewal using test values,
and lockfile portability. Physical reboot, phone taps and live broker acceptance
remain separate checks.


### Public deployment evidence — 25 October 2026

The Investing tab and HTTPS routes are deployed. Final web rollback backup:
`/var/backups/trading-web-20261025T163321` (22:03:21 IST). Current app release:
`20261025T162335-9e35f56ca62b`. Public landing/Trader pages, prefixed assets, protected
operator reads, wrong-origin rejection, monitor health and Advisor's 401 login boundary
passed. Isolated loopback Apache with the same proxy/auth helper and a synthetic
identity passed positive/negative auth, Advisor HTML/health and authenticated WebSocket
upgrade; no public test identity was added and the owner's password was not entered.
The initial WebSocket check found JSON-style environment lists were treated as literal
strings. The final profile uses Streamlit/Click's whitespace-separated multiple-value
format, with a regression test. CORS/XSRF remain enabled. Saved financial state and
independent DB integrity checks are unchanged/passing. Actual phone taps, real-owner
browser login, broker/session and power-loss acceptance remain separate.
See [complete validation and recovery](../../agentic-trader/docs/public-browser-access.md).
