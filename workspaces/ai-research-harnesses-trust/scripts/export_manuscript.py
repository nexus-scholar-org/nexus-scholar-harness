"""Render manuscript_draft.md to a self-contained Word (.docx) and HTML preview.

Real Word artifacts: markdown tables become table objects; figure images are
embedded; headings and emphasis are mapped. HTML preview embeds images by
relative path so it also renders in a plain browser.

Run:  uv run python scripts/export_manuscript.py
Outputs:
  reports/manuscript_draft_v3.docx
  reports/manuscript_draft_v3.html
"""

import re
from pathlib import Path

WS = Path(__file__).resolve().parents[3] / "workspaces" / "ai-research-harnesses-trust"
SRC = WS / "reports" / "manuscript_draft.md"
DOCX_OUT = WS / "reports" / "manuscript_draft_v3.docx"
HTML_OUT = WS / "reports" / "manuscript_draft_v3.html"

H1 = re.compile(r"^#\s+(.+)$")
H2 = re.compile(r"^##\s+(.+)$")
H3 = re.compile(r"^###\s+(.+)$")
H4 = re.compile(r"^####\s+(.+)$")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITAL = re.compile(r"\*([^*\n]+)\*")
HEAD = re.compile(r"^\|---+|^\| :--|^\| :---|^:--")
HTML_ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def esc(s: str) -> str:
    out = "".join(HTML_ESC.get(c, c) for c in s)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", out)
    return out


def parse_block(text: str):
    """Return list of ('para'|'table'|'figure'|'ref'|'list', payload)."""
    lines = text.splitlines()
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("![") and "](" in line:
            m = re.match(r"!\[.*?\]\((\S+)\)", line)
            blocks.append(("figure", m.group(1) if m else ""))
            i += 1
            continue
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|:-]+\|?$", lines[i + 1]):
            caption = ""
            if i >= 1 and lines[i - 1].startswith("**Table"):
                caption = lines[i - 1].strip()
            rows = []
            while i < n and line.startswith("|"):
                cells = line.strip().strip("|").split("|")
                if any(re.search(r"[A-Za-z0-9]", c) for c in cells):
                    rows.append([c.strip() for c in cells])
                i += 1
                if i < n:
                    line = lines[i]
            blocks.append(("table", (caption, rows)))
            continue
        if line.startswith("- ") or re.match(r"^\d+\.\s", line):
            items = []
            while i < n and (line.startswith("- ") or re.match(r"^\d+\.\s", line)):
                items.append(line.strip())
                i += 1
                if i < n:
                    line = lines[i]
            blocks.append(("list", items))
            continue
        if line.startswith("*Figure ") and line.endswith("*"):
            blocks.append(("figcaption", line[1:-1].strip()))
            i += 1
            continue
        blocks.append(("para", line))
        i += 1
    return blocks


def build_docx(blocks):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt

    doc = Document()

    def add_rich(par, s):
        pos = 0
        for m in re.finditer(r"\*\*(.+?)\*\*|`([^`]+)`", s):
            if m.start() > pos:
                par.add_run(s[pos : m.start()])
            if m.group(1) is not None:
                r = par.add_run(m.group(1))
                r.bold = True
            else:
                r = par.add_run(m.group(2))
                r.font.name = "Consolas"
            pos = m.end()
        if pos < len(s):
            par.add_run(s[pos:])

    for kind, payload in blocks:
        if kind == "para":
            line = payload
            if line.startswith("#"):
                continue
            par = doc.add_paragraph()
            add_rich(par, line)
        elif kind == "list":
            for item in payload:
                item = re.sub(r"^\d+\.\s", "", item)
                item = item.removeprefix("- ")
                par = doc.add_paragraph(style="List Bullet")
                add_rich(par, item)
        elif kind == "table":
            caption, rows = payload
            if caption:
                cp = doc.add_paragraph()
                r = cp.add_run(caption)
                r.bold = True
            header = rows[0]
            body = rows[1:]
            t = doc.add_table(rows=len(body) + 1, cols=len(header))
            t.style = "Light Grid Accent 1"
            for j, h in enumerate(header):
                cell = t.cell(0, j)
                cell.text = h.strip()
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.bold = True
            for ri, row in enumerate(body):
                for j, v in enumerate(row):
                    if j < len(header):
                        t.cell(ri + 1, j).text = v.strip()
            doc.add_paragraph()
        elif kind == "figure":
            src = (SRC.parent / payload).resolve()
            if src.exists():
                doc.add_picture(str(src), width=Inches(6.2))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                doc.add_paragraph(f"[figure file missing: {payload}]")
        elif kind == "figcaption":
            par = doc.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = par.add_run(payload)
            r.italic = True
            r.font.size = Pt(9)
    doc.save(DOCX_OUT)
    return f"DOCX: {DOCX_OUT}"


def build_html(blocks):
    out = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'><title>Manuscript v3 (preview)</title>",
        "<style>",
        "body{font-family:Georgia,serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#222}",
        "h1{font-size:1.35rem}h2{font-size:1.15rem;border-bottom:1px solid #ccc;padding-bottom:.2rem}h3{font-size:1.02rem}",
        "table{border-collapse:collapse;margin:1rem 0;font-size:.86rem;width:100%}",
        "th,td{border:1px solid #999;padding:.35rem .5rem;text-align:left;vertical-align:top}",
        "th{background:#eef}img{max-width:100%;display:block;margin:1rem auto;border:1px solid #ddd}",
        "em.fig{display:block;text-align:center;font-size:.82rem;color:#444;margin:-.4rem 0 1.4rem}",
        "code{background:#f4f4f4;padding:0 .2em}",
        ".refs{margin-top:2rem}",
        "</style></head><body>",
    ]
    for kind, payload in blocks:
        if kind == "para":
            line = payload
            if line.startswith("#"):
                continue
            if payload == "---":
                out.append("<hr>")
                continue
            if payload.startswith("**") and "**" in payload[2:]:
                out.append(f"<p><strong>{esc(payload[2:-2])}</strong></p>")
            else:
                out.append(f"<p>{esc(line)}</p>")
        elif kind == "list":
            out.append("<ul>")
            for item in payload:
                txt = re.sub(r"^\d+\.\s", "", item)
                txt = txt.removeprefix("- ")
                out.append(f"<li>{esc(txt)}</li>")
            out.append("</ul>")
        elif kind == "table":
            caption, rows = payload
            if caption:
                out.append(f"<p><strong>{esc(caption)}</strong></p>")
            out.append("<table>")
            header = [esc(c.strip()) for c in rows[0]]
            out.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead><tbody>")
            for row in rows[1:]:
                out.append("<tr>" + "".join(f"<td>{esc(c.strip())}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
        elif kind == "figure":
            out.append(f'<img src="{payload}" alt="figure">')
        elif kind == "figcaption":
            out.append(f"<em class='fig'>{esc(payload)}</em>")
    out.append("</body></html>")
    HTML_OUT.write_text("\n".join(out), encoding="utf-8")
    return f"HTML: {HTML_OUT}"


if __name__ == "__main__":
    text = SRC.read_text(encoding="utf-8")
    blocks = parse_block(text)
    kinds = {}
    for k, _ in blocks:
        kinds[k] = kinds.get(k, 0) + 1
    print("parsed blocks:", kinds)
    print(build_docx(blocks))
    print(build_html(blocks))