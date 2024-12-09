COOKIES_DIR = cookies
OUTPUT_DIR = output

import:
	make -C scripts import
	mkdir -p $(COOKIES_DIR)
	cp -r scripts/data/load/* $(COOKIES_DIR)

clean:
	rm -rf $(COOKIES_DIR)
	make -C scripts clean

compile:
	python scripts/compile.py $(COOKIES_DIR) $(OUTPUT_DIR)
