.PHONY: run test typecheck fetch clean

run:
	python src/main.py

test:
	python -m pytest tests/ -v

typecheck:
	pyright src/

fetch:
	python scripts/fetch_gen3_moves.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete