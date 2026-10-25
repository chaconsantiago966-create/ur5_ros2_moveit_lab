# Reporte

- `main.tex` — fuente LaTeX editable (las figuras están en `figuras/`).
- `main.pdf` — versión compilada.

Datos editables al inicio de `main.tex`: `\universidad`, `\profesor`, `\fecha`.

Compilar localmente (dos pasadas para el índice):

```bash
sudo apt install texlive-latex-recommended texlive-latex-extra texlive-lang-spanish texlive-fonts-recommended
cd reporte && pdflatex main.tex && pdflatex main.tex
```

En Overleaf: subir `main.tex` y la carpeta `figuras/` y compilar con pdfLaTeX.
