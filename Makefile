.PHONY: run cli reset test
run:
	python -m barcode_lib.main
cli:
	python -m barcode_lib.main --no-gui
reset:
	@read -p "Type 'DELETE ALL' to erase DBs & cache: " ans; \
	if [ "$$ans" = "DELETE ALL" ]; then \
	rm -f barcode_lib/db/*.db barcode_lib/web/product_cache.json; \
	echo "All cleared."; \
	else echo "Cancelled."; fi
test:
	python -m unittest discover -s test -p "test_*.py"
