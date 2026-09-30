"""Hand-implemented interval merging and dynamic-programming name distance."""
from datetime import date


def _season_year(season):
    """Validate YYYY-YY and return its first calendar year."""
    if (not isinstance(season, str) or len(season) != 7 or season[4] != '-'
            or not season[:4].isascii() or not season[:4].isdigit()
            or not season[5:].isascii() or not season[5:].isdigit()):
        raise ValueError(f'Invalid season: {season!r}; expected YYYY-YY')
    year = int(season[:4])
    if not 1 <= year <= 9998 or int(season[5:]) != (year + 1) % 100:
        raise ValueError(f'Invalid consecutive-year season: {season!r}')
    return year


def _season(year):
    return f'{year:04d}-{(year + 1) % 100:02d}'


def _lower_bound(values, target):
    """First position whose value is >= target; O(log n) time, O(1) space."""
    left, right = 0, len(values)
    while left < right:
        middle = (left + right) // 2
        if values[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left


def _prefer_anchor(first, second):
    # A wins corroborating A/B overlap; equal tiers preserve original input order.
    return min((first, second), key=lambda item: (item[0]['evidence_tier'], item[1]))


def merge_intervals(intervals, *, seasons, transitions=()):
    """Merge one school's direct evidence and infer only bounded Tier C gaps.

    ``intervals`` contains dictionaries with inclusive ``start_season``,
    ``end_season``, ``brand`` and direct ``evidence_tier`` (A or B). Other
    metadata is retained in the original anchor dictionaries. ``seasons`` is
    the explicit analysis window: missing calendar seasons are never created
    as inferred observations. ``transitions`` contains ISO dates for this school.

    Returns ``periods``, ``gaps`` and ``inferred`` lists. Periods are calendar-
    contiguous runs of assigned analysis seasons, with start_season, end_season,
    brand and covered_seasons. Gaps describe missing calendar ranges between
    direct runs, including endpoint gaps and excluded-season-only gaps. Each
    gap records its candidate ``seasons``, original left/right direct anchors,
    an ``inferred`` boolean and a reason. Inferred observations contain season,
    brand, left_anchor and right_anchor; the caller adds Tier C provenance.

    Overlapping different brands raise ValueError; adjacent different brands
    remain separate. Same-brand gaps require original A/B anchors and no known
    transition from the left anchor season's July 1 through the right anchor
    season's June 30, inclusive. No endpoint extrapolation or C-to-C anchoring
    occurs. Inputs are not mutated. Equal-tier duplicate evidence uses the first
    input record, while A takes precedence over B for corroborating anchors.

    For n intervals, s requested seasons, t transitions and g gaps, time is
    O(n log n + n log(s+1) + s log s + t log t + g log(t+1) + s);
    auxiliary space is O(n + s + t), excluding the metadata owned by callers.
    Merging, searches and inference use explicit loops, not interval libraries.
    """
    records = list(intervals)
    requested = sorted({_season_year(value) for value in seasons})
    transition_dates = []
    for value in transitions:
        if not isinstance(value, str):
            raise ValueError('Transition dates must be ISO YYYY-MM-DD strings')
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f'Invalid transition date: {value!r}') from error
        if parsed.isoformat() != value:
            raise ValueError(f'Invalid transition date: {value!r}')
        transition_dates.append(value)
    transition_dates.sort()

    normalized = []
    for order, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError('Every interval must be a dictionary')
        if not {'start_season', 'end_season', 'brand', 'evidence_tier'} <= record.keys():
            raise ValueError('Intervals need start_season, end_season, brand and evidence_tier')
        start, end = _season_year(record['start_season']), _season_year(record['end_season'])
        if start > end:
            raise ValueError('Interval start_season must not follow end_season')
        if record['evidence_tier'] not in ('A', 'B'):
            raise ValueError('Only original A/B evidence can anchor continuity')
        if not isinstance(record['brand'], str) or not record['brand'].strip():
            raise ValueError('Every interval needs a nonempty brand')
        normalized.append(dict(start=start, end=end, brand=record['brand'],
                               first=(record, order), last=(record, order)))
    normalized.sort(key=lambda item: (item['start'], item['end']))

    # Check conflicts before window clipping: contradictory inputs cannot vanish
    # merely because their overlapping season was omitted from the analysis.
    merged = []
    for incoming in normalized:
        if not merged:
            merged.append(incoming.copy())
            continue
        current = merged[-1]
        overlaps = incoming['start'] <= current['end']
        adjacent = incoming['start'] == current['end'] + 1
        if overlaps and current['brand'] != incoming['brand']:
            raise ValueError('Overlapping intervals assign different brands')
        if current['brand'] == incoming['brand'] and (overlaps or adjacent):
            if incoming['start'] == current['start']:
                current['first'] = _prefer_anchor(current['first'], incoming['first'])
            if incoming['end'] > current['end']:
                current['end'], current['last'] = incoming['end'], incoming['last']
            elif incoming['end'] == current['end']:
                current['last'] = _prefer_anchor(current['last'], incoming['last'])
        else:
            merged.append(incoming.copy())
    if not requested:
        return {'periods': [], 'gaps': [], 'inferred': []}

    # Clip to the requested analysis window. Direct evidence outside either end
    # cannot become an anchor for a Tier C observation at a window endpoint.
    direct = []
    for interval in merged:
        first = _lower_bound(requested, interval['start'])
        after = _lower_bound(requested, interval['end'] + 1)
        if first == after:
            continue
        direct.append({**interval, 'start': requested[first], 'end': requested[after - 1]})

    gaps, inferred = [], []

    def add_gap(start, end, left, right):
        if start > end:
            return
        first, after = _lower_bound(requested, start), _lower_bound(requested, end + 1)
        candidates = requested[first:after]
        reason = 'unbounded'
        can_infer = False
        if left is not None and right is not None:
            if left['brand'] != right['brand']:
                reason = 'different_brands'
            else:
                transition_start = f"{left['end']:04d}-07-01"
                transition_end = f"{right['start'] + 1:04d}-06-30"
                position = _lower_bound(transition_dates, transition_start)
                blocked = (position < len(transition_dates)
                           and transition_dates[position] <= transition_end)
                reason = 'known_transition' if blocked else 'bounded_same_brand'
                can_infer = not blocked
        if not candidates:
            reason, can_infer = 'excluded_seasons_only', False
        left_anchor = left['last'][0] if left else None
        right_anchor = right['first'][0] if right else None
        gaps.append(dict(start_season=_season(start), end_season=_season(end),
                         seasons=[_season(year) for year in candidates],
                         left_anchor=left_anchor, right_anchor=right_anchor,
                         inferred=can_infer, reason=reason))
        if can_infer:
            for year in candidates:
                inferred.append(dict(season=_season(year), brand=left['brand'],
                                     left_anchor=left_anchor, right_anchor=right_anchor))

    if not direct:
        add_gap(requested[0], requested[-1], None, None)
    else:
        add_gap(requested[0], direct[0]['start'] - 1, None, direct[0])
        for left, right in zip(direct, direct[1:]):
            add_gap(left['end'] + 1, right['start'] - 1, left, right)
        add_gap(direct[-1]['end'] + 1, requested[-1], direct[-1], None)

    assignments = {int(row['season'][:4]): row['brand'] for row in inferred}
    position = 0
    for year in requested:
        while position < len(direct) and direct[position]['end'] < year:
            position += 1
        if position < len(direct) and direct[position]['start'] <= year:
            assignments[year] = direct[position]['brand']
    periods = []
    for year in requested:
        if year not in assignments:
            continue
        season, brand = _season(year), assignments[year]
        if (periods and periods[-1]['brand'] == brand
                and int(periods[-1]['end_season'][:4]) + 1 == year):
            periods[-1]['end_season'] = season
            periods[-1]['covered_seasons'].append(season)
        else:
            periods.append(dict(start_season=season, end_season=season,
                                brand=brand, covered_seasons=[season]))
    return {'periods': periods, 'gaps': gaps, 'inferred': inferred}


def edit_distance(a, b):
    """Return Unicode-code-point Levenshtein distance using two-row DP.

    Insertions, deletions and substitutions each cost one. This function does
    no normalization; the caller controls case, whitespace and matching policy.
    For input lengths m and n, time is O(m*n) and auxiliary space is
    O(min(m,n)); empty-input initialization takes O(max(m,n)) or less time.
    No distance library or approximate-matching shortcut is used.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError('edit_distance inputs must be strings')
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for row, char_a in enumerate(a, start=1):
        current = [row]
        for column, char_b in enumerate(b, start=1):
            insertion = current[column - 1] + 1
            deletion = previous[column] + 1
            substitution = previous[column - 1] + (char_a != char_b)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]
