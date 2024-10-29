# obsidian-sync

Anki add-on for syncing with Obsidian.

## Functionality

The main goal of this add-on is to keep Anki and Obsidian notes in sync, with the
ability to edit the note in either app and then sync the changes to the other app.

Note templates are synced from Anki to Obsidian, so any modifications of the templates
must be performed in Anki.

If a given note has been modified in both apps, Anki takes precedence and overwrites
the changes made in Obsidian.

# Required Obsidian Vault Settings / Limitations

The vault used for syncing with Anki must be configured with the following settings.

- The [templates core plugin](https://help.obsidian.md/Plugins/Templates) must be enabled.
- Must use [Markdown-style links](https://help.obsidian.md/Linking+notes+and+files/Internal+links#Supported+formats+for+internal+links).
- Must use the Obsidian trash folder option (Settings -> Files and links -> Deleted files ->
Move to Obsidian trash (.trash folder)).

# To-Do

- [ ] Handle Wikilinks links

# Sources

## Inspired by

1. https://github.com/tansongchen/obsidian-note-synchronizer/tree/master
2. https://ankiweb.net/shared/info/327710559#
3. https://github.com/mlcivilengineer/obsankipy/tree/main

# Third Party Libraries Dependencies

markdownify
six
yaml
send2trash
