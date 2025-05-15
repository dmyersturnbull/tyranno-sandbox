# GitHub workflows

## Organization

Workflows prefixed with `_` are only triggered via `workflow_call`.
These could be later be turned into
[Composite Actions](https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action).

## Notes

### Weirdness

- In a `workflow_call`-ed job,
  [`${{ github.workflow }}` is the **caller's name**](https://github.com/orgs/community/discussions/30708#discussioncomment-3518412).

### Context, variables, and expressions

See:

- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/accessing-contextual-information-about-workflow-runs
- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/evaluate-expressions-in-workflows-and-actions

### Default shell

All workflows should have `defaults: shell: bash`.
Confusingly – even though Bash is used anyway –setting `shell: bash` adds `pipefail`.

See:

- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#defaultsrunshell
- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#exit-codes-and-error-action-preference
