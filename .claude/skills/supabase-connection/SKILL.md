# Supabase Connection

## Connection String Format

```
postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
```

## Project Details

- **Reference ID** (`project_ref`): `grkdykxrckzusbgkgsuk` (extracted from `SUPABASE_RELAI_URL` env var)
- **Full connection string**: `postgresql://postgres:[PASSWORD]@db.grkdykxrckzusbgkgsuk.supabase.co:5432/postgres` (replace `[PROJECT-ID]` in the format above with the Reference ID)
- **Password**: from env var (not stored here)

## Python

Use `psycopg2` to connect:

```python
import psycopg2
import os

conn = psycopg2.connect(
    f"postgresql://postgres:{os.environ['SUPABASE_PASSWORD']}@db.grkdykxrckzusbgkgsuk.supabase.co:5432/postgres"
)
```
