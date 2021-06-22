from typing import List, Tuple

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
        for line in open("./dataset/staffs.csv"):
            work_id, names = line.strip().split("\t", 1)
            for name in tokenize(names):
                relations.add((work_id, name))
        self.model = PageRank(relations)

    def similar_items(self, annict_id: str, n: int) -> List[Tuple[str, int]]:
        return self.model.ranks(annict_id, n)
