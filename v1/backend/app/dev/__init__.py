"""Development-only metadata package.

Never import these modules from production application code. They provide a
deterministic, clearly-synthetic demo dataset for manual end-to-end API testing
against the development PostgreSQL database (e.g. ``make seed-demo``).
"""