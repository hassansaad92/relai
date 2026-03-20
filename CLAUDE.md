# Project Instructions for Claude

## Git Workflow

**MANDATORY**: Before making ANY code changes or commits, follow the `/git-workflow` skill.

Key rules:
- Never commit to or push to `main` branch
- Always create a feature branch before making changes
- See `.claude/skills/git-workflow/SKILL.md` for complete workflow details

## Schema Rebuild

**MANDATORY**: When modifying `data/schema.sql`, follow the `/schema-rebuild` skill.

Key rules:
- Always review and update `drop_all_tables.sql`, `clear_all_data.py`, and `repopulate_supabase_data.py` to stay in sync
- The rebuild flow is: `drop_all_tables.sql` → `schema.sql` → `repopulate_supabase_data.py`
- See `.claude/skills/schema-rebuild/SKILL.md` for complete details

## Asana Workspace

**MANDATORY**: When working in the RelAI directory, follow the `/asana-workspace` skill.

Key rules:
- Only manipulate items in the RelAI workspace
- Do NOT create, update, or delete items in the Personal Workspace
- See `.claude/skills/asana-workspace/SKILL.md` for complete details
