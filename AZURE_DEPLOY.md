# Deploying to Azure App Service (`azure` branch)

This branch makes the app deployable on **Azure App Service (Linux)** for a
single-instance pilot. State lives in **SQLite on the persistent `/home` mount**
(zero DB cost). The database layer is backend-agnostic (SQLAlchemy Core, selected
by the `DATABASE_URL` env var), so upgrading to a managed DB later is a
`DATABASE_URL` change + a driver — not a rewrite.

> **Why not local SQLite?** On App Service the local disk is ephemeral and the
> `/home` mount is slow SMB-backed Azure Files. We put the DB at `/home/data/...`
> (persists across restarts/deploys, and is *outside* `wwwroot` so redeploys
> don't wipe it), run a single gunicorn worker (multiple processes on one SQLite
> file over SMB risk lock/corruption), and avoid WAL journal mode.

---

## Step 0 — Push the `azure` branch (prerequisite for the GitHub deploy path)

The portal's GitHub deployment reads from `origin`:

```bash
git push -u origin azure
```

(Skip only if deploying via `az webapp up`/zip — see Step 5, Option B.)

## Step 1 — Decide the basics

UT may already have a Resource Group / App Service Plan to reuse.

- **Resource Group:** existing UT one, or create `rg-exec-panel-sim`.
- **Region:** whatever UT standardizes on (e.g. `Central US`).
- **App Service Plan** (this is your compute cost — separate from the $0 DB):
  - **F1 (Free)** — cheapest pilot; no "Always On" (cold starts after idle), 60 min/day CPU quota. Fine for demos.
  - **B1 (Basic, ~$13/mo)** — supports Always On, steadier. Recommended if a class will hit it live.

## Step 2 — Create the Web App

**Portal → Create a resource → Web App.** Basics tab:

- **Publish:** `Code`
- **Runtime stack:** `Python 3.13` (use `3.12` if 3.13 isn't offered in your region — all deps support it)
- **Operating System:** `Linux`
- **Region / Plan:** from Step 1
- **Name:** e.g. `exec-panel-sim` → `https://exec-panel-sim.azurewebsites.net`

**Review + create → Create.**

## Step 3 — Application settings (environment variables)

**Web App → Settings → Environment variables → Application settings → + Add** each, then **Apply**:

| Name | Value | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:////home/data/executive_simulator.db` | **Four** slashes = absolute `/home/data/...`. Persists; outside `wwwroot`. |
| `SECRET_KEY` | *(generated)* | App won't boot without it. Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENAI_API_KEY` | *(your key)* | From local `.env` |
| `PORTKEY_API_KEY` | *(your key)* | From local `.env` |
| `PORTKEY_VIRTUAL_KEY` | *(your key)* | From local `.env` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Makes Azure (Oryx) `pip install -r requirements.txt` on deploy |
| `WEBSITES_PORT` | `8000` | Optional; matches the startup bind below |

## Step 4 — Startup Command

**Settings → Configuration → General settings → Startup Command.** Azure ignores
`Procfile`/`$PORT`, and the app object is `app_v2:app` (non-default), so set:

```
gunicorn app_v2:app --bind 0.0.0.0:8000 --timeout 300 --graceful-timeout 300 --keep-alive 5 --workers 1 --threads 4
```

**Save.** (`--workers 1` is deliberate for SQLite-on-Azure-Files; threads give safe concurrency.)

## Step 5 — Deploy the code

**Option A — GitHub Actions (recommended; needs Step 0):**
1. **Web App → Deployment → Deployment Center.**
2. **Source:** GitHub → authorize → org `johngraff512`, repo `executive-panel-simulator`, **branch `azure`**.
3. **Build provider:** GitHub Actions → **Save**. Azure adds a workflow to the branch and runs the first deploy; watch the repo's **Actions** tab.

**Option B — From your Mac via CLI (no GitHub):**
```bash
az webapp up --name exec-panel-sim --resource-group rg-exec-panel-sim --runtime "PYTHON:3.13"
```

## Step 6 — Verify

1. **Log stream** (Web App → Monitoring → Log stream): expect `✅ Database initialized successfully`. *(A "didn't respond to HTTP pings on port 8000" error → the Step 4 bind port is wrong.)*
2. **Health:** open `https://<app>.azurewebsites.net/health` → stats JSON.
3. **Persistence (the important one):** Web App → Development Tools → **SSH**, then:
   ```bash
   ls -la /home/data/
   ```
   Confirm `executive_simulator.db` exists. **Restart** the app (Overview → Restart) and re-check — it must still be there.
4. Run a full session in the UI (start → question → answer → end → download transcript) and confirm the transcript PDF shows timestamps.

---

## Notes / gotchas

- **Single instance only** while on SQLite — do **not** enable scale-out (the `/home` file isn't safe for concurrent writers across instances).
- **`/home` persistence is automatic** for the built-in Python image (no `WEBSITES_ENABLE_APP_SERVICE_STORAGE` — that's for custom containers only).
- **Upgrading to a managed DB later** (Azure SQL free tier or Postgres) = change `DATABASE_URL` + add a driver to `requirements.txt`. No query rewrites, but two spots in `database.py` carry the only dialect-specific code and have comments where Azure SQL needs its form: `_upsert()` (needs `MERGE`) and `get_conversation_history()` (`LIMIT` → `TOP`/`OFFSET-FETCH`).
- **Secrets:** later, move keys to **Azure Key Vault** and reference them instead of plain app settings.

## DB target cost reference

| Option | Cost | Trade-off |
|---|---|---|
| **SQLite on `/home`** (this pilot) | $0 | Single instance only; not for scale/concurrency |
| **Azure SQL DB free offer** | $0/mo (lifetime, enterprise-eligible) | T-SQL `MERGE` upsert + ODBC driver on Linux |
| **PostgreSQL Flexible B1ms** | ~$16/mo (or ~$4 stopped) | Easiest Linux driver, native JSONB |
