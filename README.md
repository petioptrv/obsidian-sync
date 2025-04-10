# obsidian-sync

Anki add-on for syncing with Obsidian. Please read [the limitations section](#required-obsidian-vault-settings--limitations)
before use.

## Functionality

The goal of this add-on is to provide an integration between Anki and Obsidian, with
the main distinguishing feature being bidirectional note syncing between the two apps.

The add-on focuses on notes rather than cards. This means that there is no deck
information ported from Anki to Obsidian as that is a card concept—for instance, a given note's
cards may reside in different decks.

The app syncs Anki note models to Obsidian's templates folder, allowing the user to
create new notes in Obsidian using the [templates core plugin](https://help.obsidian.md/Plugins/Templates). If the core plugin
is disabled, the Anki models will not be synced. See the [limitations section](#note-models-and-templates) for
further details.

If a given note has been modified in both apps, Anki takes precedence. This is because
the add-on uses last-modified timestamp for Obsidian files to determine if a note has
been recently modified and this has unintended effects when using iCloud sync (see the
[iCloud section](#icloud-sync) of the limitations for more details).

The add-on treats spaced repetition system (SRS) notes (i.e. Anki notes) as first-class
citizens and creates one Obsidian note per SRS note in Anki. That said SRS notes can
coexist with regular notes in Obsidian, so it's possible to have one regular Obsidian
note on a given topic, populated with links to SRS note sections that contain parts of the
theory relating to the concept. As long as the regular note is not created from an
SRS note template, then the add-on will not try to sync it to Anki.

### Supported Features

- All default Anki note types.
- Option to add [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI) field to the Back Template of every Anki card to allow opening the Obsidian note (works on mobile too).
- Links to other notes in Obsidian files are translated to [Obsidian URIs](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI) when synced to Anki.
- The set of embedded media (image, audio, video) files officially supported by Obsidian.
  - See [this page](https://help.obsidian.md/Files+and+folders/Accepted+file+formats) for the file formats supported by Obsidian.
  - See the [limitations section](#media) for details on how media files are handled.
  - The files are duplicated on both platforms so that they are accessible on mobile as well.
- LaTex, both in-line and blocks.
- Code, both in-line and blocks.
- Lists, including indented lists.
- Special characters.
- SRS notes can coexist with regular Obsidian notes in the Obsidian vault.

## Config

| Config                                | Description                                                                                                                                                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `add-obsidian-url-in-anki`            | Adds an extra field to all note models in Anki that will contain the [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI) associate with the note to allow quickly jumping to the note in the Obsidian app. |
| `anki-deck-name-for-obsidian-imports` | The name of the Anki deck in which the cards of notes imported from Obsidian will default to.                                                                                                                                   |
| `srs-folder-in-obsidian`              | Set a specific folder path relative to the Obsidian vault to use for SRS notes.                                                                                                                                                 |
| `sync-with-obsidian-on-anki-web-sync` | If enabled, Anki will sync with Obsidian before every sync with Anki web.                                                                                                                                                       |
| `vault-path`                          | Path to Obsidian vault.                                                                                                                                                                                                         |

## Shortcuts

| Shortcut | Description        |
|----------|--------------------|
| `Ctrl + Y` | Sync with Obsidian |

## Limitations

#### !!!! Reformatting Warning !!!!

This add-on will likely re-format your Anki and/or Obsidian notes in order to ensure that a given note can be
converted to HTML or Markdown and back to the original text in the original format. The content of the notes
will not be changed by this process. However, be sure to [back up your Anki files](https://docs.ankiweb.net/backups.html#backups)
and your [Obsidian vault](https://help.obsidian.md/Getting+started/Back+up+your+Obsidian+files) before use.

#### Media

Currently, all attachment files imported from Anki to Obsidian are copied to a dedicated folder called `srs-attachments`
placed under the designated folder used for Anki cards (see [the configs section](#config) to learn about setting the
designated folder).

#### Note Models and Templates

Anki note models are synced uni-directionally with Anki being the ground truth. This means that any modifications to the
models must happen in Anki and then be synced to the Obsidian templates.

#### WikiLinks

The addon will convert markdown links of the form `[alt text](path/to/obsidian note.md)` to HTML links with
[Obsidian URIs](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI). However, [WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
are not currently supported. The add-on will treat them as regular text.

#### Obsidian URIs on Windows

Moving or renaming a note in Obsidian on Windows without changing its content won't update the note's URI in Anki.

#### iCloud Sync

If iCloud is used to sync Obsidian files, then off-loading and
re-downloading iCloud files updates their last-modified timestamps. This makes them
appear to be recently modified even if that's not the case. For that reason, if both an Anki not and an Obsidian note
are identified as modified, Anki modifications take precedence.

Tests using iCloud Sync result in many more notes being detected as updated in Obsidian even if they have not been.
This is due to iCloud updating the metadata of the file which the add-on relies on to make change-detection more
efficient. Unfortunately, this means that many more notes will be synced needlessly if iCloud Sync is used.

Obsidian Sync seems to work better, and I have not tested other sync methods.

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
