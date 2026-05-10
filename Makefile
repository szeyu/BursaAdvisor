.PHONY: install start verbose check help

help:
	@echo "Usage:"
	@echo "  make install   Install dependencies (run once after git clone/pull)"
	@echo "  make start     Launch BursaAdvisor interactive screener"
	@echo "  make verbose   Launch with inference trace (shows intermediate facts)"
	@echo ""
	@echo "Adding a sector? Read SECTOR_GUIDE.md first."

install:
	uv sync

start: install
	uv run bursaadvisor

verbose: install
	uv run bursaadvisor --verbose