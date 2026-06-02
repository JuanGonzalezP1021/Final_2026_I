from statistics import mean, stdev

class ContactKPICalculator:
    def __init__(self, records: list[dict]):
        self.records = records

    def aht(self, filter_fn=None) -> float:
        recs = [r for r in self.records if (filter_fn is None or filter_fn(r))]
        
        total_handle = sum(r['handle_time'] + r['acw'] for r in recs)
        total_contacts = sum(r['inbound_tx'] + r['outbound_tx'] for r in recs)
        
        return total_handle / total_contacts if total_contacts else 0

    def aht_by_channel(self) -> dict:
        return {
            ch: self.aht(lambda r, c=ch: r['channel'] == c)
            for ch in ('Phone', 'Chat', 'Email')
        }

    def missed_rate(self, agent_id: str, date: str) -> float:
        recs = [r for r in self.records if r['agent_id'] == agent_id and r['date'] == date]
        
        missed = sum(r['missed_contacts'] for r in recs)
        offered = sum(r['inbound_tx'] + r['missed_contacts'] for r in recs)
        
        return missed / offered if offered else 0

    def aht_outlier_threshold(self, channel: str) -> float:
        """Returns mean + 2 sigma for BR-04 enforcement."""
        ahts = []
        for r in self.records:
            if r['channel'] != channel:
                continue
                
            tx = r['inbound_tx'] + r['outbound_tx']
            if tx == 0:
                continue
                
            ahts.append((r['handle_time'] + r['acw']) / tx)
            
        if len(ahts) < 2:
            return float('inf')
            
        return mean(ahts) + 2 * stdev(ahts)