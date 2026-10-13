# Power BI report (traditional BI view)

The Power BI report reads the **same Azure SQL `SalesData` table** as the FastAPI backend, so the 2D report and the
mixed-reality dashboard always show the same numbers.

```
Azure SQL (SalesData) --+--> FastAPI --> Web / Unity (MR dashboard)
                        +--> Power BI Desktop report (this folder)
```

## 1. Create the helper view
Run `powerbi_views.sql` in the Azure SQL query editor (adds `dbo.vw_RegionQuarter`).

## 2. Connect Power BI Desktop (Windows)
1. Home > Get data > **Azure SQL database**. Server: your `*.database.windows.net`, Database: your DB, mode **Import**.
2. Sign in with the **Database** tab (SQL username/password from your `.env`).
3. Tick `SalesData` and `vw_RegionQuarter` > Load.
4. If the connection times out, add your client IP to the Azure SQL firewall.

## 3. Model
- Select `vw_RegionQuarter[quarter]` > Column tools > **Sort by column** > `quarter_order`.
- Set `revenue` / `prev_revenue` to Currency.

## 4. DAX measures (Modeling > New measure, on `vw_RegionQuarter`)
```
Total Revenue = SUM ( vw_RegionQuarter[revenue] )

Latest Quarter Order = CALCULATE ( MAX ( vw_RegionQuarter[quarter_order] ), ALL ( vw_RegionQuarter ) )

Latest Revenue =
CALCULATE ( [Total Revenue], vw_RegionQuarter[quarter_order] = [Latest Quarter Order] )

Previous Revenue =
CALCULATE ( [Total Revenue], vw_RegionQuarter[quarter_order] = [Latest Quarter Order] - 1 )

QoQ % = DIVIDE ( [Latest Revenue] - [Previous Revenue], [Previous Revenue] )
```

## 5. Visuals (mirror the three dashboard questions)
| Dashboard question | Power BI visual |
|---|---|
| How did revenue perform this quarter? | 3 **Cards**: `Latest Revenue`, `QoQ %`, top region (Top N filter = 1 on `region` by `Latest Revenue`) + **Clustered column**: Axis `region`, Values `Latest Revenue` |
| Which region is underperforming? | **Bar chart**: Axis `region`, Values `QoQ %`, conditional colour: red when < 0 |
| What's the monthly (quarterly) trend? | **Line chart**: Axis `quarter` (sorted by `quarter_order`), Values `Total Revenue` |

Add a `region` **slicer**. Dark theme: View > Themes > pick a dark one to match the MR dashboard.

## 6. Save and commit
Save as `docs/powerbi/HoloInsights.pbix` (keep it small; do not store credentials in it) and add a screenshot
`docs/powerbi/report.png` for the report and slides.
