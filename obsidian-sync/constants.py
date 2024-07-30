ADD_ON_ID = "0"  # todo: update when available
ADD_ON_NAME = "obsidian-sync"

# CONFIG

CONF_VAULT_PATH = "vault-path"
CONF_ANKI_NOTE_IN_OBSIDIAN_PROPERTY_VALUE = "anki-note-in-obsidian-property-value"  # todo: document in the readme
CONF_FIELD_NAME_HEADER_TAG = "field-name-header-tag"

# OBSIDIAN

TEMPLATES_FOLDER_JSON_FIELD_NAME = "folder"

# properties
TEMPLATE_PROPERTY_NAME = "template"
MODEL_ID_PROPERTY_NAME = "mid"

DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_CARDS = 0

TEMPLATES_PROPERTIES_TEMPLATE = """---
mid: {model_id}
nid: 0
tags: []
date: {{{{date}}}} {{{{time}}}}
template: anki
---

"""
