# Community Design: Discord Server
**Decision:** Private Discord for paid students
**Status:** Designed ✅ | **Tier:** Paid

---

## Server Name
**Nexus Scholar Community**

---

## Channel Architecture

### 📣 Public (Visible to anyone, read-only for non-members)
| Channel | Purpose |
|:---|:---|
| `#welcome` | Server intro, rules, how to get the Paid Student role |
| `#announcements` | Course updates, new content, live session announcements |
| `#showcase` | Students share their completed capstone workflows publicly |

### 🎓 Paid Students Only (Requires "Nexus Practitioner" role)
| Channel | Purpose |
|:---|:---|
| `#general` | Open discussion |
| `#introduce-yourself` | Name, field, PhD year, what you're working on |
| `#course-questions` | Questions about specific lessons (use `/lesson 3.2` format) |
| `#capstone-help` | Peer support and feedback on capstone projects |
| `#starter-pack-support` | Help with Obsidian, Zotero, LaTeX setup |

### 🛠️ Tool-Specific Channels
| Channel | Purpose |
|:---|:---|
| `#search-kit` | scholar-search-kit usage, queries, API issues |
| `#pdf-kit` | scholar-pdf-kit usage |
| `#graph-kit` | scholar-graph-kit — share your citation network visualizations |
| `#rag-kit` | scholar-rag-kit — LLM + research discussions |
| `#bib-kit` | scholar-bib-kit — BibTeX issues |
| `#monitor-kit` | scholar-monitor-kit — alert setups |

### 💬 Academic Life Channels
| Channel | Purpose |
|:---|:---|
| `#writing-accountability` | Daily/weekly writing check-ins (Module 4.1 support) |
| `#paper-wins` | Share accepted papers, conference acceptances |
| `#vent-imposter-syndrome` | Safe space for the hard days (Module 6.3) |
| `#phd-jobs` | Job listings, postdoc opportunities, industry transitions |
| `#field-specific-lounge` | Sub-channels by research domain (STEM, Social Science, etc.) |

### 🔴 Live Events
| Channel | Purpose |
|:---|:---|
| `#live-sessions` | Announcements for monthly live Q&A |
| `#voice-coworking` | Always-open voice channel for silent co-working |
| `#office-hours` | Scheduled 1-hour open sessions with course author |

---

## Role Architecture

| Role | Color | How to Get | Permissions |
|:---|:---|:---|:---|
| `@Nexus Practitioner` | Gold | Gumroad purchase verified | All paid channels |
| `@Capstone Graduate` | Purple | Capstone passed | Special badge + Showcase pinning |
| `@Beta Tester` | Blue | Early access participants | Testing channels |
| `@Moderator` | Red | Appointed | Moderation tools |

---

## Onboarding Flow
1. Student completes Gumroad purchase
2. Receives welcome email with Discord invite link (invite is personalized/single-use)
3. Student joins server, lands in `#welcome`
4. Bot DMs: "React to this message with ✅ to verify your purchase and receive the Nexus Practitioner role"
5. Role granted → access to all paid channels unlocked
6. Prompted to post in `#introduce-yourself`

---

## Bot Recommendations
- **Carl-bot:** Role assignment, reaction roles, moderation
- **MEE6:** Welcome messages, leveling
- **Otter (custom or Zapier):** Gumroad webhook → Discord role grant automation

---

## Monthly Cadence
| Week | Event |
|:---|:---|
| Week 1 | Live Q&A (open questions, any topic) |
| Week 2 | "Workflow Wednesday" — a student shares their Nexus pipeline |
| Week 3 | Office Hours (focused on capstone help) |
| Week 4 | Paper Club — community reads and discusses one new paper together |
