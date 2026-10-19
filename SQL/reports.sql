-- Business reports for Mamaearth order and customer data.
USE mamaearth_db;

-- (a) Order totals and average order value
SELECT COUNT(*) AS total_orders,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
       ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o JOIN products p ON p.product_id = o.product_id;

-- (b) Rated and unrated orders
SELECT COUNT(*) AS total_orders, COUNT(rating) AS rated_orders,
       COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- (c1) Customers with no orders using LEFT JOIN
SELECT c.customer_id, c.name
FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0
ORDER BY c.customer_id;

-- (c2) Customers with no orders using NOT IN
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders)
ORDER BY customer_id;

-- (d) Return rates by city
SELECT c.city, COUNT(*) AS total_orders,
       SUM(o.returned) AS returned_orders,
       ROUND(100.0 * SUM(o.returned) / COUNT(*), 1) AS return_rate_pct
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.city
HAVING ROUND(100.0 * SUM(o.returned) / COUNT(*), 1) > 20
ORDER BY return_rate_pct DESC;

-- (e1) Top five customers by spend
SELECT c.customer_id, c.name,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o JOIN products p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- (e2) Customers ranked third through fifth by spend
SELECT c.customer_id, c.name,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o JOIN products p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- (f) Order count and revenue by product category
SELECT p.category, COUNT(o.order_id) AS order_count,
       ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue
FROM orders o JOIN products p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- (g) Customers whose names start with A
SELECT customer_id, name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;

-- (h) Distinct acquisition sources
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- (i) Assign a loyalty tier to each customer
SET @has_loyalty_tier = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'customers'
      AND column_name = 'loyalty_tier'
);
SET @loyalty_sql = IF(
    @has_loyalty_tier = 0,
    'ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10)',
    'SELECT 1'
);
PREPARE loyalty_stmt FROM @loyalty_sql;
EXECUTE loyalty_stmt;
DEALLOCATE PREPARE loyalty_stmt;
UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
