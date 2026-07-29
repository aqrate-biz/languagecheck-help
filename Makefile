PYTHON ?= python3
ifneq ("$(wildcard .venv/bin/python)","")
PYTHON := .venv/bin/python
endif

.PHONY: help install install-pdf serve build check clean sync-openapi render-firebase-overrides export-md export-pdf

help:
	@echo "Target disponibili:"
	@echo "  make install       Installa le dipendenze Python"
	@echo "  make install-pdf   Installa anche le dipendenze per export PDF"
	@echo "  make serve         Avvia preview locale su http://127.0.0.1:8000"
	@echo "  make build         Esegue build locale"
	@echo "  make check         Esegue build strict (pre-deploy)"
	@echo "  make export-md     Esporta tutta la docs in un unico Markdown (ordine nav + TOC)"
	@echo "  make export-pdf    Esporta Markdown + PDF (richiede make install-pdf + librerie sistema)"
	@echo "  make sync-openapi  Sincronizza openapi.yaml dentro docs/"
	@echo "  make render-firebase-overrides  Genera override Firebase da variabili ambiente"
	@echo "  make clean         Rimuove la cartella site/ e export/"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-pdf:
	$(PYTHON) -m pip install -r requirements-pdf.txt

serve:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs serve

build:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs build

check:
	$(MAKE) render-firebase-overrides
	$(PYTHON) -m mkdocs build --strict

export-md:
	$(PYTHON) scripts/export_combined.py -o export/languagecheck-help.md

export-pdf:
	@if [ -d /opt/homebrew/lib ]; then export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$${DYLD_LIBRARY_PATH:-}"; fi; \
	$(PYTHON) scripts/export_combined.py -o export/languagecheck-help.md --pdf export/languagecheck-help.pdf

render-firebase-overrides:
	@if [ -f .env.local ]; then set -a; . ./.env.local; set +a; fi; \
	$(PYTHON) scripts/render_firebase_overrides.py

sync-openapi:
	cp openapi.yaml docs/openapi.yaml

clean:
	rm -rf site export
