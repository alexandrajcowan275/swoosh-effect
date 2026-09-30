"""A low edit count must never silently resolve a tied identity."""
import pytest
from src.name_matching import resolve_school_names

MAPPING=[{'school_raw':'Cat','school':'Cat','school_id':'cat'},
         {'school_raw':'Bat','school':'Bat','school_id':'bat'},
         {'school_raw':'Reviewed alias','school':'Cat','school_id':'cat'}]

def test_explicit_alias_wins_regardless_of_string_similarity():
    matched,review=resolve_school_names(['Reviewed alias'],MAPPING,threshold=0)
    assert not review and matched[0]['school_id']=='cat'
    assert matched[0]['match_method']=='reviewed_explicit'

def test_unique_close_candidate_and_ambiguous_tie():
    matched,review=resolve_school_names(['Catt','Hat'],MAPPING,threshold=1)
    assert [(m['school_raw'],m['school_id'],m['edit_distance']) for m in matched]==[('Catt','cat',1)]
    assert review[0]['school_raw']=='Hat' and review[0]['reason']=='ambiguous_minimum'
    assert set(review[0]['candidate_ids'].split(' | '))=={'cat','bat'}

def test_empty_input_empty_name_and_threshold_limit():
    assert resolve_school_names([],MAPPING)==([],[])
    matches,review=resolve_school_names(['','Faraway University'],MAPPING,threshold=1)
    assert not matches
    assert {r['reason'] for r in review}=={'empty_name','distance_exceeds_threshold'}
    with pytest.raises(ValueError):resolve_school_names(['Cat'],MAPPING,threshold=-1)

def test_normalized_collision_requires_review():
    mapping=[{'school_raw':'One','school':'School','school_id':'one'},
             {'school_raw':'Two','school':'SCHOOL','school_id':'two'}]
    matches,review=resolve_school_names(['school'],mapping,threshold=0)
    assert not matches and review[0]['reason']=='ambiguous_minimum'
