# AI drafting

`mem save --ai` writes your session entry for you. It reads your recent git
activity, asks Claude to summarise it, shows you the draft, and saves it only if
you say so. It is optional. Everything else in `mem` works without it.

## What you need

1. **An Anthropic API key.** This is separate from a Claude app login. Create
   one at [console.anthropic.com](https://console.anthropic.com). Using the API
   costs a small amount of money. A draft is capped at 300 tokens of output, so a
   single use costs a fraction of a cent at current prices, but check your own
   plan and the current pricing.
2. **The key in your environment**, in the terminal where you run `mem`:

   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

   To keep it for future terminals, add that line to your shell's startup file,
   such as `~/.bashrc` or `~/.zshrc`. `mem` only checks that the variable is set.
   The Anthropic library reads and uses it, and `mem` never stores or prints it.
3. **A git project with some history.** The draft is built from your commits and
   changes, so a project without git has nothing to summarise.

Never commit your key. If you use a `.env` file, make sure `.env` is in your
`.gitignore`. The repository includes `.env.example` as a template, but `mem` does
not read `.env` files itself, so load it yourself (for example with
`set -a; source .env; set +a`).

## How to use it

Work, commit as you normally would, then run:

```bash
mem save --ai
```

You will see something like this (the wording is written by the model, so yours
will differ):

```text
--- Drafted entry ---
Added cart total calculation and a unit test for tax rounding. Rounding still
fails for amounts ending in .5. Next: fix the rounding and cover discounts.
---------------------
Save this entry? [y/N/edit]:
```

| You type | What happens |
| --- | --- |
| `y` | The draft is saved to the Session log as it is |
| `edit` | You type your own version, and finish with an empty line. If you type nothing, the draft is kept |
| anything else, or just Enter | Nothing is saved |

Nothing is ever written without your answer. If the terminal closes or has no
input, the draft is discarded.

## What is sent to Anthropic

Only this, and only when you run `mem save --ai`:

- The one-line summary of each commit from the **last 12 hours** (short hash and
  commit subject), limited to the project folder.
- A summary of your uncommitted changes: the **names of changed files** and how
  many lines changed in each. File contents are not sent.
- If the repository has no commits yet, a list of the files git sees as new or
  changed.

`mem`'s own `.memory` files are left out. The text is cut off at 8,000
characters. Nothing else leaves your machine: your notes file is not sent.

Because commit messages and file names are included, do not put secrets in them,
and think twice before using `--ai` on a project that is under strict
confidentiality rules.

## Settings

All optional, set as environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `MEM_MODEL` | `claude-sonnet-5-5` | Which Claude model writes the draft |
| `MEM_MAX_TOKENS` | `300` | Longest draft allowed |
| `MEM_TIMEOUT_SECONDS` | `60` | How long to wait before giving up |
| `MEM_MAX_RETRIES` | `2` | Automatic retries if the request fails |

Example, using a different model for one run:

```bash
MEM_MODEL=claude-haiku-5-5 mem save --ai
```

If a draft ends with `[draft cut off at the token limit...]`, the model ran out of
room. Raise `MEM_MAX_TOKENS`, or choose `edit` and finish it yourself.

## Safety

Commit messages and file names can come from other people, for example in a
shared repository, so they are treated as untrusted text. They are wrapped in
markers, any marker text inside them is neutralised, and they are sent in a
separate message from the instructions, which tell the model to treat them as
data and never follow them. This lowers the risk of a hostile commit message
steering the draft, but it cannot remove it, which is why you always see and
confirm the draft before it is saved.

## When it does not work

- `The --ai flag needs an ANTHROPIC_API_KEY environment variable to be set.` The
  variable is missing in this terminal. Run the `export` line again.
- `Claude API call failed: ...` followed by a message from the service. Common
  causes are an invalid key, no credit on the account, a model name that does not
  exist (check `MEM_MODEL`), or no internet connection.
- The draft is thin or vague. If there were no commits in the last 12 hours and no
  uncommitted changes, the model has almost nothing to base it on. Commit
  something first, or use `mem save "your own note"`.
- The draft is generic or off-topic. You ran it outside a git project, so there
  was no history to read. Run it from inside a git repository.

See [Troubleshooting](troubleshooting.md) for other messages.
