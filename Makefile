PREFIX ?= $(HOME)/.local

.PHONY: install uninstall autostart no-autostart icons screenshots deb rpm flatpak appimage clean

install:
	PREFIX=$(PREFIX) bash install.sh

uninstall:
	PREFIX=$(PREFIX) bash uninstall.sh

autostart:
	bash scripts/enable-autostart.sh

no-autostart:
	bash scripts/disable-autostart.sh

icons:
	python3 scripts/make_icons.py

screenshots:
	python3 scripts/make_screenshots.py

deb:
	bash scripts/build-deb.sh

rpm:
	bash scripts/build-rpm.sh

flatpak:
	bash scripts/build-flatpak.sh

appimage:
	bash scripts/build-appimage.sh

clean:
	rm -rf build
