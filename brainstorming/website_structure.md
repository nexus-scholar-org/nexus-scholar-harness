# Website Structure: Full Architecture
**Session:** 2026-08-24
**Status:** Brainstormed — Ready for design phase

---

## The Two Audiences Problem

The website serves two completely different people simultaneously:

- **Person A:** A stressed PhD student who just Googled something and stumbled onto the site. No idea what Nexus Scholar is. Must understand value in 8 seconds or they're gone.
- **Person B:** A returning paid student who just wants to get to Lesson 3.2 quickly. Every extra click is friction.

Most course sites optimize entirely for Person A (marketing) and forget Person B (experience). We must serve both from the same URL — via login-state-aware UX.

---

## Full Site Map

```
nexusscholar.io/
│
├── /                          → Homepage (Person A focus)
├── /course                    → Full curriculum overview (28 lessons)
├── /learn/[module]/[lesson]   → The lesson player (Person B focus)
├── /start                     → PhD Stage Selector quiz → personalized path
├── /toolkit                   → The 6 Nexus kits explained + install instructions
├── /capstone                  → Capstone brief, rubric, submission portal
├── /pricing                   → Free vs. Paid comparison + Gumroad widget
├── /institutions              → University licensing (B2B page)
├── /community                 → Discord invite + what's inside the server
├── /about                     → Course philosophy + author bio
├── /blog                      → Research methodology articles (SEO)
└── /changelog                 → What's new (new lessons, kit updates)
```

---

## Page-by-Page Specification

### `/` — Homepage
**One job:** Convert a confused first-time visitor into someone who clicks "Start Free."

**Above-the-fold (before scroll):**
- Tagline: *"The research skills your university forgot to teach you."*
- Subtagline: *"28 free lessons covering everything from reading your first paper to automating your literature review — built around how a PhD actually works."*
- Primary CTA: `Start Free →`
- Secondary CTA: `Take the Quiz →`
- Hero animation: scattered papers → organized citation graph → thesis outline

**Below the fold sections (in order):**
1. Pain points: 4 cards → "Drowning in papers?" / "Can't start writing?" / "Citation nightmare?" / "No idea where to begin?" → each links to relevant lesson
2. PhD Stage Selector teaser → "Not sure where to start? Take the 60-second quiz →"
3. The 6-kit toolkit visual (pipeline diagram)
4. Social proof: testimonials + institution logos (post-launch)
5. Free vs. Paid comparison strip
6. Final CTA: "28 lessons. Free forever. Start now."

**Critical decision:** NO list of 28 lessons on the homepage. That's overwhelming. The homepage answers "should I care?" — not "what will I learn?"

---

### `/start` — The PhD Stage Selector
**The most important page after the homepage.** The moment of personalization.

**Quiz Flow:**
```
Q1: What year / stage of your PhD are you in?
    Year 1 (Just started)  |  Year 2–3 (In the thick of it)
    Year 4+ (Final stages) |  PostDoc / Researcher
    Not in a PhD (self-study)
        ↓
Q2: What is your biggest pain point right now?
    Finding & organizing literature
    Reading and understanding papers
    Analyzing and synthesizing
    Writing (thesis, papers, proposals)
    Getting published / surviving peer review
    Presenting my research
    Just surviving the PhD
        ↓
Q3: How comfortable are you with Python?
    Never used it  |  Basic  |  Intermediate  |  Advanced
        ↓
[Generate My Path]
        ↓
Results: "Your Path: The Stuck Writer"
    → 7 recommended lessons shown as cards
    → CTA: "Start Lesson 1 of your path →"
    → Secondary: "See all 28 lessons instead"
```

**Named Learning Paths:**
| Path Name | Target Student | Core Lessons |
|:---|:---|:---|
| 🧭 The Ground Zero | Year 1, overwhelmed | Modules 0, 1, 2.1, 6.1, 6.3 |
| ✍️ The Stuck Writer | Writing paralysis | Modules 4.1, 4.2, 4.4, 4.5, 3.1 |
| 🔍 The Literature Miner | Drowning in papers | Modules 2.1–2.6, 3.1 |
| 🧪 The Toolkit Builder | Technically-minded | Modules 2.2, 2.3, 2.4, 3.2, 3.3, 4.3 |
| 🎓 The Final Stretch | Year 4+, pre-defence | Modules 4.1, 4.4, 5.1, 5.2, 5.3 |
| 🔬 The SLR Specialist | Doing a review now | Modules 2.1–2.6, 3.1–3.4 |

---

### `/course` — Course Overview
**The full curriculum page.** Both audiences come here.

**Structure:**
- Module accordion: click to expand → shows lessons inside with time estimates
- Each lesson row: title / duration / 🆓 or 💰 badge / "Preview" link
- Sticky sidebar: total hours / progress bar (logged-in users) / "Buy paid access" CTA
- Search bar to find a lesson by keyword
- Logged-in students see progress checkmarks inline

---

### `/learn/[module]/[lesson]` — The Lesson Player
**Where students spend 90% of their time.** Must be frictionless.

**3-Panel Layout:**
```
┌──────────────┬────────────────────────────┬─────────────┐
│   Sidebar    │       Video Player         │  Resources  │
│              │                            │             │
│  Module list │  ┌──────────────────────┐  │ script.md   │
│  with        │  │                      │  │ slides.pdf  │
│  checkmarks  │  │   YouTube embed      │  │ exercise.md │
│              │  │                      │  │ quiz        │
│  ← Prev      │  └──────────────────────┘  │             │
│  Next →      │  Lesson title + duration   │ Discord     │
│              │  Tabs:                     │ link        │
│              │  Overview / Exercise /     │             │
│              │  Quiz / Discussion         │             │
└──────────────┴────────────────────────────┴─────────────┘
```

**The "Discussion" tab:** Links to the lesson-specific Discord channel. Bridge between course and community.

**Paywall behavior:** Free lessons play fully. Paid lessons show a 90-second preview, then a non-aggressive "Unlock this lesson" overlay with the pricing comparison.

---

### `/toolkit` — The 6 Nexus Kits
**For researchers who arrive via GitHub or a paper citation.**

**Structure:**
- Intro: "The Nexus Scholar Suite is 6 open-source Python tools that automate your research pipeline"
- Animated pipeline diagram: Search → Import → Dedup → PDF → Graph → RAG → BibTeX
- 6 kit cards: name / one-sentence description / `pip install` command / link to course lesson / GitHub link

---

### `/institutions` — University Licensing
**A B2B page. Must feel professional, not course-website-ish.**

**Structure:**
- Headline: *"Give your entire PhD program a world-class research curriculum."*
- 3 pricing tiers (Department / Faculty / University)
- "Why it works" section (pedagogical argument)
- "Request a Pilot" form (name, university, role, expected student count)
- Post-launch: pilot university logos + case study quotes

---

### `/blog` — Research Methodology Articles (SEO Engine)
**Articles ranked for searches PhD students actually make:**
- "How to do a systematic literature review"
- "Best reference manager for PhD students 2025"
- "How to read a research paper quickly"
- "What is PRISMA 2020?"
- "Best Python libraries for academic research"
- "How to deal with imposter syndrome in a PhD"

Each article ends with: *"This topic is covered in depth in Module X.X — [read the full lesson →]"*

---

## Navigation: Two States

### Logged-Out (Visitor)
```
Logo | Course | Toolkit | Pricing | Institutions | Blog | [Start Free →]
```

### Logged-In (Student)
```
Logo | My Path | Course | Community | Capstone | [My Account ▾]
```

The login state completely changes the nav. Returning students should never see marketing copy.

---

## Critical User Flows

### Flow 1: First Visit → Enrollment
```
Google search → Homepage → Quiz → Personalized path generated
→ First lesson → Mid-course paywall → Pricing page
→ Gumroad purchase → Discord access granted → Continue learning
```

### Flow 2: Returning Student
```
Direct URL / bookmark → Login → Resume last visited lesson → Continue
```

### Flow 3: University Decision Maker
```
Google "research methods course PhD program" → Blog article
→ Homepage → /institutions → Request pilot form → Email conversation
```

### Flow 4: Toolkit User via GitHub
```
Nexus kit GitHub README → /toolkit page
→ "Learn how to use this kit →" → Course lesson → Enrollment
```

---

## Domain Decision
**Recommended:** `nexusscholar.io` or `nexusscholar.dev`
- `.io` has EdTech/SaaS credibility
- `.dev` signals the technical toolkit audience
- Avoid `.com` if taken — `.io` is strongly preferred in this space

---

## Open Questions Before Design Phase
1. Does the site require user accounts (login/progress tracking), or does Gumroad handle access control?
2. Is the lesson player built custom (Docusaurus + React), or do we use a headless LMS (e.g., LearnDash, Thinkific)?
3. Does the blog need a separate CMS (Ghost, Contentful) or does Docusaurus handle it?
4. Who is the author? Is there a named face/brand on the About page?
