# Command reference

Every `mem` command, what it does and what can go wrong. For a walkthrough, see
[Getting started](getting-started.md).

```text
mem init [--yes]
mem save [NOTE] [--ai]
mem status
mem last [--since DURATION]
mem list
mem search KEYWORD
mem sync SHARED_PATH
```

Run `mem --help` or `mem COMMAND --help` for a built-in summary.

## Which folder it acts on

`status` and `save` work on the project you are inside. `mem` looks for a
`.memory` folder in the current folder, then in each parent folder in turn, and
uses the first one it finds. So you can run them from any subfolder of a project.
If none is found, they stop with an error telling you to run `mem init`.

`init` always acts on the current folder exactly, never a parent.

`last`, `list`, `search` and `sync` work across all your projects and can be run
from anywhere.

## mem init

Starts tracking the current folder as a project.

```bash
mem init
mem init --yes
```

It creates `.memory/STATE.md` from a template, using the folder name as the
project name, and adds the project to your project list.

Before creating anything it checks that the folder looks like one project and
asks `Initialize here anyway? [y/N]` if not. See
[Where to run mem init](how-to-guides.md#where-to-run-mem-init) for the checks.

| Option | Meaning |
| --- | --- |
| `-y`, `--yes` | Skip the check and the question |

If the project list cannot be updated, the notes file is removed again so you can
simply retry.

Errors:

- `... already exists. This project is already tracked.` The folder already has
  notes. Use `mem save`.
- `Cancelled. Nothing was created.` You answered no to the warning.
- `No input available to confirm. Pass --yes to skip the warning.` There was no
  terminal to answer the question, for example in a script.

## mem save

Adds a dated entry to the project's Session log.

```bash
mem save "Fixed the retry backoff"
mem save $'Fixed the retry backoff\nNext: check the idempotency key'
mem save
mem save --ai
```

| Form | What happens |
| --- | --- |
| `mem save "text"` | Saves the text |
| `mem save` | Prompts `Session note:` and saves what you type |
| `mem save --ai` | Drafts the entry from your git history, then asks you to confirm. See [AI drafting](ai-drafting.md) |

You cannot give both text and `--ai`.

A save does three things in one step: it appends the entry at the end of
`STATE.md`, updates the `last_updated:` line at the top, and updates the project
list. Timestamps in the file are in your local time to the minute.

A note with several lines is kept as one bullet, with the extra lines indented
under it, and blank lines are dropped. This means a line that starts with `#`
cannot turn into a heading and break the file's structure.

Errors:

- `No memory file found at ... Run 'mem init' first.` You are not inside a
  tracked project.
- `No note provided...` You pressed Enter at the prompt without typing anything.
- `Pass either a note or --ai, not both.`
- `State file is missing its frontmatter block.`, `...frontmatter block is not
  closed.`, or `Frontmatter field 'last_updated' not found...` The `---` block at
  the top of `STATE.md` was damaged by a hand edit. Restore the lines shown in
  [How it works](how-it-works.md#the-notes-file).

## mem status

Prints the whole `.memory/STATE.md` of the project you are in.

```bash
mem status
```

It is the same as opening the file, handy for a quick look or to hand to an
assistant. Fails with `No memory file found...` outside a tracked project.

## mem last

Shows the project you touched most recently, or all projects touched within a
time window.

```bash
mem last
mem last --since 7d
```

Without `--since`, it prints the project's name, path and last-touched time,
followed by its full notes:

```text
Most recent project: web (~/Projects/shop/web)
Last touched: 2026-10-17T10:44

---
project: web
...
```

With `--since`, it prints one line per project touched in that window, most recent
first:

```text
2026-10-17T10:44  web                        ~/Projects/shop/web
2026-10-17T10:44  api                        ~/Projects/shop/api
```

or `No projects touched in the last 7d.` if there are none.

| Option | Meaning |
| --- | --- |
| `--since DURATION` | A whole number followed by `m` (minutes), `h` (hours) or `d` (days), for example `90m`, `24h`, `7d`. Zero is not allowed |

"Touched" means you ran `mem init` or `mem save` in it. Times are shown in your
local time.

Only projects whose notes exist on this machine are shown. If some entries in
your project list are not found here, for example after a
[sync](team-sync.md) or after deleting a project, a note on standard error says
how many were hidden.

Errors:

- `Invalid duration '5x'. Use a number followed by m, h, or d, e.g. '7d'.`
- `No projects tracked yet. Run 'mem init' inside a project first.`
- `None of the N tracked project(s) exist on this machine.` Everything in the list
  points somewhere that is gone.

## mem list

Lists every project you track on this machine, most recently touched first.

```bash
mem list
```

```text
2026-10-17T10:44  web                        ~/Projects/shop/web
2026-10-17T10:44  api                        ~/Projects/shop/api
```

The columns are last-touched time, project name and full path. Entries whose notes
no longer exist are hidden, with a note on standard error saying how many.

## mem search

Looks for text in the notes of every tracked project.

```bash
mem search rounding
```

```text
web (~/Projects/shop/web)
  - Added cart totals, tax rounding is still off
  - Fixed rounding
```

- The match is not case sensitive and the text is matched literally, not as a
  pattern.
- It checks every line of each project's `STATE.md`, not only the log.
- Projects are listed most recent first, and projects with no match are left out.
- With no match anywhere it prints `No matches for 'word' in any tracked project.`

If you have no tracked projects it fails with `No projects tracked yet.`

## mem sync

Merges your project list with a shared file, for keeping several machines or
people in step.

```bash
mem sync ~/Dropbox/mem-shared.json
```

```text
Synced 2 project(s) with ~/Dropbox/mem-shared.json
```

The shared file is created if it does not exist. After the merge, both your list
and the shared file hold the same entries. See [Team sync](team-sync.md) for what
this does and does not do, because project paths differ between machines.

Errors: `Shared registry at ... is corrupted` or `...malformed entry` if the
shared file is not valid.

## Exit codes and output

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | An expected error. The message is printed to standard error as `Error: ...` |
| `130` | You pressed Ctrl+C |

Normal output goes to standard output, and warnings and notes such as the hidden
project count go to standard error, so you can pipe or redirect the output of
`mem list` and `mem search` safely.

## Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `MEM_HOME` | your platform's config folder | Where the project list is kept. See [How it works](how-it-works.md#where-mem-keeps-its-data) |
| `ANTHROPIC_API_KEY` | none | Your Anthropic API key, needed only for `mem save --ai` |
| `MEM_MODEL` | `claude-sonnet-5-5` | Claude model used by `--ai` |
| `MEM_MAX_TOKENS` | `300` | Maximum length of an AI draft |
| `MEM_TIMEOUT_SECONDS` | `60` | How long to wait for the API |
| `MEM_MAX_RETRIES` | `2` | How many times to retry a failed API call |

A value that is not a valid number, or is too small, stops the command with a
message naming the variable.
