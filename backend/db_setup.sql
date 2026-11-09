-- Production database (used by app.py by default)
CREATE DATABASE IF NOT EXISTS finance_db;

USE finance_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    year INT,
    month VARCHAR(20),
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO users (name)
SELECT 'Demo User'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id = 1);

-- Test database (used by the automated test suite)
CREATE DATABASE IF NOT EXISTS finance_test_db;

USE finance_test_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    year INT,
    month VARCHAR(20),
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO users (name)
SELECT 'Test User'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id = 1);
