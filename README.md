# project-memory

`mem` keeps a lightweight, human-readable memory file inside each project and a
small global registry that tracks which project you touched most recently.

It exists for people who work across many repositories and switch between
editors, IDEs, and AI coding assistants all week. The memory file is plain
markdown, so any tool can read or write the same file and your context survives
the switch.

## How it works

- Each tracked project gets a `.memory/STATE.md` file: frontmatter plus sections
  for current focus, open issues, next steps, recent decisions, and a session log.
- A global registry at `~/.config/mem/projects.json` (macOS:
  `~/Library/Application Support/mem/projects.json`) records every project and
  when you last touched it.
- `mem save --ai` can draft a session entry from your recent git activity using
  Claude, which you then confirm or edit before it is written.

A project's `.memory/STATE.md` looks like this:

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

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/mayhemds/project-memory.git
cd project-memory
uv sync
```

Run it with `uv run mem ...`, or install the `mem` command onto your `PATH`:

```bash
uv tool install .
```

## Usage

```bash
mem init              # register the current directory as a tracked project (warns if it is not one)
mem save "fixed the auth bug"   # append a session entry
mem save --ai         # draft an entry from recent git activity with Claude
mem status            # show the current project's state file
mem last              # show the most recently touched project on this machine
mem last --since 7d   # list every project touched in the last 7 days
mem list              # list tracked projects on this machine, most recent first
mem search keyword    # grep every tracked project's state file
mem sync <path>       # merge the local registry with a shared file (for teams)
```

### Where to run `mem init`

Run `mem init` inside each individual project, not in a folder that holds many
projects (for example `~/Projects` or `~/Projects/client-a`). Notes are found by
looking upward for the nearest `.memory` folder, so a parent that is tracked
would swallow the notes of any project beneath it that has not been initialised.
`mem init` warns before creating anything when the folder has no project files
(`.git`, `pyproject.toml`, `package.json` and similar), when it is your home or
root folder, when it contains folders that look like projects, or when a parent
is already tracked. Answer `n` to cancel, or pass `--yes` to skip the check.

Install `mem` once from anywhere, such as `~/tools/project-memory`, with
`uv tool install .`; the clone is only needed to update it later.

Multi-line notes are saved as a single bullet, with the extra lines indented
under it, so a note can never add a stray heading to `STATE.md`. Inside a git
repository, `--ai` summarises activity under the current project folder, so it
also works for a project that lives in a subfolder of a monorepo.

### AI drafting

`mem save --ai` needs `ANTHROPIC_API_KEY` in the environment. This code only checks
that it is set; the SDK reads and uses the value itself, so the key is never
stored or logged by `mem`. If a draft hits the token limit it is marked as cut
off so you can raise `MEM_MAX_TOKENS` or edit it. Optional overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MEM_MODEL` | `claude-sonnet-5-5` | Claude model used for drafting |
| `MEM_MAX_TOKENS` | `300` | Output cap per draft |
| `MEM_TIMEOUT_SECONDS` | `60` | Request timeout |
| `MEM_MAX_RETRIES` | `2` | SDK retry count |
| `MEM_HOME` | platform config dir | Override the registry location |

Copy `.env.example` to `.env` as a starting point. Never commit a real key.

### Team sync

Point everyone's `mem` at the same shared JSON file (a synced folder, a shared
drive, or a git-tracked path) and run `mem sync <path>`. The merge keeps the
most recent entry per project and writes both copies back, so repeated runs from
any machine converge on the same picture.

Things to know:

- Projects are matched by absolute path, so a teammate's entries point at paths
  on their machine. `mem last` and `mem list` only show projects whose
  `.memory/STATE.md` exists on your machine, and say how many they hid.
- Registry timestamps are stored in UTC (a trailing `Z`) so entries from
  different timezones compare correctly. Older local-time entries still load.
  Timestamps inside `STATE.md` stay in your local time.
- The shared file is locked while syncing, which protects syncs on one
  filesystem. File-sync services (Dropbox, a shared drive) cannot lock across
  machines, so two machines syncing at the same instant can overwrite each
  other. The next sync repairs it.

## Development

```bash
uv sync --extra dev        # install pytest, ruff, and mypy
uv run pytest              # run the test suite
uv run pytest --cov        # with coverage
uv run ruff check .        # lint
uv run ruff format --check .
uv run mypy .              # type check
```

## Design notes

- **Atomic writes.** Every file mutation writes to a temp file and `os.replace`s
  it into position, so a crash never leaves a truncated registry or state file.
- **Advisory locking.** Registry and state-file mutations hold a lock for the
  whole read-modify-write cycle, so concurrent `mem` invocations cannot lose
  each other's updates. Locking uses `fcntl`, so it is POSIX only; on Windows
  the lock does nothing and simultaneous `mem` runs can lose an update.
- **Validated input.** The registry is user-editable JSON; every entry is
  validated with pydantic on load, and malformed data produces a clean error
  rather than a traceback.
- **Untrusted git data.** Commit messages and file names are treated as data,
  wrapped in explicit delimiters (any delimiter text inside them is neutralised),
  and separated from the system prompt at the message-role level before being
  sent to a model. You also confirm every draft before it is saved.

## License

Apache License 2.0. See [LICENSE](LICENSE).
