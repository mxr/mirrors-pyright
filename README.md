# pyright mirror

Mirror of pyright for pre-commit.

For pre-commit: see https://github.com/pre-commit/pre-commit

For pyright: see https://github.com/microsoft/pyright

### Background

Wrappers such as [`pyright-python`](https://github.com/RobertCraigie/pyright-python) install `node` and `pyright` at runtime. This is incompatible with runners like https://pre-commit.ci which need all setup to happen during hook installation. Also this makes the behavior more predictable.

Further, `pyright` is a node package, and other wrappers maintain `language: node` so you can't specify any of your python additional dependencies.

This wrapper works around both those issues. Further a daily cron releases new versions in lockstep with `pyright` releases. `node` is pinned to an LTS (24.20.0)

### Using pyright with pre-commit

Add this to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/mxr/mirrors-pyright
    rev: ''  # Use the sha / tag you want to point at
    hooks:
    -   id: pyright
```

`pyright` will run in `pre-commit's` virtual env so it won't find your project dependencies by default. To work around that, override `additional_dependencies` with your dependencies. You can also automatically keep the list up to date by using the https://github.com/mxr/sync-typing-deps hook (which uses heuristics).

```yaml
-   repo: https://github.com/mxr/mirrors-pyright
    rev: ''  # Use the sha / tag you want to point at
    hooks:
    -   id: pyright
-   repo: https://github.com/mxr/sync-typing-deps
    rev: ''  # Use the sha / tag you want to point at
    hooks:
    -   id: sync-typing-deps
```
