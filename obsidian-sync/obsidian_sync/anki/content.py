from dataclasses import dataclass
from typing import List

from obsidian_sync.anki.app.media_manager import AnkiMediaManager
from obsidian_sync.base_types.content import Field, Content, Properties, NoteProperties, LinkedAttachment, NoteContent, \
    NoteField, TemplateField
from obsidian_sync.markup_translator import MarkupTranslator


@dataclass
class AnkiContent(Content):
    properties: "AnkiProperties"
    fields: List["AnkiField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiTemplateContent(AnkiContent):
    properties: "AnkiTemplateProperties"
    fields: List["AnkiTemplateField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteContent(AnkiContent):
    properties: "AnkiNoteProperties"
    fields: List["AnkiNoteField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_content(
        cls,
        content: NoteContent,
        anki_media_manager: AnkiMediaManager,
    ) -> "AnkiNoteContent":
        properties = AnkiNoteProperties.from_properties(properties=content.properties)
        fields = AnkiNoteField.from_fields(
            fields=content.fields, anki_media_manager=anki_media_manager
        )
        return cls(properties=properties, fields=fields)


@dataclass
class AnkiProperties(Properties):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiTemplateProperties(AnkiProperties):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteProperties(NoteProperties):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_properties(cls, properties: NoteProperties) -> "AnkiNoteProperties":
        return cls(
            model_id=properties.model_id,
            model_name=properties.model_name,
            note_id=properties.note_id,
            tags=properties.tags,
            suspended=properties.suspended,
            maximum_card_difficulty=properties.maximum_card_difficulty,
            date_modified_in_anki=properties.date_modified_in_anki,
        )


@dataclass
class AnkiField(Field):
    def __post_init__(self):
        self._markup_translator = MarkupTranslator()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def set_from_markdown(self, markdown: str):
        self.text = self._markup_translator.translate_markdown_to_html(markdown=markdown)

    def set_from_html(self, html: str):
        self.text = html

    def to_markdown(self) -> str:
        markdown_text = self._markup_translator.translate_html_to_markdown(html=self.text)
        return markdown_text

    def to_html(self) -> str:
        return self.text


@dataclass
class AnkiTemplateField(TemplateField, AnkiField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteField(NoteField, AnkiField):
    attachments: List["AnkiLinkedAttachment"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_fields(
        cls,
        fields: List[NoteField],
        anki_media_manager: AnkiMediaManager,
    ) -> List["AnkiNoteField"]:
        fields = [
            AnkiNoteField.from_field(
                field=field, anki_media_manager=anki_media_manager
            )
            for field in fields
        ]
        return fields

    @classmethod
    def from_field(
        cls,
        field: NoteField,
        anki_media_manager: AnkiMediaManager,
    ) -> "AnkiNoteField":
        html_text = field.to_html()

        anki_attachments = []
        for attachment in field.attachments:
            anki_attachment = AnkiLinkedAttachment.from_attachment(
                attachment=attachment, anki_media_manager=anki_media_manager
            )
            anki_attachments.append(anki_attachment)
            html_text = html_text.replace(
                attachment.to_field_text(), anki_attachment.to_field_text()
            )

        return cls(
            name=field.name,
            text=html_text,
            attachments=anki_attachments,
        )

    def to_anki_field_text(self) -> str:
        field_text = self.text

        for attachment in self.attachments:
            field_text = field_text.replace(
                attachment.to_field_text(), attachment.to_anki_field_text()
            )

        return field_text


@dataclass
class AnkiLinkedAttachment(LinkedAttachment):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_attachment(
        cls, attachment: LinkedAttachment, anki_media_manager: AnkiMediaManager
    ) -> "AnkiLinkedAttachment":
        anki_attachment = anki_media_manager.ensure_attachment_is_in_anki(attachment=attachment)
        return cls(path=anki_attachment)

    def to_anki_field_text(self) -> str:
        return self.path.name

    def to_field_text(self) -> str:
        return str(self.path)
