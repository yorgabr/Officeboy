from pathlib import Path
from officeboy.lint.cache import LintCache


def test_cache_detects_dirty_file(tmp_path: Path):
    cache = LintCache(tmp_path)
    file_path = tmp_path / "sample.bas"

    content_v1 = "Public Sub Test()\nEnd Sub"
    file_path.write_text(content_v1, encoding="utf-8")

    assert cache.is_dirty(file_path, content_v1)

    cache.update(file_path, content_v1)
    cache.flush()

    assert not cache.is_dirty(file_path, content_v1)


def test_cache_detects_change(tmp_path: Path):
    cache = LintCache(tmp_path)
    file_path = tmp_path / "sample.bas"

    content_v1 = "Public Sub Test()\nEnd Sub"
    content_v2 = "Public Sub Test()\n    Debug.Print 1\nEnd Sub"

    file_path.write_text(content_v1, encoding="utf-8")
    cache.update(file_path, content_v1)
    cache.flush()

    assert cache.is_dirty(file_path, content_v2)