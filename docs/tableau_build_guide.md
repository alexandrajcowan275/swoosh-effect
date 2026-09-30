# Build the Tableau Public dashboard in your browser

Use **Tableau Public web authoring** on a laptop or desktop. This guide uses the publication CSVs in [`exports/tableau/`](../exports/tableau/), with **A+B as the default evidence filter**. A row in `school_season.csv` is one school-season. The outcome covers all sports at the athletic-department level.

Instructions were checked against official Tableau documentation on September 30, 2026. Section 4 flags the second-source control for confirmation in your editor: it is documented for web editing generally, but has not been tested in your Tableau Public account. Tableau Public offers browser authoring through **Create → Web Authoring**, or **My Profile → Create a Viz**. [Official Public introduction](https://www.tableau.com/blog/getting-ready-publish-your-first-data-visualization) · [Connect on the web](https://help.tableau.com/current/online/en-us/creator_connect.htm)

## 1. Upload the first CSV and check its fields

1. Sign in at [Tableau Public](https://public.tableau.com/) and open **Create → Web Authoring**. If you are on your profile, **Create a Viz** opens the same connection workflow.
2. In **Connect to Data**, choose the file-upload option and **Upload from Computer**. On this Mac, press **Command+Shift+G** in the file picker, paste `/Users/alexandracowan/Documents/ChatGPT/swoosh-effect-public/exports/tableau/`, press **Return**, select `school_season.csv`, and click **Open**. (On another computer, choose the same folder inside your clone.) Do not upload `brand_summary.csv` into the same data model.
3. On the **Data Source** page, make sure the first row is used as field names and the preview has separate columns. If the table has not been placed on the canvas automatically, drag the single uploaded table to the empty canvas.
4. Name this data source `School seasons`. Open **Sheet 1** at the bottom.
5. Tableau may prettify `points_pctile` into `Points Pctile`. In the Data pane, use each field's menu → **Rename** to restore the exact CSV names used below. Renaming here changes the workbook label, not the CSV.
6. Check the types below. Use the type icon in the Data Source preview, or a field's menu → **Change Data Type**. Use **Convert to Dimension/Measure** if Tableau placed a field on the wrong side of the Data pane.

| Fields | Type and role |
|---|---|
| `school`, `season`, `conference`, `brand`, `brand_display`, `evidence_tier`, `conference_basis`, `sponsor_source_url` | String; dimension |
| `top10`, `top25`, `season_order`, `rank` | Number (whole); measure |
| `total_points`, `points_pctile` | Number (decimal); measure |
| `sensitivity_included`, `primary_included`, `in_research_scope`, `zero_imputed` | Boolean; dimension |

Keep `season` as text, not a date. `season_order` runs 1–8 over the eight included seasons. `top10` and `top25` are **0/1 indicators**, so their averages are rates. `points_pctile` already uses a **0–100 scale**. `brand_display` provides `Nike`, `adidas`, `Under Armour`, and `Other`; blank brands remain unknown, not `Other`.

The web editor supports renaming fields, changing types and aggregations, and switching dimensions/measures. [Web feature reference](https://help.tableau.com/current/pro/desktop/en-us/server_desktop_web_edit_differences.htm)

## 2. Sheet 1 — top-10 finish rate by brand

Rename the sheet `Top-10 finish rate by brand` by opening its tab menu → **Rename**.

1. Drag `sensitivity_included` to **Filters**. Select **True** only. This is the A+B sample.
2. Drag `brand_display` to **Filters**. Select only **Nike, adidas, Under Armour, Other**; leave blank/Null unchecked.
3. Drag `brand_display` to **Rows** and `top10` to **Columns**.
4. Open the `SUM(top10)` pill's menu → **Measure → Average**. The pill must read `AVG(top10)`.
5. Set the Marks type to **Bar**. Drag another copy of `brand_display` to **Color**.
6. Open the `brand_display` pill's menu on Rows → **Sort**: descending, sort by **Field**, field `top10`, aggregation **Average**.
7. Right-click the `AVG(top10)` measure in the view → **Format Number** → **Percentage**, one decimal place. Double-click the horizontal axis and title it `Top-10 finish rate within each brand's school-seasons`.
8. Drag `top10` from the Data pane to **Label**. Change that Label pill to **Measure → Average** as well.
9. Drag `school` to **Label**, then immediately open its pill menu → **Measure → Count**. It must read `CNT(school)`, not a blue `school` dimension and not `CNTD(school)`.
10. Click **Label**, enable **Show mark labels**, and edit the label text. Use **Insert** to place the two fields with this layout: the formatted average, then `n = ` followed by the count on the next line. Use Tableau's inserted fields rather than typing placeholder tokens. If the percentage in the label is not formatted, format its `AVG(top10)` pill as Percentage too.
11. Edit the sheet title to `Top-10 finishes within each brand — A+B`. Add a second title line: `n = school-seasons; covered research cohort, not national market share`.

The four bars should be **Nike 21.1%, n=289; Under Armour 3.5%, n=86; adidas 2.4%, n=85; Other 0.0%, n=7**. They represent 61, 3, 2, and 0 top-10 finishes respectively. Keep the zero-height Other bar's row and label. Compare the exact values in [`tableau_expected_values.md`](tableau_expected_values.md).

[Sorting by a field](https://help.tableau.com/current/pro/desktop/en-us/sortgroup_sorting_computed_howto.htm) · [Web number formatting](https://help.tableau.com/current/pro/desktop/en-us/formatting_specific_numbers.htm) · [Mark labels](https://help.tableau.com/current/pro/desktop/en-us/annotations_marklabels_showhideworksheet.htm)

## 3. Sheet 2 — mean performance percentile over time

Create a **New Worksheet** with the sheet-plus icon at the bottom. Name it `Performance by brand over time`. Select **School seasons** in the Data pane.

1. Add the same two filters: `sensitivity_included = True`; `brand_display` limited to the four known display brands. Apply them on this sheet explicitly so the default is unambiguous.
2. Drag `season` to **Columns**. Its pill should be **blue/discrete**, giving eight text headers.
3. Open the `season` pill menu → **Sort**: ascending, **Field**, `season_order`, aggregation **Minimum**. Check the order: 2017-18, 2018-19, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26.
4. Drag `points_pctile` to **Rows**, then change its aggregation to **Average**. Set the Marks type to **Line**.
5. Drag `brand_display` to **Color**. Use the same brand colors as Sheet 1. Do not put `school` on Detail; this sheet needs one mean per brand-season, not one line per school.
6. Double-click the vertical axis: use a fixed range of **0 to 100**, with title `Mean performance percentile (0–100)`.
7. Drag `school` to **Tooltip** and change its pill to **Measure → Count**. Include `brand_display`, `season`, `AVG(points_pctile)`, and `CNT(school)` in the tooltip, with `n = school-seasons` and `Evidence: A+B`. Format the average as a number with two decimal places, **not Percentage**.
8. Add `AVG(points_pctile)` to **Label** if readable; otherwise retain the values and n in the tooltip. Set the title to `Mean performance percentile by season — A+B`; add `2019-20 canceled and omitted; brand membership can change each season`.

A missing brand-season has no mean: leave it blank and do not turn it into zero. In particular, Other has sparse coverage. This chart shows changing group averages, not a fixed cohort's improvement. Its vertical units are percentile points, while Sheet 1's units are percentages.

To make an optional A+B+C comparison later, duplicate Sheets 1 and 2, **replace** the `sensitivity_included` filter with `primary_included = True`, and rename both titles to A+B+C. Keeping both filters would still restrict the sheets to A+B. The provided summaries contain two tier sets; never pool their rows together.

## 4. Add a second, separate data source

First check the worksheet toolbar for **New Data Source** (hover to confirm its name), or **Data → New Data Source** where shown. The official web instructions describe this control for Cloud/Server, while the file-upload documentation includes Public. If your Public editor exposes this command, click it and upload `exports/tableau/switch_events.csv` through **Connect to Data → Files/Upload from Computer**. Name it `Switch events`. Use the same folder in the Mac file picker, this time selecting `switch_events.csv`.

Confirm that this appears as a **second selectable data source** in the Data pane before continuing with the one-workbook layout. Do not use **Add connection** within School seasons, drag Switch events next to its table, create a relationship, join, union, or blend. The switch file already contains the needed outcomes and event details. When the editor accepts the independent second source, the three worksheets can sit on one dashboard while each uses its own source. [New source in web editing](https://help.tableau.com/current/online/en-gb/datasource_using.htm) · [Browser CSV upload, including Public](https://help.tableau.com/current/online/en-us/creator_connect.htm)

**If your Public editor does not offer a separate New Data Source command:** save your current work and stop at this checkpoint. Confirm the available toolbar/menu with the current editor before continuing. Do not substitute **Add connection**, a join, or a relationship; those change the data model. The guide's remaining one-workbook steps require the two independent sources to appear in the Data pane. This account-specific step has not been live-tested.

Restore exact CSV field names if Tableau prettifies them. In this source, check:

| Fields | Type |
|---|---|
| `school`, `season`, `switch_season`, `from_brand`, `to_brand`, `observed_brand`, `evidence_tier` | String |
| `relative_season` | Number (whole) |
| `points_pctile` | Number (decimal) |
| `usable_sensitivity`, `sensitivity_included`, `outcome_available` | Boolean |

The file has **50 rows: five calendar slots for each of ten documented transitions**. Some slots have null outcomes because they are canceled or outside the study window. Keep those rows.

## 5. Sheet 3 — one small switch chart per school

Create a new worksheet named `Brand switches`, and select **Switch events** before dragging any fields. Use **Circle marks** for the browser build: individual dots make every observed season visible without drawing a line through a missing season.

1. Drag `usable_sensitivity` to **Filters** and select **True**. This keeps nine usable schools and all **45 calendar slots** for those schools. Denver is excluded because it lacks covered former-provider observations within the window.
2. **Do not filter** `sensitivity_included`, `outcome_available`, `evidence_tier`, or non-null `points_pctile` on this sheet. Those row filters would discard the missing calendar slots. Every non-null outcome in the nine retained cases is already eligible and Tier A.
3. Drag `school` to **Rows**, then drag `points_pctile` to Rows to its right. Change the second pill to **Average**. This creates a separate panel for each school.
4. Drag `relative_season` to **Columns**. Set its aggregation to **Minimum**, and its pill to **Continuous** (green). Drag `season` to **Detail**. That detail field is essential: it gives each school-season its own point instead of collapsing each school to one average.
5. Set the Marks type to **Circle**. Keep a single neutral color so provider changes do not imply an estimated effect.
6. Double-click the horizontal axis. Set the range to **Fixed: −2 to 2** and tick marks to a fixed interval of **1**, starting at −2. Title it `Calendar seasons relative to switch; 0 = first post season`. The five x positions remain visible even where no dot exists.
7. Double-click the vertical axis. Set the range to **Fixed: 0 to 100**, shared across panels, and title it `Performance percentile (0–100)`. Use Number formatting, not Percentage.
8. Open the **Analytics** pane beside Data. Drag **Reference Line** into the view, onto the **Pane** target associated with the continuous **MIN(relative_season)** field. In the line dialog choose a **Constant** of **0** and label it `Switch season`. This must be a **vertical** line through x=0 in every school panel. A horizontal line at y=0 means it was dropped onto the outcome axis; remove that line and add it to the x field instead. [Web reference lines](https://help.tableau.com/current/pro/desktop/en-us/reference_lines.htm)
9. Drag `points_pctile` to **Label**, change it to **Average**, and show labels with one decimal place. Add `season`, `observed_brand`, `evidence_tier`, `from_brand`, `to_brand`, `switch_season`, `transition_date`, and `transition_date_precision` to **Tooltip**. An individual dot is one school-season. Do not add these fields to Rows or Color.
10. Set the title to `Provider switches: descriptive case studies`. Add a second line: `A+B eligibility; all observed dots are Tier A. No dot = unavailable, not zero. No causal estimate.` Keep the null indicator if Tableau displays one; do not choose a command that plots nulls at zero or filters their rows away.

**Why dots rather than a desktop-style line setting?** Tableau's official instructions for **Special Values → Hide and break lines** are in its Desktop section; the web section documents number formatting instead. This guide does not assume that desktop-only pane exists in Public web authoring. Dots, a fixed calendar axis, and the switch reference line preserve the missing periods without that control. [Desktop/web null-formatting distinction](https://help.tableau.com/current/pro/desktop/en-us/formatting_specific_numbers.htm)

### Keep each case's n per brand visible

Keep the original school names as panel headers. Place a **Text** object immediately below the switch sheet on the dashboard and paste this count block. These are counts of observed, eligible school-seasons in each full case window, not counts of calendar slots. All are Tier A; UA means Under Armour. Update this block if you change the data or window filters.

```text
Case-window n by brand — Nike / adidas / Under Armour / Other; all Tier A
Auburn 1 / 0 / 2 / 0           Boston College 0 / 0 / 1 / 3
California 3 / 0 / 2 / 0       Cincinnati 3 / 0 / 2 / 0
Georgia Tech 0 / 2 / 0 / 1     Rutgers 1 / 2 / 0 / 0
Texas Tech 0 / 2 / 2 / 0       UCLA 3 / 0 / 1 / 0
Washington 2 / 2 / 0 / 0
```

There are **35 observed dots and 10 null slots** across the 45 calendar rows. The per-case counts and all relative-season outcomes are reproduced in [the expected-values guide](tableau_expected_values.md).

Check the key gaps: **Washington has no dot at 0** because its switch season is canceled 2019-20; **Georgia Tech has no dot at +1** for the same reason, but does have a dot at +2. Auburn and Rutgers have no dots at +1/+2 because those seasons are beyond the study window. There should be no line connecting across any of these gaps and no invented zero.

### Optional connecting lines

Keep the dot panels as the verified-data default. A connected variant needs separate line paths on either side of a missing season and visible markers for isolated observations, particularly Georgia Tech at +2. Merely changing Circle to Line can silently connect Washington across 2019-20. The desktop **Hide and break lines** control is not documented for web authoring, so this guide does not promise that it is available. If your Public editor has no confirmed gap-preserving line controls, retain Circle marks; the same outcomes, five calendar positions, switch line, and case counts remain visible.

## 6. Assemble the dashboard

Click **New Dashboard** at the bottom. Name the dashboard `The Swoosh Effect`. Use a tall, fixed layout such as **1,200 × 2,300 pixels** initially, with tiled objects; increase the height if the nine panels or footer need space.

1. Add a **Text** object at the top with this exact title:

   **The Swoosh Effect: Why the best programs wear Nike**

2. Add a subtitle Text object directly below it:

   `An observational study of NCAA Division I all-sport departments, 2017-18–2025-26 (2019-20 canceled). Direct evidence A+B shown by default. Patterns are consistent with selection and persistent strength, not proof that Nike causes success. n = school-seasons.`

3. Drag the two brand sheets from the **Sheets** list into the upper part of the dashboard. Put the top-10 bars first and the season lines below them. Keep their titles and a readable brand legend.
4. Add the switch sheet beneath them, with enough vertical space to read all nine school panels; add the case-count Text block directly underneath. Its x axis is calendar time around each switch, not the categorical season axis of Sheet 2.
5. Add a Text object above or below the switch panels:

   `Switches are descriptive case studies. Cincinnati's 2023-24 dip coincides with its July 1, 2023 move to the Big 12 and a new football head coach's first season. Conference changes, COVID gaps, and coaching changes can overlap with provider changes. Denver lacks a covered pre-switch provider season and is omitted from these nine panels.`

6. Add a compact findings Text object:

   `Nike: 61/289 top-10 finishes (21.1%); Under Armour: 3/86 (3.5%); adidas: 2/85 (2.4%), A+B. On matched samples, prior-season controls reduce major-brand coefficient magnitudes by 56–62% in A+B and 62–68% in A+B+C; every adidas/Under Armour 95% interval includes zero. Matched/lagged n, Nike/adidas/UA/Other: A+B 213/63/60/5; A+B+C 264/72/60/5. These are associations, not causal effects.`

7. Add a sources/limitations Text object at the bottom. Include clickable links through the web text editor's link control:

   `Sources: NACDA Directors' Cup standings; official athletics/board/contract evidence and labeled reporting; dated Wayback snapshots. Provider research covers 537/592 priority school-seasons: A=445, B=22, inferred C=70, unknown=55. Default A+B charts use 467 school-seasons. The cohort is selected, not a census of D1. Provider means refer to departments; team exceptions and payment disputes are not modeled. Repository, complete evidence and methods: https://github.com/alexandrajcowan275/swoosh-effect.`

   Link **NACDA Directors' Cup standings** to [NACDA's archive](https://nacda.com/sports/2018/7/17/directorscup-nacda-directorscup-previous-standings-html.aspx). Link the Cincinnati note to its [official Big 12 announcement](https://gobearcats.com/news/2022/06/10/cincinnati-to-enter-big-12-on-july-1-2023). Link the repository text to [the public project repository](https://github.com/alexandrajcowan275/swoosh-effect). The detailed [model sample-size table](../reports/model_sample_sizes.csv) provides the n for every model variant.

8. Add the exact final line:

   `Independent student project. Not affiliated with or endorsed by Nike, Inc.`

Keep all three sheets on their documented filters. Do not turn a brand sheet into a dashboard-wide filter for the unrelated switch source. Tableau supports text and layout objects in web dashboards, including clickable hyperlinks in web text objects. [Dashboard creation and objects](https://help.tableau.com/current/pro/desktop/en-us/dashboards_create.htm)

## 7. Check, publish, and copy the link

Compare the sheets with [`tableau_expected_values.md`](tableau_expected_values.md) before publishing. Check the four bar denominators, season order, the 0–100 percentile axes, all nine case panels, and the missing Washington/Georgia Tech positions. Hover a few marks to confirm the labels say A+B and n counts school-seasons.

From Public web authoring, use **Publish As…** at the upper right for a new workbook, enter `The Swoosh Effect`, then **Publish**. When editing an existing Public workbook, use its **Publish** control to save the update. This is the Public web workflow, not Desktop's Server menu. [Official Public web publishing instructions](https://www.tableau.com/blog/how-visualize-your-music-data)

Open the published **dashboard**, click **Share** in the view's toolbar, and copy its link. Open the copied link in a private/incognito browser window to check the public dashboard, its labels, tooltips, and footer. Copy this dashboard URL for the portfolio site and README. Use **Edit Details** on the published viz to add a short description and the repository/source links. [Sharing a Public viz](https://help.tableau.com/current/pro/desktop/en-us/publish_workbooks_tableaupublic.htm)

## Common mistakes to avoid

| Symptom | Fix |
|---|---|
| Top-10 chart shows 61, 3, 2 instead of rates | Change **SUM(top10)** to **AVG(top10)**, then apply Percentage formatting. |
| Percentile chart shows 9,000% | Use Number formatting on the existing 0–100 `points_pctile`; do not format it as Percentage. |
| Many tiny bars or one mark per school | Remove the blue `school` dimension from the Marks card; the label must be **CNT(school)**. |
| n counts unique schools instead of seasons | Use **Count**, not **Count (Distinct)**. |
| A+B+C chart still matches A+B | Remove `sensitivity_included`; use `primary_included=True` alone, plus the known-brand filter. |
| Extra rows or doubled denominators | Keep School seasons and Switch events as separate sources; do not join or blend them. Never stack A+B and A+B+C summary rows. |
| Unknown brands appear as Other | Restore blank brands. Other means a verified provider outside the three major brands. |
| Switch plots lose the empty calendar positions | Filter only `usable_sensitivity=True`; retain all five slots, fix x to −2…2, and keep null outcomes null. |
| One dot per school instead of one per season | Put `season` on Detail and use continuous **MIN(relative_season)** on Columns. |
| A switch reference line is horizontal | Add it to the relative-season x axis, not the outcome y axis. |
| A line crosses canceled 2019-20 | Use the documented Circle marks for the switch panels. Do not borrow an unverified Desktop null-formatting control. |
