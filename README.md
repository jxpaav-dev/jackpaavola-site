# jackpaavola.jxpaav.workers.dev

Personal site: plain HTML + one CSS file. No build step.

## Preview locally
Double-click `public/index.html`, or run `python -m http.server` in `public/` and open http://localhost:8000.

## Common edits
- **New resume:** replace `public/assets/Jack_Paavola_Resume.pdf`, update `public/resume.html` to match, change the "Updated" date.
- **New project:** copy an `<article class="project">` block in `public/projects.html`. For a write-up, copy `public/projects/pathfinder.html`.
- **LinkedIn:** linkedin.com/in/jackpaavola is linked in the footer of every page and in the Home hero.
- **Placeholders:** anything with `class="todo"` or `class="ph"` is unfinished. Search for them before sharing the link.

## Ideas queued
- Underwater robot write-up (featured on Home once it has a photo)
- E85 lab project

## Deploy
Hosted on Cloudflare Workers (static assets). `wrangler.jsonc` points at `./public`;
every push to `main` redeploys. Deploy command: `npx wrangler deploy`, no build command.
