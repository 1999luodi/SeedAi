-- Fix Faster-RCNN soybean model path to the actual ONNX file in ai_worker.

UPDATE ai_models
SET model_path = '/workspace/online/models/service/soybean/faster-rcnn.onnx',
    updated_at = CURRENT_TIMESTAMP
WHERE model_name = 'faster-rcnn-soybean';
