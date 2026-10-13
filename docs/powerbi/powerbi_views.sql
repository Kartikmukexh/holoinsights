-- Run once in Azure SQL (Query editor or SSMS). Read-only helper view for Power BI.
-- Gives Power BI a numeric quarter order and the previous-quarter revenue per region.
CREATE OR ALTER VIEW dbo.vw_RegionQuarter AS
SELECT
    region,
    quarter,
    DENSE_RANK() OVER (ORDER BY quarter)                       AS quarter_order,
    SUM(revenue)                                               AS revenue,
    LAG(SUM(revenue)) OVER (PARTITION BY region ORDER BY quarter) AS prev_revenue
FROM dbo.SalesData
GROUP BY region, quarter;
GO
