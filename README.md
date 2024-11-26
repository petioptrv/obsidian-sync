# obsidian-sync

Anki add-on for syncing with Obsidian. Please read [the limitations section](#required-obsidian-vault-settings--limitations)
before use.

## Functionality

The goal of this add-on is to provide an integration between Anki and Obsidian, with
the main feature being bidirectional note syncing between the two apps.

The add-on focuses on notes rather than cards. This means that there is no deck
information ported from Anki to Obsidian as that is a card concept and a given note's
cards may reside in different decks.

The app syncs Anki note models to Obsidian's templates folder, allowing the user to
create new notes in Obsidian using the [templates core plugin](https://help.obsidian.md/Plugins/Templates). See the
[limitations section](#note-models-and-templates) for further details.

If a given note has been modified in both apps, the most recent version is kept.

### Supported Features

- All default Anki note types.
- The set of embedded media (image, audio, video) files officially supported by Obsidian.
  - See [this page](https://help.obsidian.md/Files+and+folders/Accepted+file+formats) for the file formats supported by Obsidian.
  - See the [limitations section](#media) for details on how media files are handled.
  - The files are copied from one platform to the other so that the changes are reflected on mobile as well.
- LaTex, both in-line and blocks.
- Code, both in-line and blocks.
- Syncing "suspended" status on a per-note basis.
  - If all cards associated with the note are suspended in Anki, this property will be checked in Obsidian, otherwise it will be unchecked.
  - If a note is "suspended" (i.e. all its cards are suspended in Anki) and the property is unchecked in Obsidian, this will cause the associated Anki cards to be unsuspended.
  - If a note is not "suspended" (i.e. at least one of its cards is not suspended in Anki) and the property is checked in Obsidian, this will cause the associated Anki cards to be suspended.

## Config

| Config                                | Description                                                                                                                                                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `vault-path`                          | Path to Obsidian vault.                                                                                                                                                                                                         |
| `srs-folder-in-obsidian`              | Set a specific folder path relative to the Obsidian vault to use for SRS notes.                                                                                                                                                 |
| `sync-with-obsidian-on-anki-web-sync` | If enabled, Anki will sync with Obsidian before every sync with Anki web.                                                                                                                                                       |
| `anki-deck-name-for-obsidian-imports` | The name of the Anki deck in which the cards of notes imported from Obsidian will default to.                                                                                                                                   |
| `add-obsidian-url-in-anki`            | Adds an extra field to all note models in Anki that will contain the [Obsidian URL](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI) associate with the note to allow quickly jumping to the note in the Obsidian app. |

## Shortcuts

| Shortcut | Description        |
|----------|--------------------|
| `Ctrl + Y` | Sync with Obsidian |

## Required Obsidian Vault Settings / Limitations

#### !!!! Reformatting Warning !!!!

This add-on will likely re-format your Anki and/or Obsidian notes in order to ensure that a given note can be
converted to HTML or Markdown and back to the original text in the original format. The content of the notes
will not be changed by this process. However, be sure to [backup your Anki files](https://docs.ankiweb.net/backups.html#backups)
and your [Obsidian vault](https://help.obsidian.md/Getting+started/Back+up+your+Obsidian+files) before use.

#### Media

Currently, all attachments imported from Anki to Obsidian are copied to a dedicated folder called `srs-media` placed
under the designated folder used for Anki cards (see [the configs section](#config) to learn about setting the
designated folder).

#### Note Models and Templates

Anki note models are synced uni-directionally with Anki being the ground truth. This means that any modifications to the
models must happen in Anki and then be synced to the Obsidian templates.

#### Required Obsidian Settings

The vault used for syncing with Anki must be configured with the following settings.

- The [templates core plugin](https://help.obsidian.md/Plugins/Templates) must be enabled.
- Must use [Markdown-style links](https://help.obsidian.md/Linking+notes+and+files/Internal+links#Supported+formats+for+internal+links).

## To-Do

- [ ] Handle Wikilinks links

## Sources

### Inspired by

1. https://github.com/tansongchen/obsidian-note-synchronizer/tree/master
2. https://ankiweb.net/shared/info/327710559#
3. https://github.com/mlcivilengineer/obsankipy/tree/main

## Third Party Libraries Dependencies (shipped with the add-on)

- [markdownify](https://github.com/matthewwithanm/python-markdownify)
- [six](https://github.com/benjaminp/six)
- [PyYAML](https://github.com/yaml/pyyaml)
- [send2trash](https://github.com/arsenetar/send2trash)
