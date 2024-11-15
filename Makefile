COOKIES_DIR = cookies
OUTPUT_DIR = output

import-zh:
	mkdir -p $(COOKIES_DIR)/zh
	mkdir -p tmp; cd tmp; git clone --depth=1 https://salsa.debian.org/chinese-team/fortunes-zh.git
	python scripts/import-zh.py  tmp/fortunes-zh/ $(COOKIES_DIR)/zh
	rm -rf tmp

clean-zh:
	rm -rf $(COOKIES_DIR)/zh

import: import-zh

compile:
	python scripts/compile.py $(COOKIES_DIR) $(OUTPUT_DIR)

clean: clean-zh
	rm -rf $(OUTPUT_DIR) tmp
