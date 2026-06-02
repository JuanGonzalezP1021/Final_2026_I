from collections import Counter
from config import MAX_AGENTS_PER_TL

class AgentKPI:
    def __init__(self, agents: list[dict]):
        self.agents = agents

    def headcount(self) -> int:
        return len(self.agents)

    def headcount_by_tl(self) -> dict[str, int]:
        return dict(Counter(a['team_manager'] for a in self.agents))

    def tenurity_mix(self) -> dict[str, float]:
        n = len(self.agents) or 1
        counts = Counter(a['tenurity'] for a in self.agents)
        return {t: round(c / n, 3) for t, c in counts.items()}

    def attrition_risk(self) -> float:
        n = len(self.agents) or 1
        new_hires = sum(1 for a in self.agents if a['tenurity'] == 'New Hire')
        return round(new_hires / n, 3)

    def tls_over_capacity(self) -> list[tuple[str, int]]:
        return [
            (tl, n) for tl, n in self.headcount_by_tl().items()
            if n > MAX_AGENTS_PER_TL
        ]