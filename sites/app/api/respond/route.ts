import {
  bindings,
  ensureSchema,
  getSession,
  requestOwnerId,
} from "../../../db/runtime";
import {
  demoSessionFeedback,
  demoNextQuestion,
  CEO_CLOSING_MESSAGE,
  executiveName,
  generateNextQuestion,
  generateSessionFeedback,
  hasAIProvider,
  transcribeAudio,
  type Finding,
  type SessionFeedback,
  type TranscriptTurn,
} from "../../../lib/openai";

export const dynamic = "force-dynamic";

type ParsedResponse = {
  sessionId: string;
  responseText: string;
  responseType: "text" | "audio";
  audioFile?: File;
};

async function parseResponse(request: Request): Promise<ParsedResponse> {
  const contentType = request.headers.get("content-type") || "";
  if (contentType.includes("multipart/form-data")) {
    const form = await request.formData();
    const audio = form.get("audio");
    if (!(audio instanceof File) || !audio.size) {
      throw new Error("No spoken response was recorded.");
    }
    if (audio.size > 25 * 1024 * 1024) {
      throw new Error("The spoken response is too large.");
    }
    return {
      sessionId: String(form.get("sessionId") || ""),
      responseText: "",
      responseType: "audio",
      audioFile: audio,
    };
  }

  const body = (await request.json()) as {
    sessionId?: string;
    response?: string;
  };
  return {
    sessionId: body.sessionId || "",
    responseText: body.response?.trim() || "",
    responseType: "text",
  };
}

export async function POST(request: Request) {
  try {
    await ensureSchema();
    const runtime = bindings();
    if (!runtime.DB || !runtime.FILES) throw new Error("Sites storage is unavailable");

    const ownerId = requestOwnerId(request);
    const incoming = await parseResponse(request);
    if (!incoming.sessionId) {
      return Response.json({ error: "Session not found." }, { status: 400 });
    }

    const record = await getSession(incoming.sessionId, ownerId);
    if (!record || record.session.status !== "active") {
      return Response.json({ error: "This session is no longer active." }, { status: 404 });
    }

    let responseText = incoming.responseText;
    if (incoming.responseType === "audio") {
      if (!hasAIProvider()) {
        return Response.json(
          { error: "Voice mode needs an OpenAI key for live transcription." },
          { status: 503 },
        );
      }
      const audio = incoming.audioFile as File;
      const extension = audio.type.includes("mp4") ? "mp4" : "webm";
      const objectKey = `${ownerId}/audio/${incoming.sessionId}/turn-${record.session.current_turn}.${extension}`;
      await runtime.FILES.put(objectKey, audio.stream(), {
        httpMetadata: { contentType: audio.type || "audio/webm" },
      });
      responseText = await transcribeAudio(audio, ownerId);
    }
    if (!responseText) {
      return Response.json({ error: "Give the panel a response." }, { status: 400 });
    }

    const latestTurn = record.turns.at(-1);
    if (!latestTurn || latestTurn.response_text) {
      return Response.json(
        { error: "The latest question has already been answered." },
        { status: 409 },
      );
    }

    const responseClaim = await runtime.DB.prepare(
      `UPDATE turns SET response_text = ?, response_type = ?
       WHERE id = ? AND session_id = ? AND response_text IS NULL`,
    )
      .bind(responseText, incoming.responseType, latestTurn.id, incoming.sessionId)
      .run();
    if (!responseClaim.meta.changes) {
      return Response.json(
        { error: "This response was already submitted." },
        { status: 409 },
      );
    }

    const nextTurnNumber = record.session.current_turn + 1;
    if (nextTurnNumber > record.session.question_limit) {
      await runtime.DB.prepare(
        "UPDATE sessions SET status = 'complete', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_id = ?",
      )
        .bind(incoming.sessionId, ownerId)
        .run();

      const transcript: TranscriptTurn[] = record.turns.map((turn) => ({
        number: turn.turn_number,
        executive: turn.executive,
        executiveName: executiveName(turn.executive),
        question: turn.question,
        response:
          turn.id === latestTurn.id ? responseText : turn.response_text || "",
        responseType: (turn.id === latestTurn.id
          ? incoming.responseType
          : turn.response_type || "text") as "text" | "audio",
        isFollowup: Boolean(turn.is_followup),
      }));
      const findings = JSON.parse(record.session.analysis_json || "[]") as Finding[];
      let feedback: SessionFeedback | null = null;
      let feedbackUnavailable = false;
      try {
        feedback = hasAIProvider()
          ? await generateSessionFeedback({
              ownerId,
              companyName: record.session.company_name,
              reportType: record.session.report_type,
              findings,
              transcript,
            })
          : demoSessionFeedback(transcript);
        await runtime.DB.prepare(
          "UPDATE sessions SET feedback_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_id = ?",
        )
          .bind(JSON.stringify(feedback), incoming.sessionId, ownerId)
          .run();
      } catch {
        feedbackUnavailable = true;
      }

      return Response.json({
        complete: true,
        responseAccepted: true,
        responseType: incoming.responseType,
        questionNumber: record.session.current_turn,
        result: {
          companyName: record.session.company_name,
          reportType: record.session.report_type,
          questionCount: transcript.length,
          executiveCount: new Set(transcript.map((turn) => turn.executive)).size,
          voiceResponseCount: transcript.filter((turn) => turn.responseType === "audio").length,
          transcript,
          feedback,
          feedbackUnavailable,
          closingMessage: CEO_CLOSING_MESSAGE,
        },
      });
    }

    const executives = JSON.parse(record.session.executives_json) as string[];
    const findings = JSON.parse(record.session.analysis_json || "[]") as Finding[];
    const targetFinding = findings[(nextTurnNumber - 1) % findings.length];
    const nextQuestion = hasAIProvider()
      ? await generateNextQuestion({
          ownerId,
          companyName: record.session.company_name,
          reportType: record.session.report_type,
          executives,
          findings,
          conversation: record.turns.map((turn) => ({
            executive: turn.executive,
            question: turn.question,
            response:
              turn.id === latestTurn.id ? responseText : turn.response_text,
          })),
          latestResponse: responseText,
          allowFollowups: Boolean(record.session.allow_followups),
          targetFinding,
        })
      : demoNextQuestion(executives, nextTurnNumber - 1);

    await runtime.DB.batch([
      runtime.DB.prepare(
        `INSERT INTO turns
         (session_id, turn_number, executive, question, is_followup)
         VALUES (?, ?, ?, ?, ?)`,
      ).bind(
        incoming.sessionId,
        nextTurnNumber,
        nextQuestion.executive,
        nextQuestion.question,
        nextQuestion.isFollowup ? 1 : 0,
      ),
      runtime.DB.prepare(
        `UPDATE sessions SET current_turn = ?, updated_at = CURRENT_TIMESTAMP
         WHERE id = ? AND owner_id = ?`,
      ).bind(nextTurnNumber, incoming.sessionId, ownerId),
    ]);

    return Response.json({
      complete: false,
      responseAccepted: true,
      responseType: incoming.responseType,
      questionNumber: nextTurnNumber,
      questionLimit: record.session.question_limit,
      question: nextQuestion,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to process the response";
    return Response.json({ error: message }, { status: 500 });
  }
}
