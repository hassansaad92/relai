# Asana Workspace Management

**CRITICAL**: When working in the RelAI directory, only manipulate Asana items in the **RelAI workspace**.

## Workspace Identification

- **RelAI Workspace**: named "RelAI"
- **Personal Workspace**: named "Personal Workspace" (DO NOT USE for this project)

## Rules

1. **RelAI workspace only**: All Asana operations (tasks, projects, portfolios) must be performed in the RelAI workspace
2. **Verify before acting**: Always check the workspace context before creating or modifying any Asana items
3. **No Personal Workspace access**: Do NOT create, update, delete, or manipulate any items in the Personal Workspace when working on RelAI project

## Operations Covered

This rule applies to ALL Asana operations including:
- Creating tasks, projects, or portfolios
- Updating existing tasks or projects
- Deleting or archiving items
- Adding comments or attachments
- Managing assignments or due dates
- Any other Asana API operations

## Verification Steps

Before any Asana operation:

1. **Identify the workspace**: Ensure you're using the RelAI workspace (named "RelAI")
2. **Double-check parameters**: Verify workspace parameter in API calls
3. **Filter results**: When searching or listing items, filter to RelAI workspace only

## Examples

**Correct** - Creating task in RelAI workspace:
```
workspace: <gid of "RelAI" workspace>
project_id: <project-in-relai-workspace>
```

**Incorrect** - Using Personal Workspace:
```
workspace: <gid of "Personal Workspace"> ❌ WRONG
```
