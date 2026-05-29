from __future__ import annotations

from app.rag.text_cleaning import normalize_extracted_text_with_stats


def test_remove_control_chars() -> None:
    cleaned, stats = normalize_extracted_text_with_stats("abc\x01def")

    assert cleaned == "abcdef"
    assert stats.removed_control_chars == 1


def test_repair_admin_token_spacing() -> None:
    cleaned, stats = normalize_extracted_text_with_stats("adm in")

    assert cleaned == "admin"
    assert stats.repaired_spacing == 1


def test_repair_account_suffix_spacing() -> None:
    cleaned, _stats = normalize_extracted_text_with_stats("zlf.adm in-2107\x01")

    assert cleaned == "zlf.admin-2107"


def test_repair_email_spacing() -> None:
    cleaned, _stats = normalize_extracted_text_with_stats("user @ example . com")

    assert cleaned == "user@example.com"


def test_keep_normal_english_sentence_spacing() -> None:
    cleaned, _stats = normalize_extracted_text_with_stats("admin can login")

    assert cleaned == "admin can login"
