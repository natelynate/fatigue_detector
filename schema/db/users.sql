-- Create database
CREATE DATABASE operation;

-- Connect to the database
\c operation

-- Drop table if exists
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    joined TIMESTAMP NOT NULL,
    last_login TIMESTAMP NOT NULL
);

-- Insert root admin account
INSERT INTO users (email, password, joined, last_login)
VALUES (
    'root@gmail.com',
    '123',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);