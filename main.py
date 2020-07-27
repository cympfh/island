import collections
import random
from typing import List, Optional, Tuple

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
        fact.fit(item_users=X, show_progress=False)
        self.fact = fact

    def stat(self):
        """Debug"""
        print(
            f"Size: {len(self.rows)} x {len(self.cols)} = {len(self.rows) * len(self.cols)}"
        )
        print(
            f"{len(self.data)} cells have non-zero values (density={len(self.data) / len(self.rows) / len(self.cols)})"
        )

    def recommend(self, likes: List[str], k: int) -> List[Tuple[str, float]]:
        """Run Recommendation

        Parameters
        ----------
        likes
            List of annict_id
        k
            num of returns

        Returns
        -------
        List of annict_id
        """
        user_items = lil_matrix((1, len(self.rows)))
        for annict_id in likes:
            if annict_id in self.row_id:
                i = self.row_id[annict_id]
                user_items[(0, i)] = 2.0
        recommend_items = self.fact.recommend(
            0,
            user_items.tocsr(),
            k,
            filter_already_liked_items=True,
            recalculate_user=True,
        )
        return [(self.rows[int(i)], float(score)) for i, score in recommend_items]


class Recommendation:
    """Recommendation has a Matrix"""

    def __init__(
        self, dataset_path: str, limit_anime: int, limit_user: int,
    ):
        """init

        Parameters
        ----------
        dataset_path
            File Path of csv(annict_id, user_id, rating)
        limit_anime
            sub limit of freq of anime
        limit_user
            sub limit of freq of user
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
                return 4
            return 0.5

        with open(dataset_path) as f:
            for line in f:
                annict_id, user_id, rating = line.strip("\n").split("\t", 2)
                count_anime[annict_id] += 1
                count_user[user_id] += 1
                if rating == "null":
                    continue
                rows.append((annict_id, user_id, rate(rating)))

        mat = Matrix()

        for annict_id, user_id, ratevalue in rows:
            if count_anime[annict_id] < limit_anime:
                continue
            if count_user[user_id] < limit_user:
                continue
            mat.insert(annict_id, user_id, ratevalue)

        mat.stat()
        mat.decomposition(factors=100)

        self.mat = mat
        self.titles = titles
        self.images = images
        self.test()

    def isknown(self, annict_id: str) -> bool:
        """Known Anime?"""
        return annict_id in self.mat.row_id

    def title(self, annict_id: str) -> Optional[str]:
        """Anime Title"""
        return self.titles.get(annict_id, None)

    def image(self, annict_id: str) -> str:
        """Anime Image Url"""
        return self.images.get(annict_id, None)

    def sample_animes(self, n: int) -> str:
        """Returns List of random annict_id"""
        return random.sample(self.mat.rows, n)

    def similar_items(self, annict_id: str, n: int) -> List[Tuple[str, float]]:
        """Similar animes

        Returns
        -------
        List of (annict_id: str, score: float)
        """
        if not self.isknown(annict_id):
            return []
        i = self.mat.row_id[annict_id]
        similars = self.mat.fact.similar_items(i, n + 1)
        return [
            (self.mat.rows[int(j)], float(score))
            for j, score in similars
            if int(j) != i
        ][:n]

    def __call__(self, likes: List[str], k: int) -> List[Tuple[str, float]]:
        """Alias"""
        if not any(self.isknown(annict_id) for annict_id in likes):
            return []
        return self.mat.recommend(likes, k)

    def test(self):
        """Self Testing"""
        random.seed(42)
        sample_user_indices = random.sample(list(range(len(self.mat.cols))), 200)
        # collect likes
        likes = collections.defaultdict(list)
        for (annict_idx, user_idx), rating in self.mat.data.items():
            if user_idx not in sample_user_indices:
                continue
            if rating < 0:
                continue
            annict_id = self.mat.rows[annict_idx]
            likes[user_idx].append(annict_id)
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
        print(f"Acc@1 = { acc1 / num }")
        print(f"Acc@5 = { acc5 / num }")
        print(f"Acc@10 = { acc10 / num }")
        print(f"Acc@20 = { acc20 / num }")


class MixRecommendation:
    """Wrapper of Recommendation"""

    def __init__(self):
        """Init child recommenders"""
        self.children = [
            Recommendation("./dataset/reviews.csv", limit_anime=1, limit_user=4),
            Recommendation("./dataset/records.csv", limit_anime=1, limit_user=2),
        ]

    def sample_animes(self, k: int) -> List[str]:
        """Returns List of annict_id"""
        i = random.randrange(len(self.children))
        return random.sample(self.children[i].mat.rows, k)

    def title(self, annict_id: str) -> Optional[str]:
        """anime title"""
        for child in self.children:
            t = child.title(annict_id)
            if t:
                return t

    def image(self, annict_id: str) -> Optional[str]:
        """image url"""
        for child in self.children:
            t = child.image(annict_id)
            if t:
                return t

    def __call__(self, likes: List[str], k: int) -> List[Tuple[str, float]]:
        """Interleaving of recommend of children"""
        items = sum([child(likes, k) for child in self.children], [])
        items.sort(key=lambda item: item[1], reverse=True)
        used = set()
        ret = []
        for aid, score in items:
            if aid in used:
                continue
            used.add(aid)
            ret.append((aid, score))
        return ret[:k]

    def isknown(self, annict_id: str) -> bool:
        """is-known by any children"""
        for child in self.children:
            if child.isknown(annict_id):
                return True
        return False

    def similar_items(self, annict_id: str, n: int) -> List[Tuple[str, float]]:
        """Interleaving of similar_items of children"""
        items = sum([child.similar_items(annict_id, n) for child in self.children], [])
        items.sort(key=lambda item: item[1], reverse=True)
        used = set()
        ret = []
        for aid, score in items:
            if aid in used:
                continue
            used.add(aid)
            ret.append((aid, score))
        return ret[:n]


recommender = MixRecommendation()
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
        aids = recommender.sample_animes(20)
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

    recommend_items = recommender(likes, 20)
    return {
        "items": [
            {
                "annictId": annict_id,
                "title": recommender.title(annict_id),
                "image": recommender.image(annict_id),
                "score": float(score),
            }
            for annict_id, score in recommend_items
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
    annict_id = recommender.sample_animes(1)[0]
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
