# Italian QA scripts for Pontoon TMX

To run the script:
- Save a copy of Pontoon TMX in `data`, by running within the folder `curl -o it.all-projects.tmx --compressed https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx`
- Run`scripts/check_strings.sh` (it will create and activate a virtualenv with Python 3 and install the dependencies).

Projects analyzed:
- mozilla.org

## Hunspell

If you’re using macOS, you need to install Hunspell via `brew`

```
brew install hunspell
```

Be aware of the multiple issues existing ([one](https://github.com/blatinier/pyhunspell/issues/26), [two](https://github.com/blatinier/pyhunspell/issues/33)).

You might need to manually activate the virtualenv in `python-venv` and run these commands (Hunspell's version will change over time):

```
source python-venv/bin/activate
ln -s /usr/local/lib/libhunspell-1.7.a /usr/local/lib/libhunspell.a
ln -s /usr/local/Cellar/hunspell/1.7.0_2/lib/libhunspell-1.7.dylib /usr/local/Cellar/hunspell/1.7.0_2/lib/libhunspell.dylib
CFLAGS=$(pkg-config --cflags hunspell) LDFLAGS=$(pkg-config --libs hunspell) pip3 install hunspell
```
