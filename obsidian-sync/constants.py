ADD_ON_ID = "0"  # todo: update when available
ADD_ON_NAME = "obsidian-sync"

# CONFIG

CONF_VAULT_PATH = "vault-path"
CONF_ANKI_FOLDER = "anki-folder"
CONF_ANKI_NOTE_IN_OBSIDIAN_PROPERTY_VALUE = "anki-note-in-obsidian-property-value"  # todo: document in the readme
CONF_FIELD_NAME_HEADER_TAG = "field-name-header-tag"

# GENERAL

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ANKI

DECK_NAME_SEPARATOR = "::"

# OBSIDIAN

MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH = 200

MARKDOWN_FILE_SUFFIX = ".md"

OBSIDIAN_SETTINGS_FOLDER = ".obsidian"
OBSIDIAN_TEMPLATES_SETTINGS_FILE = "templates.json"
OBSIDIAN_APP_SETTINGS_FILE = "app.json"
OBSIDIAN_LOCAL_TRASH_FOLDER = ".trash"

OBSIDIAN_TRASH_OPTION_KEY = "trashOption"
OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE = "system"
OBSIDIAN_LOCAL_TRASH_OPTION_VALUE = "local"
OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE = "none"

TEMPLATES_FOLDER_JSON_FIELD_NAME = "folder"
TEMPLATE_DATE_FORMAT = "YYYY-MM-DD"
TEMPLATE_TIME_FORMAT = "HH:mm:ss"

ANKI_NOTE_FIELD_IDENTIFIER_COMMENT = "<!--anki-note-field-->"

# properties
MODEL_ID_PROPERTY_NAME = "mid"
NOTE_ID_PROPERTY_NAME = "nid"
TAGS_PROPERTY_NAME = "tags"
DATE_MODIFIED_PROPERTY_NAME = "date modified"
DATE_SYNCED_PROPERTY_NAME = "date synced"
ANKI_NOTE_IDENTIFIER_PROPERTY_NAME = "anki"

NOTE_PROPERTIES_BASE_STRING = (
    f"---"
    f"\n{MODEL_ID_PROPERTY_NAME}: {{model_id}}"
    f"\n{NOTE_ID_PROPERTY_NAME}: {{note_id}}"
    f"\n{TAGS_PROPERTY_NAME}: {{tags}}"
    f"\n{DATE_MODIFIED_PROPERTY_NAME}: {{date_modified}}"
    f"\n{DATE_SYNCED_PROPERTY_NAME}: {{date_synced}}"
    f"\n{ANKI_NOTE_IDENTIFIER_PROPERTY_NAME}: {{anki_note_identifier_property_value}}"
    f"\n---"
    f"\n"
)

DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_CARDS = 0
