# Website Technology Architecture
**Session:** 2026-08-24 | **Status:** Decided ✅ — Paused, ready to execute

---

## What Already Exists

The `nexus-portal` repo is the **Tailwind Plus "Syntax" template** — already customized and live at `nexus.mouadh.org`.

### Current State of the Portal
| Asset | Status |
|:---|:---:|
| Next.js + Tailwind Plus Syntax template | ✅ Live |
| Deployed at `nexus.mouadh.org` | ✅ Live |
| Sidebar navigation with 6 Nexus kits | ✅ Done |
| `toolkits/` directory with all 6 kit folders | ✅ Done |
| FlexSearch (full-text search, `⌘K`) | ✅ Built-in |
| Markdoc support (Markdown → rich pages) | ✅ Built-in |
| Dark/light mode toggle | ✅ Built-in |
| Mobile responsive | ✅ Built-in |

### What's Missing
- Homepage is still the placeholder "CacheAdvance" copy
- 28 course lessons not yet wired into the sidebar navigation
- No `/pricing`, `/start`, or `/institutions` pages
- No authentication (login/register)

---

## Available Premium Templates (in `tailwindui-templates/`)

| Template | Type | Key Sections | Best Used For |
|:---|:---|:---|:---|
| `syntax.zip` | Docs site | Sidebar nav, Markdoc, FlexSearch | **Lesson player** ← current portal |
| `radiant.zip` | SaaS marketing | Bento hero, blog (Sanity CMS), `/pricing`, testimonials, logo cloud, company page, **`/login`** | **Marketing homepage** |
| `salient.zip` | Product landing | Hero, PrimaryFeatures, SecondaryFeatures, Pricing, Testimonials, FAQs, **`/login` + `/register`** | **Course landing page / Auth** |
| `primer.zip` | Personal/author | Minimal single page | **`/about` author page** |
| `spotlight.zip` | Personal portfolio | Not yet inspected | TBD |
| `studio.zip` | Agency/creative | Not yet inspected | TBD |
| `compass.zip` | Unknown | Not yet inspected | TBD |
| `commit.zip` (extracted) | Unknown | Not yet inspected | TBD |
| `protocol.zip` (extracted) | Unknown | Not yet inspected | TBD |

---

## The 3-Template Architecture Decision

```
nexus.mouadh.org/              ← RADIANT  (front door)
                                  Premium marketing homepage
                                  Bento-grid hero, Features, Pricing,
                                  Testimonials, Blog (Sanity CMS), Logo wall

nexus.mouadh.org/docs/...      ← SYNTAX   (already live)
                                  Lesson player for all 28 lessons
                                  6 Nexus kit documentation
                                  Global search (FlexSearch)

nexus.mouadh.org/about         ← PRIMER   (author profile)
                                  Course philosophy + author bio
```

Auth routes (`/login`, `/register`) borrowed from **Salient's** `(auth)/` route group.

---

## Build Execution Plan (Prioritized)

| # | Task | Source Template | Estimated Effort | Status |
|:---:|:---|:---|:---:|:---:|
| 1 | **Wire 28 lessons into `navigation.ts` sidebar** | Syntax | 20 min | ⬜ Ready |
| 2 | **Replace homepage hero** with Nexus Scholar copy + Radiant hero component | Radiant → Syntax | 1–2 hr | ⬜ Ready |
| 3 | **Add `/pricing` page** from Radiant | Radiant | 1 hr | ⬜ Ready |
| 4 | **Add `/login` + `/register`** from Salient auth routes | Salient | 2 hr | ⬜ Ready |
| 5 | **Add `/start` quiz page** (PhD Stage Selector — custom component) | New | 3–4 hr | ⬜ Ready |
| 6 | **Connect Sanity CMS** for the blog | Radiant | 1–2 hr | ⬜ Ready |
| 7 | **Add `/institutions` page** (university licensing B2B) | Radiant components | 1–2 hr | ⬜ Ready |
| 8 | **Integrate Gumroad** for paid tier unlock | New | 1 hr | ⬜ Ready |

**Total estimated effort:** ~12–15 hours of focused work.

---

## Key File Locations

| File | Purpose |
|:---|:---|
| [`nexus-portal/src/lib/navigation.ts`](file:///c:/Users/mouadh/Documents/Harness0.0.1/nexus-portal/src/lib/navigation.ts) | **Sidebar nav config** — wire 28 lessons here first |
| [`nexus-portal/src/components/Hero.tsx`](file:///c:/Users/mouadh/Documents/Harness0.0.1/nexus-portal/src/components/Hero.tsx) | Homepage hero — replace copy here |
| [`nexus-portal/src/app/(docs)/page.md`](file:///c:/Users/mouadh/Documents/Harness0.0.1/nexus-portal/src/app/(docs)/page.md) | Homepage content (Markdoc) |
| [`nexus-portal/src/app/(docs)/docs/`](file:///c:/Users/mouadh/Documents/Harness0.0.1/nexus-portal/src/app/(docs)/docs/) | Lesson content pages go here |
| [`nexus-portal/toolkits/`](file:///c:/Users/mouadh/Documents/Harness0.0.1/nexus-portal/toolkits/) | 6 kit folders already scaffolded |
| `tailwindui-templates/extracted/radiant/` | Radiant template — harvest components from here |
| `tailwindui-templates/extracted/salient/` | Salient template — harvest auth routes from here |
| `tailwindui-templates/extracted/primer/` | Primer template — harvest author page from here |

---

## Next Session Starting Point
**First task when resuming:** Wire the 28 lessons into `navigation.ts`.

The navigation config is a simple TypeScript array at:
`c:\Users\mouadh\Documents\Harness0.0.1\nexus-portal\src\lib\navigation.ts`

It currently has 1 section ("Introduction") and 6 toolkit links.
It needs 7 module sections (Module 0 → Module 6) with all 28 lessons as links.
This single file change makes the site look like a real course immediately.
