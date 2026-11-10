import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.models import Chunk

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
HUGO_SHORTCODE_RE = re.compile(r"\{\{[%<].*?[%>]\}\}", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class SourceDocument:
    path: Path
    title: str
    text: str
    metadata: dict[str, str]


def stable_hash(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    """Parse the small YAML-like frontmatter subset used by the demo corpus."""
    if not raw.startswith("---\n"):
        return {}, raw
    try:
        header, body = raw[4:].split("\n---\n", maxsplit=1)
    except ValueError:
        return {}, raw

    metadata: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", maxsplit=1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body.lstrip()


def clean_markdown(text: str) -> str:
    text = HUGO_SHORTCODE_RE.sub(" ", text)
    text = HTML_COMMENT_RE.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_document(path: Path) -> SourceDocument:
    raw = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)
    body = clean_markdown(body)
    first_heading = HEADING_RE.search(body)
    title = metadata.get("title") or (first_heading.group(2) if first_heading else path.stem)
    return SourceDocument(path=path, title=title, text=body, metadata=metadata)


def split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("Document", text)]

    sections: list[tuple[str, str]] = []
    if text[: matches[0].start()].strip():
        sections.append(("Introduction", text[: matches[0].start()].strip()))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.end() : end].strip()
        if content:
            sections.append((match.group(2).strip(), content))
    return sections


def window_words(text: str, max_words: int = 180, overlap_words: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words
    return chunks


def chunk_document(
    document: SourceDocument,
    source_root: Path,
    max_words: int = 180,
    overlap_words: int = 30,
) -> list[Chunk]:
    relative_path = document.path.relative_to(source_root).as_posix()
    document_hash = stable_hash(f"{relative_path}\n{document.text}")
    document_id = f"doc_{stable_hash(relative_path, 12)}"
    result: list[Chunk] = []

    for section_index, (section, section_text) in enumerate(split_sections(document.text)):
        for window_index, content in enumerate(
            window_words(section_text, max_words=max_words, overlap_words=overlap_words)
        ):
            chunk_key = f"{document_id}:{section_index}:{window_index}:{content}"
            result.append(
                Chunk(
                    chunk_id=f"chk_{stable_hash(chunk_key)}",
                    document_id=document_id,
                    title=document.title,
                    section=section,
                    content=content,
                    source_path=relative_path,
                    source_url=document.metadata.get("source_url"),
                    license=document.metadata.get("license"),
                    content_hash=document_hash,
                )
            )
    return result


def load_and_chunk(source_dir: Path) -> list[Chunk]:
    paths = sorted(path for path in source_dir.rglob("*.md") if path.is_file())
    chunks: list[Chunk] = []
    for path in paths:
        chunks.extend(chunk_document(read_document(path), source_dir))
    return chunks

