# Monthly market report tools

`make_report.py` builds one month's report page from a JSON data file.
`reports/2026-10.json` is the template: copy it to `reports/YYYY-MM.json` and replace every value.

Sources: Greater Vancouver REALTORS® monthly news release and stats package (sales, prices, ratios, price_areas), liv.rent monthly rent report (liv block). Every figure must come from those sources. The `text` block (gauge_intro, rent_notes, take) is written prose in English and Chinese, drafted for Vivian to review.

Build:

    python3 _tools/make_report.py _tools/reports/YYYY-MM.json market-report-YYYY-MM.html --mode repo --archive _tools/reports/archive.json
    cp market-report-YYYY-MM.html market-report.html     # latest report

Add the month to `_tools/reports/archive.json` and rebuild the previous month's page if you want its "Earlier reports" list updated.
