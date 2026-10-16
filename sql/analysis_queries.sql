-- =====================================================================
-- SUPERSTORE PROFITABILITY & SALES ANALYSIS
-- SQLite Analysis Queries
-- Database: data/superstore.db | Table: orders
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. EXECUTIVE KPI SUMMARY
-- Computes core high-level metrics across the entire enterprise dataset.
-- ---------------------------------------------------------------------
SELECT 
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    COUNT(DISTINCT order_id) AS total_unique_orders,
    SUM(quantity) AS total_quantity_sold,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS overall_profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS enterprise_avg_discount_pct
FROM orders;


-- ---------------------------------------------------------------------
-- 2. CATEGORY PROFITABILITY BREAKDOWN
-- Compares revenue generation against actual bottom-line profitability.
-- Key Finding: Furniture delivers 32% of sales but only 6.4% of total profit.
-- ---------------------------------------------------------------------
SELECT 
    category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity) AS total_units_sold,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM orders
GROUP BY category
ORDER BY total_profit DESC;


-- ---------------------------------------------------------------------
-- 3. SUB-CATEGORY RANKING (PROFIT LEADERS VS. LOSS LEADERS)
-- Identifies top margin drivers (Copiers, Phones) vs loss-makers (Tables, Bookcases).
-- ---------------------------------------------------------------------
SELECT 
    category,
    sub_category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity) AS total_units_sold,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM orders
GROUP BY category, sub_category
ORDER BY total_profit ASC;


-- ---------------------------------------------------------------------
-- 4. REGIONAL PROFITABILITY & MARGIN COMPARISON
-- Evaluates geographic operational efficiency.
-- Key Finding: Central region has the lowest profit margin (7.92%).
-- ---------------------------------------------------------------------
SELECT 
    region,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM orders
GROUP BY region
ORDER BY total_profit DESC;


-- ---------------------------------------------------------------------
-- 5. BOTTOM 10 LOSS-MAKING STATES
-- Highlights states where discounting heavily erodes profitability.
-- Key Finding: Texas, Ohio, and Pennsylvania experience massive negative margins.
-- ---------------------------------------------------------------------
SELECT 
    state,
    region,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM orders
GROUP BY state, region
ORDER BY total_profit ASC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 6. DISCOUNT SENSITIVITY & MARGIN EROSION ANALYSIS
-- Evaluates relationship between discount levels and profitability.
-- Note: Evaluated as empirical association without claiming direct single-factor causation.
-- Key Finding: Discounts > 20% consistently flip average profit negative.
-- ---------------------------------------------------------------------
SELECT 
    CASE 
        WHEN discount = 0 THEN '0% (No Discount)'
        WHEN discount > 0 AND discount <= 0.20 THEN '1% - 20% (Low Discount)'
        WHEN discount > 0.20 AND discount <= 0.40 THEN '21% - 40% (Moderate Discount)'
        ELSE '> 40% (Deep Discount)'
    END AS discount_tier,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT order_id) AS distinct_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(profit), 2) AS avg_profit_per_transaction,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY discount_tier
ORDER BY total_profit DESC;


-- ---------------------------------------------------------------------
-- 7. YEARLY & MONTHLY SEASONALITY ANALYSIS
-- Identifies peak demand cycles (Q4 surge in November and December).
-- ---------------------------------------------------------------------
SELECT 
    order_year,
    order_month_num,
    order_month_name,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY order_year, order_month_num, order_month_name
ORDER BY order_year ASC, order_month_num ASC;


-- ---------------------------------------------------------------------
-- 8. CUSTOMER SEGMENT PERFORMANCE
-- Compares Consumer, Corporate, and Home Office purchasing behaviors.
-- ---------------------------------------------------------------------
SELECT 
    segment,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM orders
GROUP BY segment
ORDER BY total_sales DESC;


-- ---------------------------------------------------------------------
-- 9. SHIPPING MODE PERFORMANCE & TRANSIT TIME
-- Evaluates shipping speed vs operational profitability.
-- ---------------------------------------------------------------------
SELECT 
    ship_mode,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(AVG(shipping_days), 1) AS avg_shipping_days,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY ship_mode
ORDER BY total_orders DESC;


-- ---------------------------------------------------------------------
-- 10. TOP 10 MOST UNPROFITABLE PRODUCTS
-- Detailed audit of products driving the highest absolute financial losses.
-- ---------------------------------------------------------------------
SELECT 
    product_name,
    category,
    sub_category,
    SUM(quantity) AS units_sold,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_loss
FROM orders
GROUP BY product_name, category, sub_category
HAVING total_loss < 0
ORDER BY total_loss ASC
LIMIT 10;
