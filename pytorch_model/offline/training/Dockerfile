ARG BASE_IMAGE=docker.m.daocloud.io/pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
FROM ${BASE_IMAGE}

WORKDIR /workspace

RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-dri \
    libegl1-mesa \
    libxcb-dri3-0 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple/" >> /root/.pip/pip.conf && \
    echo "trusted-host = pypi.tuna.tsinghua.edu.cn" >> /root/.pip/pip.conf

COPY offline/training/requirements.txt /workspace/offline/training/requirements.txt
RUN pip install --no-cache-dir torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir -r /workspace/offline/training/requirements.txt

COPY . .

RUN pip install --no-cache-dir -e ./offline/third_party/ultralytics-src

CMD ["bash", "-lc", "sleep infinity"]
