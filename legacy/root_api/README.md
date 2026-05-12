# Legacy Root API

This directory preserves the original root-level API implementation that previously powered this
repository.

The repository has now been cut over to `backend/` as the canonical application:

- repo-root commands delegate into `backend/`
- backend code, tests, and runtime scripts all live under `backend/`
- root-level API shims have been removed
- this archive is no longer part of the active runtime path

Keep this archive only as historical context while the backend mirror stabilizes.
