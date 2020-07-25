import collections
import json
import math
import random
from typing import List, Tuple

import implicit
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from scipy.sparse import lil_matrix

#    cat anime.json | jq .data.searchWorks.edges[0].node
# {
#   "annictId": 2108,
#   "title": "魔法少女まどか☆マギカ",
#   "watchersCount": 7259,
#   "reviews": {
#     "edges": [
#       {
#         "node": {
#           "user": {
#             "name": "チェン",
#             "id": "VXNlci0xNDQwNg=="
#           }
#         }

with open("./anime.json") as f:
    dataset = json.load(f)


class Matrix:
    """Matrix-decompositionable"""

    def __init__(self):
        """Initialize as Empty"""
        self.rows = []
        self.cols = []
        self.row_id = dict()
        self.col_id = dict()
        self.data = dict()

    def insert(self, row: str, col: str, val: float):
        """Insert a value

        Parameters
        ----------
        row
            annictId (NOTE: stringified)
        col
            userId
        val
            reviewed?
        """
        if row not in self.row_id:
            self.rows.append(row)
            self.row_id[row] = len(self.row_id)
            assert self.rows[self.row_id[row]] == row
        if col not in self.col_id:
            self.cols.append(col)
            self.col_id[col] = len(self.col_id)
            assert self.cols[self.col_id[col]] == col
        i = self.row_id[row]
        j = self.col_id[col]
        self.data[(i, j)] = val

    def decomposition(self, factors: int):
        """Fitting"""
        X = lil_matrix((len(self.rows), len(self.cols)))
        for pos, val in self.data.items():
            X[pos] = val
        fact = implicit.als.AlternatingLeastSquares(factors=factors)
        fact.fit(item_users=X, show_progress=True)
        self.fact = fact

    def stat(self):
        """Debug"""
        print(
            f"Size: {len(self.rows)} x {len(self.cols)} = {len(self.rows) * len(self.cols)}"
        )
        print(
            f"{len(self.data)} cells have non-zero values (density={len(self.data) / len(self.rows) / len(self.cols)})"
        )


class Recommendation:
    """Recommendation has a Matrix"""

    def __init__(self, limit: int = 2000, sub_reviews: int = 1):
        """init

        limit
            num of animes
        sub_reviews
            Remove Users(.reviews.length < sub_reviews)
        """
        titles = dict()  # annictId -> title

        rows = []

        for anime in dataset["data"]["searchWorks"]["edges"][:limit]:
            title = anime["node"]["title"]
            annict_id = str(anime["node"]["annictId"])
            titles[annict_id] = title
            for review in anime["node"]["reviews"]["edges"]:
                user = str(review["node"]["user"]["id"])
                rows.append((annict_id, user))

        count_reviews = collections.defaultdict(int)
        for _, user in rows:
            count_reviews[user] += 1

        mat = Matrix()
        for annict_id, user in rows:
            if count_reviews[user] >= sub_reviews:
                mat.insert(annict_id, user, math.pow(count_reviews[user], 0.5))

        mat.stat()
        mat.decomposition(factors=40)

        self.mat = mat
        self.titles = titles

    def title(self, annict_id: str) -> str:
        """Anime Title"""
        return self.titles.get(annict_id, "UNKNOWN")

    def random_anime(self) -> str:
        """Returns random annictId"""
        return random.choice(self.mat.rows)

    def similar_items(self, annict_id: str, n: int) -> List[Tuple[str, float]]:
        """Similar animes

        Returns
        -------
        List of (annict_id: str, score: float)
        """
        i = self.mat.row_id[annict_id]
        similars = self.mat.fact.similar_items(i, n + 1)
        return [
            (self.mat.rows[int(j)], float(score))
            for j, score in similars
            if int(j) != i
        ][:n]


recommender = Recommendation(limit=1500, sub_reviews=5)
app = FastAPI()

origins = [
    "http://cympfh.cc",
    "http://s.cympfh.cc",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/anime/api/info")
async def anime_info(annict_id: str):
    """Returns Info"""
    relatives = recommender.similar_items(annict_id, 10)
    return {
        "annictId": annict_id,
        "title": recommender.title(annict_id),
        "relatives": [
            {
                "annictId": annict_id,
                "title": recommender.title(annict_id),
                "score": float(score),
            }
            for annict_id, score in relatives
        ],
    }


@app.get("/anime/api/recommend")
async def recommend(likes: List[str] = Query(None)):
    """Recommendation from user's likes

    Parameters
    ----------
    likes
        List of annictId
    """
    if likes is None:
        aids = random.sample(recommender.mat.rows, 20)
        return {
            "items": [
                {"annictId": aid, "title": recommender.title(aid)} for aid in aids
            ]
        }

    user_items = lil_matrix((1, len(recommender.mat.rows)))
    for annict_id in likes:
        i = recommender.mat.row_id[annict_id]
        user_items[(0, i)] = 1.0
    recommend_items = recommender.mat.fact.recommend(
        0,
        user_items.tocsr(),
        20,
        filter_already_liked_items=True,
        recalculate_user=True,
    )
    return {
        "items": [
            {
                "annictId": recommender.mat.rows[int(i)],
                "title": recommender.title(recommender.mat.rows[int(i)]),
                "score": float(score),
            }
            for i, score in recommend_items
        ],
        "source": {
            "likes": [
                {"annictId": annict_id, "title": recommender.title(annict_id)}
                for annict_id in likes
            ]
        },
    }


@app.get("/anime/recommend", response_class=HTMLResponse)
async def index_recommend():
    """Recommendation Page"""
    with open("./templates/recommend.html", "rt") as f:
        return f.read()


@app.get("/anime/{annict_id}", response_class=HTMLResponse)
async def index_anime(annict_id: str):
    """Index for Each Anime"""
    with open("./templates/index.html", "rt") as f:
        return f.read()


@app.get("/", response_class=RedirectResponse)
async def index():
    """Index: Redirect to Random Anime"""
    annict_id = recommender.random_anime()
    return RedirectResponse(f"/anime/{annict_id}")


@app.get("/anime", response_class=RedirectResponse)
async def index2():
    """Index: Redirect to Random Anime"""
    annict_id = recommender.random_anime()
    return RedirectResponse(f"/anime/{annict_id}")
