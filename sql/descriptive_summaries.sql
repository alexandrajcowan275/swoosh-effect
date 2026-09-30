-- Evidence versions remain explicit. Unassigned rows stay visible in shares.
WITH versions AS (
 SELECT 'A+B+C' AS evidence_tiers UNION ALL SELECT 'A+B'
), assigned AS (
 SELECT a.*, v.evidence_tiers,
 CASE WHEN a.evidence_tier IN ('A','B') OR (v.evidence_tiers='A+B+C' AND a.evidence_tier='C')
 THEN a.brand ELSE 'Unassigned' END AS analysis_brand
 FROM analysis_panel a CROSS JOIN versions v
)
SELECT evidence_tiers, analysis_brand AS brand,
 count(*) AS n_school_seasons, count(DISTINCT school_id) AS n_schools,
 avg(total_points) AS mean_points, median(total_points) AS median_points,
 avg(panel_points_pctile) AS mean_percentile, median(panel_points_pctile) AS median_percentile,
 count(*) FILTER (WHERE rank <= 10) AS top10_finishes,
 count(*) FILTER (WHERE rank <= 25) AS top25_finishes,
 count(*) FILTER (WHERE evidence_tier='A') AS n_tier_A,
 count(*) FILTER (WHERE evidence_tier='B') AS n_tier_B,
 count(*) FILTER (WHERE evidence_tier='C') AS n_tier_C
FROM assigned
WHERE in_research_scope AND analysis_brand <> 'Unassigned'
GROUP BY evidence_tiers, analysis_brand
ORDER BY evidence_tiers, analysis_brand;
