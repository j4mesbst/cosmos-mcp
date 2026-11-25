---
name: heroui
description: Build and verify React web designs with HeroUI v3. Use for Cosmos web projects with HeroUI buttons, links, cards, forms, dialogs and other reusable controls.
---
# HeroUI v3 in Cosmos
Use @heroui/react and @heroui/styles with React 19 and Tailwind CSS 4. Read the version-matched examples in node_modules/@heroui/react/docs/components. Import tailwindcss before @heroui/styles. Use the compound API such as Card.Header and Modal.Dialog. Avoid the v2 provider.

Use HeroUI for each interactive control and reusable UI element with a matching primitive. In particular use Button, Link, input components, Switch, Card and Modal from @heroui/react. Use semantic HTML to organize the page and compose original illustrations from noninteractive shapes. Do not build native buttons with copied HeroUI classes.

Set type, spacing and colors through CSS and HeroUI variants. Keep the brand distinct from the library defaults. Check keyboard activation, focus and app transitions. Register every UI source, package.json and the HeroUI stylesheet with Cosmos. Verify the actual page using audit-web.cjs and a real interaction.
