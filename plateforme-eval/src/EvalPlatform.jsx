import React, { useState, useMemo, useRef, useEffect } from "react";
import { Plus, Trash2, GraduationCap, PenLine, Send, RotateCcw, BookOpen } from "lucide-react";

// ---------------------------------------------------------------------------
// Utilitaires de correction (moteur d'évaluation)
// ---------------------------------------------------------------------------
const normalize = (s) =>
  (s || "")
    .toString()
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

function grade(question, reponse) {
  switch (question.type) {
    case "qcm_unique":
      return reponse === question.correctOptionId;
    case "qcm_multiple": {
      const given = new Set(reponse || []);
      const correct = new Set(question.correctOptionIds || []);
      if (given.size !== correct.size) return false;
      for (const id of given) if (!correct.has(id)) return false;
      return true;
    }
    case "vrai_faux":
      return reponse === question.correctBool;
    case "reponse_courte": {
      const accepted = (question.acceptedAnswers || []).map(normalize);
      return accepted.includes(normalize(reponse));
    }
    case "numerique": {
      const val = parseFloat(reponse);
      if (Number.isNaN(val)) return false;
      const tol = question.tolerance ?? 0;
      return Math.abs(val - question.numericValue) <= tol;
    }
    default:
      return false;
  }
}

// ---------------------------------------------------------------------------
// Marque manuscrite (check / croix) — élément signature, tracée au SVG
// ---------------------------------------------------------------------------
function InkMark({ ok, delay = 0 }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const len = el.getTotalLength();
    el.style.strokeDasharray = `${len}`;
    el.style.strokeDashoffset = `${len}`;
    const t = setTimeout(() => {
      el.style.transition = "stroke-dashoffset 0.5s ease-out";
      el.style.strokeDashoffset = "0";
    }, delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <svg width="40" height="40" viewBox="0 0 40 40" className="shrink-0">
      {ok ? (
        <path
          ref={ref}
          d="M7 20 L16 29 L33 9"
          fill="none"
          stroke="#B4402A"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          ref={ref}
          d="M9 9 L31 31 M31 9 L9 31"
          fill="none"
          stroke="#B4402A"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

function ScoreCircle({ score, max }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const len = el.getTotalLength();
    el.style.strokeDasharray = `${len}`;
    el.style.strokeDashoffset = `${len}`;
    const t = setTimeout(() => {
      el.style.transition = "stroke-dashoffset 0.8s ease-out";
      el.style.strokeDashoffset = "0";
    }, 200);
    return () => clearTimeout(t);
  }, [score, max]);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="120" height="90" viewBox="0 0 120 90">
        <ellipse
          ref={ref}
          cx="60"
          cy="45"
          rx="52"
          ry="36"
          fill="none"
          stroke="#B4402A"
          strokeWidth="3"
          transform="rotate(-4 60 45)"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono text-2xl text-[#B4402A] font-semibold">
          {score}/{max}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Application principale
// ---------------------------------------------------------------------------
export default function EvalPlatform() {
  const [mode, setMode] = useState("enseignant");
  const [questions, setQuestions] = useState([
    {
      id: "q1",
      type: "qcm_unique",
      statement: "Quelle est la capitale de la France ?",
      points: 2,
      options: [
        { id: "o1", text: "Lyon" },
        { id: "o2", text: "Paris" },
        { id: "o3", text: "Marseille" },
      ],
      correctOptionId: "o2",
    },
    {
      id: "q2",
      type: "vrai_faux",
      statement: "La Terre tourne autour du Soleil.",
      points: 1,
      correctBool: true,
    },
  ]);

  const [studentAnswers, setStudentAnswers] = useState({});
  const [graded, setGraded] = useState(false);

  const totalPoints = useMemo(
    () => questions.reduce((s, q) => s + Number(q.points || 0), 0),
    [questions]
  );

  const obtainedPoints = useMemo(() => {
    if (!graded) return 0;
    return questions.reduce((sum, q) => {
      const ok = grade(q, studentAnswers[q.id]);
      return sum + (ok ? Number(q.points) : 0);
    }, 0);
  }, [graded, questions, studentAnswers]);

  function addQuestion(q) {
    setQuestions((prev) => [...prev, { ...q, id: "q" + (prev.length + 1) + "_" + Date.now() }]);
  }
  function removeQuestion(id) {
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  }
  function resetAttempt() {
    setStudentAnswers({});
    setGraded(false);
  }

  return (
    <div className="min-h-screen bg-[#F1EEE4] text-[#1C2B4A]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'IBM Plex Mono', monospace; }
      `}</style>

      {/* Header */}
      <header className="border-b-2 border-[#1C2B4A]/15 bg-[#1C2B4A] text-[#F1EEE4]">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen size={22} strokeWidth={1.75} />
            <div>
              <h1 className="font-display text-xl tracking-tight">Le Carnet</h1>
              <p className="font-body text-[11px] uppercase tracking-[0.18em] text-[#F1EEE4]/60">
                évaluations notées automatiquement
              </p>
            </div>
          </div>
          <nav className="flex gap-1 bg-[#F1EEE4]/10 rounded-full p-1">
            <button
              onClick={() => setMode("enseignant")}
              className={`font-body text-sm px-4 py-1.5 rounded-full transition-colors flex items-center gap-1.5 ${
                mode === "enseignant" ? "bg-[#F1EEE4] text-[#1C2B4A]" : "text-[#F1EEE4]/80 hover:text-[#F1EEE4]"
              }`}
            >
              <PenLine size={14} /> Enseignant
            </button>
            <button
              onClick={() => setMode("etudiant")}
              className={`font-body text-sm px-4 py-1.5 rounded-full transition-colors flex items-center gap-1.5 ${
                mode === "etudiant" ? "bg-[#F1EEE4] text-[#1C2B4A]" : "text-[#F1EEE4]/80 hover:text-[#F1EEE4]"
              }`}
            >
              <GraduationCap size={14} /> Étudiant
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        {mode === "enseignant" ? (
          <TeacherView questions={questions} onAdd={addQuestion} onRemove={removeQuestion} totalPoints={totalPoints} />
        ) : (
          <StudentView
            questions={questions}
            answers={studentAnswers}
            setAnswers={setStudentAnswers}
            graded={graded}
            setGraded={setGraded}
            totalPoints={totalPoints}
            obtainedPoints={obtainedPoints}
            onReset={resetAttempt}
          />
        )}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Vue Enseignant
// ---------------------------------------------------------------------------
function TeacherView({ questions, onAdd, onRemove, totalPoints }) {
  const [type, setType] = useState("qcm_unique");
  const [statement, setStatement] = useState("");
  const [points, setPoints] = useState(1);
  const [options, setOptions] = useState([
    { id: "a", text: "" },
    { id: "b", text: "" },
  ]);
  const [correctOptionId, setCorrectOptionId] = useState("a");
  const [correctOptionIds, setCorrectOptionIds] = useState([]);
  const [correctBool, setCorrectBool] = useState(true);
  const [acceptedRaw, setAcceptedRaw] = useState("");
  const [numericValue, setNumericValue] = useState(0);
  const [tolerance, setTolerance] = useState(0);

  function resetForm() {
    setStatement("");
    setPoints(1);
    setOptions([
      { id: "a", text: "" },
      { id: "b", text: "" },
    ]);
    setCorrectOptionId("a");
    setCorrectOptionIds([]);
    setAcceptedRaw("");
    setNumericValue(0);
    setTolerance(0);
  }

  function submit(e) {
    e.preventDefault();
    if (!statement.trim()) return;
    const base = { type, statement, points: Number(points) || 1 };
    if (type === "qcm_unique") {
      onAdd({ ...base, options, correctOptionId });
    } else if (type === "qcm_multiple") {
      onAdd({ ...base, options, correctOptionIds });
    } else if (type === "vrai_faux") {
      onAdd({ ...base, correctBool });
    } else if (type === "reponse_courte") {
      onAdd({ ...base, acceptedAnswers: acceptedRaw.split(",").map((s) => s.trim()).filter(Boolean) });
    } else if (type === "numerique") {
      onAdd({ ...base, numericValue: Number(numericValue), tolerance: Number(tolerance) });
    }
    resetForm();
  }

  function updateOption(id, text) {
    setOptions((prev) => prev.map((o) => (o.id === id ? { ...o, text } : o)));
  }
  function addOption() {
    const nextId = String.fromCharCode(97 + options.length);
    setOptions((prev) => [...prev, { id: nextId, text: "" }]);
  }
  function removeOption(id) {
    setOptions((prev) => prev.filter((o) => o.id !== id));
  }
  function toggleMultiCorrect(id) {
    setCorrectOptionIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  return (
    <div className="grid md:grid-cols-[1fr_1.1fr] gap-10">
      {/* Formulaire */}
      <div>
        <h2 className="font-display text-2xl mb-1">Ajouter une question</h2>
        <p className="font-body text-sm text-[#1C2B4A]/60 mb-6">
          La clé de correction que vous définissez ici sert à noter automatiquement les réponses des étudiants.
        </p>

        <form onSubmit={submit} className="space-y-5">
          <div>
            <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Type de question</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="mt-1 w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-[#B4402A]/40"
            >
              <option value="qcm_unique">QCM — choix unique</option>
              <option value="qcm_multiple">QCM — choix multiple</option>
              <option value="vrai_faux">Vrai / Faux</option>
              <option value="reponse_courte">Réponse courte</option>
              <option value="numerique">Numérique</option>
            </select>
          </div>

          <div>
            <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Énoncé</label>
            <textarea
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              rows={2}
              placeholder="Rédigez la question…"
              className="mt-1 w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-[#B4402A]/40"
            />
          </div>

          {(type === "qcm_unique" || type === "qcm_multiple") && (
            <div className="space-y-2">
              <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">
                Options — cochez la ou les bonnes réponses
              </label>
              {options.map((o) => (
                <div key={o.id} className="flex items-center gap-2">
                  <input
                    type={type === "qcm_unique" ? "radio" : "checkbox"}
                    name="correct-option"
                    checked={type === "qcm_unique" ? correctOptionId === o.id : correctOptionIds.includes(o.id)}
                    onChange={() =>
                      type === "qcm_unique" ? setCorrectOptionId(o.id) : toggleMultiCorrect(o.id)
                    }
                  />
                  <input
                    value={o.text}
                    onChange={(e) => updateOption(o.id, e.target.value)}
                    placeholder={`Option ${o.id.toUpperCase()}`}
                    className="flex-1 font-body border border-[#1C2B4A]/25 rounded-md px-3 py-1.5 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#B4402A]/40"
                  />
                  <button type="button" onClick={() => removeOption(o.id)} className="text-[#1C2B4A]/40 hover:text-[#B4402A]">
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addOption}
                className="font-body text-sm text-[#B4402A] flex items-center gap-1 mt-1"
              >
                <Plus size={14} /> Ajouter une option
              </button>
            </div>
          )}

          {type === "vrai_faux" && (
            <div>
              <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Bonne réponse</label>
              <div className="mt-1 flex gap-2">
                <button
                  type="button"
                  onClick={() => setCorrectBool(true)}
                  className={`font-body text-sm px-4 py-1.5 rounded-md border ${
                    correctBool ? "bg-[#1C2B4A] text-[#F1EEE4] border-[#1C2B4A]" : "border-[#1C2B4A]/25"
                  }`}
                >
                  Vrai
                </button>
                <button
                  type="button"
                  onClick={() => setCorrectBool(false)}
                  className={`font-body text-sm px-4 py-1.5 rounded-md border ${
                    !correctBool ? "bg-[#1C2B4A] text-[#F1EEE4] border-[#1C2B4A]" : "border-[#1C2B4A]/25"
                  }`}
                >
                  Faux
                </button>
              </div>
            </div>
          )}

          {type === "reponse_courte" && (
            <div>
              <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">
                Réponses acceptées (séparées par des virgules)
              </label>
              <input
                value={acceptedRaw}
                onChange={(e) => setAcceptedRaw(e.target.value)}
                placeholder="ex : mitochondrie, la mitochondrie"
                className="mt-1 w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#B4402A]/40"
              />
            </div>
          )}

          {type === "numerique" && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Valeur exacte</label>
                <input
                  type="number"
                  value={numericValue}
                  onChange={(e) => setNumericValue(e.target.value)}
                  className="mt-1 w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white text-sm"
                />
              </div>
              <div>
                <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Tolérance ±</label>
                <input
                  type="number"
                  value={tolerance}
                  onChange={(e) => setTolerance(e.target.value)}
                  className="mt-1 w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white text-sm"
                />
              </div>
            </div>
          )}

          <div>
            <label className="font-body text-xs uppercase tracking-wide text-[#1C2B4A]/60">Points</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={points}
              onChange={(e) => setPoints(e.target.value)}
              className="mt-1 w-28 font-mono border border-[#1C2B4A]/25 rounded-md px-3 py-2 bg-white text-sm"
            />
          </div>

          <button
            type="submit"
            className="font-body text-sm bg-[#B4402A] text-white px-5 py-2.5 rounded-md hover:bg-[#9c3423] transition-colors flex items-center gap-2"
          >
            <Plus size={16} /> Ajouter la question
          </button>
        </form>
      </div>

      {/* Liste des questions */}
      <div>
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="font-display text-2xl">Questionnaire</h2>
          <span className="font-mono text-sm text-[#1C2B4A]/60">{totalPoints} pts au total</span>
        </div>
        <div className="space-y-3">
          {questions.length === 0 && (
            <p className="font-body text-sm text-[#1C2B4A]/50 italic">Aucune question pour l'instant.</p>
          )}
          {questions.map((q, i) => (
            <div key={q.id} className="bg-white border border-[#1C2B4A]/12 rounded-lg p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-[#B4402A]">Q{i + 1}</span>
                    <span className="font-body text-[10px] uppercase tracking-wide text-[#1C2B4A]/45 bg-[#1C2B4A]/5 px-2 py-0.5 rounded">
                      {typeLabel(q.type)}
                    </span>
                  </div>
                  <p className="font-body text-sm">{q.statement}</p>
                  <p className="font-mono text-xs text-[#1C2B4A]/50 mt-1">{q.points} pt(s)</p>
                </div>
                <button onClick={() => onRemove(q.id)} className="text-[#1C2B4A]/30 hover:text-[#B4402A]">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function typeLabel(t) {
  return {
    qcm_unique: "QCM unique",
    qcm_multiple: "QCM multiple",
    vrai_faux: "Vrai/Faux",
    reponse_courte: "Réponse courte",
    numerique: "Numérique",
  }[t];
}

// ---------------------------------------------------------------------------
// Vue Étudiant
// ---------------------------------------------------------------------------
function StudentView({ questions, answers, setAnswers, graded, setGraded, totalPoints, obtainedPoints, onReset }) {
  function setAnswer(id, value) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }
  function toggleMulti(id, optId) {
    setAnswers((prev) => {
      const cur = new Set(prev[id] || []);
      cur.has(optId) ? cur.delete(optId) : cur.add(optId);
      return { ...prev, [id]: Array.from(cur) };
    });
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-baseline justify-between mb-6">
        <h2 className="font-display text-2xl">Quiz</h2>
        {graded ? (
          <button onClick={onReset} className="font-body text-sm text-[#1C2B4A]/60 flex items-center gap-1 hover:text-[#B4402A]">
            <RotateCcw size={14} /> Recommencer
          </button>
        ) : (
          <span className="font-mono text-sm text-[#1C2B4A]/60">{totalPoints} pts au total</span>
        )}
      </div>

      {graded && (
        <div className="flex justify-center mb-8">
          <ScoreCircle score={obtainedPoints} max={totalPoints} />
        </div>
      )}

      <div className="space-y-5">
        {questions.map((q, i) => {
          const ok = graded ? grade(q, answers[q.id]) : null;
          return (
            <div
              key={q.id}
              className="bg-white border border-[#1C2B4A]/12 rounded-lg p-5 shadow-sm flex items-start gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-xs text-[#1C2B4A]/50">Q{i + 1}</span>
                  <span className="font-mono text-xs text-[#1C2B4A]/40">· {q.points} pt(s)</span>
                </div>
                <p className="font-body text-sm mb-3">{q.statement}</p>

                {q.type === "qcm_unique" &&
                  q.options.map((o) => (
                    <label key={o.id} className="flex items-center gap-2 mb-1.5 font-body text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        disabled={graded}
                        checked={answers[q.id] === o.id}
                        onChange={() => setAnswer(q.id, o.id)}
                      />
                      {o.text}
                    </label>
                  ))}

                {q.type === "qcm_multiple" &&
                  q.options.map((o) => (
                    <label key={o.id} className="flex items-center gap-2 mb-1.5 font-body text-sm">
                      <input
                        type="checkbox"
                        disabled={graded}
                        checked={(answers[q.id] || []).includes(o.id)}
                        onChange={() => toggleMulti(q.id, o.id)}
                      />
                      {o.text}
                    </label>
                  ))}

                {q.type === "vrai_faux" && (
                  <div className="flex gap-2">
                    {[true, false].map((v) => (
                      <button
                        key={String(v)}
                        type="button"
                        disabled={graded}
                        onClick={() => setAnswer(q.id, v)}
                        className={`font-body text-sm px-4 py-1.5 rounded-md border ${
                          answers[q.id] === v ? "bg-[#1C2B4A] text-[#F1EEE4] border-[#1C2B4A]" : "border-[#1C2B4A]/25"
                        }`}
                      >
                        {v ? "Vrai" : "Faux"}
                      </button>
                    ))}
                  </div>
                )}

                {q.type === "reponse_courte" && (
                  <input
                    disabled={graded}
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswer(q.id, e.target.value)}
                    placeholder="Votre réponse…"
                    className="w-full font-body border border-[#1C2B4A]/25 rounded-md px-3 py-1.5 text-sm"
                  />
                )}

                {q.type === "numerique" && (
                  <input
                    type="number"
                    disabled={graded}
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswer(q.id, e.target.value)}
                    placeholder="Votre réponse…"
                    className="w-40 font-mono border border-[#1C2B4A]/25 rounded-md px-3 py-1.5 text-sm"
                  />
                )}
              </div>
              {graded && <InkMark ok={ok} delay={i * 150} />}
            </div>
          );
        })}
      </div>

      {!graded && (
        <button
          onClick={() => setGraded(true)}
          className="mt-6 font-body text-sm bg-[#B4402A] text-white px-5 py-2.5 rounded-md hover:bg-[#9c3423] transition-colors flex items-center gap-2"
        >
          <Send size={16} /> Soumettre et corriger
        </button>
      )}
    </div>
  );
}
