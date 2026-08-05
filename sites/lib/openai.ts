import {
  bindings,
  ownerSafetyId,
  type RuntimeBindings,
} from "../db/runtime";

const OPENAI_API_BASE = "https://api.openai.com/v1";
const PORTKEY_API_BASE = "https://api.portkey.ai/v1";

export type AIProvider = "portkey" | "openai" | "none";

type RequestContext = {
  feature: "file_upload" | "pdf_analysis" | "panel_turn" | "transcription" | "speech" | "session_feedback";
  ownerId?: string;
};

export type Finding = {
  id: string;
  category: string;
  label: string;
  evidence: string;
};

export type PanelQuestion = {
  executive: string;
  executiveName: string;
  question: string;
  isFollowup: boolean;
};

export type DocumentAnalysis = {
  findings: Finding[];
  firstQuestion: PanelQuestion;
};

export type TranscriptTurn = {
  number: number;
  executive: string;
  executiveName: string;
  question: string;
  response: string;
  responseType: "text" | "audio";
  isFollowup: boolean;
};

export type FeedbackItem = {
  title: string;
  detail: string;
  questionNumbers: number[];
};

export type SessionFeedback = {
  summary: string;
  strengths: FeedbackItem[];
  improvements: FeedbackItem[];
  nextPracticeGoal: string;
};

export const CEO_CLOSING_MESSAGE =
  "Thank you for submitting your analysis and recommendations, and for answering our questions today.";

type ResponsesPayload = {
  output_text?: string;
  output?: Array<{
    type?: string;
    content?: Array<{ type?: string; text?: string }>;
  }>;
};

function responseText(payload: ResponsesPayload): string {
  if (payload.output_text) return payload.output_text;
  for (const item of payload.output ?? []) {
    if (item.type !== "message") continue;
    for (const content of item.content ?? []) {
      if (content.type === "output_text" && content.text) return content.text;
    }
  }
  throw new Error("OpenAI response did not contain output text");
}

async function openAIRequest(
  path: string,
  init: RequestInit,
  context: RequestContext,
): Promise<Response> {
  const runtime = bindings();
  const provider = configuredAIProvider(runtime);
  const headers = new Headers(init.headers);
  let baseUrl: string;

  if (provider === "portkey") {
    baseUrl = (runtime.PORTKEY_BASE_URL || PORTKEY_API_BASE).replace(/\/$/, "");
    headers.set("x-portkey-api-key", runtime.PORTKEY_API_KEY as string);
    if (runtime.PORTKEY_PROVIDER) {
      headers.set("x-portkey-provider", runtime.PORTKEY_PROVIDER);
    } else {
      headers.set("x-portkey-virtual-key", runtime.PORTKEY_VIRTUAL_KEY as string);
    }
    const userHash = context.ownerId
      ? await ownerSafetyId(context.ownerId)
      : undefined;
    headers.set(
      "x-portkey-metadata",
      JSON.stringify({
        app: "executive-panel-simulator-sites",
        surface: "sites",
        environment: runtime.PORTKEY_ENVIRONMENT || "development",
        feature: context.feature,
        ...(userHash ? { _user: userHash } : {}),
      }),
    );
  } else if (provider === "openai") {
    baseUrl = OPENAI_API_BASE;
    headers.set("Authorization", `Bearer ${runtime.OPENAI_API_KEY}`);
  } else {
    throw new Error("No AI provider credentials are configured");
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    const detail = await response.text();
    const providerName = provider === "portkey" ? "Portkey" : "OpenAI";
    throw new Error(`${providerName} ${path} failed (${response.status}): ${detail}`);
  }
  return response;
}

export function configuredAIProvider(
  runtime: RuntimeBindings = bindings(),
): AIProvider {
  const hasPortkeyRoute = Boolean(
    runtime.PORTKEY_PROVIDER || runtime.PORTKEY_VIRTUAL_KEY,
  );
  if (runtime.PORTKEY_API_KEY && hasPortkeyRoute) return "portkey";
  if (runtime.OPENAI_API_KEY) return "openai";
  return "none";
}

export function hasAIProvider(): boolean {
  return configuredAIProvider() !== "none";
}

export async function uploadOpenAIFile(
  file: File,
  ownerId: string,
): Promise<string> {
  const form = new FormData();
  form.set("purpose", "user_data");
  form.set("file", file, file.name);
  const response = await openAIRequest(
    "/files",
    { method: "POST", body: form },
    { feature: "file_upload", ownerId },
  );
  const payload = (await response.json()) as { id?: string };
  if (!payload.id) throw new Error("OpenAI file upload returned no file id");
  return payload.id;
}

const analysisSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    findings: {
      type: "array",
      minItems: 8,
      maxItems: 10,
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          id: { type: "string" },
          category: { type: "string" },
          label: { type: "string" },
          evidence: { type: "string" },
        },
        required: ["id", "category", "label", "evidence"],
      },
    },
    firstQuestion: {
      type: "object",
      additionalProperties: false,
      properties: {
        executive: { type: "string" },
        executiveName: { type: "string" },
        question: { type: "string" },
        isFollowup: { type: "boolean" },
      },
      required: ["executive", "executiveName", "question", "isFollowup"],
    },
  },
  required: ["findings", "firstQuestion"],
};

export async function analyzeDocument(input: {
  fileId: string;
  ownerId: string;
  companyName: string;
  reportType: string;
  executives: string[];
}): Promise<DocumentAnalysis> {
  const { OPENAI_ANALYSIS_MODEL } = bindings();
  const model = OPENAI_ANALYSIS_MODEL || "gpt-4o";
  const supportsReasoningControls = model.startsWith("gpt-5");
  const safetyIdentifier = await ownerSafetyId(input.ownerId);
  const response = await openAIRequest(
    "/responses",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        ...(supportsReasoningControls
          ? { reasoning: { effort: "low" } }
          : {}),
        store: false,
        safety_identifier: safetyIdentifier,
        instructions:
          "You are a demanding but fair executive panel. Build a coverage map of 8 to 10 substantively distinct, report-grounded issues before writing the first question. Span as many relevant dimensions as the report supports: core recommendation, customer or market, competitive response, economics, evidence quality, implementation, technology, organizational readiness, risk, and measurement. Do not create multiple findings that are merely different phrasings of the same concern. Each finding must cite a specific claim, number, assumption, omission, or proposed action from the report in its evidence field; do not invent facts. Order findings by importance, then ask one concise first question about findings[0].",
        input: [
          {
            role: "user",
            content: [
              { type: "input_file", file_id: input.fileId, detail: "low" },
              {
                type: "input_text",
                text: `Prepare an executive-panel simulation for ${input.companyName}. Report type: ${input.reportType}. Available executive roles: ${input.executives.join(", ")}. Return the analysis and the first question.`,
              },
            ],
          },
        ],
        text: {
          ...(supportsReasoningControls ? { verbosity: "low" } : {}),
          format: {
            type: "json_schema",
            name: "panel_document_analysis",
            strict: true,
            schema: analysisSchema,
          },
        },
      }),
    },
    { feature: "pdf_analysis", ownerId: input.ownerId },
  );
  return JSON.parse(responseText((await response.json()) as ResponsesPayload));
}

const turnSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    executive: { type: "string" },
    executiveName: { type: "string" },
    question: { type: "string" },
    isFollowup: { type: "boolean" },
  },
  required: ["executive", "executiveName", "question", "isFollowup"],
};

export async function generateNextQuestion(input: {
  ownerId: string;
  companyName: string;
  reportType: string;
  executives: string[];
  findings: Finding[];
  conversation: Array<{
    executive: string;
    question: string;
    response: string | null;
  }>;
  latestResponse: string;
  allowFollowups: boolean;
  targetFinding: Finding;
}): Promise<PanelQuestion> {
  const { OPENAI_TURN_MODEL } = bindings();
  const model = OPENAI_TURN_MODEL || "gpt-4o";
  const supportsReasoningControls = model.startsWith("gpt-5");
  const safetyIdentifier = await ownerSafetyId(input.ownerId);
  const response = await openAIRequest(
    "/responses",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        ...(supportsReasoningControls
          ? { reasoning: { effort: "low" } }
          : {}),
        store: false,
        safety_identifier: safetyIdentifier,
        instructions:
          "Act as a realistic executive panel. First compare the proposed topic with every prior question. Unless a follow-up is justified, ask about the supplied targetFinding and make the new question substantively different from every prior question—not a paraphrase, alternate framing, or second request for the same evidence. A follow-up is allowed only when allowFollowups is true and the latest answer was materially vague, unsupported, evasive, or failed to answer the question; a merely imperfect answer does not justify repetition. When following up, press the unanswered point directly and set isFollowup true. Otherwise set isFollowup false, rotate to the executive whose functional perspective best fits targetFinding, and advance coverage. Do not praise, coach, summarize, or reveal an assessment. Ask one natural, direct question of at most two sentences.",
        input: JSON.stringify({
          companyName: input.companyName,
          reportType: input.reportType,
          executives: input.executives,
          allowFollowups: input.allowFollowups,
          findings: input.findings,
          targetFinding: input.targetFinding,
          fullConversation: input.conversation,
          latestResponse: input.latestResponse,
        }),
        text: {
          ...(supportsReasoningControls ? { verbosity: "low" } : {}),
          format: {
            type: "json_schema",
            name: "next_panel_question",
            strict: true,
            schema: turnSchema,
          },
        },
      }),
    },
    { feature: "panel_turn", ownerId: input.ownerId },
  );
  const question = JSON.parse(
    responseText((await response.json()) as ResponsesPayload),
  ) as PanelQuestion;
  if (!input.executives.includes(question.executive)) {
    question.executive = input.executives[0] || "CEO";
    question.executiveName = executiveName(question.executive);
  }
  if (!input.allowFollowups) question.isFollowup = false;
  return question;
}

const executiveVoices: Record<string, { voice: string; delivery: string }> = {
  CEO: {
    voice: "coral",
    delivery: "Measured, decisive, and concise. Sound strategic and comfortable with silence.",
  },
  CFO: {
    voice: "cedar",
    delivery: "Analytical and skeptical, with precise emphasis on numbers, assumptions, and tradeoffs.",
  },
  CTO: {
    voice: "sage",
    delivery: "Thoughtful and technically fluent, curious but direct when testing feasibility.",
  },
  CMO: {
    voice: "verse",
    delivery: "Energetic and customer-focused, conversational while pressing for clear differentiation.",
  },
  COO: {
    voice: "marin",
    delivery: "Practical, grounded, and brisk, with emphasis on ownership, sequencing, and execution.",
  },
};

export async function synthesizeQuestion(input: {
  ownerId: string;
  executive: string;
  question: string;
}): Promise<Response> {
  const { OPENAI_SPEECH_MODEL } = bindings();
  const profile = executiveVoices[input.executive] || executiveVoices.CEO;
  return openAIRequest(
    "/audio/speech",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: OPENAI_SPEECH_MODEL || "gpt-4o-mini-tts",
        voice: profile.voice,
        input: input.question,
        instructions: `Speak as a human senior executive in a live boardroom. ${profile.delivery} Use natural pacing, subtle emphasis, and brief conversational pauses. Avoid an announcer cadence and do not add words that are not in the question.`,
        response_format: "mp3",
        speed: 0.98,
      }),
    },
    { feature: "speech", ownerId: input.ownerId },
  );
}

const feedbackItemSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    title: { type: "string" },
    detail: { type: "string" },
    questionNumbers: {
      type: "array",
      minItems: 1,
      maxItems: 3,
      items: { type: "integer" },
    },
  },
  required: ["title", "detail", "questionNumbers"],
};

const feedbackSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    summary: { type: "string" },
    strengths: {
      type: "array",
      minItems: 2,
      maxItems: 3,
      items: feedbackItemSchema,
    },
    improvements: {
      type: "array",
      minItems: 2,
      maxItems: 3,
      items: feedbackItemSchema,
    },
    nextPracticeGoal: { type: "string" },
  },
  required: ["summary", "strengths", "improvements", "nextPracticeGoal"],
};

export async function generateSessionFeedback(input: {
  ownerId: string;
  companyName: string;
  reportType: string;
  findings: Finding[];
  transcript: TranscriptTurn[];
}): Promise<SessionFeedback> {
  const { OPENAI_FEEDBACK_MODEL, OPENAI_TURN_MODEL } = bindings();
  const model = OPENAI_FEEDBACK_MODEL || OPENAI_TURN_MODEL || "gpt-4o";
  const supportsReasoningControls = model.startsWith("gpt-5");
  const safetyIdentifier = await ownerSafetyId(input.ownerId);
  const itemCount = input.transcript.length <= 4 ? 2 : 3;
  const response = await openAIRequest(
    "/responses",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        ...(supportsReasoningControls ? { reasoning: { effort: "low" } } : {}),
        store: false,
        safety_identifier: safetyIdentifier,
        instructions:
          "You are an expert executive communication coach at a top business school. The executive named in each transcript turn ASKED the question; the presenter/student supplied every response. Address all feedback directly to the presenter using second person (you/your). Never describe an executive as having given an answer, and never say that the CEO, CFO, CTO, CMO, or COO should improve something. Executive titles may only identify who asked a question—for example, 'In your response to the CFO’s question…'. Evaluate only the substance visible in the supplied transcript and report findings. Produce warm, candid, evidence-based coaching. Every strength and improvement must cite the question number or numbers containing the evidence and explain the specific behavior to repeat or change. Do not give generic praise, invent report facts, infer vocal tone or confidence from a text transcript, or claim the presenter said something that is not present. Keep titles to 3-6 words and details to 2-3 concise sentences.",
        input: JSON.stringify({
          companyName: input.companyName,
          reportType: input.reportType,
          requestedItemsPerSection: itemCount,
          reportFindings: input.findings,
          transcript: input.transcript,
        }),
        text: {
          ...(supportsReasoningControls ? { verbosity: "low" } : {}),
          format: {
            type: "json_schema",
            name: "executive_panel_session_feedback",
            strict: true,
            schema: feedbackSchema,
          },
        },
      }),
    },
    { feature: "session_feedback", ownerId: input.ownerId },
  );
  return feedbackForPresenter(JSON.parse(
    responseText((await response.json()) as ResponsesPayload),
  ) as SessionFeedback);
}

function presenterVoice(text: string): string {
  return text
    .replace(
      /\bThe (CEO|CFO|CTO|CMO|COO)\s+/g,
      (_, role: string) => `In your response to the ${role}'s question, you `,
    )
    .replace(
      /\b(CEO|CFO|CTO|CMO|COO)\s+(should|could)\s+/g,
      (_, role: string, modal: string) =>
        `In your response to the ${role}'s question, you ${modal} `,
    );
}

function feedbackForPresenter(feedback: SessionFeedback): SessionFeedback {
  const rewriteItem = (item: FeedbackItem): FeedbackItem => ({
    ...item,
    detail: presenterVoice(item.detail),
  });
  return {
    ...feedback,
    summary: presenterVoice(feedback.summary),
    strengths: feedback.strengths.map(rewriteItem),
    improvements: feedback.improvements.map(rewriteItem),
    nextPracticeGoal: presenterVoice(feedback.nextPracticeGoal),
  };
}

export function demoSessionFeedback(transcript: TranscriptTurn[]): SessionFeedback {
  const finalQuestion = Math.max(1, transcript.length);
  return {
    summary:
      "You completed the full panel and responded across several executive perspectives. Review the transcript for places where a direct claim could be paired with stronger report evidence.",
    strengths: [
      {
        title: "Stayed With the Panel",
        detail: "You responded to each executive question and carried the recommendation through the complete session.",
        questionNumbers: [1],
      },
      {
        title: "Addressed Multiple Perspectives",
        detail: "Your responses engaged more than one functional concern rather than treating the recommendation as a single-issue decision.",
        questionNumbers: [finalQuestion],
      },
    ],
    improvements: [
      {
        title: "Lead With the Answer",
        detail: "On your next attempt, begin each response with a one-sentence answer before adding evidence and context.",
        questionNumbers: [1],
      },
      {
        title: "Make Evidence Explicit",
        detail: "Name the report fact, assumption, or metric supporting each major claim so the panel can distinguish evidence from judgment.",
        questionNumbers: [finalQuestion],
      },
    ],
    nextPracticeGoal:
      "Use a three-part response: direct answer, one concrete piece of evidence, and the implication for the executive decision.",
  };
}

export async function transcribeAudio(
  file: File,
  ownerId: string,
): Promise<string> {
  const { OPENAI_TRANSCRIBE_MODEL } = bindings();
  const form = new FormData();
  form.set("model", OPENAI_TRANSCRIBE_MODEL || "whisper-1");
  form.set("file", file, file.name || "response.webm");
  const response = await openAIRequest(
    "/audio/transcriptions",
    { method: "POST", body: form },
    { feature: "transcription", ownerId },
  );
  const payload = (await response.json()) as { text?: string };
  if (!payload.text?.trim()) throw new Error("Audio transcription was empty");
  return payload.text.trim();
}

export function demoAnalysis(
  companyName: string,
  executives: string[],
): DocumentAnalysis {
  const firstRole = executives[0] || "CEO";
  return {
    findings: [
      { id: "recommendation", category: "Strategy", label: "Core recommendation", evidence: "Test the central choice and the tradeoff it requires." },
      { id: "market", category: "Customer", label: "Market thesis", evidence: "Validate the addressable market and customer urgency." },
      { id: "economics", category: "Finance", label: "Economic case", evidence: "Test the financial assumptions and return profile." },
      { id: "execution", category: "Operations", label: "Execution plan", evidence: "Probe owners, milestones, dependencies, and resources." },
      { id: "risk", category: "Risk", label: "Risk posture", evidence: "Surface failure modes and contingency actions." },
      { id: "competition", category: "Competition", label: "Competitive response", evidence: "Challenge differentiation and likely competitor moves." },
      { id: "technology", category: "Technology", label: "Technical feasibility", evidence: "Test technical dependencies and delivery constraints." },
      { id: "evidence", category: "Evidence", label: "Evidence quality", evidence: "Separate demonstrated facts from untested assumptions." },
    ],
    firstQuestion: {
      executive: firstRole,
      executiveName: executiveName(firstRole),
      question: `You are asking us to back this recommendation for ${companyName}. What is the single most important assumption that must be true, and what evidence proves it?`,
      isFollowup: false,
    },
  };
}

export function demoNextQuestion(
  executives: string[],
  turnNumber: number,
): PanelQuestion {
  const role = executives[turnNumber % executives.length] || "CEO";
  const prompts = [
    "What tradeoff are you asking leadership to make, and why is it the right one now?",
    "Which two assumptions have the greatest effect on the financial return?",
    "Why will the target customer choose this over the strongest available alternative?",
    "Who owns the first ninety days, and what milestone tells us execution is on track?",
    "Which dependency is most likely to delay delivery, and how will you de-risk it?",
    "What is the most damaging plausible failure mode, and what contingency have you funded?",
    "Which claim in your recommendation has the weakest evidence today?",
    "What outcome should leadership measure first to know whether this decision is working?",
  ];
  return {
    executive: role,
    executiveName: executiveName(role),
    question: prompts[turnNumber % prompts.length],
    isFollowup: false,
  };
}

export function executiveName(role: string): string {
  return (
    {
      CEO: "Sarah Chen",
      CFO: "Michael Rodriguez",
      CTO: "Dr. Lisa Kincaid",
      CMO: "James Thompson",
      COO: "Rebecca Johnson",
    }[role] || role
  );
}
