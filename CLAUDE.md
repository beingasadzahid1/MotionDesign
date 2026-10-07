# MotionDesign

Motion design workspace. Launch videos, motion pieces and share copy for projects.

## Layout

- `README.md`: project readme.
- `brag/`: vendored snapshot of [latent-spaces/brag](https://github.com/latent-spaces/brag) at `fd7de7e`. An agent skill that turns a project into a short launch video with music, motion and share copy.
  - `brag/skills/brag/`: full `/brag` skill (Hyperframes workflow). Entry point `SKILL.md`, plus `references/`, `assets/`, `scripts/`.
  - `brag/skills/brag-slim/`: lean `/brag-slim` skill, no Hyperframes or bundled assets.
  - `brag/examples/`: five sample projects with finished brag outputs.
  - `brag/docs/`: launch site source.
  - `brag/PRODUCT.md`: brand brief for brag itself (voice, audience, anti-references).
  - `brag/scripts/`: `check-brag-slim.mjs`, `check-docs.mjs` consistency checks.

## Working in brag/

- It's a vendored copy, not a submodule. Upstream history isn't here. To update, re-copy from upstream and note the new commit in the commit message.
- Its `.claude/`, `.claude-plugin/`, `.codex-plugin/` and `.opencode/` configs only load from a repo root. Inside `brag/` they're inert reference.
- Skill links under `brag/.agents`, `brag/.claude` and `brag/.opencode` are symlinks into `brag/skills/`. Keep them as links.
- Run the checks from inside `brag/`: `node scripts/check-docs.mjs` and `node scripts/check-brag-slim.mjs`.
