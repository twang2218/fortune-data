COOKIES_DIR = cookies
OUTPUT_DIR = output

import-zh:
	mkdir -p $(COOKIES_DIR)/zh
	python scripts/import-zh.py  ../../ref/debian-fortunes-zh/ $(COOKIES_DIR)/zh

clean-zh:
	rm -rf $(COOKIES_DIR)/zh

import: import-zh

compile:
	python scripts/compile.py $(COOKIES_DIR) $(OUTPUT_DIR)

clean: clean-zh
	rm -r $(OUTPUT_DIR)
