# Azure App Service — Deployment & Operations Runbook (`azure` branch)

**Status: ✅ LIVE pilot.** A full executive-simulator session (PDF upload → analysis →
Q&A → transcript) was run successfully end-to-end on Azure.

| | |
|---|---|
| **Live URL** | https://exec-panel-sim-eqccebashuedepfy.centralus-01.azurewebsites.net |
| **App name** | `exec-panel-sim` |
| **Resource group** | `AIExecutivePanel` |
| **Subscription** | `MGMT-graffjm1` |
| **Region / Plan** | Central US / **F1 Free** |
| **Runtime** | Python 3.13 (Linux) |
| **Database** | SQLite at **`/home/data/executive_simulator.db`** (persistent `/home` mount, $0) |
| **Deploy method** | Manual zip deploy from Azure Cloud Shell (GitHub Actions was blocked — see note) |

> **Architecture:** state lives in SQLite on the persistent `/home` mount. The DB layer is
> backend-agnostic (SQLAlchemy Core, chosen by `DATABASE_URL`), so moving to a managed DB later
> is an env-var + driver change, not a rewrite. Single instance only while on SQLite.

---

## 1. Starting / accessing the app

- **It's always deployed** — just open the **Live URL** above. On the **Free (F1)** plan there's no
  "Always On", so after idle the first request **cold-starts** (10–30s); subsequent requests are fast.
- **Health check:** `…/health` returns `{"status":"healthy","database":{...}}`. (This is the app's own
  route — not Azure's "Health check" feature, which is disabled on Free and isn't needed.)
- **Restart** (portal: Overview → Restart, or CLI):
  ```bash
  az webapp restart --resource-group AIExecutivePanel --name exec-panel-sim
  ```
- **Watch it boot / debug:** Cloud Shell →
  ```bash
  az webapp log tail --resource-group AIExecutivePanel --name exec-panel-sim
  ```
  Ready = gunicorn `Listening at: http://0.0.0.0:8000` + `✅ Database initialized successfully`.

## 2. Required app settings (Environment variables)

If you ever recreate the app, the settings below marked **required** are mandatory. The AI keys follow a fallback order — see the note under the table.

| Name | Value | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:////home/data/executive_simulator.db` | **Required.** **FOUR slashes** = absolute `/home/data/...`. Three slashes = relative path → "no such table" errors. |
| `SECRET_KEY` | *(secret)* | **Required.** App refuses to boot without it. Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `PORTKEY_API_KEY` | *(secret)* | **Required for UT API access.** Used together with `PORTKEY_VIRTUAL_KEY`. |
| `PORTKEY_VIRTUAL_KEY` | *(secret)* | **Required for UT API access.** Used together with `PORTKEY_API_KEY`. |
| `OPENAI_API_KEY` | *(secret)* | **Optional fallback only.** Ignored when both Portkey vars are set. Used solely if Portkey isn't fully configured — this is a personal OpenAI-billed key, so leave it unset once on Portkey. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | **Required.** Makes Azure run `pip install` on deploy. Without it, deps aren't installed. |
| `WEBSITES_PORT` | `8000` | **Required.** Matches the gunicorn bind in the startup command. |

**AI key precedence** (see [app_v2.py:103-127](app_v2.py)): if **both** `PORTKEY_API_KEY` and `PORTKEY_VIRTUAL_KEY` are present, the app routes all calls through the UT Portkey gateway and never reads `OPENAI_API_KEY`. Only if the Portkey pair is missing/incomplete does it fall back to a direct OpenAI client using `OPENAI_API_KEY`. With neither, it runs in demo mode. For the UT setup, set the two Portkey vars and omit `OPENAI_API_KEY` entirely.

**Startup command** (Configuration → **Stack settings** → Startup command):
```
gunicorn app_v2:app --bind 0.0.0.0:8000 --timeout 300 --graceful-timeout 300 --keep-alive 5 --workers 1 --threads 4
```
`--workers 1` is deliberate for SQLite-on-Azure-Files (multiple processes risk lock/corruption); threads give concurrency.

## 3. Redeploying after code changes

Push your change to the `azure` branch on GitHub, then in **Cloud Shell**:

```bash
# (first time in a fresh Cloud Shell session)
git clone --branch azure --single-branch https://YOUR_PAT@github.com/johngraff512/executive-panel-simulator.git
cd executive-panel-simulator

# (each redeploy)
git pull
zip -r ../app.zip . -x ".git/*" "venv/*" "flask_session/*" "*.db" "*__pycache__*"
az webapp deploy --resource-group AIExecutivePanel --name exec-panel-sim --src-path ../app.zip --type zip
```

`YOUR_PAT` = a GitHub classic PAT with `repo` scope. **Watch the build time** — a real build with
dependency install takes **minutes**; a 1-second "Build successful" means the build didn't run (check
`SCM_DO_BUILD_DURING_DEPLOYMENT=true`). The deploy command may print *"failed to start within 10 mins"*
— that's a cold-start poll timeout, not necessarily a real failure; verify with `…/health`.

> **Why manual zip and not GitHub Actions CI/CD?** Deployment Center → GitHub failed with
> *"Cannot find SourceControlToken with name GitHub"* — the UT enterprise tenant blocks Azure from
> storing a GitHub OAuth token. Manual zip deploy (above) sidesteps it. Setting up push-to-deploy CI/CD
> later requires the **OIDC / federated-identity** route (no token) — a future task.

## 4. Further testing checklist

**Functional (run real sessions):**
- [ ] Each executive mix (CEO/CFO/CTO/CMO/COO); 1 vs several executives
- [ ] Toggles: follow-up questions on/off, web research on/off, AI feedback on/off
- [ ] PDF variety: small + large reports; a scanned/image-heavy PDF; a non-PDF (error handling)
- [ ] Full flow to completion → **download the transcript PDF**, confirm timestamps & content render
- [ ] Audio responses (if used) play back

**Persistence (the pilot's core assumption):**
- [ ] Run a session, then **restart the app**, then confirm prior data survives:
      `…/health` session count stays > 0; SSH check `sqlite3 /home/data/executive_simulator.db ".tables"`
      lists `progressive_cache questions responses sessions`
- [ ] Redeploy code, confirm `/home/data` DB still persists (it's outside `wwwroot`)

**Load / limits (single-instance pilot risk areas):**
- [ ] A few simultaneous users (simulate a class) — watch for slowness or DB-lock errors in `log tail`
- [ ] A very large PDF — confirm it finishes under the 300s request timeout
- [ ] Cold-start delay after idle is acceptable for your use (or consider B1 Basic + Always On)

**Cost watch:**
- [ ] Confirm the F1 plan is the only compute cost; DB is $0 (SQLite). No managed-DB charges.

## 5. Gotchas we hit (so they don't bite again)

- **Hostname has a unique suffix** — it's `exec-panel-sim-eqccebashuedepfy.centralus-01.azurewebsites.net`,
  not the bare `exec-panel-sim.azurewebsites.net`.
- **`DATABASE_URL` needs four slashes** — three gave `no such table` (relative, ephemeral path).
- **`SCM_DO_BUILD_DURING_DEPLOYMENT=true` is required** or dependencies never install (1-second "build").
- **Startup command lives under Stack settings**, not General settings, in the current portal.
- **App's `/health` ≠ Azure's Health-check feature** (the latter is disabled on Free; fine).

## 6. Future / out of scope

- **CI/CD (push-to-deploy):** set up GitHub Actions via **OIDC federated identity** (the token-free route the
  tenant allows). Until then, redeploy manually (Section 3).
- **Scale-out / managed DB:** to move past single-instance, switch `DATABASE_URL` to **Azure SQL free tier**
  ($0, needs T-SQL `MERGE` + ODBC) or **Postgres Flexible** (~$16/mo). The DB layer is built for it; two spots
  in `database.py` carry the only dialect-specific code (`_upsert()` and the `LIMIT` in `get_conversation_history`).
- **Secrets:** move keys from plain app settings into **Azure Key Vault** references.
