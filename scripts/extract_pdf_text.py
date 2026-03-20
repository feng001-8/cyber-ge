from __future__ import annotations

import argparse
from pathlib import Path


def extract_with_pypdf(pdf_path: Path) -> tuple[str, int]:
    import pypdf  # type: ignore

    reader = pypdf.PdfReader(str(pdf_path))
    pages = len(reader.pages)
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        parts.append(f"\n\n===== PAGE {i + 1}/{pages} =====\n")
        parts.append(page.extract_text() or "")
    return "".join(parts), pages


def extract_with_pypdf2(pdf_path: Path) -> tuple[str, int]:
    import PyPDF2  # type: ignore

    reader = PyPDF2.PdfReader(str(pdf_path))
    pages = len(reader.pages)
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        parts.append(f"\n\n===== PAGE {i + 1}/{pages} =====\n")
        parts.append(page.extract_text() or "")
    return "".join(parts), pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=str)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    text = ""
    pages = 0
    errors: list[str] = []
    for extractor in (extract_with_pypdf, extract_with_pypdf2):
        try:
            text, pages = extractor(pdf_path)
            break
        except Exception as e:
            errors.append(f"{extractor.__name__}: {e}")

    if not text:
        raise SystemExit("PDF extract failed: " + " | ".join(errors))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8", errors="ignore")

    print(f"ok pages={pages} chars={len(text)} out={out_path}")


if __name__ == "__main__":
    main()

