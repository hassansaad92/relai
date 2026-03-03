# Git Workflow

**CRITICAL**: This workflow MUST be followed for all code changes in branch-protected repositories.

## Rules

1. **Never push directly to `main`**: All changes must go through feature branches
2. **Always create a new branch** before making any code changes:
   - Feature branches: `feature/description`
   - Bug fixes: `fix/description`
   - Documentation: `docs/description`
   - Refactoring: `refactor/description`
3. **Before making changes**:
   - Check current branch with `git branch --show-current`
   - If on `main`, create and checkout a new branch
4. **After committing**:
   - Push the branch to remote: `git push -u origin <branch-name>`
   - **NEVER** push to main
5. **Use pull requests**: All changes to main must go through PR review

## Workflow Steps

When making changes:

1. **Check current branch**:
   ```bash
   git branch --show-current
   ```

2. **If on main, create feature branch**:
   ```bash
   git checkout -b feature/descriptive-name
   ```

3. **Make changes, stage, and commit**:
   ```bash
   git add <files>
   git commit -m "Your message"
   ```

4. **Push to feature branch**:
   ```bash
   git push -u origin feature/descriptive-name
   ```

5. **Create PR** to merge into main (use `gh pr create` if available)

## Before ANY Commit

- Verify you're not on `main` branch
- If on `main`, stop and create a feature branch first
- Only proceed with commits when on a feature branch
