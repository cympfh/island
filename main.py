import collections
import random
from typing import List, Tuple

import implicit
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from scipy.sparse import lil_matrix


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
        images = dict()  # annict_id -> ImageUrl

        with open("./dataset/works.csv") as f:
            for line in f:
                annict_id, image, title = line.strip("\n").split("\t", 2)
                titles[annict_id] = title
                images[annict_id] = image

        rows = []  # List of (annict_id, user_id, rating)
        count_anime = collections.defaultdict(int)  # annict_id -> count
        count_user = collections.defaultdict(int)  # user_id -> count

        def rate(rating: str) -> float:
            if rating == "bad":
                return -1
            if rating == "good":
                return 1
            if rating == "great":
                return 2
            return 0.5

        # if os.path.exists("./dataset/records.csv"):
        #     with open("./dataset/records.csv") as f:
        #         for line in f:
        #             annict_id, user_id, rating = line.strip("\n").split(
        #                 " ", 2
        #             )  # TODO delimiter!
        #             if rating == "null":
        #                 continue
        #             count_user[user_id] += 1
        #             rows.append((annict_id, user_id, rate(rating) * 0.2))

        with open("./dataset/reviews.csv") as f:
            for line in f:
                annict_id, user_id, rating = line.strip("\n").split("\t", 2)
                count_anime[annict_id] += 1
                count_user[user_id] += 1
                rows.append((annict_id, user_id, rate(rating)))

        mat = Matrix()

        LIMIT_ANIME = 1
        LIMIT_USER = 4
        for annict_id, user_id, ratevalue in rows:
            if count_anime[annict_id] < LIMIT_ANIME:
                continue
            if count_user[user_id] < LIMIT_USER:
                continue
            mat.insert(annict_id, user_id, ratevalue)

        mat.stat()
        mat.decomposition(factors=40)

        self.mat = mat
        self.titles = titles
        self.images = images

    def isknown(self, annict_id: str) -> bool:
        """Known Anime?"""
        return annict_id in self.mat.row_id

    def title(self, annict_id: str) -> str:
        """Anime Title"""
        return self.titles.get(annict_id, "UNKNOWN")

    def image(self, annict_id: str) -> str:
        """Anime Image Url"""
        return self.images.get(annict_id, "UNKNOWN")

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
    if not recommender.isknown(annict_id):
        raise HTTPException(status_code=404, detail="Item not found")
    relatives = recommender.similar_items(annict_id, 10)
    return {
        "annictId": annict_id,
        "title": recommender.title(annict_id),
        "image": recommender.image(annict_id),
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
                {
                    "annictId": aid,
                    "title": recommender.title(aid),
                    "image": recommender.image(aid),
                }
                for aid in aids
            ]
        }

    user_items = lil_matrix((1, len(recommender.mat.rows)))
    for annict_id in likes:
        if recommender.isknown(annict_id):
            i = recommender.mat.row_id[annict_id]
            user_items[(0, i)] = 1.2
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
                "image": recommender.image(recommender.mat.rows[int(i)]),
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


@app.get("/anime/random", response_class=RedirectResponse)
async def index_random():
    """Redirect to Random /anime/{annict_id}"""
    annict_id = recommender.random_anime()
    return RedirectResponse(f"/anime/{annict_id}")


@app.get("/anime/{annict_id}", response_class=HTMLResponse)
async def index_anime_graph(annict_id: str):
    """Index for Each Anime"""
    if not recommender.isknown(annict_id):
        raise HTTPException(status_code=404, detail="Item not found")
    with open("./templates/anime.html", "rt") as f:
        return f.read()


@app.get("/", response_class=RedirectResponse)
async def index():
    """Redirect to /anime"""
    return RedirectResponse("/anime")


@app.get("/anime", response_class=HTMLResponse)
async def index_anime():
    """Index of All"""
    with open("./templates/index.html", "rt") as f:
        return f.read()
