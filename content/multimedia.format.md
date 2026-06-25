# Multimedia content format

Use `multimedia.md` for video and podcast cards. Categories are level-2 headings; each media item is a level-4 heading followed by metadata and a thumbnail link.

```md
#### “<Title>”
- Language: <flag emoji>
- Type: <Optional type>
- Program: <Optional programme>
- Event: <Optional event>
- Institution: <Optional institution>
- Topic: <Comma-separated topic tags>
- Duration: <N min>
- Uploaded: <DD Month YYYY>
- Location: <Optional location>
- Description: <Optional long text; use \n\n for intentional paragraphs>

[▶️ ![Thumbnail](<thumbnail URL>)](<media URL>)
```

Rules:
- Sine qua non: every video or podcast must include `- Duration: <N min>` before `- Uploaded:`.
- Calculate duration from the final linked media URL, rounding to the nearest whole minute.
- Keep `Topic` comma-separated so tags render consistently.
- Use YouTube thumbnail URLs that match the video ID whenever possible.
