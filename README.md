# Kowndinya Boyalakuntla

Personal academic website, published with Jekyll and GitHub Pages.

Content is stored in `_config.yml` and `_data/`. Run `bundle exec jekyll serve` for a local preview.

## Curriculum vitae

The website and PDF share the same YAML content. Set `in_cv: false` on an entry in `_data/publications.yml` to omit it from the CV webpage and PDF. With Python 3 and TeX Live installed:

```sh
python -m pip install -r cv/requirements.txt
python cv/build_cv.py
```

This generates `cv/content.tex` and compiles `cv/kowndinya-cv.tex` into `pdfs/Kowndinya_Boyalakuntla_CV.pdf`. The former resume URL is retained as a copy of the current CV. The two `.tex` files can also be compiled directly with `pdflatex` from the `cv/` directory. TeX packages include `newpxtext`, `sourcesanspro`, `microtype`, `enumitem`, and `lastpage`.

## Credits

The original site was adapted from [Keunhong Park’s template](https://github.com/keunhong/keunhong.github.io), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). DM Sans is distributed under the included SIL Open Font License. Research papers and project images retain their respective rights.
