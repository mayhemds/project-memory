# Team sync

`mem sync` merges your list of tracked projects with a shared file, so the list
can be kept in step across machines or people. Read this page before relying on
it, because project locations are different on every computer and that limits
what sync can do.

## What it does

```bash
mem sync ~/Dropbox/mem-shared.json
```

1. Reads your project list and the shared file (creating the shared file if it
   does not exist).
2. Combines them. If both have an entry for the same project path, the one touched
   most recently wins.
3. Writes the combined list back to **both** your machine and the shared file.

Running it again from any machine moves everyone toward the same list. The shared
file can live anywhere you can read and write: a synced folder such as Dropbox, a
shared network drive, or a path inside a git repository.

## What it does not do

**It does not copy anyone's notes.** Sync only shares the list of project names,
paths and last-touched times. The `STATE.md` notes stay in each project folder. To
share notes, share the project itself, for example by committing `.memory/` to
git. See [Commit the notes, or keep them private](how-to-guides.md#commit-the-notes-or-keep-them-private).

**Entries for paths that do not exist on your machine are hidden.** A project is
identified by its full path, such as `/home/ana/work/shop`. On a teammate's
machine that path does not exist, so after a sync their entry is in your list but
`mem list` and `mem last` skip it, with a note saying how many were hidden. This is
deliberate: otherwise a teammate's project could appear as your "most recent".

In practice sync is useful in two situations:

- **Several of your own machines with the same folder layout**, for example the
  same username and a `~/Projects` folder on each. The paths match, so each
  machine sees the others' recent activity once the project folders are present.
- **A shared record**, where you want one file listing who touched which project
  and when, even if you cannot open every project locally.

If your machines use different paths, sync will not give you a unified view.

## Times and time zones

Entries in the project list are stored in UTC, marked with a trailing `Z`, so
people in different time zones compare correctly. Older entries without the `Z` are
read as your local time. The times inside each `STATE.md` stay in the local time of
whoever wrote them.

## Two people syncing at once

While syncing, `mem` locks both your list and the shared file, which stops two
syncs on the same computer from colliding. File-sync services such as Dropbox
copy files between computers and cannot lock across them, so if two machines sync
at the same moment, one may overwrite the other. Nothing is permanently lost,
because the next sync merges by most recent entry again and repairs it.

The lock uses a feature that Windows lacks, so on Windows there is no locking and
simultaneous runs can lose an update.

## Errors

- `Shared registry at ... is corrupted` means the shared file is not valid JSON.
  Fix it by hand, or move it aside and run `mem sync` again to create a fresh one.
- `Shared registry at ... has a malformed entry` means an entry is missing
  `name`, `path` or `last_updated`, or has a badly formed time.
- `Could not acquire lock ... within 5s` means another `mem` is holding the lock.
  See [Troubleshooting](troubleshooting.md#could-not-acquire-lock).
