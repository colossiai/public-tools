
# #What does "user client" mean?

```

⏺ "use client" is a Next.js directive that marks a component (and its entire import subtree) as a client component — meaning it runs in the browser.

  By default, Next.js components are server components — they render on the server, ship zero JS to the browser, and cannot use React hooks or browser APIs.

  When you need useState, useEffect, event handlers (onClick, onChange), or browser APIs, you add "use client" at the top of the file to opt into client-side rendering.

  In this project:
  - layout.tsx — server component (no directive). Just static HTML shell, no interactivity needed.
  - page.tsx — client component ("use client"). Needs useState for auth, useEffect for fetching session, onClick handlers, etc.
  - All components in src/components/ — also client components, since they use hooks and event handlers.

```