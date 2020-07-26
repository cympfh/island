# island

Anime Recommendation powerd by Annict

## Requirements

- Python3

## Setup

### Update Dataset

This step can be skipped (if you don't need update).

Get Access Token from https://annict.jp/settings/apps . Then,

```bash
TOKEN=XXX bash ./fetch.sh > anime.json
```

_NOTE_: All you need is backup. This fetching sometimes fails.

### Lanch Server

Recommendation Model be fitted at first.
This may take only several seconds.

```bash
pip isntall -r requirements.txt
make server
```

