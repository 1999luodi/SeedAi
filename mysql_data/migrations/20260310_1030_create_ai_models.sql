-- 新增模型配置表：管理模型名称、路径、类别列表等信息
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

-- 默认模型（类别顺序固定：0腐烂，1发芽，2未发芽）
INSERT INTO ai_models (model_name, model_path, class_count, class_list, is_active)
SELECT 'yolov5-soybean', '/workspace/online/models/service/soybean/yolov5-soybean.onnx', 3, '["腐烂","发芽","未发芽"]', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM ai_models WHERE model_name = 'yolov5-soybean'
);
