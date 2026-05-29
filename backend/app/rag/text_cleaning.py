from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HORIZONTAL_SPACE_PATTERN = re.compile(r"[^\S\r\n]+")
BLANK_LINE_PATTERN = re.compile(r"\n{3,}")
ACCOUNT_SUFFIX_SPLIT_PATTERN = re.compile(
    r"\b([A-Za-z]{2,12})\s+([A-Za-z]{1,8})(?=[._-]\d|\d)"
)
KNOWN_TOKEN_SPLITS = (
    (re.compile(r"\badm\s+in\b", re.IGNORECASE), "admin"),
)


@dataclass(frozen=True)
class TextCleaningStats:
    original_length: int
    cleaned_length: int
    removed_control_chars: int
    repaired_spacing: int


def _preserve_case_replacement(match: re.Match[str], replacement: str) -> str:
    value = match.group(0)
    if value.isupper():
        return replacement.upper()
    if value[:1].isupper():
        return replacement.capitalize()
    return replacement


def remove_control_chars(text: str) -> tuple[str, int]:
    matches = CONTROL_CHAR_PATTERN.findall(text)
    return CONTROL_CHAR_PATTERN.sub("", text), len(matches)


def collapse_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = HORIZONTAL_SPACE_PATTERN.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    return BLANK_LINE_PATTERN.sub("\n\n", text).strip()


def repair_token_spacing(text: str) -> tuple[str, int]:
    repaired = 0

    def replace_known(match: re.Match[str], replacement: str) -> str:
        nonlocal repaired
        repaired += 1
        return _preserve_case_replacement(match, replacement)

    for pattern, replacement in KNOWN_TOKEN_SPLITS:
        text = pattern.sub(
            lambda match, repl=replacement: replace_known(match, repl), text
        )

    text, count = re.subn(r"(?<=\w)\s+([@._-])\s+(?=\w)", r"\1", text)
    repaired += count
    text, count = re.subn(r"(?<=\w)\s+([@._-])(?=\w)", r"\1", text)
    repaired += count
    text, count = re.subn(r"(?<=\w)([@._-])\s+(?=\w)", r"\1", text)
    repaired += count

    text, count = ACCOUNT_SUFFIX_SPLIT_PATTERN.subn(r"\1\2", text)
    repaired += count
    return text, repaired


def normalize_extracted_text(text: str) -> str:
    cleaned, _stats = normalize_extracted_text_with_stats(text)
    return cleaned


def normalize_extracted_text_with_stats(text: str) -> tuple[str, TextCleaningStats]:
    original_length = len(text)
    text = unicodedata.normalize("NFKC", text)
    text, removed_control_chars = remove_control_chars(text)
    text, repaired_spacing = repair_token_spacing(text)
    text = collapse_whitespace(text)
    stats = TextCleaningStats(
        original_length=original_length,
        cleaned_length=len(text),
        removed_control_chars=removed_control_chars,
        repaired_spacing=repaired_spacing,
    )
    return text, stats
