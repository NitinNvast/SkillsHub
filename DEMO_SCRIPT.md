# SkillsHub — Demo Script
## 2–3 Minute End-to-End Walkthrough

---

## SETUP (do before judges arrive)

```bash
# 1. Ensure containers are running
docker compose up -d

# 2. Verify seeding is complete
docker compose exec backend uv run python -m app.seed.seed_employees

# 3. Open two browser tabs
#    Tab 1: http://localhost:3000  (start at landing page)
#    Tab 2: http://localhost:8000/docs  (backup — API explorer)
```

**Pre-warm the demo:**
- Log in as HR once, run the 4 search queries to warm the Voyage AI cache
- Log in as Employee once, check the profile page is showing
- Have the employee resume PDF ready to upload

---

## SCENE 1 — Landing Page (10 seconds)

*Open Tab 1 at `http://localhost:3000`*

> "This is SkillsHub — an AI-powered skills intelligence platform. Two things make it different: it ingests resumes intelligently using Claude, and it answers HR questions in natural language with real reasoning. Let me show you."

*Click **Sign in***

---

## SCENE 2 — Employee Upload (45 seconds)

*Login as `emp@demo.com` / `demo1234`*

> "An employee logs in and uploads their resume. It's just a PDF drag-and-drop."

*Drop a PDF or click upload → watch the loading state*

> "Claude Sonnet is running. It extracts skills, proficiency levels, years of experience, and project histories — and then runs a second inference pass to surface skills the resume implies but doesn't mention."

*Wait for success screen*

> "Done in about 20 seconds. The profile is now in the HR review queue."

---

## SCENE 3 — HR Review Queue (30 seconds)

*Switch to `hr@demo.com` / `demo1234` → Review Queue*

> "HR sees the extracted profile. Notice the ✨ inferred skills — for example, this candidate has Next.js experience, so the system inferred React at 97% confidence. It quotes the resume to justify every skill. HR can edit, correct, or approve."

*Click Approve & Publish*

> "Approved. The profile is now embedded and searchable."

---

## SCENE 4 — Semantic Search — the money shot (60 seconds)

*Navigate to Search*

> "Now the interesting part. HR types a real question — not a list of keywords."

*Click the first demo chip:*
**"Who can lead a React project that also needs WebSocket experience?"**

*Wait for results (~3–5 seconds)*

> "Look at this. We retrieved 20 candidates using vector similarity, then Claude re-ranked them with a match score and a plain-English reason for each one."

*Point to top result:*

> "Priya Sharma — 94%. 'Expert in React, 6 years. Led a real-time trading dashboard with WebSocket feeds serving 50,000 daily users. Currently unallocated.' That's not a keyword match. That's reasoning."

*Click 'Show strengths & gaps' on the card*

> "Expand the card — specific strengths cited, and honest gaps. That's what HR actually needs."

*Run second query:*
**"Find a backend dev in Pune with at least 3 years of Java and payment gateway integration"**

> "Location detected, minimum years extracted as a filter, then semantic re-rank on top. Rahul Mehta — Pune, 5 years Java, implemented Razorpay and Stripe on production services."

---

## SCENE 5 — Dashboard Skill Gap (15 seconds)

*Navigate to Dashboard*

> "And here on the dashboard — the skill gap panel. We can see which skills the team is light on. This is the stretch goal: a live talent pool coverage map, no manual audit required."

---

## SCENE 6 — Wrap (10 seconds)

> "One docker compose up, it's fully running. Anthropic API, Voyage AI, pgvector — the full AI stack. The code is clean, documented, and ready. That's SkillsHub."

---

## BACKUP PLAN (if live demo breaks)

1. **API broken:** Open `http://localhost:8000/docs` → demonstrate the search endpoint directly via Swagger UI
2. **Search returns no results:** The seed data didn't load — run `docker compose exec backend uv run python -m app.seed.seed_employees` in terminal
3. **Slow response:** Pre-warn the judges: "Calling Voyage AI + Claude, give it 5 seconds"
4. **Full outage:** Use screenshots in `PRESENTATION.md` — describe what would have happened

---

## KEY PHRASES TO MEMORIZE

- "Not keyword matching — semantic understanding of the question"
- "Evidence-backed — Claude quotes the resume for every skill extracted"
- "The WHY is more impressive than the WHO — that reasoning string is what HR cares about"
- "Skill inference — Next.js means React, Spring Boot means Java. We make that explicit."
- "One command to run the whole stack"
