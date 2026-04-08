import hashlib
import json
from pathlib import Path


class LintCache:
    def __init__(self, root: Path):
        self.cache_dir = root / ".officeboy_cache" / "lint"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {}

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def is_dirty(self, file_path: Path, content: str) -> bool:
        key = str(file_path)
        return self.index.get(key) != self._hash(content)

    def update(self, file_path: Path, content: str):
        self.index[str(file_path)] = self._hash(content)

    def flush(self):
        self.index_path.write_text(
            json.dumps(self.index, indent=2),
            encoding="utf-8",
        )