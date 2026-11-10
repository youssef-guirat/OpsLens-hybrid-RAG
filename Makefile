.PHONY: install fetch index api ui test lint eval

install:
	uv sync --extra dev

fetch:
	uv run python -m scripts.fetch_open_docs

index:
	uv run python -m scripts.build_index

api:
	uv run uvicorn app.main:app --reload

ui:
	uv run streamlit run ui/streamlit_app.py

test:
	uv run pytest

lint:
	uv run ruff check .

eval:
	uv run python -m scripts.evaluate

