FROM pytorch/pytorch:1.9.0-cuda11.1-cudnn8-runtime

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 git ninja-build libglib2.0-0 libxrender-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 安装Python依赖
RUN pip install --upgrade pip

# 复制requirements文件
COPY ./pytorch_model/requirements.txt /tmp/requirements.txt

# 安装Python包
RUN pip install -r /tmp/requirements.txt

# 设置工作目录
WORKDIR /workspace

# 默认命令
CMD ["python", "inference.py"]