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

