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
mem init              # register the current directory as a tracked project
mem save "fixed the auth bug"   # append a session entry
mem save --ai         # draft an entry from recent git activity with Claude
mem status            # show the current project's state file
mem last              # show the most recently touched project
mem last --since 7d   # list every project touched in the last 7 days
mem list              # list all tracked projects, most recent first
mem search keyword    # grep every tracked project's state file
mem sync <path>       # merge the local registry with a shared file (for teams)
```

### AI drafting

`mem save --ai` reads `ANTHROPIC_API_KEY` from the environment (the SDK reads it
directly; the key is never handled by this code). Optional overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MEM_MODEL` | `claude-sonnet-5` | Claude model used for drafting |
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

## Development

```bash
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
  each other's updates.
- **Validated input.** The registry is user-editable JSON; every entry is
  validated with pydantic on load, and malformed data produces a clean error
  rather than a traceback.
- **Untrusted git data.** Commit messages and file names are treated as data,
  wrapped in explicit delimiters, and separated from the system prompt at the
  message-role level before being sent to a model.

## License

Apache License 2.0. See [LICENSE](LICENSE).
