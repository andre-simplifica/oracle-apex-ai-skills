# Export Modes

## Official Snapshot

Use when the intent is to update the project repository with a new version of the APEX application.

Requires:

- clean git status or isolated scope;
- official folder defined in the profile;
- export options defined;
- structure validation;
- commit/push if the project rule requires it.

## Temporary Inspection

Use when the intent is to understand a page/component.

Rules:

- export to `/tmp`;
- do not replace the snapshot;
- do not stage;
- do not execute install;
- delete or ignore afterwards.

## App Builder Fallback

Use when SQLcl is unavailable and the project profile allows it.

After downloading through Builder:

- validate file/folder;
- import into the official snapshot using the project script, if one exists;
- inspect the diff.
