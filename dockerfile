# 使用 Python 基礎映像
FROM python:3.11

# 更新和安裝必要的系統庫
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && apt-get clean

# 設置工作目錄
WORKDIR /app

# 複製要求文件並安裝 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式文件
COPY . .

# 指定執行命令
EXPOSE 3000
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
