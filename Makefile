SHELL := /bin/bash

check:
	poetry run ruff check .
	pyright .

format:
	poetry run ruff check --fix .
	poetry run ruff format .

test:
	poetry run pytest

