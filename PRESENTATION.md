# SkillsHub — Presentation Outline
## 7 Slides · Hackathon Submission

---

## SLIDE 1 — Title & Hook

**Title:** SkillsHub
**Subtitle:** AI-Powered Skills Intelligence · Find the right people, not just the right keywords

**Hook line (speak this):**
> "When HR asks 'who knows React and has built real-time systems?' — they shouldn't have to ping 10 managers. They should just be able to ask. We built the system that understands the question."

**Visual:** Landing page screenshot — clean SaaS design with the tagline

---

## SLIDE 2 — The Problem

**Header:** The skills data problem is worse than you think

**Three columns:**

| Where skills live today | The cost | The ask |
|---|---|---|
| Scattered spreadsheets | Projects staffed by gut feel | "Ping all managers" |
| Outdated profiles | Experts hidden in the team | Manual cross-referencing |
| Someone's head | Wrong person on the wrong project | Days of back-and-forth |

**Key stat:** _Skills data is the most underutilized asset in software companies_

**Visual:** Before/after — messy spreadsheet vs. SkillsHub search results

---

## SLIDE 3 — Our Solution & Architecture

**Header:** Two hard problems, solved with AI

**Left side — Hard Problem #1: Smart Ingestion**
```
PDF Resume → pypdf extract
         → Groq llama-3.3-70b-versatile (tool_use)
         → StructuredProfile JSON
              • Skills + proficiency + evidence
              • Projects + technologies
              • Certifications
         → Skill Inference Engine
              • 40+ deterministic rules (Next.js → React)
              • Groq llama-3.1-8b-instant contextual inferences
         → Review Queue → HR Approval
```

**Right side — Hard Problem #2: Semantic Search**
```
NL Query → Groq llama-3.3-70b-versatile (parse + filter)
         → Voyage AI embedding (query vector)
         → pgvector HNSW retrieval (top 20)
         → Full profile load
         → Groq llama-3.3-70b-versatile re-rank
              • Match score 0-100
              • Plain-English reasoning
              • Strengths + gaps per candidate
         → Ranked results with explanations
```

**Visual:** Architecture diagram (text above serves as the diagram)

---

## SLIDE 4 — Live Demo: Resume Ingestion

**Header:** Upload a resume → get a structured profile in 20 seconds

**What to show:**
1. Employee uploads a PDF resume
2. AI extraction loading screen ("Claude AI is extracting skills…")
3. Review queue shows the extracted profile
4. Skills with ✨ inferred badge (e.g., Next.js → React inferred at 97%)
5. HR approves → profile is live

**Callouts on slide:**
- "Evidence per skill — AI quotes the resume to justify every extraction"
- "Confidence scores — uncertain extractions flagged for HR review"
- "Skill inference — 40+ rules + LLM to surface implicit knowledge"

**Visual:** Screenshot of review detail page showing skills with inferred badges

---

## SLIDE 5 — Live Demo: Semantic Search

**Header:** Ask in plain English. Get ranked candidates with AI reasoning.

**Show these queries:**
1. _"Who can lead a React project that also needs WebSocket experience?"_
   → Priya Sharma, 94% — "Expert in React (6y), built real-time trading dashboard with WebSocket feeds"

2. _"Find a backend dev in Pune with at least 3 years of Java and payment gateway integration"_
   → Rahul Mehta, 91% — "5y Java expert, implemented Razorpay + Stripe on 3 production services, based in Pune"

**Callouts:**
- "AI Query Understanding panel — shows parsed filters, required skills, location detected"
- "Score ring — 0–100 match score with principled deductions"
- "Strengths & gaps — expand each card for details"
- "Retrieved 20 candidates via vector search → re-ranked by LLM reasoning"

**Visual:** Search results screenshot with ResultCard + ScoreRing

---

## SLIDE 6 — Tech Decisions & Stretch Goals

**Header:** Built for speed, quality, and demo reliability

**Stack table:**

| Layer | Choice | Why |
|---|---|---|
| LLM | Groq llama-3.3-70b-versatile + llama-3.1-8b-instant | Tool use = structured output, no JSON parsing hacks |
| Embeddings | Voyage AI voyage-3-large | Best retrieval quality for technical text |
| Vector DB | PostgreSQL + pgvector HNSW | No extra infra, ACID guarantees, hybrid SQL+vector |
| Backend | FastAPI + SQLAlchemy async | Async throughout, type-safe, fast iteration |
| Frontend | Next.js 15 App Router | Server/client split, clean routing, fast dev |
| Infra | Docker Compose | One command to run the full stack |

**Stretch Goals Completed:**
- ✅ Skill Inference Engine — 40+ deterministic rules + Claude Haiku contextual inferences
- ✅ Skill Gap Analysis — dashboard shows talent pool coverage by skill

---

## SLIDE 7 — What's Next

**Header:** Production roadmap

**Near-term (1–2 months):**
- Conversational search refinement ("only show those available next month")
- Team builder — HR describes a project, AI proposes a team with rationale
- GitHub integration — infer active skills from recent commits

**Medium-term (3–6 months):**
- Bulk CSV/folder resume import
- Skills taxonomy editor for HR
- Project-based skill gap analysis

**Vision:**
> SkillsHub becomes the living, AI-maintained skills graph of your engineering org — accurate, always up-to-date, and queryable in plain English.

**Demo credentials on slide:**
```
HR:       hr@demo.com     / demo1234
Employee: emp@demo.com    / demo1234
Repo:     github.com/[your-handle]/skillshub
```

---

## SPEAKING NOTES

**Total time:** ~8 minutes (presentation) + 2–3 min demo = 10–11 min

**Pace:**
- Slides 1–2: 90 seconds (problem statement, be punchy)
- Slide 3: 2 minutes (architecture — walk through both pipelines)
- Slides 4–5: 3 minutes (demo — this is where you win)
- Slide 6: 1 minute (stack + stretch goals)
- Slide 7: 30 seconds (roadmap, invite questions)

**Key phrases to hit:**
- "Not keyword matching — semantic understanding"
- "Evidence-backed extraction — Claude quotes the resume for every skill"
- "The WHY is more impressive than the WHO"
- "One docker compose up and you're running"
