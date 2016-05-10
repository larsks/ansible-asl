%.css: %.less
	lesscpy $< $@

all: style.css
