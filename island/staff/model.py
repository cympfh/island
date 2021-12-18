from typing import List, Tuple

from island.database import StaffDB
from island.staff.pagerank import PageRank


def tokenize(names: str) -> List[str]:
    ls = names.split("、")
    ls = [name for name in ls if len(name) < 10]
    return ls


class StaffModel:
    def __init__(self):
        """
        データセットの読み込み, PageRank モデルの構築
        """
        relations = set()
        for _id, names, work_id, _dt in StaffDB():
            for name in tokenize(names):
                relations.add((work_id, name))
        self.model = PageRank(relations)

    def similar_items(self, work_id: str, num: int) -> List[Tuple[str, float]]:
        """ここで自分自身を除く"""
        res = self.model.ranks(work_id, num + 3, depth=3)
        return [(u, p) for u, p in res if u != work_id][:num]
