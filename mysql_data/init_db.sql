-- SeedAI 数据库初始化脚本（基线）
-- 仅用于首次建库。
-- 后续结构变更请统一放到 migrations/*.sql，并通过 migrate.py 执行。

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_dataset CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE ai_dataset;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role INT DEFAULT 0  -- 0-普通用户，1-管理员，2-超级管理员
);

-- 创建数据集表
CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'detection',  -- classification 或 detection
    item_count INT DEFAULT 0,  -- 数据集项目数量
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 创建图片表
CREATE TABLE IF NOT EXISTS images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    dataset_id INT NOT NULL,
    uploaded_by INT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500) NOT NULL,
    width INT,
    height INT,
    annotations_path VARCHAR(500),  -- 存储COCO标注文件路径
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- 创建默认用户
-- 注意：密码 '123456' 经过 bcrypt 加密后的哈希值
INSERT INTO users (username, email, password_hash, role) 
SELECT 'admin', 'admin@admin.com', '$2b$12$L2DP88C6F7Nh4MrzR7gIlOvGjgt.lRQAi33jZ2VQ5EtAaBXQ5mxYq', 2
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

INSERT INTO users (username, email, password_hash, role) 
SELECT 'user1', 'user1@example.com', '$2b$12$L2DP88C6F7Nh4MrzR7gIlOvGjgt.lRQAi33jZ2VQ5EtAaBXQ5mxYq', 0
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'user1');

-- 创建索引
CREATE INDEX idx_datasets_created_by ON datasets(created_by);
CREATE INDEX idx_images_dataset_id ON images(dataset_id);
CREATE INDEX idx_images_uploaded_by ON images(uploaded_by);