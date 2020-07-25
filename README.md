# island

Anime Recommendation powerd by Annict

## Requirements

- Python3

## Setup

### Update Dataset

This step can be skipped (if you don't need update).

Get Access Token from https://annict.jp/settings/apps

```bash
TOKEN=... bash ./fetch.sh > anime.json
```

### Lanch Server

Recommendation Model be fitted at first.
This may take only several seconds.

```bash
pip isntall -r requirements.txt
make server
```

