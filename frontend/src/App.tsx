import { useState } from "react";

const BACKEND_URL = "http://localhost:8000";

const suggestions = [
  "What servers had critical CPU incidents?",
  "Which server had memory issues?",
  "What was the highest CPU usage recorded?",
];

const stats = [
  { label: "Incidents Indexed", value: "12" },
  { label: "Servers Monitored", value: "4" },
  { label: "Avg Faithfulness", value: "0.75" },
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setAnswer("");
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") break;
          try {
            const parsed = JSON.parse(data);
            if (parsed.token) setAnswer((prev) => prev + parsed.token);
          } catch {}
        }
      }
    } catch {
      setAnswer("Error: could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-cyan-50 flex">

      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside className="w-64 min-h-screen bg-white border-r border-cyan-100 flex flex-col px-5 py-8 shrink-0">

        {/* Brand */}
        <div className="flex items-center gap-2.5 mb-10">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center shadow-sm">
            <span className="text-white text-xs font-bold tracking-tight">AI</span>
          </div>
          <div>
            <p className="text-xs font-bold text-slate-800 leading-none">Incident AI</p>
            <p className="text-xs text-slate-400 mt-0.5">Intelligence Platform</p>
          </div>
        </div>

        {/* Stats */}
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
          Overview
        </p>
        <div className="flex flex-col gap-3 mb-10">
          {stats.map((s) => (
            <div key={s.label} className="bg-cyan-50 rounded-lg px-4 py-3 border border-cyan-100">
              <p className="text-lg font-bold text-teal-600">{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Suggested queries */}
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
          Try asking
        </p>
        <div className="flex flex-col gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => setQuestion(s)}
              className="text-left text-xs text-slate-600 hover:text-teal-600 hover:bg-teal-50 px-3 py-2.5 rounded-lg border border-transparent hover:border-teal-100 transition-all leading-snug"
            >
              {s}
            </button>
          ))}
        </div>

        <div className="mt-auto" />
      </aside>

      {/* ── Main panel ───────────────────────────────────────── */}
      <div className="flex-1 flex flex-col">

        {/* Top bar */}
        <header className="bg-white border-b border-cyan-100 px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold text-slate-800">Query Incidents</h1>
            <p className="text-xs text-slate-400">Ask natural language questions about your infrastructure</p>
          </div>
          <div className="flex items-center gap-1.5 bg-teal-50 border border-teal-200 text-teal-600 text-xs font-medium px-3 py-1.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            RAG Pipeline Active
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 flex flex-col items-center justify-center px-8 py-10">
          <div className="w-full max-w-2xl flex flex-col gap-6">

            {/* Empty state heading */}
            {!answer && !loading && (
              <div className="text-center mb-2">
                <h2 className="text-xl font-bold text-slate-700 mb-1">What do you want to know?</h2>
                <p className="text-slate-400 text-sm">Ask anything about your infrastructure incidents</p>
              </div>
            )}

            {/* Search box */}
            <form onSubmit={handleSubmit}>
              <div className="bg-white border border-cyan-200 rounded-2xl p-3 shadow-sm flex gap-2 focus-within:border-teal-400 focus-within:ring-2 focus-within:ring-teal-100 transition-all">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask anything about your incidents..."
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold px-6 py-2.5 rounded-xl transition-all shadow-sm"
                >
                  {loading ? "Thinking…" : "Ask"}
                </button>
              </div>
            </form>

            {/* Answer */}
            {(answer || loading) && (
              <div className="bg-white border border-cyan-100 rounded-2xl shadow-sm overflow-hidden">
                <div className="flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-teal-50 to-cyan-50 border-b border-cyan-100">
                  <div className="w-2 h-2 rounded-full bg-teal-400" />
                  <span className="text-xs font-semibold text-teal-600 uppercase tracking-widest">
                    AI Response
                  </span>
                </div>
                <div className="px-6 py-6">
                  <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                    {answer}
                    {loading && (
                      <span className="inline-block w-2 h-4 bg-teal-400 ml-0.5 animate-pulse rounded-sm" />
                    )}
                  </p>
                </div>
              </div>
            )}

            {/* Suggestion chips below input when no answer */}
            {!answer && !loading && (
              <div className="flex flex-wrap gap-2 justify-center">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => setQuestion(s)}
                    className="text-xs bg-white border border-cyan-200 text-slate-500 hover:border-teal-400 hover:text-teal-600 px-4 py-2 rounded-full transition-all shadow-sm"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

          </div>
        </main>
      </div>
    </div>
  );
}
