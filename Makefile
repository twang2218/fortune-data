COOKIES_DIR = cookies

generate:
	uv run scripts/main.py

generate-test:
	uv run scripts/main.py test.jsonl

generate-stats:
	uv run scripts/main.py --stats

strfile:
	find $(COOKIES_DIR)/tier1 -type f ! -name "*.md" -exec strfile {} \;
	find $(COOKIES_DIR)/tier2 -type f ! -name "*.md" -exec strfile {} \;

test:
	uv run pytest -vv

clean:
	ruff clean
	rm -rf .pytest_cache
	find scripts -type d -name __pycache__ -exec rm -rf {} \+

clean-all: clean clean-data
	rm -rf .venv

clean-data:
	rm -rf cookies

clean-cache:
	rm -rf .cache

format:
	ruff check --select I --fix
	ruff format
