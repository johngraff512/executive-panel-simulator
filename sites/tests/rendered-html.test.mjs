import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

test("contains the executive panel product and simulation constraint", async () => {
  const [page, simulator, layout] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/SimulatorSpike.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);

  assert.match(page, /SimulatorSpike/);
  assert.match(layout, /Executive Panel Simulator/);
  assert.match(simulator, /Face the room before the room matters/);
  assert.match(simulator, /Voice responses are submitted as\s+spoken/);
  assert.match(simulator, /no transcript review or do-over/);
  assert.match(simulator, /The executives are ready for you/);
  assert.match(simulator, /Enter the room/);
  assert.doesNotMatch(`${page}${simulator}${layout}`, /codex-preview|react-loading-skeleton/i);
});

test("declares Sites storage and removes disposable starter UI", async () => {
  const [hosting, packageJson] = await Promise.all([
    readFile(new URL("../.openai/hosting.json", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  const hostingConfig = JSON.parse(hosting);
  assert.equal(hostingConfig.d1, "DB");
  assert.equal(hostingConfig.r2, "FILES");
  assert.match(hostingConfig.project_id, /^appgprj_/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});

test("supports realistic PDF uploads and non-JSON error responses", async () => {
  const [nextConfig, simulator, worker] = await Promise.all([
    readFile(new URL("../next.config.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/SimulatorSpike.tsx", import.meta.url), "utf8"),
    readFile(new URL("../worker/index.ts", import.meta.url), "utf8"),
  ]);

  assert.match(nextConfig, /bodySizeLimit:\s*"52mb"/);
  assert.match(nextConfig, /unoptimized:\s*true/);
  assert.match(simulator, /response\.status === 413/);
  assert.match(simulator, /exceeds the 50 MB PDF upload limit/);

  const imageCount = simulator.match(/<Image\b/g)?.length ?? 0;
  const unoptimizedCount = simulator.match(/\bunoptimized\b/g)?.length ?? 0;
  assert.equal(unoptimizedCount, imageCount);
  assert.match(worker, /if \(!env\.ASSETS \|\| !env\.IMAGES\)/);
  assert.match(worker, /Response\.redirect/);
});

test("prefers Portkey and adds privacy-preserving tracking metadata", async () => {
  const [provider, health, envExample, speechRoute] = await Promise.all([
    readFile(new URL("../lib/openai.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/api/health/route.ts", import.meta.url), "utf8"),
    readFile(new URL("../.env.example", import.meta.url), "utf8"),
    readFile(new URL("../app/api/speech/route.ts", import.meta.url), "utf8"),
  ]);

  assert.match(provider, /PORTKEY_API_KEY && hasPortkeyRoute/);
  assert.match(provider, /x-portkey-api-key/);
  assert.match(provider, /x-portkey-virtual-key/);
  assert.match(provider, /x-portkey-provider/);
  assert.match(provider, /x-portkey-metadata/);
  assert.match(provider, /app:\s*"executive-panel-simulator-sites"/);
  assert.match(provider, /surface:\s*"sites"/);
  assert.match(provider, /_user:\s*userHash/);
  assert.match(provider, /gpt-4o-mini-tts/);
  assert.match(provider, /coral/);
  assert.match(provider, /cedar/);
  assert.match(provider, /sage/);
  assert.match(provider, /verse/);
  assert.match(provider, /marin/);
  assert.match(provider, /targetFinding/);
  assert.match(provider, /substantively different from every prior question/);
  assert.match(speechRoute, /latestTurn\.question/);
  assert.match(health, /provider/);
  assert.match(envExample, /PORTKEY_API_KEY=/);
  assert.match(envExample, /PORTKEY_VIRTUAL_KEY=/);
  assert.match(envExample, /OPENAI_SPEECH_MODEL=gpt-4o-mini-tts/);
});

test("reveals a non-editable transcript and specific coaching after completion", async () => {
  const [simulator, styles, provider, respondRoute, speechRoute, migration, schema] = await Promise.all([
    readFile(new URL("../app/SimulatorSpike.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../lib/openai.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/api/respond/route.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/api/speech/route.ts", import.meta.url), "utf8"),
    readFile(new URL("../drizzle/0002_right_karnak.sql", import.meta.url), "utf8"),
    readFile(new URL("../db/schema.ts", import.meta.url), "utf8"),
  ]);

  assert.match(simulator, /AI performance feedback/);
  assert.match(simulator, /What you did well/);
  assert.match(simulator, /Areas for improvement/);
  assert.match(simulator, /Session transcript/);
  assert.match(simulator, /className="report-masthead"/);
  assert.match(simulator, /<h1>\{sessionResult\.companyName\}<\/h1>/);
  assert.doesNotMatch(simulator, /You stayed in the room/);
  assert.match(simulator, /Executive Panel Simulator _ \$\{safeCompanyName\}/);
  assert.match(styles, /@page \{ size: letter/);
  assert.match(simulator, /revealed only after the session/);
  assert.match(simulator, /cannot be edited/);
  assert.match(simulator, /Print \/ save as PDF/);
  assert.match(provider, /generateSessionFeedback/);
  assert.match(provider, /Every strength and improvement must cite the question number/);
  assert.match(provider, /Do not give generic praise/);
  assert.match(provider, /the presenter\/student supplied every response/);
  assert.match(provider, /Address all feedback directly to the presenter using second person/);
  assert.match(provider, /feedbackForPresenter/);
  assert.match(provider, /In your response to the \$\{role\}'s question, you/);
  assert.match(provider, /session_feedback/);
  assert.match(provider, /Thank you for submitting your analysis and recommendations, and for answering our questions today/);
  assert.match(respondRoute, /responseClaim\.meta\.changes/);
  assert.match(respondRoute, /feedback_json/);
  assert.match(respondRoute, /closingMessage:\s*CEO_CLOSING_MESSAGE/);
  assert.match(speechRoute, /body\.kind === "closing"/);
  assert.match(speechRoute, /executive:\s*isClosing \? "CEO"/);
  assert.match(simulator, /The CEO closes the meeting/);
  assert.match(simulator, /Continue to feedback/);
  assert.match(simulator, /playClosing/);
  assert.match(migration, /ADD `feedback_json` text/);
  assert.match(schema, /feedbackJson:\s*text\("feedback_json"\)/);
});
