# 20 — Markdown Parser (TypeScript)

**Categories:** ReDoS, XSS, Edge Cases, Parsing Order

## Bug 1: No HTML Sanitization — XSS via Raw HTML in Markdown

The `allowHtml` option defaults to `true`, but there is no code that actually acts on this option — raw HTML in the input is passed straight through to the output. An attacker can inject `<script>alert('xss')</script>` or `<img onerror="..." src="x">` into the markdown, and it will appear verbatim in the generated HTML. The `escapeHtml()` utility function exists but is never called within `markdownToHtml()`.

**Fix:** When `allowHtml` is false (which should be the default), sanitize the input before processing:

```typescript
if (!opts.allowHtml) {
  html = escapeHtml(html);
}
```

Or better, always sanitize and use an allowlist of safe HTML tags.

## Bug 2: ReDoS via Catastrophic Backtracking in Bold/Italic Patterns

The bold regex `/(\*\*|__)(.*?)\1/g` and italic regex `/(\*|_)(.*?)\1/g` use `.*?` (lazy match) with backreferences. On input like `**bold **bold **bold **bold **bold **bold **` (many unclosed bold markers), the regex engine backtracks exponentially trying to match. An attacker can submit a carefully crafted string that causes the parser to hang for seconds or minutes, creating a denial-of-service condition.

**Fix:** Use more constrained patterns that cannot backtrack catastrophically:

```typescript
// Bold: match non-greedy but exclude the delimiter character
html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
```

## Bug 3: Parsing Order Breaks Nested Formatting (Bold Inside Italic)

Bold and italic are processed sequentially: bold first, then italic. This means `***bold and italic***` is first converted to `*<strong>bold and italic</strong>*` by the bold rule. Then the italic rule tries to match `*...*` and picks up the `*` delimiters surrounding the `<strong>` tag, producing garbled nested output. Similarly, `*italic with **bold** inside*` breaks because the bold pass consumes the inner `**` first, and then the italic pass sees mismatched `*` delimiters.

**Fix:** Handle the combined `***text***` case first with a dedicated rule, or use a proper token-based parser instead of sequential regex replacements:

```typescript
// Handle bold+italic first
html = html.replace(/\*{3}(.+?)\*{3}/g, "<strong><em>$1</em></strong>");
// Then bold, then italic
```

## Bug 4: Images Processed After Links — Image Syntax Consumed as Link

The image regex (`![alt](src)`) is applied after the link regex (`[text](url)`). Since the link pattern `\[([^\]]+)\]\(([^)]+)\)` also matches the `[alt](src)` portion of `![alt](src)`, images are first converted into `!<a href="src">alt</a>` by the link rule, and the image rule never gets a chance to match. All images render as broken text with a leading `!`.

**Fix:** Process images before links:

```typescript
// Images first
html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />');
// Then links
html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, `<a href="$2">$1</a>`);
```

## Bug 5: No Handling of Null/Undefined/Empty Input

The function has no guard for empty, null, or undefined input. Calling `markdownToHtml("")` produces `<p></p>` (though the cleanup regex should remove it, the wrapping creates an empty paragraph first). Calling `markdownToHtml(null as any)` or `markdownToHtml(undefined as any)` throws a runtime error because `.replace()` is called on a non-string. The `maxLength` option is defined but never checked inside `markdownToHtml()` — the `validateMarkdown()` function exists separately but is never called.

**Fix:** Add input validation at the start:

```typescript
function markdownToHtml(input: string, options: ParserOptions = {}): string {
  if (!input || typeof input !== "string") {
    return "";
  }
  if (opts.maxLength && input.length > opts.maxLength) {
    throw new Error(`Input exceeds max length of ${opts.maxLength}`);
  }
  // ...
}
```

## Bug 6: Link `href` Not Sanitized — `javascript:` Protocol XSS

The link regex blindly inserts the URL into an `href` attribute: `<a href="$2">`. An attacker can use markdown like `[click me](javascript:alert('xss'))` to create a link that executes JavaScript when clicked. There is no validation or sanitization of the URL protocol.

**Fix:** Validate that URLs use safe protocols:

```typescript
function sanitizeUrl(url: string): string {
  const allowed = ["http:", "https:", "mailto:"];
  try {
    const parsed = new URL(url);
    if (!allowed.includes(parsed.protocol)) {
      return "#";
    }
    return url;
  } catch {
    return url; // relative URL, allow
  }
}
```
