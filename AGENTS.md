# Agents

### Permissions

You may:

- list or read files (excluding those in `.aiignore`)
- run commands listed [below](#commands)
- suggest changes

You must get express approval to:

- create, delete, rename, or modify files
- run commands not listed [below](#commands)

Unless expressly told otherwise, you must request express approval each time.
You must list either the files and specific changes or the exact commands.

# Commands

- Format (limited to modified files): `just format`
- Auto-fix some lint issues `just fix`
- Find and list lint issues: `just check-ruff`
- Run fast tests: `just test-fast`

## Conventions

- Assume Python 3.14+ and modern features:
  - Use PEP 695-style generic syntax (e.g. `class MyClass[T]`).
  - Use `pathlib` instead of `os.path`.
  - Use f-strings instead of `str.format`.
  - Use `|` to join types (e.g. `str | None`).
- Use type annotations everywhere except `self` and `cls`.
- Where possible, use `@dataclass(frozen=True, slots=True)` or an equivalent.
- A class should either hold data or do something, not both.
- A function or method should do only one thing.
- Prefer a Scala-inspired blend of functional and object-oriented programming.
  - Write immutable classes.
  - Chain or compose methods to transform data.
- Apply inversion of control.
- Let exceptions bubble up or catch and re-raise.
  Don't arbitrarily wrap code in `try` blocks.
- Omit obvious docstrings and comments.
  - Use docstrings to (e.g.) explain non-obvious parameters and edge cases.
  - Use comments to explain tricky or unusual code.
- Prefer Ruff / Black style, including double quotes.
- Don't add empty lines for spacing in function or method bodies.
  If a function or method is that long, it should be split up.
