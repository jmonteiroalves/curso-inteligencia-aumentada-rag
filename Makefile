.PHONY: help validate test smoke setup compose-up compose-down

help:
	@echo "validate  - checa estrutura, datasets e TODOs"
	@echo "test      - roda todos os smoke tests (sem serviços externos)"
	@echo "smoke     - executa os demos das soluções"
	@echo "setup     - instala dependências com uv"
	@echo "compose-up- sobe Ollama; use --profile vectors|pgvector|graph para extras"

validate:
	python3 scripts/validate_repo.py

test:
	@set -e; for d in 0*_*/; do \
		echo "== $$d"; \
		(cd "$$d" && python3 -m unittest discover -s tests -v); \
	done

smoke:
	@set -e; for d in 0*_*/; do \
		echo "== $$d"; \
		(cd "$$d" && python3 solucao/run_demo.py > /dev/null && echo "ok"); \
	done

setup:
	uv venv --python 3.11
	uv sync

compose-up:
	docker compose up -d ollama

compose-down:
	docker compose down
