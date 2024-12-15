COOKIES_DIR = cookies
PACKAGE_DIR = dist
VERSION = 0.1.0

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

clean-dist:
	rm -rf $(PACKAGE_DIR)

format:
	ruff check --select I --fix
	ruff format

package: clean-dist
	mkdir -p $(PACKAGE_DIR)
	cp -r $(COOKIES_DIR)/tier1 $(PACKAGE_DIR)/
	cp -r $(COOKIES_DIR)/tier2 $(PACKAGE_DIR)/
	cp LICENSE-DATA $(PACKAGE_DIR)/
	cp NOTICE $(PACKAGE_DIR)/
	cd $(PACKAGE_DIR) && zip -r fortune-data-$(VERSION).zip tier1 tier2 LICENSE-DATA NOTICE
	@echo "Package created: $(PACKAGE_DIR)/fortune-data-$(VERSION).zip"
