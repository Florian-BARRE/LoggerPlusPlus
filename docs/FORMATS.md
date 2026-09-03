# Formats and the auto-width grammar

## The auto-width token

A standard Loguru format field looks like `{level.name:<8}`. LoggerPlusPlus extends this with a
grow-to-fit `auto` width and an optional truncation clause:

```text
{field:<align><width>[cap~trunc]}
```

| Part    | Values                    | Default | Meaning                                          |
|---------|---------------------------|---------|--------------------------------------------------|
| `field` | `identifier`, `level.name`, `extra[key]`, dotted paths | — | which record value to render |
| `align` | `<` `>` `^`               | `<`     | left / right / center                            |
| `width` | `auto` or an integer      | —       | grow-to-fit, or a fixed width                    |
| `cap`   | integer inside `[...]`    | none    | maximum width                                    |
| `trunc` | `left` `right` `middle`   | none    | which side to cut on overflow (adds an ellipsis) |

Examples:

```text
{identifier:<auto}                grow to fit, left-aligned
{identifier:^auto~middle}         grow to fit, centered, cut the middle if capped later
{identifier:<auto[18~middle]}     grow to fit but never wider than 18, cut the middle
{name:<20~right}                  fixed width 20, cut the tail
{extra[service]:>auto[12~left]}   right-aligned, capped at 12, cut the head
```

### How `auto` behaves

`auto` uses a process-global registry that remembers the **longest value seen so far** for each
field. Every line is padded to that maximum, so a column grows to fit but never shrinks and never
jitters. `LoggerClass` pre-registers its identifier, so the first line is already aligned to it.

Bare (`identifier`) and wrapped (`extra[identifier]`) spellings of the same field share one width
bucket, so seeding one aligns the other.

### Truncation

When a value is longer than the effective width and a `trunc` mode is set, it is shortened with a
single ellipsis (`…`) and padded to the width:

| Mode     | `VeryLongServiceName` at width 12 |
|----------|-----------------------------------|
| `right`  | `VeryLongSer…`                    |
| `left`   | `…LongServiceName`* (tail kept)   |
| `middle` | `VeryL…Name`                      |

*the left mode keeps the last `width - 1` characters.

Without a `trunc` mode, an overlong value is hard-cut to the width (Loguru precision formatting),
with no ellipsis.

> Widths are measured in **terminal cells** (visual width), using the standard library only: an
> East-Asian wide/full-width glyph (for example CJK) counts as two cells and a combining or
> zero-width mark counts as zero, so those columns align correctly. Control characters and ANSI
> escape sequences are stripped from field values before measuring and rendering, so a stray
> newline or colour code cannot break or misalign a log line.
>
> Known limitation: width is measured per code point, not per grapheme cluster. A ZWJ emoji
> sequence (such as a family emoji) or an emoji with a skin-tone modifier is drawn as a single
> two-cell glyph but is measured as two cells per component, so a value containing such emoji can
> reserve a slightly-too-wide column. A precise fix would require grapheme segmentation (a
> third-party dependency), which this package deliberately avoids.

## Ready-made formats

Each format subclasses `str`: an instance *is* a format string, so it can be passed directly to
`add(format=...)`. All are colorized by default and use middle-truncated auto widths for their
variable fields.

| Format          | Fields (in order)                                                  |
|-----------------|--------------------------------------------------------------------|
| `ClassicFormat` | time · level · `[identifier]` · `name:line` · message              |
| `ShortFormat`   | time · level · `[identifier]` · message                            |
| `OpsFormat`     | time · level · `[identifier]` · PID/TID · message                  |
| `DebugFormat`   | time · level · `[identifier]` · PID/TID · `name:line` · message    |
| `MinimalFormat` | `identifier -> message`                                            |
| `PlainFormat`   | Short layout, uncolored by default — for file sinks                |
| `FileFormat`    | Classic layout (with `name:line`), uncolored by default — for file sinks |

### Overrides

`format()` (invoked by instantiating the class) accepts keyword overrides. Common ones:

| Override            | Type          | Default    | Applies to        |
|---------------------|---------------|------------|-------------------|
| `colorized`         | `bool`        | `True`     | all formats       |
| `level_width`       | `int \| str`  | `8`        | all except Minimal|
| `identifier_width`  | `int \| str`  | `"auto"`   | all formats       |
| `sep`               | `str`         | `" \| "`   | all except Minimal|
| `name_width`, `line_width` | `int \| str` | `"auto"` | Classic, Debug (accepted by Short for signature parity) |
| `process_name_width`, `process_id_width`, `thread_name_width`, `thread_id_width` | `int \| str` | `"auto"` | Ops, Debug |

```python
from loggerplusplus import formats

formats.ClassicFormat(colorized=False)                 # plain, for file sinks
formats.ShortFormat(level_width=5, sep="  ")           # tighter layout
formats.DebugFormat(identifier_width=20)               # fixed identifier column
```

### Theming

Every shipped format accepts a `theme` override to recolor its segments without rewriting the
format. The default reproduces the historical colors exactly, so omitting `theme` changes nothing.

```python
from loggerplusplus import Theme, formats

theme = Theme(timestamp="cyan", identifier="magenta", separator="dim")
formats.ShortFormat(theme=theme)
```

`Theme` is a frozen dataclass with the color roles `timestamp`, `identifier`, `name`, `line`,
`process`, `thread`, and `separator` (loguru markup color names, `#rrggbb` hex, or 8-bit codes). An
invalid color is rejected at `Theme(...)` construction with a clear, field-named error, rather than
crashing loguru later inside `add()`. The log level and message stay on loguru's dynamic `<level>`
color and are intentionally not themeable. With `colorized=False`, all color tags are dropped
(including the theme's), yielding a plain template suitable for file sinks.

### Selecting by name

Because a format is chosen by class name, a service can drive it from configuration:

```python
import os
from loggerplusplus import formats

name = os.environ.get("LOGGING_LPP_FORMAT", "DebugFormat")
fmt = getattr(formats, name, formats.DebugFormat)()
```

### Adding a format

Subclass `BaseFormat` and implement `format(cls, **overrides) -> str`, composing segments with the
shared builders (`cls._timestamp()`, `cls._level(width)`, `cls._identifier(width)`,
`cls._process_thread(...)`, `cls._location(...)`, `cls._message()`, `cls._sep(...)`) and
`cls.build(*parts)`. Add the class to `formats/__init__.py` `__all__`. Never rename an existing
format — downstream selects it by name.
