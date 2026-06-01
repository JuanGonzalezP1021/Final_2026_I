from __future__ import annotations
from statistics import mean, median, stdev
from collections import defaultdict

class ProductivityKPI:
    def __init__(self, records: list):
        self.records = records

    def avg_occupancy(self) -> float:
        vals = [r['occupancy'] for r in self.records
                if r['login_duration'] > 0]
        return mean(vals) if vals else 0.0

    def occupancy_distribution(self) -> dict:
        vals = [r['occupancy'] for r in self.records
                if r['login_duration'] > 0]
        if not vals:
            return {}
        s = sorted(vals)
        return {
            'mean':   round(mean(vals), 3),
            'median': round(median(vals), 3),
            'stdev':  round(stdev(vals), 3) if len(vals) > 1 else 0,
            'p10':    round(s[len(s)//10], 3),
            'p90':    round(s[(len(s)*9)//10], 3),
        }

    def occupancy_by_tl(self, agent_to_tl: dict) -> dict:
        buckets = defaultdict(list)
        for r in self.records:
            tl = agent_to_tl.get(r['agent_id'])
            if tl and r['login_duration'] > 0:
                buckets[tl].append(r['occupancy'])
        return {tl: round(mean(v), 3) for tl, v in buckets.items()}