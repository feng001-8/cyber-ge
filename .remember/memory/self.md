# Dependency and Environment Issues

Mistake: Running dev server before dependencies are installed
Wrong: `npm run dev` fails with `sh: astro: command not found`
Correct:
 Run `npm ci` (or `npm install`) in the project root first, then run `npm run dev`.

Mistake: npm install fails due to npm cache ownership
Wrong: `npm ci` fails with EPERM and root-owned files under `~/.npm`
Correct:
 Fix ownership once with `sudo chown -R $(id -u):$(id -g) ~/.npm`, then reinstall dependencies.

Mistake: Git merge blocked by local generated `.astro` changes
Wrong: merge aborts with "local changes would be overwritten" on `.astro/content-assets.mjs` and `.astro/data-store.json`
Correct:
 On the branch where merge runs, discard generated-file changes first with `git restore .astro/content-assets.mjs .astro/data-store.json`, then merge again.
