# Contributing to Crypto Attribution Engine

Thank you for contributing to the Crypto Attribution Engine project! This document outlines our development process, branching model, and coding guidelines.

---

## 🌿 Branching Model

We operate on a 4-tier Git branching model:

- **`main`**: Production releases only. Protected branch; code must pass full integration & Docker testing.
- **`develop`**: Central integration branch for ongoing features.
- **`feature/frontend`**: Dedicated branch for UI/UX, React components, 3D WebGL Three.js visuals, and styling.
- **`feature/backend`**: Dedicated branch for Python tracing algorithms, Etherscan integrations, chain adapters, and FastAPI endpoints.

---

## 🛠️ Local Development Setup

### Backend
```bash
cd v2/backend
pip install -r requirements.txt
python eth_txs.py test
python pattern_detector.py
python report_generator.py
python api.py
```

### Frontend
```bash
cd v2/frontend
npm install
npm run dev
```

---

## 📝 Commit Conventions

We enforce [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` A new feature (e.g., `feat: add TRON USDT multi-chain adapter`)
- `fix:` A bug fix (e.g., `fix: correct decimal normalization for 6-decimal tokens`)
- `docs:` Documentation only changes (e.g., `docs: update API endpoints table`)
- `style:` Changes that do not affect code logic (formatting, missing semicolons)
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `test:` Adding or updating unit tests
- `ci:` Changes to CI/CD workflows and configuration

---

## ✅ Pull Request Process

1. Ensure all test suites pass locally before submitting a PR.
2. Verify that `npm run build` succeeds with zero errors.
3. Link the relevant issue or task ticket in your PR description.
4. Request review from at least one core contributor.
