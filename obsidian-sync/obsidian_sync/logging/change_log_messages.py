from dataclasses import dataclass


@dataclass
class ChangeLogMessage:
    pass


@dataclass
class CreatedAnkiTemplateInObsidian(ChangeLogMessage):
    model_name: str


@dataclass
class SyncedAnkiTemplateWithObsidianTemplate(ChangeLogMessage):
    model_name: str


@dataclass
class DeletedTemplateFromObsidian(ChangeLogMessage):
    model_name: str
