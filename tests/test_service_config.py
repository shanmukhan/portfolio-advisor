"""Real-process checks for private service configuration and durable storage."""

import json
import os
import sqlite3
import subprocess
import sys
from decimal import Decimal
from pathlib import Path


def test_private_service_environment_and_persistence(tmp_path):
    root = Path(__file__).resolve().parents[1]
    database = tmp_path / 'persistent.sqlite3'
    credentials = tmp_path / '.env'
    credentials.write_text(f'ADVISOR_MODE=demo\nADVISOR_DB={database}\n')
    env = {**os.environ, 'ADVISOR_ENV_FILE': str(credentials), 'PYTHONPATH': str(root)}
    script = '''
from advisor.config import Settings, environment_file
from advisor.storage import connect, add_purchase
import json
settings = Settings()
db = connect(settings.db)
add_purchase(db, '2026-10-25', 'INFY', 1234.50, 'service-test')
db.close()
print(json.dumps({'db': settings.db, 'mode': settings.mode, 'env': str(environment_file())}))
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=tmp_path, env=env,
                            check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == {'db': str(database), 'mode': 'demo', 'env': str(credentials)}
    # A second process reads the same config after restart. Independently inspect SQLite.
    subprocess.run([sys.executable, '-c', 'from advisor.config import Settings; '
                    'from advisor.storage import connect; connect(Settings().db).close()'],
                   cwd=tmp_path, env=env, check=True)
    with sqlite3.connect(database) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        rows = db.execute('SELECT symbol, gross_amount FROM purchases').fetchall()
    assert [(symbol, Decimal(str(amount))) for symbol, amount in rows] == [('INFY', Decimal('1234.50'))]
    assert not (tmp_path / 'advisor.sqlite3').exists()


def test_local_environment_file_default(monkeypatch):
    from advisor.config import environment_file
    monkeypatch.delenv('ADVISOR_ENV_FILE', raising=False)
    assert environment_file() == Path(__file__).resolve().parents[1] / '.env'


def test_login_renewal_uses_private_environment(tmp_path):
    root = Path(__file__).resolve().parents[1]
    credentials = tmp_path / '.env'
    env = {**os.environ, 'ADVISOR_ENV_FILE': str(credentials), 'PYTHONPATH': str(root)}
    subprocess.run([sys.executable, '-c',
                    'from scripts.login import update_env; '
                    'update_env("test-key", "test-secret", "test-token")'],
                   cwd=tmp_path, env=env, check=True, capture_output=True)
    from dotenv import dotenv_values
    saved = dotenv_values(credentials)
    assert saved['ADVISOR_MODE'] == 'live'
    assert saved['KITE_ACCESS_TOKEN'] == 'test-token'


def test_lockfile_contains_only_portable_pinned_dependencies():
    root = Path(__file__).resolve().parents[1]
    lines = [line for line in (root / 'requirements.lock').read_text().splitlines()
             if line.strip() and not line.startswith('#')]
    assert lines
    assert all('==' in line and not line.startswith('-') and 'file:' not in line
               and '/Users/' not in line for line in lines)
