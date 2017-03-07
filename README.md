# US Unemployment Rates from 1990 - 2016

TL;DR:

```bash
$ python retrieve.py # or nohup python retrieve.py &
$ python transform.py
```

`retrieve.py` creates a folder `data/`, in which a folder `pages/` is created to store the raw HTML pages for every year / month / state / county combination (35,100 total HTML pages, ~ 3.75 GB). It also creates a `reference.json` file to map all codes for each of the four levels of granularity to their full text (i.e. `01` maps to `Alabama` or `M12` maps to `December`, etc).

`transform.py` iterates through files in `data/pages/` and creates `result.json` at the root of the project.

By Jay Ravaliya