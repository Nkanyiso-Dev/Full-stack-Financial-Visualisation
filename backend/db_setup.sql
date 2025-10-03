CREATE DATABASE IF NOT EXISTS finance_db;

USE finance_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE financial_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    year INT,
    month VARCHAR(20),
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO users (name) VALUES ('Jane Doe'), ('John Smith');
