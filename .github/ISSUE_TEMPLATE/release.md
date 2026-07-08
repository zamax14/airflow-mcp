---
name: Release
about: Preparation and closing checklist for a release
title: "[RELEASE] v"
labels: "type:chore"
assignees: ""
---

## Version

<!-- e.g. v0.1.0 -->

## Scope

<!-- Which tools, transports or capabilities are included in this release -->

## Included commits

<!-- List of relevant commits or PRs since the previous release -->

## Preparation checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run mypy src` passes
- [ ] `uv run pytest` passes
- [ ] Environment variables documented in `.env.example`
- [ ] develop -> main PR created and approved

## Closing checklist

- [ ] PR merged into main
- [ ] Version tag created on main (`git tag v...`)
- [ ] Issue closed

## Notes

<!-- Risks, external dependencies or special deployment instructions -->
