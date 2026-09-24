# Executive Panel Simulator: development handoff

Updated September 24, 2026. This plan covers the ChatGPT Sites implementation in `sites/`, not the older Flask app at the repository root.

## Current baseline

- Live test Site: <https://executive-panel-simulator-test.utexas.chatgpt.site>
- Sites project ID: `appgprj_6a7298770edc8191a195f5d93cef57d7`
- Published version: 6, deployed successfully from commit `769932636754e1a1a7ff7ba8739e6a4f0d0800e4` on `codex/sites-feasibility-spike`.
- Current scope: one PDF-backed panel session, typed or spoken answers, executive speech, a closing message, an end-of-session transcript, AI coaching, and a printable report. There is no saved-attempt history or cross-session progress view.
- The Site is active with `workspace_all` access. The current signed-in account is the owner; no other editors are listed. A different UT account should verify its editing rights before relying on this existing Site.
- Local checks at the baseline: `npm run lint` and `npm test` pass. The six existing tests mainly check source text and build output; they do not verify a complete live session.
- Recent production Worker error logs returned no events in the last seven days. This is not proof that all user flows work.

## Phase 1: prove the deployed experience (first work session)

1. In the deployed Site, run a complete session using a consented, nonconfidential PDF and the UT Portkey route. Check `/api/health` in the signed-in browser: `d1`, `r2`, and `ai` should be true and `mode` should be `live`. Confirm the allowed model aliases for analysis, panel turns, transcription, speech, and feedback. The Site's stored secret values are intentionally hidden from this handoff.
2. Test both typed and spoken answers, a follow-up on a weak answer, the CEO closing, the final transcript and feedback, and print/save as PDF. Repeat the microphone path in the browsers students will use and confirm permission denial produces a useful recovery path.
3. Verify that a second student cannot retrieve or act on the first student's session. Check behavior for a signed-out request and for a request without Sites identity headers. Record latency and failure at PDF analysis, each turn, transcription, speech, and feedback.

**Done when:** a short test record names the browser, PDF size, provider/model aliases, results of each flow, and any failures. Keep test transcripts and student content out of the repository.

## Phase 2: make a small student pilot safe and recoverable

1. Require a verified Sites identity in every API route. `requestOwnerId()` currently falls back to the shared string `local-preview` when the identity header is missing; keep any local preview bypass explicit and unavailable in production. Add route-level tests for missing identity and cross-user access.
2. Decide and publish a retention period. `documents.expires_at` is set to 24 hours, but there is no deletion job. Add cleanup for R2 PDFs and audio, D1 sessions/turns/feedback, and uploaded provider files. Confirm the cleanup actually runs and document the student-facing data notice.
3. Make response submission recoverable. The current route claims a turn before generating the next question; a provider failure or lost response can leave that turn answered without a way to continue. Add idempotent retries, persisted completion/results, and a session-status endpoint so a refresh can resume safely. Return stable, student-friendly errors while logging diagnostic detail privately.
4. Add bounded upload and request controls: validation beyond the PDF header, audio type/length checks, per-user rate limits, and timeouts. Check that provider error bodies and report text are not echoed to students or logs.
5. Add a small integration suite for create session → answer turns → completion, including concurrent/double submit, provider failure, reload, and ownership. Keep the existing build/lint checks. Add minimal telemetry for error rates, latency, and provider cost without storing report text in analytics.

**Done when:** the pilot can recover from refreshes and transient provider failures, student data expires as stated, identity and ownership checks pass, and a complete live rehearsal succeeds.

## Phase 3: evaluate with a limited class pilot

1. Invite a small group of students and instructors through the intended Sites access policy. Collect structured feedback on question realism, repeated questions, voice usability, the quality of cited coaching, and report readability.
2. Review a sample of consented sessions against the source reports. Check that questions stay grounded, rotate appropriately across chosen roles, and that feedback quotes the correct question numbers and addresses the presenter. Tune prompts and model aliases using those observations.
3. Decide whether saved attempts and progress over time are pedagogically useful before building them. If approved, design the data model and retention rules first; then add history, comparisons, and instructor reporting.

**Done when:** there is a documented go/no-go decision for a wider rollout, with observed reliability, latency, cost, accessibility, and learning-value evidence.

## Continue under another UT license

1. Open the GitHub repository `johngraff512/executive-panel-simulator` from the other account, confirm repository access, and check out `codex/sites-feasibility-spike`. The local `origin/codex/sites-feasibility-spike` reference matches the deployed commit above; a fresh remote check was unavailable in this session because `github.com` did not resolve.
2. Sign in to the UT Sites workspace with the other license and check the role on project `appgprj_6a7298770edc8191a195f5d93cef57d7`. The current Site metadata lists only the original account as owner and no editors. If the second account cannot edit, have the owner or workspace administrator grant editor access. If the accounts are in different workspaces and access cannot be granted, create a new Site from this source and record its new project ID and URL; do not assume D1/R2 data or environment variables transfer.
3. For a new Site, configure the `DB` and `FILES` bindings and the required Portkey secrets through that Site's environment settings. Use `sites/.env.example` for variable names, not for secret values. Verify the UT credential and model permissions with the other account. Never commit `.env.local` or secret values.
4. From `sites/`, use Node.js 22.13 or newer and run `npm ci`, `npm run lint`, and `npm test`. Make changes on a new `codex/` branch, push the exact tested commit, then save and deploy a Sites version from that commit. Verify deployment status and perform the live smoke test again.
5. Paste this instruction into a new task on the other license: **“Continue the Executive Panel Simulator Sites project from `sites/NEXT_STEPS.md`. Start with Phase 1, inspect the current deployed Site and repository branch, and complete Phase 2 before a student pilot. Keep the existing Sites project ID if this account has editor access; otherwise report the access constraint before creating a replacement Site.”**

The older `sites/README.md` still describes the initial spike and says transcripts are never returned to the browser. That was superseded by the completed-session report. Update that README when revising product documentation.
