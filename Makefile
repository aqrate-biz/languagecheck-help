PYTHON ?= python3
ifneq ("$(wildcard .venv/bin/python)","")
PYTHON := .venv/bin/python
endif

.PHONY: help install serve build check clean sync-openapi render-firebase-overrides

help:
	@echo "Target disponibili:"
	@echo "  make install       Installa le dipendenze Python"
	@echo "  make serve         Avvia preview locale su http://127.0.0.1:8000"
	@echo "  make build         Esegue build locale"
	@echo "  make check         Esegue build strict (pre-deploy)"
	@echo "  make sync-openapi  Sincronizza openapi.yaml dentro docs/"
	@echo "  make render-firebase-overrides  Genera override Firebase da variabili ambiente"
	@echo "  make clean         Rimuove la cartella site/"

install:
	$(PYTHON) -m pip install -r requirements.txt

serve:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs serve

build:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs build

check:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs build --strict

render-firebase-overrides:
	@if [ -f .env.local ]; then set -a; . ./.env.local; set +a; fi; \
	$(PYTHON) scripts/render_firebase_overrides.py

sync-openapi:
	cp openapi.yaml docs/openapi.yaml

clean:
	rm -rf site