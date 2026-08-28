# Nexus Scholar Course — Product Strategy
**Session Date:** 2026-08-24
**Status:** Decisions Locked ✅

---

## Business Model: Freemium

### 🆓 Free Tier — "The Open Course"
- All **26 Part 1 lessons** publicly accessible on course website
- Video lessons embedded from YouTube (public channel)
- All exercises and quizzes rendered on the website
- Nexus toolkit remains fully open-source on GitHub

**Purpose:** Discoverability, community growth, toolkit adoption

---

### 💰 Paid Tier — "The Professional Track"
**Price point TBD ($49–$149 one-time OR $19/month)**

| Feature | Free | Paid |
|:---|:---:|:---:|
| All 26 Part 1 video lessons | ✅ | ✅ |
| Exercises & quizzes | ✅ | ✅ |
| Part 2: Agentic Curriculum | ❌ | ✅ |
| Part 3: Under the Hood | ❌ | ✅ |
| Verifiable Certificate (Credly/LinkedIn) | ❌ | ✅ |
| Starter Pack Download | ❌ | ✅ |
| Private Discord Community | ❌ | ✅ |
| Companion Jupyter Notebooks | ❌ | ✅ |
| Live Q&A Sessions | ❌ | ✅ |
| Capstone Project Review | ❌ | ✅ |

---

## Platform Stack

```
Free Side                         Paid Side
─────────────────────             ─────────────────────
GitHub Pages (website)      →     Gumroad / LemonSqueezy (payment)
YouTube (video hosting)           Private GitHub repo (notebooks)
GitHub (source / issues)          Discord (community server)
                                  Beehiiv (newsletter / updates)
                                  Credly (verifiable certificates)
```

**Key principle:** No Udemy. No complex LMS. 100% revenue retained.
The website is a Docusaurus site built directly from the existing markdown files.

---

## Capstone Project: "Build Your Own Nexus Workflow"

**Decision:** ✅ Capstone = Student designs and implements a custom Nexus research pipeline

**Concept:** Instead of a graded exam, students demonstrate mastery by solving a real research problem. They document and submit a "Nexus Workflow Portfolio" — a structured report showing how they combined the 6 kits to automate a specific research task.

→ See `capstone_design.md` for full spec.

---

## Certificate: Verifiable Credential

**Decision:** ✅ Credly badge + LinkedIn-shareable credential

→ See `certificate_strategy.md` for full spec.

---

## Starter Pack: All Possible Artifacts

**Decision:** ✅ Maximum value download bundle

→ See `starter_pack_manifest.md` for full spec.

---

## Community: Discord

**Decision:** ✅ Private Discord server for paid students

→ See `community_design.md` for full spec.

---

## Missing Lessons Identified

Two gaps surfaced during brainstorming:
1. **Grant Writing** → Proposed Module 2.6
2. **Collaborative Research with Git** → Proposed Module 4.5

→ See `missing_lessons.md` for full spec.
