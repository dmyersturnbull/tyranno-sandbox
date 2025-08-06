# GitHub workflows and actions

## Organization

There are
[Composite Actions](https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action)
under [`.github/actions/`](actions/).
Additionally, some [workflows](workflows/) are prefixed with `_`.
These are reusable workflows, which are only triggered via `workflow_call`.
The reusable workflows need multiple jobs, or are simply to specialized to be actions.

## Notes

GitHub Actions have a lot of sharp objects.

### `github.workflow` context variable

In a `workflow_call`-ed job,
[`${{ github.workflow }}` is the **caller's name**](https://github.com/orgs/community/discussions/30708#discussioncomment-3518412).

### When expressions are evaluated

Be careful when using `${{}}` inside a shell `run` block;
they're not evaluated at the same time.
Enclose them in single quotes to remind you that the shell will only see the literal;
e.g. `if [[ "$variable" == '${{ inputs.rerun }}'`.

### Truthy and falsey strings

Values in `${{}}` are typed, but they're implicitly coerced to boolean.
A string is true iff it's non-empty, meaning that `'false'` is actually true.
This is important because some values are always strings:
inputs to actions, outputs from actions, and anything from Bash.

The best practice for getting a boolean from Bash is to write to `$GITHUB_OUTPUT`
**only** if the value is true; leave the variable unset if its value is false.
For example:

```yaml
- id: detect-changes
  run: |
    [[ -z "$(git status --porcelain)" ]] || echo "changes=true" >> $GITHUB_OUTPUT
- if: ${{ steps.detect-changes.outputs.changes }}
```

Otherwise, you'll need `${{ steps.detect-changes && steps.detect-changes != 'false' }}`,
and it's very easy to make a mistake.

### Shell

**`shell: bash` is different from the default Bash shell.**

GitHub workflows use Bash as the default shell.
However, specifying `shell: bash` explicitly turns on `pipefail`.
Terrible behavior aside, always specify `shell: bash`.
In a workflow, you can use `defaults: shell: bash`.
But composite actions don't currently support `defaults`, so you'll need to specify it per step.

See:

- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#defaultsrunshell
- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#exit-codes-and-error-action-preference

### Context, variables, and expressions

See:

- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/accessing-contextual-information-about-workflow-runs
- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/evaluate-expressions-in-workflows-and-actions
