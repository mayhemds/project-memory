# Getting started

This guide takes you from nothing installed to a tracked project in about five
minutes. You do not need an account, an API key or an internet connection to use
`mem` after it is installed.

## What you get

`mem` keeps a short notes file inside each of your projects, at
`.memory/STATE.md`. It records what you are working on, what is broken, what
comes next and a dated log of each work session. Because it is plain markdown,
you, your editor and any AI coding assistant can read and write the same file,
so your context survives when you switch tools or come back after a week.

`mem` also keeps one small list on your machine of every project you track and
when you last touched each one. That is what lets `mem last` answer "what was I
working on?" without you remembering which folder it was.

## 1. Install

You need two things: Python 3.12 or newer, and a tool called
[uv](https://docs.astral.sh/uv/) that installs Python programs.

**Install uv** (skip this if `uv --version` already works):

```bash
# Linux and macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Open a new terminal afterwards so the `uv` command is found.

**Install mem.** Clone the repository somewhere that is not one of your projects.
`~/tools` is a good choice:

```bash
mkdir -p ~/tools
cd ~/tools
git clone https://github.com/mayhemds/project-memory.git
cd project-memory
uv tool install .
```

The last command puts a `mem` command on your PATH, so it works from every
folder. You only need the cloned folder again when you want to update.

**Check it worked:**

```bash
mem --help
```

You should see the list of commands. If you get `command not found`, run
`uv tool update-shell`, open a new terminal and try again.

## 2. Start tracking a project

Go into a real project folder, the one that holds your code, and run `mem init`:

```bash
cd ~/Projects/shop/web
mem init
```

```text
Initialized project memory at ~/Projects/shop/web/.memory/STATE.md
```

This creates a `.memory` folder with one file in it and adds the project to your
list. It does not change any of your code.

> **Run `mem init` inside each project, never in a folder that only holds other
> projects.** If your layout is `Projects/shop/web` and `Projects/shop/api`,
> initialise `web` and `api` separately, not `Projects` or `shop`. Notes are found
> by looking upward for the nearest `.memory` folder, so a tracked parent would
> collect the notes of every untracked project beneath it. `mem init` warns you
> before it does this. See [Where to run mem init](how-to-guides.md#where-to-run-mem-init).

## 3. Write your first entry

```bash
mem save "Added cart totals, tax rounding is still off"
```

```text
Saved to ~/Projects/shop/web/.memory/STATE.md
```

Each save adds a dated entry to the Session log and updates the project's
last-touched time. You can run `mem save` from any folder inside the project, not
just the top.

For a longer note, put it on several lines (this form works in bash and zsh).
Everything stays together in one entry:

```bash
mem save $'Fixed the rounding bug\nNext: add tests for discounts'
```

Or run `mem save` with no text and type the note when asked.

## 4. Read it back

```bash
mem status
```

prints the whole file for the project you are in. Here is what it looks like
after the two saves above:

```markdown
---
project: web
status: in-progress
last_updated: 2026-10-17T10:44
---

# web

## Current focus
(what you're actively doing right now, one line)

## Open issues / bugs
-

## Next steps / todo
-

## Recent decisions
-

## Session log

### 2026-10-17T10:44
- Added cart totals, tax rounding is still off

### 2026-10-17T10:44
- Fixed the rounding bug
  Next: add tests for discounts
```

## 5. Fill in the rest by hand

`mem save` only writes the Session log. The other sections are yours. Open
`.memory/STATE.md` in any editor and replace the placeholders with what is true
today:

- **Current focus**: one line on what you are doing right now.
- **Open issues / bugs**: things that are broken or unresolved.
- **Next steps / todo**: what you will do next, in order.
- **Recent decisions**: choices you made and why, so you do not re-argue them.

Keep the lines between `---` at the top and keep `last_updated:` in them,
because `mem` updates that line on every save. Keep `## Session log` as the last
section, because new entries are added at the end of the file.

## 6. Pick up where you left off

Next time you sit down, from any folder:

```bash
mem last
```

```text
Most recent project: web (~/Projects/shop/web)
Last touched: 2026-10-17T10:44

---
project: web
...
```

It shows the project you saved to most recently, followed by its full notes. To
see everything you touched this week:

```bash
mem last --since 7d
```

```text
2026-10-17T10:44  web                        ~/Projects/shop/web
2026-10-17T10:44  api                        ~/Projects/shop/api
```

## The daily routine

1. **Start of the session:** `mem last` (or `mem status` inside a project).
2. **During the session:** edit "Current focus" and "Next steps" when they change.
3. **End of the session:** `mem save "what I did, what is next"`.

That is the whole habit. Two minutes at the end of a session saves far more than
that at the start of the next one.

## Where to go next

- [How-to guides](how-to-guides.md): recipes for common situations, including
  using `mem` with AI coding assistants and moving projects.
- [Command reference](command-reference.md): every command and option.
- [AI drafting](ai-drafting.md): let Claude draft the entry from your git history.
- [Troubleshooting](troubleshooting.md): what the error messages mean.
