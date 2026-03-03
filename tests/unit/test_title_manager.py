"""Unit tests for TitleManager, focusing on peek_next_title and core.next_title."""
import os
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch

from youtube_updater.core.title_manager import TitleManager
from youtube_updater.core import YouTubeUpdaterCore


def _make_title_manager(tmp_path, titles):
    """Create a TitleManager backed by a real titles file in tmp_path."""
    titles_file = str(tmp_path / "titles.txt")
    applied_file = str(tmp_path / "applied-titles.txt")
    history_file = str(tmp_path / "history.log")

    # Write initial titles
    with open(titles_file, "w") as f:
        f.write("\n".join(titles) + "\n")

    # Create empty support files
    for path in (applied_file, history_file):
        open(path, "w").close()

    return TitleManager(titles_file, applied_file, history_file), titles_file


class TestPeekNextTitle(TestCase):
    """Task 3: peek_next_title must not rotate the file."""

    def test_peek_next_title_does_not_rotate_file(self, tmp_path=None):
        """peek_next_title() called 3 times should always return the first title."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            mgr, titles_file = _make_title_manager(tmp, ["A", "B", "C"])

            # Call peek_next_title three times
            result1 = mgr.peek_next_title()
            result2 = mgr.peek_next_title()
            result3 = mgr.peek_next_title()

            # Each call should return "A" without advancing
            self.assertEqual(result1, "A")
            self.assertEqual(result2, "A")
            self.assertEqual(result3, "A")

            # File should still have "A" as first line
            with open(titles_file) as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(lines[0], "A")
            self.assertEqual(lines, ["A", "B", "C"])

    def test_peek_next_title_empty_file_returns_none(self):
        """peek_next_title on an empty file returns None."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            mgr, _ = _make_title_manager(tmp, [])
            result = mgr.peek_next_title()
            self.assertIsNone(result)


class TestNextTitlePropertyDoesNotConsume(TestCase):
    """Task 3: core.next_title must not consume (rotate) the title file."""

    def _make_core_with_titles(self, tmp_path, titles):
        """Build a YouTubeUpdaterCore wired to a real TitleManager."""
        from youtube_updater.core.config_manager import ConfigManager
        from youtube_updater.core.status_manager import StatusManager

        titles_file = str(tmp_path / "titles.txt")
        applied_file = str(tmp_path / "applied-titles.txt")
        history_file = str(tmp_path / "history.log")

        with open(titles_file, "w") as f:
            f.write("\n".join(titles) + "\n")
        for path in (applied_file, history_file):
            open(path, "w").close()

        title_manager = TitleManager(titles_file, applied_file, history_file)

        config = MagicMock(spec=["get_client_secrets_path", "get_file_paths"])
        config.get_client_secrets_path.return_value = str(tmp_path / "client_secrets.json")
        config.get_file_paths.return_value = {
            "titles_file": titles_file,
            "applied_titles_file": applied_file,
            "history_log": history_file,
            "token_path": str(tmp_path / "token.pickle"),
        }

        youtube_client = MagicMock()
        youtube_client.get_live_stream_info.return_value = {
            "is_live": True,
            "title": "Old Title",
            "video_id": "vid123",
        }

        core = YouTubeUpdaterCore(
            config_manager=config,
            title_manager=title_manager,
            youtube_client=youtube_client,
        )
        return core, titles_file

    def test_next_title_property_does_not_consume_title(self):
        """Accessing core.next_title 3 times then calling update_title() should
        only advance the titles file by 1 position."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            core, titles_file = self._make_core_with_titles(tmp, ["A", "B", "C"])

            # Access next_title property three times -- should not rotate
            t1 = core.next_title
            t2 = core.next_title
            t3 = core.next_title

            self.assertEqual(t1, "A")
            self.assertEqual(t2, "A")
            self.assertEqual(t3, "A")

            # Now actually update (this should rotate once)
            core.update_title()

            # After update, next_title should now return "B"
            self.assertEqual(core.next_title, "B")

            # File should have B at front
            with open(titles_file) as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(lines[0], "B")
