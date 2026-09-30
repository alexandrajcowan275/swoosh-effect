"""Add official fall/winter sport observations without inventing year-end scores."""
import hashlib
import json
import re
from pathlib import Path
import pandas as pd
import pdfplumber
from parse_standings import ROOT

FALL = ["Women's Cross Country", "Men's Cross Country", "Women's Field Hockey",
        'Football (FBS)', 'Football (FCS)', "Women's Soccer", "Men's Soccer",
        "Women's Volleyball", "Men's Water Polo"]
WINTER = ["Women's Basketball", "Men's Basketball", "Women's Bowling", 'Fencing',
          "Women's Gymnastics", "Men's Gymnastics", "Women's Ice Hockey",
          "Men's Ice Hockey", 'Rifle', 'Skiing', "Women's Swimming and Diving",
          "Men's Swimming and Diving", "Women's Indoor Track and Field",
          "Men's Indoor Track and Field", "Men's Wrestling"]
WINTER_2026 = WINTER[:3] + ["Women's Fencing", "Men's Fencing"] + WINTER[4:-1] + ["Women's Wrestling", "Men's Wrestling"]


def normalized(value):
    return ''.join(c.lower() for c in value if c.isalnum())


def identify(prefix, schools):
    """Match a school already in the same season's final PDF; fail on unknowns.

    Ignore only punctuation/spacing/case, not substantive name differences.
    Longest prefix avoids conflating e.g. Michigan and Michigan State.
    """
    normalized_prefix = normalized(prefix)
    candidates = [s for s in schools if normalized_prefix.startswith(normalized(s))]
    if not candidates:
        raise ValueError(f'Unmatched seasonal school/conference: {prefix!r}')
    school = max(candidates, key=lambda s: len(normalized(s)))
    length = len(normalized(school))
    count = 0
    for index, character in enumerate(prefix):
        count += character.isalnum()
        if count == length:
            # Include closing school-name punctuation before the conference.
            end = index + 1
            while end < len(prefix) and prefix[end] in ').':
                end += 1
            return school, prefix[:end].strip(), prefix[end:].strip()
    raise ValueError(prefix)


def parse_source(source, schools):
    period, season = source['period'], source['season']
    names = FALL if period == 'fall' else WINTER_2026 if season == '2025-26' else WINTER
    path = ROOT/source['file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError(f'Checksum changed: {path}')
    rows, summaries = [], []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=1)
            if page_number == 1:
                # Reject a source whose columns changed order, even if its count is unchanged.
                header = ('W.CC M.CC W.FH FBS FB FCS FB W.SOC M.SOC W.VB M.WP'
                          if period == 'fall' else
                          'W.BB M.BB W.Bowl Fencing W.Gym M.Gym W.IHoc M.IHoc Rifle Skiing W.SW M.SW W.In.T&F M.In.T&F M.WR')
                if period == 'winter' and season == '2025-26':
                    header = header.replace('Fencing', 'W.Fencing M.Fencing').replace('M.WR', 'W.WR M.WR')
                if normalized(header) not in normalized(text):
                    raise ValueError(f'Unexpected sport column order: {season} {period}')
            for line in text.splitlines():
                if not re.match(r'^\d+\s+\D', line):
                    continue
                match = re.fullmatch(r'(\d+)\s+(.+?)\s*(FBS|FCS|DI)\s+(.+)', line)
                if not match:
                    raise ValueError(f'Unparsed source row: {season} {period} {line}')
                rank, prefix, division, values = match.groups()
                school, source_school, conference = identify(prefix, schools)
                cells = re.sub(r'(?<=\d)(COVID)', r' \1', values).split()
                expected = 1+2*len(names)+(2 if period == 'winter' else 0)
                if len(cells) != expected:
                    raise ValueError(f'{season} {period} {school}: {len(cells)} cells != {expected}: {cells}')
                total = float(cells[0])
                period_total = total if period == 'fall' else float(cells[-2])
                fall_total = total if period == 'fall' else float(cells[-1])
                summary = dict(season=season, school=school, period=period, source_rank=int(rank),
                               source_school=source_school, source_conference=conference, division=division,
                               published_cumulative_points=total, published_period_points=period_total,
                               published_fall_points=fall_total, source_url=source['source_url'], source_page=page_number)
                summaries.append(summary)
                for i, sport in enumerate(names):
                    place, value = cells[1+2*i:3+2*i]
                    excluded = value.lower() == 'x'
                    points = None if excluded or value == '##' else float(value)
                    rows.append(dict(summary, sport=sport, sport_points=points,
                                     source_value=value, source_place=place,
                                     sport_place=int(place) if place.isdigit() else None,
                                     excluded_at_publication=excluded, value_method='printed',
                                     published_counted_points=0.0 if excluded else points))
    result = pd.DataFrame(rows)
    # Three PDF cells display Excel overflow ('##'). Recover a value only
    # when the row has exactly one unknown and its published subtotal fixes it.
    for school, group in result.groupby('school'):
        hidden = group.index[group.source_value == '##']
        if len(hidden):
            if len(hidden) != 1:
                raise ValueError(f'Multiple unknown source cells: {season} {school}')
            recovered = round(group.published_period_points.iloc[0] - group.published_counted_points.sum(), 2)
            if not 0 <= recovered <= 100:
                raise ValueError(f'Invalid recovered overflow cell: {season} {school}: {recovered}')
            result.loc[hidden, ['sport_points','published_counted_points']] = recovered
            result.loc[hidden, 'value_method'] = 'derived_from_published_subtotal_single_overflow_cell'
    return result, pd.DataFrame(summaries)


def main():
    final = pd.read_csv(ROOT/'data/processed/standings.csv')
    all_rows, all_summaries = [], []
    for source in json.loads((ROOT/'data/seasonal_sources.json').read_text()):
        names = final.loc[final.season==source['season'], 'school'].tolist()
        rows, summaries = parse_source(source, names)
        all_rows.append(rows); all_summaries.append(summaries)
        print(source['season'], source['period'], len(summaries), 'school rows', flush=True)
    rows = pd.concat(all_rows, ignore_index=True)
    summaries = pd.concat(all_summaries, ignore_index=True)
    rows.to_csv(ROOT/'data/processed/seasonal_sport_observations.csv', index=False)
    summaries.to_csv(ROOT/'data/processed/seasonal_standings.csv', index=False)

if __name__ == '__main__': main()
