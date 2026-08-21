.PHONY: lint format lint-check identity-check test test-fast test-no-coverage migrate reindex gazetteers ogm-nightly cache-prime cache-prime-background kamal-registry-login transfer-readiness transfer-readiness-full

BACKEND_DIR = backend

lint:
	@echo "Checking backend-focused code with ruff..."
	cd $(BACKEND_DIR) && ruff check app tests scripts

format:
	@echo "Formatting backend-focused code with ruff..."
	cd $(BACKEND_DIR) && ruff format app tests scripts
	cd $(BACKEND_DIR) && ruff check --fix app tests scripts

lint-check:
	@echo "Checking formatting without modifying files..."
	cd $(BACKEND_DIR) && ruff format --check app tests scripts
	cd $(BACKEND_DIR) && ruff check app tests scripts

identity-check:
	./scripts/verify_identity_cleanup.sh

test:
	@echo "Running backend test suite..."
	cd $(BACKEND_DIR) && pytest --full-trace

test-fast:
	@echo "Running backend test suite in parallel..."
	cd $(BACKEND_DIR) && pytest -n 4

test-no-coverage:
	@echo "Running backend test suite without coverage requirements..."
	cd $(BACKEND_DIR) && pytest --full-trace

migrate:
	cd $(BACKEND_DIR) && python scripts/run_migrations.py

reindex:
	cd $(BACKEND_DIR) && python scripts/run_index.py

gazetteers:
	cd $(BACKEND_DIR) && python scripts/run_gazetteers.py

ogm-nightly:
	cd $(BACKEND_DIR) && python scripts/trigger_ogm_nightly_sync.py

cache-prime:
	cd $(BACKEND_DIR) && python scripts/prime_generated_caches.py $(ARGS)

cache-prime-background:
	cd $(BACKEND_DIR) && ./scripts/start_cache_prime_background.sh $(ARGS)

kamal-registry-login:
	./scripts/kamal_registry_login.sh

transfer-readiness:
	./scripts/verify_transfer_readiness.sh

transfer-readiness-full:
	./scripts/verify_transfer_readiness.sh --full-history
