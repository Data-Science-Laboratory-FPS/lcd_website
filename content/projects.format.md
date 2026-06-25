# Projects content format

Use `projects.md` for project cards. Each project is separated by `---`.

```md
### <emoji> <ACRONYM or name>: <Expanded title>
meta: <Project type / scope>
website: <Optional URL>
funding: <Optional funding partner or programme>
summary: <One paragraph summary>

---
```

Rules:
- `meta` and `summary` are required.
- `website` and `funding` are optional; omit them when unavailable.
- Keep summaries as a single paragraph so the parser can read the complete value.
