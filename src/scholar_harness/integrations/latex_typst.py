"""LaTeX and Typst academic typesetting exporter."""

from __future__ import annotations

import re
from pathlib import Path


class AcademicTypesettingExporter:
    """Converts grounded markdown synthesis and bibliographies into LaTeX and Typst."""

    _LATEX_ESCAPES = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }

    _LIST_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
    _TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
    _TABLE_SEP_CELL_RE = re.compile(r"^:?-{3,}:?$")

    @classmethod
    def _escape_latex(cls, text: str) -> str:
        """Escape LaTeX specials in prose so %, _, &, # do not break compilation."""
        return "".join(cls._LATEX_ESCAPES.get(ch, ch) for ch in text)

    @staticmethod
    def _split_table_row(line: str) -> list[str]:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in stripped.split("|")]

    @classmethod
    def _convert_tables(cls, text: str) -> str:
        """Convert GitHub-flavoured Markdown pipe tables into LaTeX tabulars.

        Runs after escaping, so cell text is already LaTeX-safe; the ``|``
        separators are not LaTeX specials and survive unchanged.
        """
        lines = text.split("\n")
        output: list[str] = []
        i = 0
        total = len(lines)
        while i < total:
            line = lines[i]
            is_row = bool(cls._TABLE_ROW_RE.match(line))
            is_sep = (
                is_row
                and i + 1 < total
                and bool(cls._TABLE_ROW_RE.match(lines[i + 1]))
                and [
                    cell
                    for cell in cls._split_table_row(lines[i + 1])
                    if cell
                ]
                and all(
                    cls._TABLE_SEP_CELL_RE.match(cell)
                    for cell in cls._split_table_row(lines[i + 1])
                    if cell
                )
            )
            if not is_sep:
                output.append(line)
                i += 1
                continue

            header = cls._split_table_row(line)
            separator = cls._split_table_row(lines[i + 1])
            rows: list[list[str]] = []
            j = i + 2
            while j < total and cls._TABLE_ROW_RE.match(lines[j]):
                rows.append(cls._split_table_row(lines[j]))
                j += 1

            ncols = max([len(header), *(len(row) for row in rows)] or [1])
            alignment = (separator + ["---"] * ncols)[:ncols]
            spec = "".join(
                "c" if cell.startswith(":") and cell.endswith(":")
                else "r" if cell.endswith(":")
                else "l"
                for cell in alignment
            )

            def pad(row: list[str]) -> list[str]:
                return (row + [""] * ncols)[:ncols]

            output.append(r"\begin{table}[h]")
            output.append(r"\centering")
            output.append(r"\begin{tabular}{" + spec + "}")
            output.append(r"\hline")
            output.append(" & ".join(pad(header)) + r" \\")
            output.append(r"\hline")
            for row in rows:
                output.append(" & ".join(pad(row)) + r" \\")
            output.append(r"\hline")
            output.append(r"\end{tabular}")
            output.append(r"\end{table}")
            i = j
        return "\n".join(output)

    @classmethod
    def _convert_lists(cls, text: str) -> str:
        """Convert Markdown bullet/numbered lists into LaTeX list environments."""
        lines = text.split("\n")
        output: list[str] = []
        stack: list[tuple[int, str]] = []
        total = len(lines)
        i = 0
        while i < total:
            line = lines[i]
            match = cls._LIST_ITEM_RE.match(line)
            if match:
                indent = len(match.group(1).expandtabs(2))
                marker = match.group(2)
                env = "enumerate" if marker[0].isdigit() else "itemize"
                while stack and stack[-1][0] > indent:
                    output.append(f"\\end{{{stack.pop()[1]}}}")
                if stack and stack[-1][0] == indent:
                    if stack[-1][1] != env:
                        output.append(f"\\end{{{stack.pop()[1]}}}")
                        stack.append((indent, env))
                        output.append(f"\\begin{{{env}}}")
                else:
                    stack.append((indent, env))
                    output.append(f"\\begin{{{env}}}")
                output.append("\\item " + match.group(3))
                i += 1
                continue

            if not line.strip():
                # Keep a list open when the next non-blank line continues it.
                j = i + 1
                while j < total and not lines[j].strip():
                    j += 1
                if j >= total or not cls._LIST_ITEM_RE.match(lines[j]):
                    while stack:
                        output.append(f"\\end{{{stack.pop()[1]}}}")
                output.append("")
                i += 1
                continue

            if stack and line[:1].isspace():
                output.append(line)  # continuation line inside the current item
            else:
                while stack:
                    output.append(f"\\end{{{stack.pop()[1]}}}")
                output.append(line)
            i += 1
        return "\n".join(output)

    @classmethod
    def export_latex(
        cls,
        markdown_path: Path | str,
        bib_path: Path | str,
        output_path: Path | str,
    ) -> Path:
        """Convert markdown literature review to publication-ready LaTeX section."""
        md_file = Path(markdown_path)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        content = md_file.read_text(encoding="utf-8") if md_file.exists() else "# Literature Review\n\nNo synthesis found."

        # 1. Protect citations and converted headers with placeholders, then
        #    escape LaTeX specials in the prose, then restore. Escaping after
        #    conversion would corrupt the commands; converting after escaping
        #    would miss tokens that contain underscores or hashes.
        tokens: list[str] = []

        def stash_text(text: str) -> str:
            tokens.append(text)
            return f"\x00{len(tokens) - 1}\x00"

        def stash(match: re.Match) -> str:
            return stash_text(match.group(0))

        def header_replacer(match: re.Match) -> str:
            level = len(match.group(1))
            command = {1: "section", 2: "subsection", 3: "subsubsection"}[level]
            return stash_text(f"\\{command}{{{cls._escape_latex(match.group(2))}}}")

        def restore(match: re.Match) -> str:
            token = tokens[int(match.group(1))]
            if token.startswith("\\"):
                return token
            if token.startswith("[SCI-") and "#" not in token:
                return f"\\cite{{{token[1:-1]}}}"
            cite_key = token[1:-1].split("#")[0].replace("-", "_")
            return f"\\cite{{{cite_key}}}"

        latex_body = re.sub(
            r"^(#{1,3}) (.*)$", header_replacer, content, flags=re.MULTILINE
        )
        latex_body = re.sub(
            r"\[[A-Za-z0-9\-_]+#[A-Za-z0-9\-_]+#[A-Za-z0-9\-_]+\]",
            stash,
            latex_body,
        )
        latex_body = re.sub(r"\[(SCI-\d+)\]", stash, latex_body)
        latex_body = cls._escape_latex(latex_body)
        latex_body = re.sub(r"\x00(\d+)\x00", restore, latex_body)

        # 3. Transform bold/italic formatting, then block structures. Block
        #    conversion runs last because list markers and table pipes are not
        #    LaTeX specials and the cell prose is already escaped.
        latex_body = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", latex_body)
        latex_body = re.sub(r"\*(.*?)\*", r"\\textit{\1}", latex_body)
        latex_body = cls._convert_tables(latex_body)
        latex_body = cls._convert_lists(latex_body)

        # 4. Wrap with LaTeX template. Only emit \bibliography when the file
        #    actually exists, otherwise the generated document cannot compile.
        bib_file = Path(bib_path) if bib_path else None
        bib_name = bib_file.name if bib_file else "references.bib"
        if bib_file and bib_file.exists():
            bibliography = (
                f"\\bibliographystyle{{IEEEtran}}\n"
                f"\\bibliography{{{bib_name.replace('.bib', '')}}}\n"
            )
        else:
            bibliography = (
                "% No .bib file was present at export time; "
                "bibliography omitted.\n"
            )
        latex_doc = (
            f"% Generated by Nexus Scholar Harness\n"
            f"\\documentclass{{article}}\n"
            f"\\usepackage[utf8]{{inputenc}}\n"
            f"\\usepackage{{amsmath,amssymb}}\n"
            f"\\usepackage{{cite}}\n"
            f"\\usepackage{{hyperref}}\n\n"
            f"\\begin{{document}}\n\n"
            f"{latex_body}\n\n"
            f"{bibliography}\n"
            f"\\end{{document}}\n"
        )

        out_file.write_text(latex_doc, encoding="utf-8")
        return out_file

    @classmethod
    def export_typst(
        cls,
        markdown_path: Path | str,
        bib_path: Path | str,
        output_path: Path | str,
    ) -> Path:
        """Convert markdown literature review to Typst format."""
        md_file = Path(markdown_path)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        content = md_file.read_text(encoding="utf-8") if md_file.exists() else "= Literature Review\n\nNo synthesis found."

        # 1. Transform atomic citation tokens to @citekey
        def typst_cite_replacer(match: re.Match) -> str:
            raw_token = match.group(1)
            parts = raw_token.split("#")
            cite_key = parts[0].replace("-", "_")
            return f"@{cite_key}"

        typst_body = re.sub(r"\[([A-Za-z0-9\-_]+#[A-Za-z0-9\-_]+#[A-Za-z0-9\-_]+)\]", typst_cite_replacer, content)
        typst_body = re.sub(r"\[(SCI-\d+)\]", r"@\1", typst_body)

        # 2. Transform Markdown headers to Typst headers (=, ==, ===)
        typst_body = re.sub(r"^### (.*)$", r"=== \1", typst_body, flags=re.MULTILINE)
        typst_body = re.sub(r"^## (.*)$", r"== \1", typst_body, flags=re.MULTILINE)
        typst_body = re.sub(r"^# (.*)$", r"= \1", typst_body, flags=re.MULTILINE)

        # 3. Wrap with Typst template. Only emit a bibliography when the file
        #    exists, so the generated document stays compilable.
        bib_file = Path(bib_path) if bib_path else None
        bib_name = bib_file.name if bib_file else "references.bib"
        if bib_file and bib_file.exists():
            bibliography = f"#bibliography(\"{bib_name}\")\n"
        else:
            bibliography = (
                "// No .bib file was present at export time; "
                "bibliography omitted.\n"
            )
        typst_doc = (
            f"// Generated by Nexus Scholar Harness\n"
            f"#set page(paper: \"a4\", margin: (x: 2cm, y: 2.5cm))\n"
            f"#set text(font: \"Liberation Serif\", size: 11pt)\n\n"
            f"{typst_body}\n\n"
            f"{bibliography}"
        )

        out_file.write_text(typst_doc, encoding="utf-8")
        return out_file
