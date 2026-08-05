import {
  bindings,
  ensureSchema,
  requestOwnerId,
} from "../../../db/runtime";
import {
  analyzeDocument,
  configuredAIProvider,
  demoAnalysis,
  hasAIProvider,
  uploadOpenAIFile,
} from "../../../lib/openai";

export const dynamic = "force-dynamic";

const MAX_PDF_BYTES = 50 * 1024 * 1024;

function safeFilename(filename: string): string {
  return filename.replace(/[^a-zA-Z0-9._-]/g, "_").slice(-120);
}

function parseExecutives(value: FormDataEntryValue | null): string[] {
  if (typeof value !== "string") return [];
  try {
    const roles = JSON.parse(value);
    if (!Array.isArray(roles)) return [];
    return roles.filter((role): role is string =>
      ["CEO", "CFO", "CTO", "CMO", "COO"].includes(role),
    );
  } catch {
    return [];
  }
}

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get("report");
    const companyName = String(form.get("companyName") || "").trim();
    const reportType = String(form.get("reportType") || "Business recommendation").trim();
    const executives = parseExecutives(form.get("executives"));
    const questionLimit = Math.min(
      12,
      Math.max(3, Number(form.get("questionLimit") || 6)),
    );
    const allowFollowups = String(form.get("allowFollowups")) !== "false";

    if (!(file instanceof File)) {
      return Response.json({ error: "Choose a PDF report." }, { status: 400 });
    }
    if (!companyName) {
      return Response.json({ error: "Enter a company name." }, { status: 400 });
    }
    if (!executives.length) {
      return Response.json(
        { error: "Select at least one executive." },
        { status: 400 },
      );
    }
    if (file.size > MAX_PDF_BYTES) {
      return Response.json(
        { error: "The report must be smaller than 50 MB." },
        { status: 413 },
      );
    }
    if (file.type !== "application/pdf" || (await file.slice(0, 5).text()) !== "%PDF-") {
      return Response.json({ error: "The uploaded file is not a valid PDF." }, { status: 400 });
    }

    await ensureSchema();
    const runtime = bindings();
    if (!runtime.DB || !runtime.FILES) {
      throw new Error("Sites storage bindings are unavailable");
    }

    const ownerId = requestOwnerId(request);
    const sessionId = crypto.randomUUID();
    const documentId = crypto.randomUUID();
    const objectKey = `${ownerId}/documents/${documentId}/${safeFilename(file.name)}`;
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    await runtime.FILES.put(objectKey, file.stream(), {
      httpMetadata: { contentType: "application/pdf" },
      customMetadata: { ownerId, sessionId, expiresAt },
    });

    await runtime.DB.batch([
      runtime.DB.prepare(
        `INSERT INTO documents
         (id, owner_id, object_key, filename, status, expires_at)
         VALUES (?, ?, ?, ?, 'processing', ?)`,
      ).bind(documentId, ownerId, objectKey, file.name, expiresAt),
      runtime.DB.prepare(
        `INSERT INTO sessions
         (id, owner_id, document_id, company_name, report_type,
          executives_json, question_limit, allow_followups)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      ).bind(
        sessionId,
        ownerId,
        documentId,
        companyName,
        reportType,
        JSON.stringify(executives),
        questionLimit,
        allowFollowups ? 1 : 0,
      ),
    ]);

    let analysis = demoAnalysis(companyName, executives);
    let openaiFileId: string | null = null;
    const live = hasAIProvider();
    if (live) {
      openaiFileId = await uploadOpenAIFile(file, ownerId);
      analysis = await analyzeDocument({
        fileId: openaiFileId,
        ownerId,
        companyName,
        reportType,
        executives,
      });
    }

    await runtime.DB.batch([
      runtime.DB.prepare(
        `UPDATE documents
         SET status = 'ready', analysis_json = ?, openai_file_id = ?
         WHERE id = ? AND owner_id = ?`,
      ).bind(JSON.stringify(analysis.findings), openaiFileId, documentId, ownerId),
      runtime.DB.prepare(
        `INSERT INTO turns
         (session_id, turn_number, executive, question, is_followup)
         VALUES (?, 1, ?, ?, ?)`,
      ).bind(
        sessionId,
        analysis.firstQuestion.executive,
        analysis.firstQuestion.question,
        analysis.firstQuestion.isFollowup ? 1 : 0,
      ),
    ]);

    return Response.json({
      sessionId,
      mode: live ? "live" : "demonstration",
      provider: configuredAIProvider(),
      questionNumber: 1,
      questionLimit,
      question: analysis.firstQuestion,
      findingsCount: analysis.findings.length,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to prepare the panel";
    return Response.json({ error: message }, { status: 500 });
  }
}
