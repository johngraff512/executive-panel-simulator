# Executive Panel Simulator — Sites feasibility spike

This is a short, deployable-shape spike for running the Executive Panel Simulator as a ChatGPT Site. It lives alongside the current application so the existing implementation remains untouched while the Sites architecture is evaluated.

## Product scope

The initial Site is intentionally a focused, single-session simulation:

- Students upload one PDF report and choose a panel, question limit, and follow-up behavior.
- The panel asks role-specific questions grounded in the report and adapts to each response.
- Voice answers are transcribed privately on the server and submitted immediately. The transcript is never returned to the browser, shown for review, or editable.
- Text mode remains available for accessibility and development testing.
- Attempts, history, cross-session comparisons, and improvement tracking are explicitly deferred beyond the initial Site version.

## What the spike validates

- A vinext Site can host the simulator's React UI and server routes in one project.
- D1 can hold session and turn state; R2 can hold the source PDF and transient audio.
- The PDF-analysis route uses one structured OpenAI response to extract findings and generate the opening question.
- Each panel turn uses one structured OpenAI response to choose the executive, decide whether to follow up, and generate the next question.
- Voice input supports WebM and MP4 browser recording formats; audio is stored, transcribed server-side, and never exposed as editable text.
- The app runs in a clearly labeled demonstration mode without an API key so the UI and text-response flow can be evaluated safely.

## Run locally

Requires Node.js 22.13 or newer.

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Copy `.env.example` to `.env.local`, then add the existing UT `PORTKEY_API_KEY` and `PORTKEY_VIRTUAL_KEY` pair for live PDF analysis and voice transcription. The Site prefers Portkey, uses a direct `OPENAI_API_KEY` only as an optional fallback, and otherwise runs with deterministic demo questions and voice disabled.

Every Portkey request is tagged with `app=executive-panel-simulator-sites`, `surface=sites`, the configured environment, the request feature, and a one-way hash of the Sites user ID. This supports per-surface, per-feature, and privacy-preserving user analysis in Portkey without returning a transcript to the student.

Verification commands:

```bash
npm run lint
npm test
npm run build
```

## Architecture

- `app/SimulatorSpike.tsx`: the complete single-session user experience
- `app/api/analyze/route.ts`: PDF validation, R2 upload, D1 session creation, and report analysis
- `app/api/respond/route.ts`: text/audio intake, private transcription, adaptive panel turn, and completion
- `lib/openai.ts`: structured Responses API and transcription calls with model roles isolated behind helpers
- `db/runtime.ts`: idempotent D1 schema setup and session access
- `drizzle/`: generated migration history
- `.openai/hosting.json`: Sites D1 and R2 binding declarations

## Remaining feasibility gates

The spike should not be treated as production-ready until these checks are completed in the target workspace:

1. Validate the UT virtual key's allowed model names for Responses, file upload, and transcription; override the three model variables if the gateway uses different aliases.
2. Deploy privately and test Sites-injected identity, D1 migrations, R2 limits, microphone permissions, and supported browsers.
3. Set retention and cleanup rules for uploaded reports, audio, transcripts, and session rows.
4. Add rate limits, upload malware/content checks, observability, structured error handling, and accessibility testing.
5. Measure real report-analysis and turn latency before deciding whether streamed status updates are needed.

Saved attempts and improvement-over-time features belong to a later phase after the initial simulation experience is validated.
