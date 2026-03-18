❯ ~/.claude/memory/MEMORY.md is the only entry point to search your global memory?

```
⏺ Yes, MEMORY.md is the main entry point. Here's how the memory system works:

  How Memory Loading Works

  1. MEMORY.md is automatically loaded into every conversation context
  2. Only the first 200 lines of MEMORY.md are loaded (to manage context size)
  3. Other files (like java.md, go.md) are NOT automatically loaded

  Why Separate Files Still Help

  Even though other files aren't auto-loaded, they're useful for:

  1. Organization: Keep related preferences together
  2. Future reference: I can read them when working on language-specific tasks
  3. Avoiding truncation: Keep MEMORY.md concise so nothing important gets cut off after line 200

  Best Practice Structure

  MEMORY.md (auto-loaded, keep under 200 lines):
  - High-level summaries
  - Most important preferences that apply broadly
  - Quick reference bullets

  Topic files (java.md, go.md, etc.):
  - Detailed preferences
  - I can read these when context is relevant
  - Reference them in MEMORY.md so I know they exist

  Current Setup

  Your MEMORY.md now lists "Java: Maven, JMH" and "Go: samber/lo" - those key preferences are in the auto-loaded file, which is perfect. The separate files provide detail if
  needed later.
```