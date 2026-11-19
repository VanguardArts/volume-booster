PREFIX ?= $(HOME)/.local

.PHONY: install uninstall deb clean

install:
	PREFIX=$(PREFIX) bash install.sh

uninstall:
	PREFIX=$(PREFIX) bash uninstall.sh

deb:
	bash scripts/build-deb.sh

clean:
	rm -rf build
