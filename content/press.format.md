# Press content format

Use `press.md` for press cards. Each article is a level-4 heading followed by Spanish metadata fields.

```md
#### “<Headline>”
- Fecha: <DD/MM/YYYY>
- URL: <Article URL>
- Miniatura: <Optional local image path>
- Tipo de proyecto: <Project/category>
- Etiqueta clínica: <Clinical tag>
- Servicio hospitalario: <Care area / service>
- Resumen: <One paragraph summary>
```

Rules:
- `Fecha`, `URL`, `Tipo de proyecto`, `Etiqueta clínica`, `Servicio hospitalario`, and `Resumen` are required.
- `Miniatura` is optional and should point to a stable local asset when automatic thumbnails are not suitable.
- Keep summaries concise and in one paragraph for parser compatibility.
