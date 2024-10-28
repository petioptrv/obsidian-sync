# obsidian-sync

Anki add-on for syncing with Obsidian.

## Functionality

The main goal of this add-on is to keep Anki and Obsidian notes in sync, with the
ability to edit the note in either app and then sync the changes to the other app.

Note templates are synced from Anki to Obsidian, so any modifications of the templates
must be performed in Anki.

If a given note has been modified in both apps, Anki takes precedence and overwrites
the changes made in Obsidian.

For now, notes can be deleted from Obsidian only if Obsidian is set to move deleted
notes to its own `.trash` folder (Settings -> Files and links -> Deleted files ->
Move to Obsidian trash (.trash folder)).

# Required Obsidian Vault Settings

The vault used for syncing with Anki must ensure the following settings.

- Must use [Markdown-style links](https://help.obsidian.md/Linking+notes+and+files/Internal+links#Supported+formats+for+internal+links).
- The [templates core plugin](https://help.obsidian.md/Plugins/Templates) must be enabled.

# Limitations

- Currently only handles markdown-style links. WikiLinks support is planned.

# To-Do

- [ ] Handle Wikilinks links

# Sources

## Inspired by

1. https://github.com/tansongchen/obsidian-note-synchronizer/tree/master
2. https://ankiweb.net/shared/info/327710559#

# Third Party Libraries Dependencies

markdownify
six
yaml
send2trash
