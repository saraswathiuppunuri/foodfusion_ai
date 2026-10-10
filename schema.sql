-- ==============================================================
-- FoodAI: Online Food Ordering System - Powered by AI
-- MySQL Database Schema and Initial Seed Data
-- ==============================================================

CREATE DATABASE IF NOT EXISTS food_ordering_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_ordering_ai;

-- 1. Restaurants Table
CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    cuisine VARCHAR(100) NOT NULL,
    rating FLOAT DEFAULT 4.2,
    avg_prep_time INT DEFAULT 20, -- in minutes
    address VARCHAR(255) NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    phone VARCHAR(30),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Menu Items / Dishes Table
CREATE TABLE IF NOT EXISTS dishes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    is_veg BOOLEAN DEFAULT TRUE,
    spice_level VARCHAR(20) DEFAULT 'medium', -- mild, medium, spicy
    calories INT DEFAULT 350,
    protein_g INT DEFAULT 12,
    image_url VARCHAR(255),
    tags VARCHAR(255), -- Comma-separated tags for TF-IDF scikit-learn
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- 3. Surplus Food Deals Table (Feature 2: Zero-Waste)
CREATE TABLE IF NOT EXISTS surplus_deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dish_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    original_price DECIMAL(10,2) NOT NULL,
    discounted_price DECIMAL(10,2) NOT NULL,
    quantity_available INT NOT NULL,
    waste_saved_kg DECIMAL(5,2) DEFAULT 0.5,
    co2_saved_kg DECIMAL(5,2) DEFAULT 1.2,
    expiry_time DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, sold_out, expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- 4. Customer Orders Table (Feature 5: Predictive Tracking)
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(30),
    delivery_address TEXT,
    total_amount DECIMAL(10,2) NOT NULL,
    order_type VARCHAR(30) DEFAULT 'regular', -- regular, surplus, group, nl_ai
    status VARCHAR(30) DEFAULT 'placed', -- placed, preparing, out_for_delivery, delivered, delayed
    predicted_prep_min INT DEFAULT 20,
    actual_prep_min INT DEFAULT NULL,
    predicted_delivery_min INT DEFAULT 15,
    delay_flag BOOLEAN DEFAULT FALSE,
    delay_reason VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    dish_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE
);

-- 6. User Dietary & Past Taste Profiles (Feature 4: Scikit-learn TF-IDF)
CREATE TABLE IF NOT EXISTS user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    preferred_cuisines VARCHAR(255),
    dietary_preference VARCHAR(50) DEFAULT 'none', -- vegetarian, vegan, halal, gluten-free, none
    spice_preference VARCHAR(30) DEFAULT 'medium',
    avg_budget DECIMAL(10,2) DEFAULT 300.0,
    past_order_tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Group Order Sessions (Feature 3: Group Optimizer)
CREATE TABLE IF NOT EXISTS group_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_code VARCHAR(20) NOT NULL UNIQUE,
    host_name VARCHAR(100) NOT NULL,
    total_budget DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) DEFAULT 'open', -- open, optimized, placed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS group_order_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_order_id INT NOT NULL,
    member_name VARCHAR(100) NOT NULL,
    budget DECIMAL(10,2) NOT NULL,
    diet_preference VARCHAR(50),
    spice_level VARCHAR(20),
    assigned_dishes TEXT,
    share_amount DECIMAL(10,2) DEFAULT 0.0,
    FOREIGN KEY (group_order_id) REFERENCES group_orders(id) ON DELETE CASCADE
);
