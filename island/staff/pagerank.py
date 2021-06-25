import random
from collections import defaultdict
from typing import List, Set, Tuple


class PageRank:
    """アニメ-スタッフ 二部グラフ用の PageRank"""

    def __init__(self, relations: Set[Tuple[str, str]], num_staff_freq: int = 3):
        """グラフの構築

        Parameters
        ----------
        relations
            エッジ集合
        num_staff_freq
            登場回数がコレ未満のスタッフ名は使わない
        """
        staff_freq = defaultdict(int)
        for (_, name) in relations:
            staff_freq[name] += 1

        work2name = defaultdict(list)  # work_id -> name
        name2work = defaultdict(list)  # name -> work_id
        for (work, name) in relations:
            if staff_freq[name] < num_staff_freq:
                continue
            work2name[work].append(name)
            name2work[name].append(work)

        # name を経由した work -> work なグラフ
        # graph = name2work . work2name
        graph = defaultdict(list)
        for (u, names) in work2name.items():
            for name in names:
                for v in name2work[name]:
                    graph[u].append(v)

        del work2name
        del name2work
        self.graph = graph

    def ranks(self, cur: str, num: int, depth: int) -> List[Tuple[str, float]]:
        """cur から高々 depth だけ辿って到達する頂点とその確率を返す

        Parameters
        ----------
        cur
            現在地点
        num
            上位いくつ欲しいか
        depth
            残りどれだけ深く潜るか
        """
        if depth <= 0 or len(self.graph[cur]) == 0:
            return [(cur, 1.0)]

        neigh = defaultdict(float)
        m = len(self.graph[cur])
        for u in self.graph[cur]:
            neigh[u] += 1.0 / m

        neigh: List[Tuple[str, float]] = list(neigh.items())
        neigh.sort(key=lambda item: item[1], reverse=True)
        neigh = neigh[:num]

        reached = defaultdict(float)
        for u, p in neigh:
            reached[u] += p
            for v, q in self.ranks(u, num, depth - 1):
                reached[v] += p * q
        reached = list(reached.items())
        reached.sort(key=lambda item: item[1], reverse=True)
        reached = reached[:num]

        return reached
