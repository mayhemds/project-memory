# project-memory

`mem` keeps a short notes file inside each of your projects, so you always know
where you left off. It records what you are working on, what is broken, what
comes next and a dated log of each session, and it keeps one small list of which
project you touched most recently.

It is made for people who work across many projects and switch between editors,
terminals and AI coding assistants all week. The notes are plain markdown, so any
tool can read and write the same file and your context survives every switch.

Everything runs on your machine. No account is needed. The only feature that goes
online is the optional `mem save --ai`, which asks Claude to draft an entry from
your git history.

## Quick start

You need Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
mkdir -p ~/tools && cd ~/tools
git clone https://github.com/mayhemds/project-memory.git
cd project-memory
uv tool install .
```

Then, inside one of your projects:

```bash
cd ~/Projects/my-app
mem init                         # start tracking this project
mem save "Added login, tests next"   # log what you did
mem status                       # read the notes
mem last                         # from anywhere: what was I working on?
```

Run `mem init` inside each individual project, not in a folder that only holds
other projects such as `~/Projects`. `mem init` warns you if the folder looks
wrong.

## Documentation

| Read this | When you want to |
| --- | --- |
| [Getting started](docs/getting-started.md) | Install `mem` and track your first project, step by step |
| [How-to guides](docs/how-to-guides.md) | Solve a specific problem: use it with an AI assistant, move a project, review your week, script it |
| [Command reference](docs/command-reference.md) | Look up every command, option, message and exit code |
| [AI drafting](docs/ai-drafting.md) | Have Claude write your session entries, and know what is sent |
| [Team sync](docs/team-sync.md) | Share the project list between machines, and understand its limits |
| [How it works](docs/how-it-works.md) | See what files `mem` writes, where, and why |
| [Troubleshooting](docs/troubleshooting.md) | Fix an error message |

## Commands at a glance

```bash
mem init              # register the current folder as a tracked project (warns if it is not one)
mem save "note"       # add a dated entry to the session log
mem save --ai         # draft the entry from recent git activity with Claude
mem status            # show the current project's notes
mem last              # show the project you touched most recently
mem last --since 7d   # list every project touched in the last 7 days
mem list              # list tracked projects on this machine, most recent first
mem search keyword    # search every tracked project's notes
mem sync <path>       # merge your project list with a shared file
```

## What the notes file looks like

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

`mem save` writes the Session log. The other sections are yours to edit.

## Development

```bash
uv sync --extra dev        # install pytest, ruff, and mypy
uv run pytest              # run the test suite
uv run pytest --cov        # with coverage
uv run ruff check .        # lint
uv run ruff format --check .
uv run mypy .              # type check
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
