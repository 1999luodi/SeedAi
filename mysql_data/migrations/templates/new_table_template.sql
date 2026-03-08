-- Create a new business table.
-- Rename file before running, e.g. 20260308_1015_create_seed_metrics.sql

CREATE TABLE IF NOT EXISTS seed_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    dataset_id BIGINT NOT NULL,
    image_id BIGINT NULL,
    metric_name VARCHAR(128) NOT NULL,
    metric_value DECIMAL(12, 4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_seed_metrics_dataset_id (dataset_id),
    INDEX idx_seed_metrics_image_id (image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
