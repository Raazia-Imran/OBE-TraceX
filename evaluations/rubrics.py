"""Versioned rubric rules transcribed from the supplied D1-D7 originals."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
RUBRICS = {
 'D1': {'title': 'Proposal defense', 'maxima': [3, 3, 3, 3], 'plos': [2, 7, 3, 11]},
 'D2': {'title': 'Semester 1 progress', 'maxima': [5, 5, 5, 5], 'plos': [2, 8, 9, 10]},
 'D3': {'title': 'Semester 1 evaluation', 'maxima': [12, 12, 12, 12], 'plos': [2, 3, 11, 10]},
 'D4': {'title': 'Semester 2 progress', 'maxima': [16, 8, 8, 8, 8], 'plos': [2, 8, 9, 10, 11]},
 'D5': {'title': 'Final report', 'maxima': [4] * 8, 'plos': [2, 3, 3, 12, 7, 8, 10, 10]},
 'D6': {'title': 'Final evaluation', 'maxima': [8] * 5, 'plos': [10] * 5},
}
STAGES = tuple(RUBRICS)
STAGE_CHOICES = [(k, f'{k} · {v["title"]}') for k, v in RUBRICS.items()]
RULESET = 'ned-supplied-d1-d6-v1'
def seat_number(value):
    value = str(value).strip().upper()
    if not re.fullmatch(r'[A-Z]{2}-[0-9]{5}', value):
        raise ValueError('Seat number must use AA-00000, for example SE-24001.')
    return value

def number(value):
    if value is None or isinstance(value, bool) or str(value).strip() == '':
        raise ValueError('A required mark is missing.')
    try: result = Decimal(str(value))
    except InvalidOperation as error: raise ValueError('Invalid mark.') from error
    if not result.is_finite(): raise ValueError('Marks must be finite numbers.')
    return result

def percentage(value):
    match = re.search(r'\((\d+)\s*%\)', str(value))
    if not match or int(match[1]) not in (0, 25, 50, 75, 100):
        raise ValueError('Expected an approved rubric percentage in parentheses.')
    return Decimal(match[1])

def weighted(stage, percentages):
    maxima = RUBRICS[stage]['maxima']
    if len(percentages) != len(maxima): raise ValueError('Wrong criterion count.')
    values = [number(x) for x in percentages]
    if any(x not in (0, 25, 50, 75, 100) for x in values): raise ValueError('Invalid attainment level.')
    if stage == 'D4' and values[-1] not in (0, 100): raise ValueError('D4 timely submission must be 0 or 100 percent.')
    return [x * Decimal(m) / 100 for x, m in zip(values, maxima)]

def display(value):
    return format(number(value).quantize(Decimal('.01'), rounding=ROUND_HALF_UP), '.2f')
