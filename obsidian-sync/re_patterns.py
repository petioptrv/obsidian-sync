import re


anki_model_id_property_in_obsidian_capture_pattern = re.compile(
    r'^---\s*(?:.*\n)*?mid\s*:\s*anki\s*(?:.*\n)*?---'
)
