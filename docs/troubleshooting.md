# Troubleshooting

Find the message you saw, and what to do about it. Messages that begin with
`Error:` are expected problems, and the command exits with code 1.

## Installing

### `mem: command not found`

The folder `uv` installs commands into is not on your PATH yet.

```bash
uv tool update-shell
```

Then open a new terminal. If it still fails, run `uv tool list`. If `project-memory`
is not listed, install again with `uv tool install .` from the cloned folder.

### `uv: command not found`

Install `uv` first. See [Getting started](getting-started.md#1-install).

### `requires a different Python` or a Python version error

`mem` needs Python 3.12 or newer. `uv` can fetch one for you:

```bash
uv python install 3.12
```

then install `mem` again.

### I updated the repository but `mem` still behaves the old way

`uv` installs from a copy. Refresh it:

```bash
cd ~/tools/project-memory
git pull
uv tool install . --reinstall
```

## Starting a project

### `Warning: ... Initialize here anyway? [y/N]`

`mem init` thinks the folder may be the wrong place. Read the reason shown. If you
are in a folder that holds projects, answer `n` and run `mem init` inside one of
them. If you really want to track this folder, answer `y`, or run `mem init --yes`.
See [Where to run mem init](how-to-guides.md#where-to-run-mem-init).

### `Error: No input available to confirm. Pass --yes to skip the warning.`

`mem init` wanted to ask a question and there was no terminal to answer it, for
example when run from a script. Use `mem init --yes`.

### `Error: ... already exists. This project is already tracked.`

The folder already has `.memory/STATE.md`. You do not need to run `init` again.
Use `mem save`.

### I ran `mem init` in the wrong folder

Delete the folder it created and carry on:

```bash
rm -r .memory
```

The mistaken entry then disappears from `mem list` and `mem last` by itself.

## Saving and reading

### `Error: No memory file found at ... Run 'mem init' first.`

You are not inside a tracked project, so `mem` found no `.memory` folder in the
current folder or any parent. Check where you are with `pwd`, `cd` into the project
and try again, or run `mem init` there.

### Notes went into the wrong project

A parent folder is tracked, so `mem` used its `.memory` instead of the one you
expected. Check by running `mem status` in the project and reading the heading. To
fix it, run `mem init` inside the project so it gets its own notes, and move the
entries that belong to it by hand. See
[Where to run mem init](how-to-guides.md#where-to-run-mem-init).

### `Error: State file is missing its frontmatter block.` and similar

The top of `STATE.md` was edited and no longer has the shape `mem` expects. It
must start with a line containing only `---`, contain a `last_updated:` line, and
close with another `---`:

```markdown
---
project: web
status: in-progress
last_updated: 2026-10-17T10:44
---
```

Put those lines back and run `mem save` again.

### `Error: No note provided.`

You ran `mem save` with no text and pressed Enter at the prompt. Give a note, for
example `mem save "what I did"`.

### `Error: Pass either a note or --ai, not both.`

Use one or the other.

### My multi-line note looks odd

Notes are saved as a single bullet, with extra lines indented under it, and blank
lines are removed. This is on purpose, so a note can never break the structure of
the file.

## Finding projects

### `mem last` or `mem list` does not show a project I know I have

They show only projects whose notes exist on this machine, and they print a note
on standard error saying how many were hidden. Check that the project still has
`.memory/STATE.md`. A project you moved or deleted is hidden until you run
`mem save` in its new location.

### `Error: No projects tracked yet. Run 'mem init' inside a project first.`

Your project list is empty. Run `mem init` in a project.

### `Error: None of the N tracked project(s) exist on this machine.`

Every entry points to a folder that is not here. This usually happens after
copying a project list from another computer. Run `mem init` in a project here.

### `Error: Invalid duration '5x'. Use a number followed by m, h, or d`

`--since` needs a whole number and a unit: `m` minutes, `h` hours, `d` days, for
example `--since 7d`.

## The project list

### `Registry file at ... is corrupted` or `has a malformed entry`

`projects.json` was damaged or edited into something invalid. The message gives its
location. You have two choices:

- Open it and fix the JSON. Each entry needs `name`, `path` and `last_updated`
  (formatted like `2026-10-17T10:44Z`).
- Move it aside and let `mem` rebuild it:

  ```bash
  mv ~/.config/mem/projects.json ~/.config/mem/projects.json.bak
  ```

  Then run `mem save "Rebuilt the project list"` inside each project. A save adds
  the project back to the list. Your notes are not affected.

### Could not acquire lock

`Error: Could not acquire lock on ....lock within 5s. Another 'mem' process may be
stuck.`

Another `mem` command was running and did not finish in time. Check for one:

```bash
ps aux | grep '[m]em '
```

If one is stuck, end it, and try again. If nothing is running, the `.lock` file
left behind is harmless to delete.

## AI drafting

See [AI drafting](ai-drafting.md#when-it-does-not-work) for these:

- `The --ai flag needs an ANTHROPIC_API_KEY environment variable to be set.`
- `Claude API call failed: ...`
- `MEM_MAX_TOKENS must be an integer` and similar messages about a bad setting
- A draft that is thin, vague or off-topic

## Syncing

See [Team sync](team-sync.md#errors).

## Still stuck

Run the command again and copy the full output, including the line starting with
`Error:`, then open an issue at
<https://github.com/mayhemds/project-memory/issues>. Say which operating system you
use and the output of `uv tool list`.
