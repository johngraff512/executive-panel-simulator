import { bindings } from "../../../db/runtime";
import {
  configuredAIProvider,
  hasAIProvider,
} from "../../../lib/openai";

export const dynamic = "force-dynamic";

export async function GET() {
  const runtime = bindings();
  const provider = configuredAIProvider(runtime);
  return Response.json({
    status: "ready",
    runtime: "sites-worker",
    capabilities: {
      d1: Boolean(runtime.DB),
      r2: Boolean(runtime.FILES),
      ai: hasAIProvider(),
      openai: provider === "openai",
      portkey: provider === "portkey",
      voice: hasAIProvider(),
    },
    provider,
    mode: hasAIProvider() ? "live" : "demonstration",
  });
}
