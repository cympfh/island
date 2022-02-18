# island

Anime Recommendation powerd by Annict

## Requirements

- Python3

## Setup

### Update Dataset

This step can be skipped (if you don't need update).

Dataset are (already) exists in `dataset/` directory.
To update them, get Access Token from https://annict.jp/settings/apps . Then,

```bash
TOKEN=XXX make dataset
```

This may take several hours (for `dataset-records`).

### Lanch Server

Recommendation Model(s) will be fitted at first.
This may take several seconds.

```bash
$ poetry install
$ make server
```

