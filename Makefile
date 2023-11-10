.PHONY: setup
setup:
	python3.9 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

.PHONY: run
run:
	source venv/bin/activate && uvicorn --reload main:app