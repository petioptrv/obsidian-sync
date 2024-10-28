from dataclasses import dataclass

from obsidian_sync.content import Content


@dataclass
class Template:
    content: Content
    model_name: str
