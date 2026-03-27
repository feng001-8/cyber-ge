# Dependency and Environment Issues

Mistake: Running dev server before dependencies are installed
Wrong: `npm run dev` fails with `sh: astro: command not found`
Correct:
 Run `npm ci` (or `npm install`) in the project root first, then run `npm run dev`.

Mistake: npm install fails due to npm cache ownership
Wrong: `npm ci` fails with EPERM and root-owned files under `~/.npm`
Correct:
 Fix ownership once with `sudo chown -R $(id -u):$(id -g) ~/.npm`, then reinstall dependencies.
