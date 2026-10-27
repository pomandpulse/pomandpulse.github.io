# PersianPulse site runbook

Site: https://pomandpulse.github.io (GitHub Pages, source = GitHub Actions)

## How it works
- `_src/data/pieces.json` is the single data file (site info, pieces, glossary words).
- `_src/build.py` (Python standard library only) builds the site into `_site/`.
- A piece is published when its `date` is on or before the cutoff: the most recent Saturday on or before yesterday (Pacific time). Override with `--through YYYY-MM-DD`.
- `.github/workflows/site.yml` builds and deploys every Sunday 11:00 PT (`0 18 * * 0`, UTC), on manual run, and on pushes to `_src/` or the workflow.

## Add a piece
1. Add an object to `pieces` in `_src/data/pieces.json` (id, slug, date, topic, title, caption, alt, sources, title_fa, caption_fa, alt_fa).
2. Add `_src/img/<id>_en.jpg`, `_en_t.jpg`, `_fa.jpg`, `_fa_t.jpg` (1280 and 640 px wide) and `_src/dl/<id>_<lang>_hi.jpg` / `.pdf`.
3. Test: `python3 _src/build.py --out /tmp/site --through 2099-01-01`.
4. `git fetch origin main && git rebase origin/main`, commit, push.

## Add a glossary word
Append `{"term","def","term_fa","def_fa"}` to `words` in the data file.

## Future ideas (not built)
Newsletter, book, extra sections.

## Rules
Never publish drafts, secrets or tokens. Educational content, not medical advice.
