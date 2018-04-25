all: dwarf-assembly

dwarf-assembly:
	$(MAKE) -C src/ $@
	ln -s src/$@ ./$@
