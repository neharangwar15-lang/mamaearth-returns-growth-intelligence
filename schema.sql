-- Mamaearth capstone: MySQL Workbench schema
-- Select/run this script in MySQL Workbench. It recreates the tables.
CREATE DATABASE IF NOT EXISTS mamaearth_db;
USE mamaearth_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    city_tier INT NOT NULL,
    signup_date DATE NOT NULL,
    acquisition_source VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE orders (
    order_id VARCHAR(10) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    order_date DATE NOT NULL,
    quantity INT NOT NULL,
    discount_pct INT NULL,
    payment_method VARCHAR(10) NOT NULL,
    rating INT NULL,
    returned INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id)
        REFERENCES products(product_id)
) ENGINE=InnoDB;
