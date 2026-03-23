"""Integration tests for title edge cases: CRLF, Unicode, empty lines, whitespace."""

import os

from youtube_updater.core.title_manager import TitleManager


def _make_tm(tmp_path, titles_content=""):
    """Create a TitleManager with given titles content."""
    titles_file = tmp_path / "titles.txt"
    titles_file.write_text(titles_content)
    applied_file = tmp_path / "applied-titles.txt"
    history_log = tmp_path / "history.log"
    return TitleManager(str(titles_file), str(applied_file), str(history_log))


class TestCRLFLineEndings:
    """Windows-style line endings (CRLF) in titles.txt."""

    def test_crlf_titles_read_cleanly(self, tmp_path):
        tm = _make_tm(tmp_path, "Title One\r\nTitle Two\r\nTitle Three\r\n")
        title = tm.get_next_title()
        assert title == "Title One"
        assert "\r" not in title

    def test_crlf_rotation_preserves_content(self, tmp_path):
        tm = _make_tm(tmp_path, "First\r\nSecond\r\n")
        tm.get_next_title()  # rotates "First" to end
        title = tm.get_next_title()
        assert title == "Second"
        assert "\r" not in title

    def test_mixed_line_endings(self, tmp_path):
        tm = _make_tm(tmp_path, "LF Title\nCRLF Title\r\nAnother LF\n")
        titles = []
        for _ in range(3):
            t = tm.get_next_title()
            titles.append(t)
            assert "\r" not in t
        assert titles == ["LF Title", "CRLF Title", "Another LF"]

    def test_crlf_peek_does_not_include_cr(self, tmp_path):
        tm = _make_tm(tmp_path, "Peek Me\r\n")
        peeked = tm.peek_next_title()
        assert peeked == "Peek Me"
        assert "\r" not in peeked

    def test_crlf_archive(self, tmp_path):
        tm = _make_tm(tmp_path, "Archive Me\r\n")
        title = tm.get_next_title()
        tm.archive_title(title)
        applied = (tmp_path / "applied-titles.txt").read_text()
        assert "Archive Me" in applied
        assert "\r\n\r\n" not in applied  # no double line breaks


class TestUnicodeTitles:
    """Non-ASCII characters in titles."""

    def test_arabic_title(self, tmp_path):
        tm = _make_tm(tmp_path, "Sunday Liturgy - القداس الإلهي\n")
        title = tm.get_next_title()
        assert title == "Sunday Liturgy - القداس الإلهي"

    def test_coptic_title(self, tmp_path):
        tm = _make_tm(tmp_path, "ⲡⲓⲛⲓϣϯ ⲛ̀ⲧⲉ ⲡⲓⲥⲁⲃⲃⲁⲧⲟⲛ\n")
        title = tm.get_next_title()
        assert "ⲡⲓⲛⲓϣϯ" in title

    def test_emoji_title(self, tmp_path):
        tm = _make_tm(tmp_path, "Live Stream 🔴 Sunday Service\n")
        title = tm.get_next_title()
        assert "🔴" in title

    def test_unicode_rotation(self, tmp_path):
        tm = _make_tm(tmp_path, "English Title\nعنوان عربي\n日本語タイトル\n")
        t1 = tm.get_next_title()
        assert t1 == "English Title"
        t2 = tm.get_next_title()
        assert t2 == "عنوان عربي"
        t3 = tm.get_next_title()
        assert t3 == "日本語タイトル"

    def test_unicode_archive(self, tmp_path):
        tm = _make_tm(tmp_path, "القداس الإلهي\n")
        title = tm.get_next_title()
        tm.archive_title(title)
        applied = (tmp_path / "applied-titles.txt").read_text()
        assert "القداس الإلهي" in applied


class TestEmptyAndWhitespace:
    """Edge cases with empty lines, whitespace-only lines, blank files."""

    def test_empty_lines_skipped(self, tmp_path):
        tm = _make_tm(tmp_path, "Title One\n\n\nTitle Two\n")
        t1 = tm.get_next_title()
        assert t1 == "Title One"
        t2 = tm.get_next_title()
        assert t2 == "Title Two"

    def test_whitespace_only_lines_skipped(self, tmp_path):
        tm = _make_tm(tmp_path, "  \nReal Title\n   \n")
        title = tm.get_next_title()
        assert title == "Real Title"

    def test_trailing_whitespace_stripped(self, tmp_path):
        tm = _make_tm(tmp_path, "Title With Trailing Spaces   \n")
        title = tm.get_next_title()
        assert title == "Title With Trailing Spaces"

    def test_single_title_rotates_to_itself(self, tmp_path):
        tm = _make_tm(tmp_path, "Only Title\n")
        t1 = tm.get_next_title()
        assert t1 == "Only Title"
        t2 = tm.get_next_title()
        assert t2 == "Only Title"
