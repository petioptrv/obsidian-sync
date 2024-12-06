from dataclasses import dataclass, field
from typing import Dict, List

from obsidian_sync.obsidian.obsidian_note import ObsidianNote


@dataclass
class ObsidianNotesResult:
    new_notes: List[ObsidianNote]
    updated_notes: Dict[int, ObsidianNote]
    unchanged_notes: Dict[int, ObsidianNote]
