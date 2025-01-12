-- ================================================
--  StockEase Database Schema
--  Version: 1.0
--  Author: Hitarth Shah
--  Description: Core database structure for StockEase
-- ================================================

-- Create database
CREATE DATABASE stockease_db;
\c stockease_db;

-- ========================
-- USERS TABLE
-- ========================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) CHECK (role IN ('admin', 'staff')) DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- SUPPLIERS TABLE
-- ========================
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- PRODUCTS TABLE
-- ========================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    brand VARCHAR(50),
    barcode VARCHAR(100) UNIQUE,
    cost_price NUMERIC(10,2) NOT NULL,
    selling_price NUMERIC(10,2) NOT NULL,
    current_stock INT DEFAULT 0,
    reorder_level INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- PURCHASES TABLE
-- ========================
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    supplier_id INT REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    purchase_date DATE DEFAULT CURRENT_DATE,
    total_amount NUMERIC(12,2),
    created_by INT REFERENCES users(user_id) ON DELETE SET NULL
);

-- ========================
-- PURCHASE ITEMS TABLE
-- ========================
CREATE TABLE purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INT REFERENCES purchases(purchase_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ========================
-- SALES TABLE
-- ========================
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12,2),
    payment_method VARCHAR(20) CHECK (payment_method IN ('cash', 'card', 'upi')) DEFAULT 'cash',
    created_by INT REFERENCES users(user_id) ON DELETE SET NULL
);

-- ========================
-- SALE ITEMS TABLE
-- ========================
CREATE TABLE sale_items (
    sale_item_id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES sales(sale_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ========================
-- STOCK MOVEMENTS TABLE
-- ========================
CREATE TABLE stock_movements (
    movement_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    movement_type VARCHAR(20) CHECK (movement_type IN ('purchase', 'sale', 'adjustment')),
    quantity INT NOT NULL,
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_id INT,
    created_by INT REFERENCES users(user_id) ON DELETE SET NULL
);

-- ================================================
-- TRIGGERS: Auto-update stock
-- ================================================

-- When purchase item is added, increase product stock
CREATE OR REPLACE FUNCTION update_stock_on_purchase()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET current_stock = current_stock + NEW.quantity
    WHERE product_id = NEW.product_id;

    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id, created_by)
    VALUES (NEW.product_id, 'purchase', NEW.quantity, NEW.purchase_id, NULL);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_stock_purchase
AFTER INSERT ON purchase_items
FOR EACH ROW
EXECUTE FUNCTION update_stock_on_purchase();

-- When purchase item deleted, reduce stock
CREATE OR REPLACE FUNCTION reduce_stock_on_purchase_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET current_stock = current_stock - OLD.quantity
    WHERE product_id = OLD.product_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_stock_purchase_delete
AFTER DELETE ON purchase_items
FOR EACH ROW
EXECUTE FUNCTION reduce_stock_on_purchase_delete();

-- When sale item is added, decrease stock
CREATE OR REPLACE FUNCTION reduce_stock_on_sale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET current_stock = current_stock - NEW.quantity
    WHERE product_id = NEW.product_id;

    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id, created_by)
    VALUES (NEW.product_id, 'sale', -NEW.quantity, NEW.sale_id, NULL);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_stock_sale
AFTER INSERT ON sale_items
FOR EACH ROW
EXECUTE FUNCTION reduce_stock_on_sale();

-- When sale item deleted, restore stock
CREATE OR REPLACE FUNCTION restore_stock_on_sale_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET current_stock = current_stock + OLD.quantity
    WHERE product_id = OLD.product_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_restore_stock_sale_delete
AFTER DELETE ON sale_items
FOR EACH ROW
EXECUTE FUNCTION restore_stock_on_sale_delete();

-- ================================================
-- END OF FILE
-- ================================================
