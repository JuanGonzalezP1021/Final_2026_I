from statistics import mean, stdev
from config import (MAX_CONTACTS_PER_AGENT_DAY,
                    MISSED_THRESHOLD_PER_DAY)
from domain.exceptions.custom_exceptions import BusinessRuleError


def assert_aht_in_range(contact_aht, channel_population_aht):
    '''BR-04: outlier guard via mean + 2 sigma'''
    if len(channel_population_aht) < 30:
        return
    mu = mean(channel_population_aht)
    sd = stdev(channel_population_aht)
    upper = mu + 2 * sd
    if contact_aht > upper:
        raise BusinessRuleError('BR-04',
            f'AHT {contact_aht:.0f}s exceeds mean+2sigma '
            f'({upper:.0f}s)')


def assert_tx_volume(daily_tx_so_far, new_tx):
    '''BR-05: daily transaction sanity cap.'''
    total = daily_tx_so_far + new_tx
    if total > MAX_CONTACTS_PER_AGENT_DAY:
        raise BusinessRuleError('BR-05',
            f'daily transactions {total} exceed max '
            f'{MAX_CONTACTS_PER_AGENT_DAY}')


def assert_missed_threshold(daily_missed):
    '''BR-06: SLA breach threshold.'''
    if daily_missed >= MISSED_THRESHOLD_PER_DAY:
        raise BusinessRuleError('BR-06',
            f'missed contacts {daily_missed} reached '
            f'SLA breach threshold')