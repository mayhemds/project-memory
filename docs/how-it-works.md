# How it works

What `mem` stores, where it stores it, and the choices behind it. You do not need
to read this to use `mem`, but it helps when something looks odd.

## The two kinds of file

1. **A notes file in each project**: `<project>/.memory/STATE.md`.
2. **One project list per user**: a small JSON file recording every project you
   track and when you last touched it.

`mem` writes nothing else, and it never touches your code. The only other file it
creates is a short-lived `.lock` file next to each of the two files above, used to
stop two `mem` commands from writing at once.

## The notes file

`mem init` creates this from a template:

```markdown
---
project: checkout-api
status: in-progress
last_updated: 2026-03-14T16:20
---

# checkout-api

## Current focus
Retry handling for the payment provider webhook.

## Open issues / bugs
- Idempotency key not sent on retry (intermittent duplicate charges)

## Next steps / todo
- Add integration test for the duplicate-charge path

## Recent decisions
- Keep retries in the worker, not the HTTP handler

## Session log

### 2026-03-14T16:20
- Fixed retry backoff. Next: verify idempotency key is attached.
```

What `mem` changes, and what is left to you:

| Part | Who writes it |
| --- | --- |
| `project:` | `mem init`, once, from the folder name |
| `status:` | You. `mem` never changes it |
| `last_updated:` | `mem save`, every time, in your local time |
| The four sections (focus, issues, next steps, decisions) | You, or an AI assistant |
| `## Session log` entries | `mem save`, added at the very end of the file |

Rules to keep it working if you edit it by hand:

- Keep the `---` line at the very top, the `last_updated:` line, and the closing
  `---`. `mem save` stops with an error if they are missing or damaged.
- Keep `## Session log` as the last section. New entries are appended at the end
  of the file, wherever that is.
- Each entry is a `### YYYY-MM-DDTHH:MM` heading followed by a bulleted note. Use
  the same shape if you add entries by hand, so tools and people read them the
  same way.
- Windows-style (CRLF) line endings are kept as they are.

## Where mem keeps its data

**The project list** is a file named `projects.json` in `mem`'s config folder:

| System | Location |
| --- | --- |
| Linux | `~/.config/mem/projects.json` (or under `$XDG_CONFIG_HOME` if you set it) |
| macOS | `~/Library/Application Support/mem/projects.json` |
| Windows | a folder named `mem` inside your user profile's app data folder |

To put it somewhere else, set `MEM_HOME` to a folder, for example in your shell's
startup file:

```bash
export MEM_HOME="$HOME/Dropbox/mem"
```

The file is a JSON list you can read and edit:

```json
[
  {
    "name": "web",
    "path": "/home/ana/Projects/shop/web",
    "last_updated": "2026-10-17T10:44Z"
  }
]
```

- `name` is the folder name, refreshed on each save.
- `path` is the full folder path. This is how `mem` tells projects apart.
- `last_updated` is in UTC, marked with a `Z`. Older entries without the `Z` are
  read as local time.

Each entry is checked when the file is loaded. If you break it by hand, `mem`
says which file and why, rather than failing with a stack trace.

## How a project is found

For `save` and `status`, `mem` starts in your current folder and looks for a
`.memory` folder, then in the parent, and so on up to the top of the disk, using
the first one it finds. This is why you can work from a subfolder, and also why a
tracked parent folder collects the notes of untracked projects beneath it. See
[Where to run mem init](how-to-guides.md#where-to-run-mem-init).

## Design choices

- **Plain markdown, one file per project.** Anything that can read text can use
  it: your editor, `grep`, git, an AI assistant. There is no database or
  background process.
- **Atomic writes.** A file is first written in full under a temporary name and
  then swapped into place. A crash or power cut leaves either the old complete
  file or the new complete file, never half of one.
- **Locking.** While `mem` reads, changes and writes a file, it holds a lock, so
  two `mem` commands running together cannot silently drop each other's changes.
  It waits up to five seconds for the lock. Locking relies on a feature that is
  missing on Windows, where it does nothing, so on Windows two simultaneous runs
  can lose an update.
- **Checked input.** The project list can be edited by hand or arrive from a
  teammate, so every entry is validated on load and bad data produces a clear
  message.
- **Untrusted git text.** For [AI drafting](ai-drafting.md), commit messages and
  file names are treated as data, marked with delimiters, and sent separately
  from the instructions. You also confirm every draft.
- **Friendly failures.** Expected problems print `Error: ...` and exit with
  code 1. Unexpected ones print `Unexpected error: ...` instead of a stack trace.

## What `mem` does not do

- It does not watch your files or git history in the background. It only acts when
  you run a command.
- It does not send anything over the network except when you run `mem save --ai`.
- It does not sync notes between machines. [Sync](team-sync.md) shares only the
  project list.
- It does not read `.env` files.
