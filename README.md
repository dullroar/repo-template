# repo-template

The template for new repositories. It gives every repository the same layout for humans and for coding agents.

## Use it

1. On GitHub, select **Use this template**. Or run `gh repo create <name> --template dullroar/repo-template`.
2. Follow the "Template-only rules" section of [AGENTS.md](./AGENTS.md).
3. Delete the example files and the template-only section.

## Layout

| Path | Purpose |
| --- | --- |
| [AGENTS.md](./AGENTS.md) | Rules for agents. `CLAUDE.md` points to it. |
| [docs/](./docs/README.md) | Documents for humans. |
| [memory/](./memory/AGENTS.md) | Facts for agents. One file for each fact. |
| [plans/](./plans/AGENTS.md) | Work plans, run by agents. |
| [scripts/](./scripts/AGENTS.md) | Scripts for agents and CI. |
| `Dockerfile` | Ubuntu environment for the project. Delete it for Windows-only projects. |

## Checks

```bash
python3 scripts/build_indexes.py   # rebuild the generated indexes
python3 scripts/check_context.py   # run all checks
```

## Run the plans

Use [ralph-looper](https://github.com/dullroar/ralph-looper). See [docs/ralph-looper.md](./docs/ralph-looper.md).

## License

MIT. See [LICENSE](./LICENSE).
