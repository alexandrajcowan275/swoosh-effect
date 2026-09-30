"""Preserve reviewed mappings; flag ambiguous or distant fuzzy candidates."""
if __package__:
    from .algorithms import edit_distance
else:
    from algorithms import edit_distance


def normalize_name(value):
    return ' '.join(value.casefold().split())


def resolve_school_names(raw_names, mapping_records, threshold=2):
    """Return (accepted matches, manual review) without guessing tied matches.

    Reviewed exact raw-name mappings always take precedence. New names can match
    a unique closest canonical name within ``threshold`` edits. Equal minima,
    empty names and candidates beyond the threshold require manual review.
    The distance is a string similarity measure, not independent identity proof.

    For R names, M mapping rows, K canonical candidates and maximum string
    length L, worst-case time is O(M + K log K + R*L log R + R*K*L^2).
    Auxiliary space is O(M+K+R+L), excluding returned records. Exact reviewed
    lookups avoid scanning K candidates; their reported distance costs O(L^2).
    Core distances use the hand-written dynamic program.
    """
    if not isinstance(threshold,int) or threshold<0:
        raise ValueError('threshold must be a nonnegative integer')
    explicit={};canonical={}
    for row in mapping_records:
        raw=row['school_raw'];target=(row['school'],row['school_id'])
        if raw in explicit and explicit[raw]!=target:
            raise ValueError(f'Conflicting reviewed mapping for {raw}')
        if target[1] in canonical and canonical[target[1]]!=target[0]:
            raise ValueError(f'Conflicting canonical name for {target[1]}')
        explicit[raw]=target;canonical[target[1]]=target[0]
    matches=[];reviews=[]
    canonical_candidates=sorted(canonical.items())
    for raw in sorted(set(raw_names)):
        normalized=normalize_name(raw)
        if raw in explicit:
            school,school_id=explicit[raw]
            matches.append(dict(school_raw=raw,school=school,school_id=school_id,match_method='reviewed_explicit',
                edit_distance=edit_distance(normalized,normalize_name(school))))
            continue
        candidates=[];best=None
        if normalized:
            for school_id,school in canonical_candidates:
                distance=edit_distance(normalized,normalize_name(school))
                if best is None or distance<best:
                    best=distance;candidates=[(school,school_id)]
                elif distance==best:
                    candidates.append((school,school_id))
        if best is not None and best<=threshold and len(candidates)==1:
            school,school_id=candidates[0]
            matches.append(dict(school_raw=raw,school=school,school_id=school_id,match_method='fuzzy_unique_within_threshold',edit_distance=best))
        else:
            reason='empty_name' if not normalized else 'no_candidates' if best is None else 'distance_exceeds_threshold' if best>threshold else 'ambiguous_minimum'
            reviews.append(dict(school_raw=raw,closest_distance=best,threshold=threshold,
                candidate_schools=' | '.join(x[0] for x in candidates),candidate_ids=' | '.join(x[1] for x in candidates),reason=reason))
    return matches,reviews
