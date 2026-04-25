# Makefile
TEXTUAL = .venv/bin/textual
PYTHON  = .venv/bin/python3

run:
	$(PYTHON) src/main.py

dev:
	$(TEXTUAL) run --dev src/ui/app.py 2>debug.log

test:
	$(PYTHON) -m unittest discover tests -v

fetch:
	$(PYTHON) scripts/fetch_gen3_moves.py

typecheck:
	$(PYTHON) -m pyright src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete