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

    def random_walk(self, start: str, cur: str, n: int) -> str:
        """ランダムウォークする

        Parameters
        ----------
        start
            始点 (work)
        cur
            現在地点
        n
            あと何歩歩くか
        """
        if n <= 0:
            return cur
        if len(self.graph[cur]) == 0 or (n > 1 and random.random() < 0.5):  # restat
            return self.random_walk(start, start, n - 1)
        v = random.choice(self.graph[cur])
        return self.random_walk(start, v, n - 1)

    def ranks(self, work: str, num: int) -> List[Tuple[str, int]]:
        """work を始点にした近傍頂点のランクを返す

        Parameters
        ----------
        work
            これを始点にする
        num
            返すアイテム数

        Returns
        -------
        (work, rank) の列を返す
            rank は高いほど近傍アイテム
            引数の work は除いている
        """
        count = defaultdict(int)
        for _ in range(num * 40):
            goal = self.random_walk(work, work, 5)
            if goal == work:
                continue
            count[goal] += 1
        items = list(count.items())
        items.sort(key=lambda item: item[1], reverse=True)
        items = items[:num]
        return items
