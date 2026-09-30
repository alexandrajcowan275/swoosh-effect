# Downloading the source PDFs

The public repository contains parsed observations and provenance, but does not redistribute the 24 Directors' Cup source PDFs. `./run.sh` downloads missing or invalid PDFs automatically, verifies each file against the SHA-256 recorded in the frozen manifests, then rebuilds the analysis and runs the test suite. The downloaded files in `data/raw/` are ignored by Git.

The manifests [final standings](../data/sources.json) and [fall/winter standings](../data/seasonal_sources.json) preserve the original source URLs, NACDA landing URLs, retrieval dates, filenames, and checksums. A normal run reuses valid cached files. `./run.sh --download` refreshes all 24 PDFs but still requires the original hashes; it does not alter the manifests or accept changed source material.

If an automatic download fails:

1. Open the PDF link below, or use its NACDA page's download button.
2. Save the original PDF bytes under the exact relative filename shown, creating `data/raw/` if necessary. Do not print the page to PDF or resave it through a PDF editor, because that changes the bytes.
3. Run `./run.sh` again. The same checksum validation applies to manually downloaded files.

A changed checksum stops the build. Do not replace a manifest hash just to pass the check: an upstream document change requires a new source audit and may change the results. If the original bytes are no longer available, the committed processed CSVs, charts, and Tableau exports remain available for inspection, but a complete from-source rebuild is blocked until the audited input is recovered.

Sponsor webpages and search logs are also excluded from the publication repository. Accepted sponsor evidence remains traceable through source URLs, Wayback snapshot URLs and dates, and source types in the evidence tables; the build does not need to download those pages.

| Local filename | Source PDF | NACDA landing page |
| --- | --- | --- |
| `data/raw/2017-18-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2018/7/18/Jan11overallDI.pdf) | [NACDA page](https://nacda.com/documents/2018/7/18/Jan11overallDI.pdf) |
| `data/raw/2017-18-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2018/7/18/April26overallDI.pdf) | [NACDA page](https://nacda.com/documents/2018/7/18/April26overallDI.pdf) |
| `data/raw/2017-18.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2018/7/18/June29overallDI.pdf) | [NACDA page](https://nacda.com/documents/2018/7/18//June29overallDI.pdf?id=1799) |
| `data/raw/2018-19-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2019/1/9/JAN10Overall.pdf) | [NACDA page](https://nacda.com/documents/2019/1/9/JAN10Overall.pdf) |
| `data/raw/2018-19-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2019/4/23/April25DIOverall.pdf) | [NACDA page](https://nacda.com/documents/2019/4/23/April25DIOverall.pdf) |
| `data/raw/2018-19.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2019/6/27/June28DIOverall.pdf) | [NACDA page](https://nacda.com/documents/2019/6/27//June28DIOverall.pdf?id=3678) |
| `data/raw/2020-21-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2021/6/1/June3OverallDI.pdf) | [NACDA page](https://nacda.com/documents/2021/6/1/June3OverallDI.pdf) |
| `data/raw/2020-21-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2021/6/1/June3OverallWinterDI.pdf) | [NACDA page](https://nacda.com/documents/2021/6/1/June3OverallWinterDI.pdf) |
| `data/raw/2020-21.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2021/7/1/July2OverallDI.pdf) | [NACDA page](https://nacda.com/documents/2021/7/1//July2OverallDI.pdf?id=4339) |
| `data/raw/2021-22-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2022/1/12/Jan_13OverallStandings.pdf) | [NACDA page](https://nacda.com/documents/2022/1/12/Jan_13OverallStandings.pdf) |
| `data/raw/2021-22-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2022/4/21/April21Overall.pdf) | [NACDA page](https://nacda.com/documents/2022/4/21/April21Overall.pdf) |
| `data/raw/2021-22.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2022/6/30/FinalDIstandings.pdf) | [NACDA page](https://nacda.com/documents/2022/6/30/FinalDIstandings.pdf) |
| `data/raw/2022-23-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2023/1/13/Jan_12OverallStandings_Update.pdf) | [NACDA page](https://nacda.com/documents/2023/1/13/Jan_12OverallStandings_Update.pdf) |
| `data/raw/2022-23-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2023/4/21/April21Overall.pdf) | [NACDA page](https://nacda.com/documents/2023/4/21/April21Overall.pdf) |
| `data/raw/2022-23.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2023/6/27/Final22.23Standings.pdf) | [NACDA page](https://nacda.com/documents/2023/6/27/Final22.23Standings.pdf) |
| `data/raw/2023-24-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2024/1/9/23.24DI_FinalFallOverall.pdf) | [NACDA page](https://nacda.com/documents/2024/1/9/23.24DI_FinalFallOverall.pdf) |
| `data/raw/2023-24-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2024/4/22/23.24DI_WinterOverall_4.25.pdf) | [NACDA page](https://nacda.com/documents/2024/4/22/23.24DI_WinterOverall_4.25.pdf) |
| `data/raw/2023-24.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2024/6/26/23.24FinalDI.pdf) | [NACDA page](https://nacda.com/documents/2024/6/26/23.24FinalDI.pdf) |
| `data/raw/2024-25-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2025/1/21/24.25DI_FinalFallOverall.pdf) | [NACDA page](https://nacda.com/documents/2025/1/21/24.25DI_FinalFallOverall.pdf) |
| `data/raw/2024-25-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2025/4/22/24.25DI_WinterOverall_4.24.pdf) | [NACDA page](https://nacda.com/documents/2025/4/22/24.25DI_WinterOverall_4.24.pdf) |
| `data/raw/2024-25.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2025/6/23/24.25DivIStandingsFinal.pdf) | [NACDA page](https://nacda.com/documents/2025/6/23/24.25DivIStandingsFinal.pdf) |
| `data/raw/2025-26-fall.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2026/1/20/25.26DI_FinalFallOverall.pdf) | [NACDA page](https://nacda.com/documents/2026/1/20/25.26DI_FinalFallOverall.pdf) |
| `data/raw/2025-26-winter.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2026/4/20/25.26DI_WinterOverall_4.23.pdf) | [NACDA page](https://nacda.com/documents/2026/4/20/25.26DI_WinterOverall_4.23.pdf) |
| `data/raw/2025-26.pdf` | [Download PDF](https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/nacda.com/documents/2026/6/24/25.26DI_Final.pdf) | [NACDA page](https://nacda.com/documents/2026/6/24/25.26DI_Final.pdf) |
