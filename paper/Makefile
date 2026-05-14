PDF=main.pdf

.PHONY: all clean

all: $(PDF)

$(PDF): main.tex refs.bib
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -C main.tex
	rm -f *.bbl *.blg *.fls *.fdb_latexmk

