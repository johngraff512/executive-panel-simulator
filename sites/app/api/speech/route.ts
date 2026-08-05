import {
  ensureSchema,
  getSession,
  requestOwnerId,
} from "../../../db/runtime";
import {
  CEO_CLOSING_MESSAGE,
  hasAIProvider,
  synthesizeQuestion,
} from "../../../lib/openai";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    if (!hasAIProvider()) {
      return Response.json(
        { error: "Natural executive voices require a live AI provider." },
        { status: 503 },
      );
    }

    const body = (await request.json()) as {
      sessionId?: string;
      kind?: "question" | "closing";
    };
    if (!body.sessionId) {
      return Response.json({ error: "Session not found." }, { status: 400 });
    }

    await ensureSchema();
    const ownerId = requestOwnerId(request);
    const record = await getSession(body.sessionId, ownerId);
    const latestTurn = record?.turns.at(-1);
    const isClosing = body.kind === "closing";
    const validStatus = isClosing
      ? record?.session.status === "complete"
      : record?.session.status === "active";
    if (!record || !latestTurn || !validStatus) {
      return Response.json({ error: "Active question not found." }, { status: 404 });
    }

    const audio = await synthesizeQuestion({
      ownerId,
      executive: isClosing ? "CEO" : latestTurn.executive,
      question: isClosing ? CEO_CLOSING_MESSAGE : latestTurn.question,
    });
    return new Response(audio.body, {
      headers: {
        "Content-Type": audio.headers.get("content-type") || "audio/mpeg",
        "Cache-Control": "private, no-store",
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to generate speech";
    return Response.json({ error: message }, { status: 500 });
  }
}
