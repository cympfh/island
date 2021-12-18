import collections
import logging
import random
from typing import List, Optional, Tuple

import implicit
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from rich.logging import RichHandler
from scipy.sparse import lil_matrix

from island.database import RDB, RecordDB, ReviewDB, WorkDB
from island.staff.model import StaffModel

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("uvicorn")


class Matrix:
    """Matrix-decompositionable"""

    def __init__(self):
        """Initialize as Empty"""
        self.rows = []
        self.cols = []
        self.row_id = dict()
        self.col_id = dict()
        self.data = dict()

    def insert(self, row: int, col: int, val: float):
        """Insert a value

        Parameters
        ----------
        row
            workId
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
        fact = implicit.als.AlternatingLeastSquares(factors=factors, iterations=10)
        fact.fit(item_users=X.tocoo(), show_progress=False)
        self.fact = fact

    def stat(self):
        """Debug"""
        logger.info(
            f"Size: {len(self.rows)} x {len(self.cols)} = {len(self.rows) * len(self.cols)}"
        )
        logger.info(
            f"{len(self.data)} cells have non-zero values (density={len(self.data) / len(self.rows) / len(self.cols)})"
        )

    def recommend(self, likes: List[int], n: int) -> List[Tuple[int, float]]:
        """Run Recommendation

        Parameters
        ----------
        likes
            List of work_id
        n
            num of returns

        Returns
        -------
        List of (work_id and score)
        """
        user_items = lil_matrix((1, len(self.rows)))
        for work_id in likes:
            if work_id in self.row_id:
                i = self.row_id[work_id]
                user_items[(0, i)] = 2.0
        recommend_items = self.fact.recommend(
            0,
            user_items.tocsr(),
            n,
            filter_already_liked_items=True,
            recalculate_user=True,
        )
        return [(self.rows[int(i)], float(score)) for i, score in recommend_items]


class Recommendation:
    """Recommendation has a Matrix"""

    def __init__(
        self,
        dataset: RDB,
        limit_anime: int,
        limit_user: int,
    ):
        """init

        Parameters
        ----------
        dataset
            RDB of Record(work_id, user_id, rating)
            This is reviews or records.
        limit_anime
            sub limit of freq of anime
        limit_user
            sub limit of freq of user
        """
        logger.info("Initializing a Recommender for %s", dataset.table)

        titles = dict()  # work_id -> title
        images = dict()  # work_id -> ImageUrl

        for work_id, title, image, _dt in WorkDB():
            titles[work_id] = title
            images[work_id] = image

        rows = []  # List of (work_id, user_id, rating)
        count_anime = collections.defaultdict(int)  # work_id -> count
        count_user = collections.defaultdict(int)  # user_id -> count

        def rate(rating: str) -> float:
            if rating == "bad":
                return -1
            if rating == "good":
                return 1
            if rating == "great":
                return 4
            return 0.5

        for _id, user_id, work_id, rating, _dt in dataset:
            count_anime[work_id] += 1
            count_user[user_id] += 1
            if rating is None:
                continue
            rows.append((work_id, user_id, rate(rating)))

        mat = Matrix()

        for work_id, user_id, ratevalue in rows:
            if count_anime[work_id] < limit_anime:
                continue
            if count_user[user_id] < limit_user:
                continue
            mat.insert(work_id, user_id, ratevalue)

        mat.stat()
        mat.decomposition(factors=200)

        self.mat = mat
        self.titles = titles
        self.images = images
        self.test()

    def isknown(self, work_id: int) -> bool:
        """Known Anime?"""
        return work_id in self.mat.row_id

    def title(self, work_id: int) -> Optional[str]:
        """Anime Title"""
        return self.titles.get(work_id, None)

    def image(self, work_id: int) -> str:
        """Anime Image Url"""
        return self.images.get(work_id, None)

    def sample_animes(self, n: int) -> List[int]:
        """Returns List of random work_id"""
        return random.sample(self.mat.rows, n)

    def similar_items(self, work_id: int, n: int) -> List[Tuple[int, float]]:
        """Similar animes

        Returns
        -------
        List of (work_id: int, score: float)
        """
        if not self.isknown(work_id):
            return []
        i = self.mat.row_id[work_id]
        similars = self.mat.fact.similar_items(i, n + 1)
        return [
            (self.mat.rows[int(j)], float(score))
            for j, score in similars
            if int(j) != i
        ][:n]

    def __call__(self, likes: List[int], n: int) -> List[Tuple[int, float]]:
        """Recommend"""
        if not any(self.isknown(work_id) for work_id in likes):
            return []
        return self.mat.recommend(likes, n)

    def test(self):
        """Self Testing"""
        random.seed(42)
        sample_user_indices = random.sample(list(range(len(self.mat.cols))), 200)
        # collect likes
        likes = collections.defaultdict(list)
        for (work_id, user_idx), rating in self.mat.data.items():
            if user_idx not in sample_user_indices:
                continue
            if rating < 0:
                continue
            work_id = self.mat.rows[work_id]
            likes[user_idx].append(work_id)
        # testing
        acc1 = 0
        acc5 = 0
        acc10 = 0
        acc20 = 0
        num = 0
        for _ in range(5):
            for user_idx in sample_user_indices:
                if len(likes[user_idx]) < 3:
                    continue
                ans = random.choice(likes[user_idx])  # pseudo answer
                likes[user_idx].remove(ans)  # pseudo input
                pred = self.mat.recommend(likes[user_idx], 20)
                num += 1
                if ans in [pair[0] for pair in pred[:1]]:
                    acc1 += 1
                if ans in [pair[0] for pair in pred[:5]]:
                    acc5 += 1
                if ans in [pair[0] for pair in pred[:10]]:
                    acc10 += 1
                if ans in [pair[0] for pair in pred[:20]]:
                    acc20 += 1
        logger.info(f"Acc@1 = { acc1 / num }")
        logger.info(f"Acc@5 = { acc5 / num }")
        logger.info(f"Acc@10 = { acc10 / num }")
        logger.info(f"Acc@20 = { acc20 / num }")


class MixRecommendation:
    """Wrapper of Multiple Recommendations"""

    def __init__(self):
        """Init child recommenders"""
        self.children = [
            Recommendation(ReviewDB(), limit_anime=5, limit_user=5),
            Recommendation(RecordDB(), limit_anime=5, limit_user=3),
        ]

    def sample_animes(self, n: int) -> List[int]:
        """Returns List of work_id"""
        i = random.randrange(len(self.children))
        return random.sample(self.children[i].mat.rows, n)

    def title(self, work_id: int) -> Optional[str]:
        """anime title"""
        for child in self.children:
            t = child.title(work_id)
            if t:
                return t

    def image(self, work_id: int) -> Optional[str]:
        """image url"""
        for child in self.children:
            t = child.image(work_id)
            if t:
                return t

    def __call__(self, likes: List[int], n: int) -> List[Tuple[int, float]]:
        """Mixture of recommend of children"""
        items = sum([child(likes, n) for child in self.children], [])
        items.sort(key=lambda item: item[1], reverse=True)
        used = set()
        ret = []
        for work_id, score in items:
            if work_id in used:
                continue
            used.add(work_id)
            ret.append((work_id, score))
        return ret[:n]

    def isknown(self, work_id: int) -> bool:
        """is-known by any children"""
        for child in self.children:
            if child.isknown(work_id):
                return True
        return False

    def similar_items(self, work_id: int, n: int) -> List[Tuple[int, float]]:
        """Mixture of similar_items of children"""
        items = sum([child.similar_items(work_id, n) for child in self.children], [])
        items.sort(key=lambda item: item[1], reverse=True)
        used = set()
        ret = []
        for work_id, score in items:
            if work_id in used:
                continue
            used.add(work_id)
            ret.append((work_id, score))
        return ret[:n]


recommender = MixRecommendation()
works = recommender.sample_animes(20)
staff_model = StaffModel()

logger.info("Launching a Web Server")
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

logger.info("Ready")


@app.get("/anime/api/info")
async def anime_info(work_id: int):
    """Returns Info"""
    if not recommender.isknown(work_id):
        raise HTTPException(status_code=404, detail="Item not found")
    relatives_watch = recommender.similar_items(work_id, 5)
    relatives_staff = [
        (work_id, score)
        for (work_id, score) in staff_model.similar_items(work_id, 10)
        if recommender.isknown(work_id)
    ][:5]

    return {
        "workId": work_id,
        "title": recommender.title(work_id),
        "image": recommender.image(work_id),
        "relatives_watch": [
            {
                "workId": work_id,
                "title": recommender.title(work_id),
                "score": float(score),
            }
            for work_id, score in relatives_watch
        ],
        "relatives_staff": [
            {
                "workId": work_id,
                "title": recommender.title(work_id),
                "score": float(score),
            }
            for work_id, score in relatives_staff
        ],
    }


@app.get("/anime/api/recommend")
async def recommend(likes: List[int] = Query(None)):
    """Recommendation from user's likes

    Parameters
    ----------
    likes
        List of workId
    """
    if likes is None:
        works = recommender.sample_animes(20)
        return {
            "items": [
                {
                    "workId": work_id,
                    "title": recommender.title(work_id),
                    "image": recommender.image(work_id),
                }
                for work_id in works
            ]
        }

    recommend_items = recommender(likes, 20)
    return {
        "items": [
            {
                "workId": work_id,
                "title": recommender.title(work_id),
                "image": recommender.image(work_id),
                "score": float(score),
            }
            for work_id, score in recommend_items
        ],
        "source": {
            "likes": [
                {"workId": work_id, "title": recommender.title(work_id)}
                for work_id in likes
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
    """Redirect to Random /anime/{work_id}"""
    work_id = recommender.sample_animes(1)[0]
    return RedirectResponse(f"/anime/{work_id}")


@app.get("/anime/{work_id}", response_class=HTMLResponse)
async def index_anime_graph(work_id: int):
    """Index for Each Anime"""
    if not recommender.isknown(work_id):
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
