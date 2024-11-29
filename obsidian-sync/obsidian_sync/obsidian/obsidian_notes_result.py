from dataclasses import dataclass
from typing import Dict, List, Set

from obsidian_sync.obsidian.obsidian_note import ObsidianNote


@dataclass
class ObsidianNotesResult:
    existing_notes: Dict[int, ObsidianNote]
    new_notes: List[ObsidianNote]
    deleted_note_ids: Set[int]
    corrupted_notes: Set[int]
