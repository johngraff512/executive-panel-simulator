"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";

type Executive = {
  role: string;
  name: string;
  focus: string;
  image: string;
};

type Question = {
  executive: string;
  executiveName: string;
  question: string;
  isFollowup: boolean;
};

type Health = {
  mode: "live" | "demonstration";
  provider: "portkey" | "openai" | "none";
  capabilities: {
    d1: boolean;
    r2: boolean;
    ai: boolean;
    openai: boolean;
    portkey: boolean;
    voice: boolean;
  };
};

type AnalyzeResponse = {
  error?: string;
  sessionId: string;
  mode: "live" | "demonstration";
  provider: "portkey" | "openai" | "none";
  questionNumber: number;
  question: Question;
};

type PanelResponse = {
  error?: string;
  complete: boolean;
  questionNumber: number;
  question?: Question;
  result?: SessionResult;
};

type TranscriptTurn = {
  number: number;
  executive: string;
  executiveName: string;
  question: string;
  response: string;
  responseType: "text" | "audio";
  isFollowup: boolean;
};

type FeedbackItem = {
  title: string;
  detail: string;
  questionNumbers: number[];
};

type SessionFeedback = {
  summary: string;
  strengths: FeedbackItem[];
  improvements: FeedbackItem[];
  nextPracticeGoal: string;
};

type SessionResult = {
  companyName: string;
  reportType: string;
  questionCount: number;
  executiveCount: number;
  voiceResponseCount: number;
  transcript: TranscriptTurn[];
  feedback: SessionFeedback | null;
  feedbackUnavailable: boolean;
};

const executives: Executive[] = [
  { role: "CEO", name: "Sarah Chen", focus: "Strategy and enterprise value", image: "/executives/sarah_chen.png" },
  { role: "CFO", name: "Michael Rodriguez", focus: "Economics, risk, and return", image: "/executives/michael_rodriguez.png" },
  { role: "CTO", name: "Dr. Lisa Kincaid", focus: "Feasibility and technology", image: "/executives/lisa_kincaid.png" },
  { role: "CMO", name: "James Thompson", focus: "Customers and differentiation", image: "/executives/james_thompson.png" },
  { role: "COO", name: "Rebecca Johnson", focus: "Execution and operations", image: "/executives/rebecca_johnson.png" },
];

function currentExecutive(question: Question | null): Executive {
  return executives.find((item) => item.role === question?.executive) ?? executives[0];
}

async function readApiResponse<T extends { error?: string }>(
  response: Response,
  fallbackMessage: string,
): Promise<T> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const data = (await response.json()) as T;
    if (!response.ok) throw new Error(data.error || fallbackMessage);
    return data;
  }

  const responseText = (await response.text()).trim();
  if (response.status === 413) {
    throw new Error("The report exceeds the 50 MB PDF upload limit.");
  }
  throw new Error(responseText || fallbackMessage);
}

export function SimulatorSpike() {
  const [phase, setPhase] = useState<"setup" | "preparing" | "ready" | "session" | "complete">("setup");
  const [health, setHealth] = useState<Health | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [reportType, setReportType] = useState("Strategic recommendation");
  const [selected, setSelected] = useState(["CEO", "CFO", "COO"]);
  const [questionLimit, setQuestionLimit] = useState(6);
  const [allowFollowups, setAllowFollowups] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [question, setQuestion] = useState<Question | null>(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [responseMode, setResponseMode] = useState<"voice" | "text">("voice");
  const [textResponse, setTextResponse] = useState("");
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [liveMode, setLiveMode] = useState(false);
  const [voiceReady, setVoiceReady] = useState(false);
  const [naturalVoiceReady, setNaturalVoiceReady] = useState(false);
  const [sessionResult, setSessionResult] = useState<SessionResult | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const activeQuestionAudio = useRef<HTMLAudioElement | null>(null);
  const speechUrls = useRef(new Map<string, string>());
  const speechLoads = useRef(new Map<string, Promise<string | null>>());

  useEffect(() => {
    const speechUrlCache = speechUrls.current;
    fetch("/api/health")
      .then(async (response) => (await response.json()) as Health)
      .then((data) => setHealth(data))
      .catch(() => setHealth(null));
    return () => {
      stopMedia();
      stopQuestionAudio();
      speechUrlCache.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  function toggleExecutive(role: string) {
    setSelected((roles) =>
      roles.includes(role)
        ? roles.length === 1
          ? roles
          : roles.filter((item) => item !== role)
        : [...roles, role],
    );
  }

  async function preparePanel(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !companyName.trim()) return;
    setError("");
    setPhase("preparing");
    const form = new FormData();
    form.set("report", file);
    form.set("companyName", companyName.trim());
    form.set("reportType", reportType);
    form.set("executives", JSON.stringify(selected));
    form.set("questionLimit", String(questionLimit));
    form.set("allowFollowups", String(allowFollowups));
    try {
      const response = await fetch("/api/analyze", { method: "POST", body: form });
      const data = await readApiResponse<AnalyzeResponse>(
        response,
        "Unable to prepare the panel",
      );
      setSessionId(data.sessionId);
      setQuestion(data.question);
      setQuestionNumber(data.questionNumber);
      setLiveMode(data.mode === "live");
      setVoiceReady(data.mode !== "live");
      setNaturalVoiceReady(false);
      setPhase("ready");
      if (data.mode === "live") {
        void loadSpeech(data.sessionId, data.question)
          .then((url) => setNaturalVoiceReady(Boolean(url)))
          .finally(() => setVoiceReady(true));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to prepare the panel");
      setPhase("setup");
    }
  }

  function browserSpeak(questionToSpeak: Question) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(questionToSpeak.question);
    const fallbackDelivery: Record<string, { rate: number; pitch: number }> = {
      CEO: { rate: 0.92, pitch: 1.02 },
      CFO: { rate: 0.9, pitch: 0.88 },
      CTO: { rate: 0.94, pitch: 1.08 },
      CMO: { rate: 1, pitch: 0.98 },
      COO: { rate: 0.97, pitch: 1.04 },
    };
    const delivery = fallbackDelivery[questionToSpeak.executive] || fallbackDelivery.CEO;
    utterance.rate = delivery.rate;
    utterance.pitch = delivery.pitch;
    window.speechSynthesis.speak(utterance);
  }

  function speechKey(id: string, questionToSpeak: Question) {
    return `${id}:${questionToSpeak.executive}:${questionToSpeak.question}`;
  }

  async function loadSpeech(id: string, questionToSpeak: Question): Promise<string | null> {
    const key = speechKey(id, questionToSpeak);
    const cached = speechUrls.current.get(key);
    if (cached) return cached;
    const pending = speechLoads.current.get(key);
    if (pending) return pending;

    const load = fetch("/api/speech", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: id }),
    })
      .then(async (response) => {
        if (!response.ok) return null;
        const url = URL.createObjectURL(await response.blob());
        speechUrls.current.set(key, url);
        return url;
      })
      .catch(() => null)
      .finally(() => speechLoads.current.delete(key));
    speechLoads.current.set(key, load);
    return load;
  }

  function stopQuestionAudio() {
    activeQuestionAudio.current?.pause();
    activeQuestionAudio.current = null;
    window.speechSynthesis?.cancel();
  }

  async function speakQuestion(questionToSpeak: Question, id = sessionId) {
    stopQuestionAudio();
    if (liveMode || id !== sessionId) {
      const url = await loadSpeech(id, questionToSpeak);
      if (url) {
        const audio = new Audio(url);
        activeQuestionAudio.current = audio;
        try {
          await audio.play();
          return;
        } catch {
          // A browser can still block delayed playback; Replay remains available.
        }
      }
    }
    browserSpeak(questionToSpeak);
  }

  function enterRoom() {
    if (!question || !voiceReady) return;
    setPhase("session");
    void speakQuestion(question);
  }

  async function submitText() {
    const responseText = textResponse.trim();
    if (!responseText) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, response: responseText }),
      });
      await handlePanelResponse(response);
      setTextResponse("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit the response");
    } finally {
      setBusy(false);
    }
  }

  async function startRecording() {
    setError("");
    if (!health?.capabilities.voice) {
      setError("Voice transcription needs Portkey or OpenAI runtime credentials for a live test.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      const preferredMimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/mp4")
          ? "audio/mp4"
          : "";
      const recorder = preferredMimeType
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);
      mediaStream.current = stream;
      mediaRecorder.current = recorder;
      audioChunks.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size) audioChunks.current.push(event.data);
      };
      recorder.onstop = () => void submitRecording();
      recorder.start();
      setElapsed(0);
      setRecording(true);
      timer.current = setInterval(() => setElapsed((value) => value + 1), 1000);
    } catch {
      setError("Microphone access is required for voice simulation.");
    }
  }

  function stopRecording() {
    if (mediaRecorder.current?.state === "recording") mediaRecorder.current.stop();
    setRecording(false);
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    mediaStream.current?.getTracks().forEach((track) => track.stop());
    mediaStream.current = null;
  }

  function stopMedia() {
    if (timer.current) clearInterval(timer.current);
    if (mediaRecorder.current?.state === "recording") {
      mediaRecorder.current.onstop = null;
      mediaRecorder.current.stop();
    }
    mediaStream.current?.getTracks().forEach((track) => track.stop());
  }

  async function submitRecording() {
    const mimeType = mediaRecorder.current?.mimeType || "audio/webm";
    const extension = mimeType.includes("mp4") ? "mp4" : "webm";
    const audio = new Blob(audioChunks.current, { type: mimeType });
    audioChunks.current = [];
    if (!audio.size) return;
    setBusy(true);
    setError("");
    const form = new FormData();
    form.set("sessionId", sessionId);
    form.set("audio", audio, `spoken-response.${extension}`);
    try {
      const response = await fetch("/api/respond", { method: "POST", body: form });
      await handlePanelResponse(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit the spoken response");
    } finally {
      setBusy(false);
    }
  }

  async function handlePanelResponse(response: Response) {
    const data = await readApiResponse<PanelResponse>(
      response,
      "The panel could not continue",
    );
    if (data.complete) {
      if (!data.result) throw new Error("The session ended without a transcript.");
      setSessionResult(data.result);
      setPhase("complete");
      stopQuestionAudio();
      return;
    }
    if (!data.question) throw new Error("The panel returned no next question.");
    setQuestion(data.question);
    setQuestionNumber(data.questionNumber);
    await speakQuestion(data.question);
  }

  function restart() {
    stopQuestionAudio();
    speechUrls.current.forEach((url) => URL.revokeObjectURL(url));
    speechUrls.current.clear();
    speechLoads.current.clear();
    setPhase("setup");
    setSessionId("");
    setQuestion(null);
    setQuestionNumber(1);
    setTextResponse("");
    setError("");
    setVoiceReady(false);
    setNaturalVoiceReady(false);
    setSessionResult(null);
  }

  const activeExecutive = currentExecutive(question);
  const progress = `${Math.round((questionNumber / questionLimit) * 100)}%`;

  return (
    <main className="site-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <Image src="/mccombs-logo.jpg" alt="McCombs School of Business" width={70} height={42} unoptimized />
          <div>
            <span className="eyebrow">McCombs practice lab</span>
            <strong>Executive Panel Simulator</strong>
          </div>
        </div>
        <div className="runtime-pill" data-live={health?.mode === "live"}>
          <span /> {health?.provider === "portkey"
            ? "Portkey connected"
            : health?.provider === "openai"
              ? "OpenAI connected"
              : "Feasibility mode"}
        </div>
      </header>

      {phase === "setup" && (
        <section className="setup-layout">
          <div className="hero-copy">
            <span className="section-kicker">Defend the recommendation</span>
            <h1>Face the room before the room matters.</h1>
            <p>
              Upload your report, choose the executives, and practice answering
              direct questions under pressure. Voice responses are submitted as
              spoken—there is no transcript review or do-over.
            </p>
            <div className="proof-row">
              <div><b>01</b><span>Grounded in your report</span></div>
              <div><b>02</b><span>Adaptive follow-ups</span></div>
              <div><b>03</b><span>Voice-first realism</span></div>
            </div>
          </div>

          <form className="setup-card" onSubmit={preparePanel}>
            <div className="form-heading">
              <div><span>Session setup</span><h2>Prepare your panel</h2></div>
              <span className="step-badge">Private pilot</span>
            </div>

            <label className="field-label" htmlFor="company">Company</label>
            <input id="company" value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="e.g. Rivian" required />

            <div className="two-column">
              <div>
                <label className="field-label" htmlFor="reportType">Presentation</label>
                <select id="reportType" value={reportType} onChange={(event) => setReportType(event.target.value)}>
                  <option>Strategic recommendation</option>
                  <option>Case analysis</option>
                  <option>Investment pitch</option>
                  <option>Product launch</option>
                </select>
              </div>
              <div>
                <label className="field-label" htmlFor="questionLimit">Questions</label>
                <select id="questionLimit" value={questionLimit} onChange={(event) => setQuestionLimit(Number(event.target.value))}>
                  <option value={4}>4 · Quick pressure test</option>
                  <option value={6}>6 · Standard session</option>
                  <option value={8}>8 · Deep dive</option>
                </select>
              </div>
            </div>

            <span className="field-label">Executive panel</span>
            <div className="executive-picker">
              {executives.map((executive) => (
                <button key={executive.role} type="button" className={selected.includes(executive.role) ? "selected" : ""} onClick={() => toggleExecutive(executive.role)} aria-pressed={selected.includes(executive.role)}>
                  <Image src={executive.image} alt="" width={43} height={43} unoptimized />
                  <span><b>{executive.role}</b><small>{executive.name}</small></span>
                </button>
              ))}
            </div>

            <label className="upload-field">
              <input
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => {
                  const selectedFile = event.target.files?.[0] ?? null;
                  if (selectedFile && selectedFile.size > 50 * 1024 * 1024) {
                    setFile(null);
                    setError("The report must be smaller than 50 MB.");
                    event.target.value = "";
                    return;
                  }
                  setError("");
                  setFile(selectedFile);
                }}
                required
              />
              <span className="upload-icon">↥</span>
              <span><b>{file ? file.name : "Choose your PDF report"}</b><small>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB ready` : "Up to 50 MB · text and charts included"}</small></span>
            </label>

            <label className="switch-row">
              <input type="checkbox" checked={allowFollowups} onChange={(event) => setAllowFollowups(event.target.checked)} />
              <span><b>Allow adaptive follow-ups</b><small>The panel may press an unsupported or evasive answer.</small></span>
            </label>

            {error && <p className="error-banner" role="alert">{error}</p>}
            <button className="primary-action" type="submit" disabled={!file || !companyName.trim()}>
              Prepare the executive room <span>→</span>
            </button>
          </form>
        </section>
      )}

      {phase === "preparing" && (
        <section className="center-state" aria-live="polite">
          <div className="pulse-mark"><span /><span /><span /></div>
          <span className="section-kicker">Reading the room</span>
          <h1>The panel is reviewing your report.</h1>
          <p>Identifying challengeable assumptions, evidence gaps, and execution risks.</p>
          <div className="analysis-steps"><span className="done">PDF secured</span><span className="active">Strategic analysis</span><span>First question</span></div>
        </section>
      )}

      {phase === "ready" && question && (
        <section className="center-state ready-state" aria-live="polite">
          <span className="section-kicker">The panel is assembled</span>
          <h1>The executives are ready for you.</h1>
          <p>
            Your report has been reviewed and the first question is prepared.
            Take a breath. The simulation begins when you enter the room.
          </p>
          <div className="ready-panel" aria-label="Selected executive panel">
            {executives.filter((item) => selected.includes(item.role)).map((executive) => (
              <div key={executive.role}>
                <Image src={executive.image} alt="" width={64} height={64} unoptimized />
                <span><b>{executive.name}</b><small>{executive.role}</small></span>
              </div>
            ))}
          </div>
          <button className="primary-action compact enter-room" type="button" onClick={enterRoom} disabled={!voiceReady}>
            {voiceReady ? "Enter the room →" : "Preparing executive voices…"}
          </button>
          <small className="voice-disclosure">
            {naturalVoiceReady
              ? "Executive dialogue uses distinct AI-generated voices."
              : voiceReady
                ? "Natural voices are unavailable; this session will use your device voice."
                : "Generating distinct voices for the executive panel."}
          </small>
        </section>
      )}

      {phase === "session" && question && (
        <section className="session-layout">
          <aside className="panel-rail">
            <span className="section-kicker">In the room</span>
            <h2>Executive panel</h2>
            <div className="panel-list">
              {executives.filter((item) => selected.includes(item.role)).map((executive) => (
                <div key={executive.role} className={executive.role === question.executive ? "active" : ""}>
                  <Image src={executive.image} alt="" width={48} height={48} unoptimized />
                  <span><b>{executive.name}</b><small>{executive.role} · {executive.focus}</small></span>
                </div>
              ))}
            </div>
            <div className="session-note"><b>Simulation rule</b><p>Spoken answers are submitted exactly as delivered. No transcript review or editing.</p></div>
          </aside>

          <div className="question-stage">
            <div className="session-progress"><span>Question {questionNumber} of {questionLimit}</span><div><i style={{ width: progress }} /></div><span>{liveMode ? "Live AI" : "Demo logic"}</span></div>
            <article className="question-card">
              <div className="speaker-line">
                <Image src={activeExecutive.image} alt={activeExecutive.name} width={65} height={65} unoptimized />
                <div><span>{question.isFollowup ? "Follow-up" : activeExecutive.role}</span><h2>{activeExecutive.name}</h2><p>{activeExecutive.focus}</p></div>
                <button type="button" className="listen-button" onClick={() => void speakQuestion(question)} aria-label="Replay question">↻ Replay</button>
              </div>
              <blockquote>{question.question}</blockquote>
            </article>

            <div className="response-card">
              <div className="response-heading"><div><span>Your response</span><h3>Answer the panel</h3></div><div className="mode-toggle"><button type="button" className={responseMode === "voice" ? "active" : ""} onClick={() => setResponseMode("voice")}>Voice</button><button type="button" className={responseMode === "text" ? "active" : ""} onClick={() => setResponseMode("text")}>Text</button></div></div>
              {responseMode === "voice" ? (
                <div className="voice-control">
                  <button type="button" className={recording ? "record-button recording" : "record-button"} onClick={recording ? stopRecording : startRecording} disabled={busy}>
                    <span>{recording ? "■" : "●"}</span>{recording ? "Submit spoken response" : "Begin spoken response"}
                  </button>
                  <p>{recording ? `Recording ${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")} · stopping submits immediately` : busy ? "Your response is with the panel…" : "Your transcript is used privately by the panel and is not shown for editing."}</p>
                </div>
              ) : (
                <div className="text-control">
                  <textarea value={textResponse} onChange={(event) => setTextResponse(event.target.value)} placeholder="Answer directly, then support it with evidence…" rows={4} />
                  <button type="button" onClick={submitText} disabled={busy || !textResponse.trim()}>{busy ? "Panel is considering…" : "Submit response →"}</button>
                </div>
              )}
              {error && <p className="error-banner" role="alert">{error}</p>}
            </div>
          </div>
        </section>
      )}

      {phase === "complete" && sessionResult && (
        <section className="results-shell">
          <div className="results-hero">
            <span className="completion-mark">✓</span>
            <div>
              <span className="section-kicker">Session complete</span>
              <h1>You stayed in the room.</h1>
              <p>{sessionResult.companyName} · {sessionResult.reportType}</p>
            </div>
            <div className="completion-grid">
              <div><b>{sessionResult.questionCount}</b><span>questions faced</span></div>
              <div><b>{sessionResult.executiveCount}</b><span>executives engaged</span></div>
              <div><b>{sessionResult.voiceResponseCount}</b><span>spoken responses</span></div>
            </div>
          </div>

          <section className="feedback-section" aria-labelledby="feedback-title">
            <div className="results-heading">
              <div><span className="section-kicker">Executive communication coaching</span><h2 id="feedback-title">AI performance feedback</h2></div>
              <small>Generated from this session’s transcript and report analysis</small>
            </div>
            {sessionResult.feedback ? (
              <>
                <p className="feedback-summary">{sessionResult.feedback.summary}</p>
                <div className="feedback-grid">
                  <article className="feedback-card strength-card">
                    <h3>What you did well</h3>
                    {sessionResult.feedback.strengths.map((item) => (
                      <div key={`${item.title}-${item.questionNumbers.join("-")}`}>
                        <span>{item.questionNumbers.map((number) => `Q${number}`).join(" · ")}</span>
                        <h4>{item.title}</h4>
                        <p>{item.detail}</p>
                      </div>
                    ))}
                  </article>
                  <article className="feedback-card improvement-card">
                    <h3>Areas for improvement</h3>
                    {sessionResult.feedback.improvements.map((item) => (
                      <div key={`${item.title}-${item.questionNumbers.join("-")}`}>
                        <span>{item.questionNumbers.map((number) => `Q${number}`).join(" · ")}</span>
                        <h4>{item.title}</h4>
                        <p>{item.detail}</p>
                      </div>
                    ))}
                  </article>
                </div>
                <div className="practice-goal"><span>Next practice goal</span><p>{sessionResult.feedback.nextPracticeGoal}</p></div>
              </>
            ) : (
              <div className="feedback-unavailable" role="status">
                <h3>Feedback could not be generated</h3>
                <p>Your complete transcript is still available below for review.</p>
              </div>
            )}
          </section>

          <section className="transcript-section" aria-labelledby="transcript-title">
            <div className="results-heading">
              <div><span className="section-kicker">Review after the room</span><h2 id="transcript-title">Session transcript</h2></div>
              <button type="button" className="print-button" onClick={() => window.print()}>Print / save as PDF</button>
            </div>
            <p className="transcript-note">The transcript is revealed only after the session. Spoken responses appear exactly as transcribed and cannot be edited.</p>
            <div className="transcript-list">
              {sessionResult.transcript.map((turn) => {
                const executive = executives.find((item) => item.role === turn.executive) ?? executives[0];
                return (
                  <article key={turn.number} className="transcript-turn">
                    <div className="transcript-speaker">
                      <Image src={executive.image} alt="" width={46} height={46} unoptimized />
                      <div><span>Question {turn.number}{turn.isFollowup ? " · Follow-up" : ""}</span><h3>{turn.executiveName}</h3><small>{turn.executive}</small></div>
                    </div>
                    <blockquote>{turn.question}</blockquote>
                    <div className="transcript-answer"><span>Your {turn.responseType === "audio" ? "spoken response · transcribed" : "written response"}</span><p>{turn.response}</p></div>
                  </article>
                );
              })}
            </div>
          </section>

          <div className="results-actions">
            <button className="primary-action compact" type="button" onClick={restart}>Start another pressure test</button>
          </div>
        </section>
      )}
    </main>
  );
}
