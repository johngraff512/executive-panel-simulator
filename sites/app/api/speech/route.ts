import {
  ensureSchema,
  getSession,
  requestOwnerId,
} from "../../../db/runtime";
import { hasAIProvider, synthesizeQuestion } from "../../../lib/openai";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    if (!hasAIProvider()) {
      return Response.json(
        { error: "Natural executive voices require a live AI provider." },
        { status: 503 },
      );
    }

    const body = (await request.json()) as { sessionId?: string };
    if (!body.sessionId) {
      return Response.json({ error: "Session not found." }, { status: 400 });
    }

    await ensureSchema();
    const ownerId = requestOwnerId(request);
    const record = await getSession(body.sessionId, ownerId);
    const latestTurn = record?.turns.at(-1);
    if (!record || !latestTurn || record.session.status !== "active") {
      return Response.json({ error: "Active question not found." }, { status: 404 });
    }

    const audio = await synthesizeQuestion({
      ownerId,
      executive: latestTurn.executive,
      question: latestTurn.question,
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
