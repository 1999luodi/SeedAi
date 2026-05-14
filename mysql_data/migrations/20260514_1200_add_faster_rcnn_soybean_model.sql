-- Add Faster-RCNN soybean model config with explicit class-id mapping.
-- ONNX class id mapping:
-- 0 -> Ungerminated
-- 1 -> Germinated

CREATE TABLE IF NOT EXISTS ai_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(120) NOT NULL UNIQUE,
    model_path VARCHAR(500) NOT NULL,
    class_count INT NOT NULL DEFAULT 0,
    class_list TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_models_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO ai_models (model_name, model_path, class_count, class_list, is_active)
VALUES (
    'faster-rcnn-soybean',
    '/workspace/online/models/service/soybean/faster-rcnn-soybean.onnx',
    2,
    '["Ungerminated","Germinated"]',
    FALSE
)
ON DUPLICATE KEY UPDATE
    model_path = VALUES(model_path),
    class_count = VALUES(class_count),
    class_list = VALUES(class_list),
    updated_at = CURRENT_TIMESTAMP;
