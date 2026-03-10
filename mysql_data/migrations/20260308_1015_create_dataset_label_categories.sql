-- 新增数据集标签类别配置表
CREATE TABLE IF NOT EXISTS dataset_label_categories (
    dataset_id INT NOT NULL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL DEFAULT 'detection',
    categories TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_dataset_label_categories_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
