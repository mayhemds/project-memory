# How-to guides

Short recipes for specific situations. If you have not installed `mem` yet, start
with [Getting started](getting-started.md).

Contents:

- [Where to run mem init](#where-to-run-mem-init)
- [Track a new project](#track-a-new-project)
- [Track an existing project you were already working on](#track-an-existing-project-you-were-already-working-on)
- [Resume after a break](#resume-after-a-break)
- [Review what you did this week](#review-what-you-did-this-week)
- [Find a note across all projects](#find-a-note-across-all-projects)
- [Use mem with an AI coding assistant](#use-mem-with-an-ai-coding-assistant)
- [Switch between editors and tools](#switch-between-editors-and-tools)
- [Commit the notes, or keep them private](#commit-the-notes-or-keep-them-private)
- [Move or rename a project](#move-or-rename-a-project)
- [Stop tracking a project](#stop-tracking-a-project)
- [Update or uninstall mem](#update-or-uninstall-mem)
- [Use mem in a script](#use-mem-in-a-script)

## Where to run mem init

Run `mem init` inside each individual project, in the folder that holds that
project's files (the one with `.git`, `package.json`, `pyproject.toml` or
similar).

Say your folders look like this:

```text
Projects/
  shop/
    web/        <- a project: run mem init here
    api/        <- a project: run mem init here
  blog/         <- a project: run mem init here
  experiments/  <- only holds other things: do not run mem init here
```

**Why not in `Projects` or `shop`?** `mem` finds your notes by looking upward
from where you are for the nearest `.memory` folder. If `shop` is tracked and
`web` is not, then `mem save` inside `web` writes into `shop`'s notes, and the
notes for every project under `shop` end up mixed together. Once `web` has its
own `.memory`, it wins, so the mix-up only affects projects you have not
initialised yet.

`mem init` checks for this before it creates anything. It warns you, and asks
`Initialize here anyway? [y/N]`, when:

| The folder... | The warning says |
| --- | --- |
| has none of the usual project files | it does not look like a project folder |
| has no project files but contains folders that do | it holds projects, and names some of them, so run `mem init` inside one |
| is your home folder or `/` | it is not a project |
| is inside a folder that is already tracked | a parent is tracked, this would nest a project inside it |

Answer `n` to cancel, and nothing is created. Pass `--yes` to skip the question
when you really do want to initialise a folder that does not look like a project:

```bash
mem init --yes
```

The files `mem` treats as signs of a project are `.git`, `pyproject.toml`,
`setup.py`, `requirements.txt`, `package.json`, `deno.json`, `Cargo.toml`,
`go.mod`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `Gemfile`,
`composer.json`, `mix.exs`, `Package.swift`, `CMakeLists.txt`, `Makefile`, and any
`*.sln` or `*.csproj` file.

If you initialised the wrong folder, see
[Stop tracking a project](#stop-tracking-a-project).

## Track a new project

```bash
cd ~/Projects/blog
mem init
```

Then open `.memory/STATE.md`, set "Current focus" and add the first items under
"Next steps". Finish with `mem save "Set up the project"` so the log has a first
entry.

## Track an existing project you were already working on

The steps are the same as for a new project. Before you run `mem save`, take two
minutes to write down where things stand, because that is the part you will
forget:

1. `mem init`
2. Edit `.memory/STATE.md`: current focus, open problems, next steps, and any
   decisions you do not want to revisit.
3. `mem save "Started tracking. Currently halfway through the checkout refactor."`

## Resume after a break

From anywhere:

```bash
mem last
```

This shows the project you saved to most recently and its full notes. If you
worked on something else in between, use
[the weekly view](#review-what-you-did-this-week) to see all of it, then
`cd` into the project and run `mem status`.

`mem last` and `mem list` order projects by when you last ran `mem init` or
`mem save` in them. Editing `STATE.md` by hand does not count, so finish a
session with a `mem save` even if it is a short one.

## Review what you did this week

```bash
mem last --since 7d     # last 7 days
mem last --since 24h    # last 24 hours
mem last --since 90m    # last 90 minutes
```

Units are `m` (minutes), `h` (hours) and `d` (days). Projects are listed with the
most recent first.

To see every project you track, not just recent ones, run `mem list`.

## Find a note across all projects

```bash
mem search rounding
```

```text
web (~/Projects/shop/web)
  - Added cart totals, tax rounding is still off
  - Fixed rounding
```

Search is not case sensitive and matches the text you give literally, so `a.b`
finds `a.b` and not `aXb`. It looks at every line of every tracked project's
notes, including the focus, issues and decisions sections, not only the log.

## Use mem with an AI coding assistant

The notes file is plain markdown, so any assistant that can read your project can
use it. There are two ways to set this up.

**Option 1: let the assistant run `mem`.** If your assistant can run terminal
commands, ask it to finish each session with:

```bash
mem save "short summary of what was done and what is next"
```

This is the safer option, because `mem` writes the entry in the right format and
updates your project list at the same time.

**Option 2: let the assistant edit the file.** If it cannot run commands, ask it
to edit `.memory/STATE.md` directly. In that case the project list is not
updated, so run `mem save "Updated notes"` yourself afterwards if you want
`mem last` to see the session.

Either way, put a standing instruction in the file your assistant reads for
project rules, such as `CLAUDE.md`, `AGENTS.md` or `.cursorrules`. This wording
works well:

```markdown
## Project memory

At the start of a session, read `.memory/STATE.md` to see the current focus,
open issues, next steps and recent decisions.

During the session, keep "Current focus" and "Next steps" accurate.

Before you finish, record the session with `mem save "<summary>"`. If you cannot
run commands, append an entry at the end of the Session log in this format:

### YYYY-MM-DDTHH:MM
- What was done, what is unresolved, what comes next.

Never delete earlier log entries, and keep the `---` block at the top intact.
```

You can also have Claude write the entry for you from your git history. See
[AI drafting](ai-drafting.md).

## Switch between editors and tools

Nothing to configure. The notes live in the project folder, not in an editor or
tool, so they are there whichever one you open next. Make a habit of reading
`mem status` when you open a project and running `mem save` when you leave.

## Commit the notes, or keep them private

`.memory/` is an ordinary folder, so whether it goes into git is up to you.

**Keep it private** (the usual choice for personal notes): add this line to the
project's `.gitignore`:

```text
.memory/
```

**Share it with the team**: commit `.memory/STATE.md`. Everyone then sees the same
focus, issues and decisions. Expect merge conflicts if two people save at once,
and resolve them like any text file.

Whichever you choose, add `.memory/*.lock` to `.gitignore` if you commit the
folder. The `.lock` file is created while `mem` writes and is safe to ignore.

## Move or rename a project

`mem` remembers each project by its full folder path.

**Moving a project folder.** The `.memory` folder moves with it. Run
`mem save "Moved the project"` in the new location. That registers the new path.
The old entry is hidden automatically from `mem list` and `mem last` because its
notes no longer exist at the old path.

**Renaming the folder.** The name shown by `mem list` follows the folder name and
updates on your next `mem save`. The `project:` line at the top of `STATE.md` is
written once by `mem init` and is not updated, so edit it by hand if you care.

## Stop tracking a project

1. Delete the project's notes: `rm -r .memory` inside the project folder.
2. The project stops appearing in `mem list` and `mem last` straight away,
   because those only show projects whose notes still exist.
3. To remove the stale line from the registry as well, open `projects.json` (see
   [How it works](how-it-works.md#where-mem-keeps-its-data)) and delete that
   project's entry, or leave it. It is harmless.

## Update or uninstall mem

**Update:**

```bash
cd ~/tools/project-memory
git pull
uv tool install . --reinstall
```

`--reinstall` is needed because `uv` installs from your local copy and will not
refresh it otherwise.

**Uninstall** the command:

```bash
uv tool uninstall project-memory
```

This leaves your notes and the project list untouched. To remove those too,
delete each project's `.memory` folder and the `mem` folder described in
[How it works](how-it-works.md#where-mem-keeps-its-data).

## Use mem in a script

Commands exit with `0` on success and `1` on an expected error, with the message
on standard error. Pressing Ctrl+C exits with `130`.

Two commands can stop to ask a question, and fail instead of guessing when there
is no terminal to answer:

- `mem init` asks before initialising a folder that does not look like a project.
  Pass `--yes` to skip the question.
- `mem save` with no text asks for a note. Always pass the text in a script.

```bash
mem init --yes
mem save "Nightly build passed"
```

`mem save --ai` always asks you to confirm the draft, so it is not meant for
scripts.
