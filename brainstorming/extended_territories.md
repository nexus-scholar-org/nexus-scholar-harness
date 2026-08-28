# Brainstorming Session 2: Extended Territories
**Date:** 2026-08-24
**Status:** Ideas captured — Pending prioritization

---

## Territory 1: Student Onboarding — The PhD Stage Selector

### The Problem
"Start at Module 0" is one-size-fits-all. A Year 4 PhD student doesn't need Module 1.1 — they need Module 4.1 and the toolkit immediately.

### The Solution: 3-Question Onboarding Quiz
Landing page → quiz → personalized learning path:

**Question 1:** What year of your PhD are you in?
- Year 1 (Just started)
- Year 2–3 (In the thick of it)
- Year 4+ (Final stages)
- PostDoc / Researcher
- Not in a PhD (Self-study)

**Question 2:** What is your biggest pain point right now?
- Finding & organizing literature
- Actually reading and understanding papers
- Analyzing and synthesizing what I've read
- Writing (thesis, papers, proposals)
- Getting published / surviving peer review
- Presenting my research
- Just surviving the PhD

**Question 3:** How comfortable are you with Python?
- Never used it
- Basic (I've run scripts someone else wrote)
- Intermediate (I can write my own scripts)
- Advanced

**Output:** A named learning path with a shortlist of 6–10 recommended lessons. Examples:
- 🛤️ **"The Overwhelmed Year 1"** → Modules 0, 1, 2.1, 2.2, 6.1, 6.3
- 🛤️ **"The Stuck Writer"** → Modules 4.1, 4.2, 4.4, 4.5, 3.1
- 🛤️ **"The SLR Builder"** → Modules 2.1–2.6, 3.1–3.4
- 🛤️ **"The Toolkit Power User"** → Modules 2.2, 2.3, 2.4, 3.2, 3.3, 4.3

### UX Impact
The course's first message to the student is: *"We see you specifically."* This is the first wow moment.

---

## Territory 2: Internationalization

### The Problem
55%+ of global PhD students are non-native English speakers. The barrier is confidence, not content.

### Three-Layer Approach

**Layer 1 (Free, immediate):**
- Auto-generated YouTube subtitles + manually corrected English captions
- Published `.srt` files on GitHub for each video so anyone can translate

**Layer 2 (Community-powered):**
- Discord channel `#translations` for paid students to volunteer subtitles
- Top translators credited in the course and given a special Discord role (`@Language Ambassador`)

**Layer 3 (Design standard):**
- A "Plain Language" style guide for all scripts
  - No idioms or colloquialisms
  - Maximum 20 words per sentence
  - One idea per sentence
  - International examples in all exercises (not just US/UK-centric scenarios)
- Makes machine translation dramatically more accurate

### Quick Win
Add a language selector to the course website that shows available subtitle languages per video.

---

## Territory 3: The Course as a Research Paper

### Concept
Publish a peer-reviewed journal article describing the pedagogical design of this course. Creates academic credibility that no marketing budget can buy.

### Proposed Title
*"Nexus Scholar: A Competency-Based Open Curriculum for Research Automation in the 21st Century"*

### Target Journals
| Journal | Publisher | OA? |
|:---|:---|:---:|
| Journal of Information Science | Sage | No (consider APC) |
| Education for Information | IOS Press | Optional |
| Information Processing & Management | Elsevier | No |
| PLOS ONE | PLOS | Yes ✅ |
| Journal of Academic Librarianship | Elsevier | No |

**Recommendation:** PLOS ONE for maximum open-access reach, or Journal of Information Science for domain credibility.

### Paper Structure
1. **Introduction:** The research automation literacy gap in modern PhD programs
2. **Related Work:** Existing research methods curricula and their limitations
3. **Curriculum Design:** The PhD lifecycle framework, competency mapping, 7-scene arc, Bloom's taxonomy alignment
4. **The Nexus Scholar Suite:** Overview of the 6 open-source tools as pedagogical anchors
5. **Open Freemium Model:** Rationale for the free/paid split as an access equity decision
6. **Preliminary Evaluation:** Student completion data, capstone quality metrics (post-launch)
7. **Conclusion & Future Work**

### Strategic Impact
- Every university library that subscribes gets it pushed to faculty inboxes
- University acquisition committees see it → institutional licensing conversations start
- Makes the course *citable* in other papers
- Separates this from a random Udemy course permanently

### Timeline
- Write after first cohort completes the course (need evaluation data for Section 6)
- Target submission: ~6 months post-launch

---

## Territory 4: University Partnerships

### The Model
Sell institutional licenses to universities at a flat annual rate — bypassing the one-student-at-a-time sales motion entirely.

### Pricing Tiers
| Tier | Students | Price/year | Includes |
|:---|:---:|:---:|:---|
| Department | ≤50 students | $2,000/yr | All paid content + Discord |
| Faculty | ≤200 students | $6,000/yr | + 2 live Q&A sessions/yr |
| University | Unlimited | $15,000/yr | + Custom onboarding workshop |

### The Pitch to a PhD Director
> *"Your students spend 3 months figuring out basic research workflows that this course covers in a weekend. For less than the cost of one conference registration, every student in your program has a world-class research automation curriculum."*

### The Sales Motion
1. **Publish the journal paper** (Territory 3) → academic credibility layer
2. **Offer a free institutional pilot** to 3 target universities (all content unlocked for one semester, ask for testimonials and completion data)
3. **Collect results** → build a one-page institutional case study
4. **Pitch the next 10 universities** using the case study + paper

### Target Institutions (First Wave)
- Research-intensive universities with large PhD programs
- Universities in countries with high PhD enrollment (US, UK, Germany, China, India, Brazil)
- Universities with existing open-science / research methodology centers

---

## Territory 5: The Course Website

### Tagline Candidates
1. *"Stop drowning in papers. Start doing science."*
2. *"The research skills your university forgot to teach you."*
3. *"From 500 unread papers to a publishable systematic review — in one weekend."*
4. *"The PhD survival kit. No PhD required to start."*

**Recommendation:** Option 2 — it names the pain directly without being overwhelming.

### Homepage Structure
| Section | Content |
|:---|:---|
| **Hero** | Tagline + "Start Free" CTA + 60-second trailer video |
| **Pain Points** | 4 cards with direct lesson links: Citations / Finding papers / Blank page / PDFs |
| **The PhD Stage Selector** | Embedded 3-question quiz → personalized path |
| **The Toolkit** | Visual of 6 Nexus kits as interconnected nodes |
| **Social Proof** | Student testimonials + institution logos (post-launch) |
| **Free vs. Paid** | Comparison table |
| **About** | Short bio + course philosophy |
| **Footer** | Discord, GitHub, YouTube, Newsletter |

### Tech Stack
- **Framework:** Docusaurus (markdown-native, already compatible with our content files)
- **Homepage:** Custom React component for Hero + Quiz sections
- **Video:** Embedded YouTube (unlisted for paid, public for free)
- **Payment:** Gumroad embed widget
- **Analytics:** Plausible (privacy-respecting, no cookie banners)

### Visual Identity Direction
- Dark mode default (researchers work at night)
- Deep navy + electric teal accent (trust + innovation)
- Typography: Inter (clean, academic, readable)
- No stock photos — use abstract data visualization graphics
- Animated hero: papers → organized knowledge graph

---

## Priority Order (Recommended)

| Priority | Territory | Reason |
|:---:|:---|:---|
| 1 | Territory 5: Website | Students need a home before anything else |
| 2 | Territory 1: Onboarding Quiz | Built into the website |
| 3 | Territory 4: University Partnerships | Can start outreach pre-launch |
| 4 | Territory 3: Research Paper | Needs post-launch data |
| 5 | Territory 2: Internationalization | Ongoing, community-driven |
