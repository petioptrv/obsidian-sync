from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from obsidian_sync.base_types.content import Field, Content, Properties, NoteProperties, LinkedAttachment, NoteContent
from obsidian_sync.markup_translator import MarkupTranslator

if TYPE_CHECKING:  # avoids circular import
    from obsidian_sync.anki.anki_app import AnkiApp


@dataclass
class AnkiContent(Content):
    properties: "AnkiProperties"
    fields: List["AnkiField"]


@dataclass
class AnkiTemplateContent(AnkiContent):
    properties: "AnkiTemplateProperties"


@dataclass
class AnkiNoteContent(AnkiContent):
    properties: "AnkiNoteProperties"

    @classmethod
    def from_content(cls, content: NoteContent, anki_app: "AnkiApp", markup_translator: MarkupTranslator) -> "AnkiNoteContent":
        properties = AnkiNoteProperties.from_properties(properties=content.properties)
        fields = AnkiField.from_fields(
            fields=content.fields, anki_app=anki_app, markup_translator=markup_translator
        )
        return cls(properties=properties, fields=fields)


@dataclass
class AnkiProperties(Properties):
    pass


@dataclass
class AnkiTemplateProperties(AnkiProperties):
    pass


@dataclass
class AnkiNoteProperties(NoteProperties):
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
    attachments: List["AnkiLinkedAttachment"]
    _markup_translator: MarkupTranslator

    @classmethod
    def from_fields(cls, fields: List[Field], anki_app: "AnkiApp", markup_translator: MarkupTranslator) -> List["AnkiField"]:
        fields = [
            AnkiField.from_field(field=field, anki_app=anki_app, markup_translator=markup_translator)
            for field in fields
        ]
        return fields

    @classmethod
    def from_field(cls, field: Field, anki_app: "AnkiApp", markup_translator: MarkupTranslator) -> "AnkiField":
        html_text = field.to_html()

        anki_attachments = []
        for attachment in field.attachments:
            anki_attachment = AnkiLinkedAttachment.from_attachment(
                attachment=attachment, anki_app=anki_app
            )
            anki_attachments.append(anki_attachment)
            html_text = html_text.replace(
                attachment.to_field_text(), anki_attachment.to_field_text()
            )

        return cls(
            name=field.name,
            text=html_text,
            attachments=anki_attachments,
            _markup_translator=markup_translator,
        )

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
class AnkiLinkedAttachment(LinkedAttachment):
    @classmethod
    def from_attachment(
        cls, attachment: LinkedAttachment, anki_app: "AnkiApp"
    ) -> "AnkiLinkedAttachment":
        anki_attachment = anki_app.ensure_attachment_is_in_anki(attachment=attachment)
        return cls(path=anki_attachment)

    def to_field_text(self) -> str:
        return str(self.path)
