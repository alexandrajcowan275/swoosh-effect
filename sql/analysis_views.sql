-- Official all-sport department total is the outcome, never a sum of seasonal cells.
CREATE OR REPLACE VIEW analysis_panel AS
SELECT s.*, c.brand, c.brand_raw, c.verified AS sponsor_verified,
       c.source_url AS sponsor_source_url, c.in_research_scope,
       c.evidence_tier, c.source_type, c.covered, c.inferred
FROM standings s
JOIN sponsor_coverage c USING (school_id, season);

-- All retained zeros have a reviewed D1 program interval.
CREATE OR REPLACE VIEW primary_panel AS
SELECT * FROM analysis_panel WHERE in_research_scope AND evidence_tier IN ('A','B','C');

CREATE OR REPLACE VIEW sensitivity_panel AS
SELECT * FROM analysis_panel WHERE in_research_scope AND evidence_tier IN ('A','B');

-- Historical read-only view, retained for comparisons with the previous audit.
CREATE OR REPLACE VIEW verified_observed_panel AS
SELECT * FROM analysis_panel
WHERE sponsor_verified = 'Y' AND observed_in_final;

-- Require consecutive calendar years with both brands verified; gaps are not switches.
-- Nike and Jordan normalize to Nike before this query.
CREATE OR REPLACE VIEW brand_switches AS
WITH history AS (
 SELECT school_id, school, season, brand, source_url,
        lag(brand) OVER w AS previous_brand,
        lag(season) OVER w AS previous_season,
        lag(source_url) OVER w AS previous_source_url
 FROM sponsor_coverage WHERE verified = 'Y'
 WINDOW w AS (PARTITION BY school_id ORDER BY season)
)
SELECT * FROM history
WHERE brand <> previous_brand
AND cast(left(season,4) AS INTEGER) = cast(left(previous_season,4) AS INTEGER) + 1;
