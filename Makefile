.PHONY: install run test lint format docker-build docker-up docker-down logs

install:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	python3 bot.py

test:
	pytest --cov=. --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

logs:
	docker compose logs -f
