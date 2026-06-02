from __future__ import annotations
from statistics import mean, median, stdev
from collections import defaultdict

class ProductivityKPI:
    def __init__(self, records: list):
        self.records = records

    def _occupancy(self, record: dict) -> float:
        if record.get('occupancy') is not None:
            try:
                return float(record['occupancy'])
            except (TypeError, ValueError):
                pass
        login = record.get('login_duration', 0) or 0
        busy = record.get('busy_duration', 0) or 0
        result = busy / login if login else 0.0
        return min(result, 1.0)

    def _utilization(self, record: dict) -> float:
        if record.get('utilization') is not None:
            try:
                return float(record['utilization'])
            except (TypeError, ValueError):
                pass
        login = record.get('login_duration', 0) or 0
        busy = record.get('busy_duration', 0) or 0
        available = record.get('available_duration', 0) or 0
        result = (busy + available) / login if login else 0.0
        return min(result, 1.0)

    def _productivity_score(self, record: dict) -> float:
        if record.get('productivity_score') is not None:
            try:
                return float(record['productivity_score'])
            except (TypeError, ValueError):
                pass
        occ = min(self._occupancy(record), 1.0)
        util = min(self._utilization(record), 1.0)
        login = max(record.get('login_duration', 0) or 1, 1)
        aux = record.get('aux_duration', 0) or 0
        aux_ratio = min(aux / login, 1.0)
        return (0.5 * occ + 0.3 * util + 0.2 * (1 - aux_ratio)) * 100

    def avg_occupancy(self) -> float:
        vals = [self._occupancy(r) for r in self.records]
        return mean(vals) if vals else 0.0

    def avg_utilization(self) -> float:
        vals = [self._utilization(r) for r in self.records]
        return mean(vals) if vals else 0.0

    def avg_productivity_score(self) -> float:
        vals = [self._productivity_score(r) for r in self.records]
        return mean(vals) if vals else 0.0
    
    

    def occupancy_distribution(self) -> dict:
        vals = [self._occupancy(r) for r in self.records
                if (r.get('login_duration', 0) or 0) > 0]
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
            tl = agent_to_tl.get(r.get('agent_id'))
            if tl and (r.get('login_duration', 0) or 0) > 0:
                buckets[tl].append(self._occupancy(r))
        return {tl: round(mean(v), 3) for tl, v in buckets.items()}