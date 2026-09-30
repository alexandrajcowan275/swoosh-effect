"""Boundary behavior for the hand-implemented algorithms."""
from copy import deepcopy
import pytest
from src.algorithms import edit_distance, merge_intervals


def evidence(start, end=None, brand='Nike', tier='A', **metadata):
    return dict(start_season=start, end_season=end or start, brand=brand,
                evidence_tier=tier, **metadata)


def test_empty_intervals_and_seasons():
    assert merge_intervals([], seasons=[]) == {'periods': [], 'gaps': [], 'inferred': []}
    result = merge_intervals([], seasons=['2021-22'])
    assert result['periods'] == result['inferred'] == []
    assert result['gaps'][0]['reason'] == 'unbounded'
    assert merge_intervals([evidence('2021-22')], seasons=[])['periods'] == []


def test_overlap_adjacent_and_nested_intervals_merge_without_inference():
    rows = [evidence('2021-22', '2022-23'), evidence('2018-19', '2020-21'),
            evidence('2019-20', '2021-22'), evidence('2019-20')]
    saved = deepcopy(rows)
    seasons = ['2018-19', '2019-20', '2020-21', '2021-22', '2022-23']
    result = merge_intervals(rows, seasons=seasons)
    assert result['periods'] == [dict(start_season='2018-19', end_season='2022-23',
                                     brand='Nike', covered_seasons=seasons)]
    assert result['inferred'] == result['gaps'] == []
    assert rows == saved


def test_conflicting_overlap_raises_even_if_conflict_season_is_excluded():
    rows = [evidence('2018-19', '2020-21'), evidence('2019-20', brand='adidas')]
    with pytest.raises(ValueError, match='different brands'):
        merge_intervals(rows, seasons=['2018-19', '2020-21'])


def test_adjacent_different_brands_remain_separate():
    result = merge_intervals([evidence('2020-21'), evidence('2021-22', brand='adidas')],
                             seasons=['2020-21', '2021-22'])
    assert len(result['periods']) == 2
    assert result['gaps'] == result['inferred'] == []


def test_same_brand_gap_fills_from_original_direct_anchors_only():
    left = evidence('2018-19', source_url='left', season='2018-19')
    right = evidence('2022-23', tier='B', source_url='right', season='2022-23')
    seasons = ['2017-18', '2018-19', '2020-21', '2021-22', '2022-23', '2023-24']
    result = merge_intervals([left, right], seasons=seasons)
    assert [row['season'] for row in result['inferred']] == ['2020-21', '2021-22']
    assert all(row['left_anchor'] is left and row['right_anchor'] is right
               for row in result['inferred'])
    assert [gap['reason'] for gap in result['gaps']] == [
        'unbounded', 'bounded_same_brand', 'unbounded']
    assert [p['covered_seasons'] for p in result['periods']] == [
        ['2018-19'], ['2020-21', '2021-22', '2022-23']]


@pytest.mark.parametrize('transition', ['2018-07-01', '2020-01-01', '2023-06-30'])
def test_transition_in_either_anchor_season_or_gap_blocks_continuity(transition):
    result = merge_intervals([evidence('2018-19'), evidence('2022-23')],
                             seasons=['2018-19', '2020-21', '2022-23'],
                             transitions=[transition])
    assert result['inferred'] == []
    assert result['gaps'][0]['reason'] == 'known_transition'


def test_outside_transition_dates_do_not_block_and_switch_back_does():
    rows = [evidence('2018-19'), evidence('2022-23')]
    seasons = ['2018-19', '2020-21', '2022-23']
    assert len(merge_intervals(rows, seasons=seasons,
                              transitions=['2018-06-30', '2023-07-01'])['inferred']) == 1
    assert merge_intervals(rows, seasons=seasons,
                           transitions=['2020-07-01', '2021-07-01'])['inferred'] == []


def test_different_brand_gap_does_not_fill_and_c_cannot_anchor():
    result = merge_intervals([evidence('2020-21'), evidence('2022-23', brand='adidas')],
                             seasons=['2020-21', '2021-22', '2022-23'])
    assert result['inferred'] == []
    assert result['gaps'][0]['reason'] == 'different_brands'
    with pytest.raises(ValueError, match='original A/B'):
        merge_intervals([evidence('2020-21', tier='C')], seasons=['2020-21'])


def test_excluded_season_is_detected_but_never_minted_as_observation():
    result = merge_intervals([evidence('2018-19'), evidence('2020-21')],
                             seasons=['2018-19', '2020-21'])
    assert result['inferred'] == []
    assert result['gaps'][0]['reason'] == 'excluded_seasons_only'
    assert result['gaps'][0]['start_season'] == '2019-20'
    assert result['gaps'][0]['seasons'] == []
    assert len(result['periods']) == 2


def test_anchor_provenance_uses_nearest_direct_boundary_and_a_precedence():
    first = evidence('2017-18', source_url='old')
    left_b = evidence('2018-19', tier='B', source_url='left_b')
    left_a = evidence('2018-19', source_url='left_a')
    right = evidence('2021-22', tier='B', source_url='right')
    result = merge_intervals([first, left_b, left_a, right],
                             seasons=['2017-18', '2018-19', '2020-21', '2021-22'])
    assert result['inferred'][0]['left_anchor'] is left_a
    assert result['inferred'][0]['right_anchor'] is right


def test_outside_window_anchors_cannot_fill_either_window_endpoint():
    result = merge_intervals([evidence('2017-18'), evidence('2022-23')],
                             seasons=['2018-19', '2020-21', '2021-22'])
    assert result['inferred'] == result['periods'] == []


@pytest.mark.parametrize('season', ['2021-23', '2021', '21-22', '2021/22', '0000-01'])
def test_invalid_seasons_raise(season):
    with pytest.raises(ValueError, match='season'):
        merge_intervals([], seasons=[season])


def test_reversed_interval_and_invalid_date_raise():
    with pytest.raises(ValueError, match='must not follow'):
        merge_intervals([evidence('2022-23', '2021-22')], seasons=['2021-22'])
    with pytest.raises(ValueError, match='date'):
        merge_intervals([], seasons=[], transitions=['2021-02-30'])


@pytest.mark.parametrize(('a', 'b', 'expected'), [
    ('', '', 0), ('', 'school', 6), ('school', '', 6), ('Nike', 'Nike', 0),
    ('kitten', 'sitting', 3), ('school', 'schol', 1), ('schol', 'school', 1),
    ('cat', 'cut', 1), ('ab', 'ba', 2), ('é', 'e', 1), ('Nike', 'nike', 1),
])
def test_edit_distance_edge_cases(a, b, expected):
    assert edit_distance(a, b) == expected
    assert edit_distance(b, a) == expected


def test_edit_distance_requires_strings():
    with pytest.raises(TypeError, match='strings'):
        edit_distance(None, 'school')
