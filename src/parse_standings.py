"""Parse NACDA final PDFs with pdfplumber, preserving published spring coverage.

The final PDFs contain 14 spring sports plus fall/winter subtotals, NOT every
sport. Never invent the missing sport breakdown or the value behind an 'x'.
"""
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ['Baseball', "Women's Golf", "Men's Golf", "Women's Lacrosse",
          "Men's Lacrosse", "Women's Rowing", 'Softball', "Women's Tennis",
          "Men's Tennis", "Women's Outdoor Track and Field",
          "Men's Outdoor Track and Field", "Men's Volleyball",
          "Women's Water Polo", "Women's Beach Volleyball"]


def parse_pdf(path, season, source_url):
    """Return one school-season table and a long spring-sport table.

    Numeric sport_points are published counted points. An x has unknown raw
    points (null), excluded=True, and counted_points=0. Explicit zeros stay 0.
    Column boundaries come from the PDF's actual header cells, not name guesses.
    """
    schools, sports = [], []
    expected_row_count = 0
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            expected_row_count += sum(bool(re.match(r'^\d+\s+\D', line)) for line in (page.extract_text() or '').splitlines())
            tables = page.find_tables()
            if not tables:
                raise ValueError(f'{season} page {page_number}: missing header table')
            # Header cells below merged note: locate the row with Institution.
            header = next((row for row in tables[0].rows
                           if any(cell and 'Institution' in (page.crop(cell).extract_text() or '')
                                  for cell in row.cells)), None)
            if header is None:
                # Some last pages omit the bottom header row; earlier page geometry is unchanged.
                if page_number == 1:
                    raise ValueError('No Institution header')
            else:
                school_cell, conference_cell, division_cell = header.cells[1:4]
                school_left, conference_left, division_left = school_cell[0], conference_cell[0], division_cell[0]
            words = page.extract_words(x_tolerance=1, y_tolerance=2)
            rank_words = [w for w in words if w['x1'] < school_left and re.fullmatch(r'\d+', w['text'])]
            for rank_word in rank_words:
                row = sorted([w for w in words if abs(w['top']-rank_word['top']) < 1.5], key=lambda w:w['x0'])
                school = ' '.join(w['text'] for w in row if school_left <= w['x0'] < conference_left)
                conference = ' '.join(w['text'] for w in row if conference_left <= w['x0'] < division_left)
                tail = [w['text'] for w in row if w['x0'] >= division_left]
                if 'Regional' in tail:
                    i = tail.index('Regional')
                    if tail[i:i+2] == ['Regional', 'Canceled']:
                        tail[i:i+2] = ['Regional Canceled']
                if len(tail) == 32 and re.fullmatch(r'\d+(?:\.\d+)?', tail[0]):
                    # A tight PDF gap can merge the division into the conference word.
                    match = re.fullmatch(r'(.*?)(FBS|FCS|DI)', conference)
                    if not match:
                        raise ValueError(f'{season}: unparsed division for {school}: {conference}')
                    conference, division_token = match.groups()
                    conference = conference.strip()
                    tail.insert(0, division_token)
                if len(tail) != 33:
                    raise ValueError(f'{season} page {page_number}, {school}: expected division + 32 cells, got {tail}')
                # Visually verified source-layout exceptions. These split printed
                # text only; they do not infer historical conference membership.
                if season in {'2017-18', '2018-19'} and school == "St. Mary's College of CaliforniaWCC" and not conference:
                    school, conference = "St. Mary's College of California", 'WCC'
                if season == '2022-23' and school == 'Merrimack Northeast' and conference == '(Fall 2023)':
                    school, conference = 'Merrimack', 'Northeast (Fall 2023)'
                if not school or not conference:
                    raise ValueError(f'{season}: blank school/conference: {school!r}, {conference!r}')
                division, *values = tail
                total = float(values[0])
                subtotals = dict(zip(['fall', 'winter', 'spring'] if season in ['2017-18','2018-19'] else ['spring','winter','fall'], map(float, values[-3:])))
                base = dict(season=season, school=school, conference=conference,
                            rank=int(rank_word['text']), total_points=total)
                schools.append(dict(base, division=division, **{k+'_points':v for k,v in subtotals.items()},
                                    source_url=source_url, source_page=page_number))
                for index, sport in enumerate(SPORTS):
                    place, raw = values[1+2*index:3+2*index]
                    excluded = raw.lower() == 'x'
                    points = None if excluded else float(raw)
                    sports.append(dict(base, sport=sport, sport_points=points,
                                       sport_place=int(place) if place.isdigit() else None, source_place=place, excluded=excluded,
                                       counted_points=0.0 if excluded else points,
                                       source_value=raw, source_url=source_url, source_page=page_number))
    if len(schools) != expected_row_count:
        raise ValueError(f'{season}: coordinate rows {len(schools)} != text rows {expected_row_count}')
    return pd.DataFrame(schools), pd.DataFrame(sports)


def main():
    standings, sport_frames, validations = [], [], []
    for source in json.loads((ROOT/'data/sources.json').read_text()):
        path = ROOT/source['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Raw PDF checksum changed: {path}')
        school, sport = parse_pdf(path, source['season'], source['source_url'])
        assert not school.duplicated(['season','school']).any()
        assert school['total_points'].is_monotonic_decreasing
        assert school['rank'].equals(school.total_points.rank(method='min', ascending=False).astype(int))
        school['points_pctile'] = school.total_points.rank(method='average', pct=True)*100
        sport = sport.merge(school[['season','school','points_pctile']], on=['season','school'], validate='many_to_one')
        spring = sport.groupby('school').counted_points.sum()
        spring_error = (school.set_index('school').spring_points-spring).abs()
        total_error = (school.total_points-school[['spring_points','winter_points','fall_points']].sum(axis=1)).abs()
        assert spring_error.max() < 0.011, f'{source["season"]}: spring sum mismatch'
        assert total_error.max() < 0.011, f'{source["season"]}: total sum mismatch'
        expected_top5 = json.loads((ROOT/'tests/fixtures/top5.json').read_text())[source['season']]
        assert school.head(5)[['school','total_points']].values.tolist() == expected_top5
        validations.append(dict(season=source['season'], school_rows=len(school), sport_rows=len(sport),
                                max_spring_sum_error=float(spring_error.max()), max_total_sum_error=float(total_error.max()),
                                spring_mismatches=school.loc[school.school.map(spring_error)>0.11,['school','spring_points']].to_dict('records'),
                                top5=school.head(5)[['rank','school','total_points']].to_dict('records'),
                                coverage='14 spring sports; fall/winter subtotals only'))
        standings.append(school); sport_frames.append(sport)
    out = ROOT/'data/processed'; out.mkdir(exist_ok=True)
    pd.concat(standings).to_csv(out/'standings.csv', index=False)
    long = pd.concat(sport_frames)
    long.to_csv(out/'spring_sport_points.csv', index=False)
    (ROOT/'reports/validation.json').write_text(json.dumps(validations, indent=2)+'\n')
    print(pd.DataFrame(validations).drop(columns=['top5','spring_mismatches','coverage']).to_string(index=False))
    print(long.head(10).drop(columns=['source_url']).to_string(index=False))

if __name__ == '__main__':
    main()
