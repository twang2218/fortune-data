import:
	uv run main.py

test:
	uv run pytest

clean:
	ruff clean
	find . -type d -name __pycache__ -exec rm -rf {} \+
	rm -rf data/{extract,transform,load}

format:
	ruff check --select I --fix
	ruff format
