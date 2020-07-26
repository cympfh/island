# island

Anime Recommendation powerd by Annict

## Requirements

- Python3

## Setup

### Update Dataset

This step can be skipped (if you don't need).

Dataset are (already) exists in `dataset/` directory.
To update them, get Access Token from https://annict.jp/settings/apps . Then,

```bash
TOKEN=XXX make dataset-works dataset-reviews dataset-records
```

_NOTE_ `make dataset-records` takes many hours.
If you don't have enough time, `make` only `dataset-works` and `dataset-reviews`.

#### dataset-works

`anime_id (annict_id)` vs `imageUrl` vs `title`

#### dataset-reviews

Reviews are text-comments by users for anime works.

`anime_id (annict_id)` vs `user_id` vs `rating`

### Lanch Server

Recommendation Model be fitted at first.
This may take only several seconds.

```bash
pip isntall -r requirements.txt
make server
```

