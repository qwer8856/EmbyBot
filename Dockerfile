FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装编译环境依赖
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 拷贝项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 启动命令（根据你实际项目）
CMD ["python", "main.py"]
