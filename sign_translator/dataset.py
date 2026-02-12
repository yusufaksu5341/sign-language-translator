from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
VID_ID_PATTERN = re.compile(r"(?P<vid_id>\d{2,4}-\d{2})$")


@dataclass(frozen=True)
class DatasetItem:
    label: str
    vid_id: str
    path: Path


def parse_word_and_video_id(stem: str) -> tuple[str, str]:
    """
    Expected filename pattern: '<word>_<vid-id>'
    Example: 'Anlamak_12-01'
    """
    if "_" not in stem:
        raise ValueError(f"Invalid filename (missing underscore): {stem}")

    word_part, maybe_vid = stem.rsplit("_", 1)
    match = VID_ID_PATTERN.match(maybe_vid)
    if not match:
        raise ValueError(f"Invalid filename (missing vid-id suffix): {stem}")

    label = " ".join(word_part.split()).strip()
    if not label:
        raise ValueError(f"Invalid filename (empty label): {stem}")

    return label, match.group("vid_id")


def iter_video_files(dataset_dir: Path) -> Iterable[Path]:
    for path in sorted(dataset_dir.glob("*")):
        if path.suffix.lower() in VIDEO_EXTENSIONS and path.is_file():
            yield path


def load_dataset_index(dataset_dir: str | Path) -> list[DatasetItem]:
    dataset_root = Path(dataset_dir)
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_root}")

    items: list[DatasetItem] = []
    skipped = 0

    for video_path in iter_video_files(dataset_root):
        try:
            label, vid_id = parse_word_and_video_id(video_path.stem)
            items.append(DatasetItem(label=label, vid_id=vid_id, path=video_path))
        except ValueError:
            skipped += 1

    if not items:
        raise RuntimeError(
            f"No valid dataset files found in {dataset_root}. "
            "Expected pattern: <word>_<vid-id>.mp4"
        )

    print(f"[dataset] valid files: {len(items)} | skipped: {skipped}")
    unique_labels = len({item.label for item in items})
    print(f"[dataset] unique labels: {unique_labels}")
    return items
