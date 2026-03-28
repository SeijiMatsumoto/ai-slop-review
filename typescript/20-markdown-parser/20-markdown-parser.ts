// AI-generated PR — review this code
// Description: "Added lightweight markdown-to-HTML parser for rendering user content"

interface ParserOptions {
  allowHtml?: boolean;
  linkTarget?: string;
  maxLength?: number;
}

const defaultOptions: ParserOptions = {
  allowHtml: true,
  linkTarget: "_blank",
  maxLength: 50_000,
};

/**
 * Convert a markdown string to HTML.
 */
function markdownToHtml(input: string, options: ParserOptions = {}): string {
  const opts = { ...defaultOptions, ...options };

  let html = input;

  // Headings (h1 - h6)
  html = html.replace(/^(#{1,6})\s+(.+)$/gm, (_match, hashes, content) => {
    const level = hashes.length;
    return `<h${level}>${content}</h${level}>`;
  });

  // Bold: **text** or __text__
  html = html.replace(/(\*\*|__)(.*?)\1/g, "<strong>$2</strong>");

  // Italic: *text* or _text_
  html = html.replace(/(\*|_)(.*?)\1/g, "<em>$2</em>");

  // Strikethrough: ~~text~~
  html = html.replace(/~~(.*?)~~/g, "<del>$1</del>");

  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Code blocks: ```code```
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_match, lang, code) => {
    const langAttr = lang ? ` class="language-${lang}"` : "";
    return `<pre><code${langAttr}>${code}</code></pre>`;
  });

  // Blockquotes: > text
  html = html.replace(/^>\s+(.+)$/gm, "<blockquote>$1</blockquote>");

  // Unordered lists: - item or * item
  html = html.replace(/^[\-\*]\s+(.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

  // Links: [text](url)
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    `<a href="$2" target="${opts.linkTarget}">$1</a>`
  );

  // Images: ![alt](src)
  html = html.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    '<img src="$2" alt="$1" />'
  );

  // Horizontal rules: --- or ***
  html = html.replace(/^(\-{3,}|\*{3,})$/gm, "<hr />");

  // Line breaks: double newline becomes paragraph
  html = html.replace(/\n\n+/g, "</p><p>");
  html = `<p>${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, "");

  return html;
}

/**
 * Escape HTML entities for safe rendering in non-HTML contexts.
 */
function escapeHtml(text: string): string {
  const entities: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return text.replace(/[&<>"']/g, (char) => entities[char]);
}

/**
 * Strip all markdown formatting and return plain text.
 */
function stripMarkdown(input: string): string {
  let text = input;

  // Remove headers
  text = text.replace(/^#{1,6}\s+/gm, "");

  // Remove bold/italic
  text = text.replace(/(\*{1,2}|_{1,2})(.*?)\1/g, "$2");

  // Remove links, keep text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

  // Remove images
  text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1");

  // Remove code blocks
  text = text.replace(/```[\s\S]*?```/g, "");

  // Remove inline code
  text = text.replace(/`([^`]+)`/g, "$1");

  // Remove blockquotes
  text = text.replace(/^>\s+/gm, "");

  // Remove list markers
  text = text.replace(/^[\-\*]\s+/gm, "");

  // Remove horizontal rules
  text = text.replace(/^(\-{3,}|\*{3,})$/gm, "");

  return text;
}

/**
 * Validate that markdown input is safe to render.
 */
function validateMarkdown(input: string, maxLength: number = 50_000): { valid: boolean; error?: string } {
  if (input.length > maxLength) {
    return { valid: false, error: `Input exceeds max length of ${maxLength}` };
  }

  // Check for excessively nested patterns
  const nestingPattern = /(\*{1,2}|\_{1,2}){5,}/;
  if (nestingPattern.test(input)) {
    return { valid: false, error: "Excessively nested formatting detected" };
  }

  return { valid: true };
}

// --- Example usage ---

const markdown = `
# Welcome to My Blog

This is a **bold statement** and this is *italic text*.

Here's some \`inline code\` and a [link](https://example.com).

## Code Example

\`\`\`typescript
function hello(name: string): string {
  return \`Hello, \${name}!\`;
}
\`\`\`

> This is a blockquote with important info.

- Item one
- Item two
- Item three

---

Check out this image: ![logo](https://example.com/logo.png)

Have a ~~bad~~ great day!
`;

const html = markdownToHtml(markdown);
console.log(html);

export { markdownToHtml, escapeHtml, stripMarkdown, validateMarkdown };
export type { ParserOptions };
