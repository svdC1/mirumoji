## Description

<!-- Summary of the changes and the motivation behind them -->

## Related Issue

<!-- e.g. Closes #123 -->

## Surface

<!-- Tick all that apply -->

- [ ] Server (FastAPI backend)
- [ ] Frontend (web UI)
- [ ] CLI (`mirumoji`)
- [ ] GUI launcher (`mirumoji gui`)
- [ ] Docker / Compose
- [ ] Documentation
- [ ] CI / tooling

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Improvement / refactor
- [ ] Documentation
- [ ] Breaking change

## Checklist

- [ ] I have read the [Contributing Guide](https://svdc1.github.io/mirumoji/docs/Contributing)
- [ ] My changes don't break existing functionality
- [ ] I added or updated tests where it makes sense

### Quality Gates

<!-- Run the gates relevant to the surfaces you touched -->

- [ ] Python &rarr; `ruff check apps/mirumoji/src` and `ruff format --check apps/mirumoji/src`
- [ ] Python &rarr; `cd apps/mirumoji && mypy src`
- [ ] Python &rarr; `cd apps/mirumoji && pytest`
- [ ] Frontend &rarr; `cd apps/frontend && npm run lint` and `npx prettier --check src`
- [ ] Frontend &rarr; `cd apps/frontend && npm test`

## Additional Context

<!-- Screenshots, notes, or anything else reviewers should know -->
