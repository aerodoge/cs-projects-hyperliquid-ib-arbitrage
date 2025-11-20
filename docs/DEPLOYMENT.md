# 部署指南

本文档提供生产环境部署的详细步骤和最佳实践。

## 目录

- [环境准备](#环境准备)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [系统服务配置](#系统服务配置)
- [监控和告警](#监控和告警)
- [备份和恢复](#备份和恢复)
- [性能优化](#性能优化)
- [安全建议](#安全建议)

## 环境准备

### 系统要求

**最低配置：**

- CPU: 1 核
- 内存: 512 MB
- 磁盘: 1 GB
- 网络: 稳定的互联网连接

**推荐配置：**

- CPU: 2 核
- 内存: 2 GB
- 磁盘: 10 GB（用于日志存储）
- 网络: 低延迟连接

**操作系统：**

- Ubuntu 20.04 / 22.04 LTS
- CentOS 7 / 8
- Debian 10 / 11
- macOS 12+

### 软件依赖

```bash
# Python 3.8+
python3 --version

# pip
pip3 --version

# Git (可选)
git --version

# Docker (如果使用 Docker 部署)
docker --version
```

## 生产环境部署

### 方式一：传统部署

#### 1. 创建部署目录

```bash
# 创建应用目录
sudo mkdir -p /opt/hyperliquid-collector
cd /opt/hyperliquid-collector

# 设置权限
sudo chown -R $USER:$USER /opt/hyperliquid-collector
```

#### 2. 部署代码

```bash
# 克隆或复制代码
git clone <your-repo-url> .
# 或者
cp -r /path/to/source/* .
```

#### 3. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置（使用生产环境配置）
nano .env
```

**生产环境配置示例：**

```bash
# Hyperliquid 配置
SYMBOL=xyz:NVDA
USE_TESTNET=false
PERP_DEXS=xyz

# Prometheus 配置
PUSH_GATEWAY_URL=prometheus-gateway.prod.internal:9091
JOB_NAME=hyperliquid_nvda_prod

# 采集配置
FETCH_INTERVAL=60
```

#### 5. 测试运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试
python src/test_final.py

# 前台运行（测试）
python src/main.py
```

#### 6. 生产运行

```bash
# 创建日志目录
mkdir -p /var/log/hyperliquid-collector

# 后台运行
nohup python src/main.py > /var/log/hyperliquid-collector/collector.log 2>&1 &

# 记录进程 ID
echo $! > /var/run/hyperliquid-collector.pid
```

### 方式二：Docker 部署

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行采集器
CMD ["python", "src/main.py"]
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  hyperliquid-collector:
    build: .
    container_name: hyperliquid-nvda-collector
    restart: unless-stopped
    environment:
      - SYMBOL=xyz:NVDA
      - USE_TESTNET=false
      - PERP_DEXS=xyz
      - PUSH_GATEWAY_URL=pushgateway:9091
      - JOB_NAME=hyperliquid_nvda
      - FETCH_INTERVAL=60
    networks:
      - monitoring
    depends_on:
      - pushgateway
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  pushgateway:
    image: prom/pushgateway:latest
    container_name: prometheus-pushgateway
    restart: unless-stopped
    ports:
      - "9091:9091"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```

#### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f hyperliquid-collector

# 停止服务
docker-compose down
```

#### 4. Docker 管理命令

```bash
# 重启服务
docker-compose restart hyperliquid-collector

# 查看状态
docker-compose ps

# 进入容器
docker-compose exec hyperliquid-collector bash

# 更新代码
docker-compose pull
docker-compose up -d
```

## 系统服务配置

### Systemd 服务（Linux）

#### 1. 创建服务文件

```bash
sudo nano /etc/systemd/system/hyperliquid-collector.service
```

#### 2. 服务配置

```ini
[Unit]
Description = Hyperliquid NVDA Data Collector
After = network.target
Wants = network-online.target

[Service]
Type = simple
User = hyperliquid
Group = hyperliquid
WorkingDirectory = /opt/hyperliquid-collector
Environment = "PATH=/opt/hyperliquid-collector/.venv/bin"
ExecStart = /opt/hyperliquid-collector/.venv/bin/python /opt/hyperliquid-collector/src/main.py
Restart = always
RestartSec = 10
StandardOutput = append:/var/log/hyperliquid-collector/collector.log
StandardError = append:/var/log/hyperliquid-collector/error.log

# 资源限制
MemoryLimit = 512M
CPUQuota = 50%

[Install]
WantedBy = multi-user.target
```

#### 3. 创建专用用户

```bash
# 创建系统用户
sudo useradd -r -s /bin/false hyperliquid

# 设置目录权限
sudo chown -R hyperliquid:hyperliquid /opt/hyperliquid-collector
sudo chown -R hyperliquid:hyperliquid /var/log/hyperliquid-collector
```

#### 4. 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start hyperliquid-collector

# 设置开机自启
sudo systemctl enable hyperliquid-collector

# 查看状态
sudo systemctl status hyperliquid-collector

# 查看日志
sudo journalctl -u hyperliquid-collector -f
```

#### 5. 服务管理

```bash
# 停止服务
sudo systemctl stop hyperliquid-collector

# 重启服务
sudo systemctl restart hyperliquid-collector

# 禁用开机自启
sudo systemctl disable hyperliquid-collector

# 查看配置
sudo systemctl show hyperliquid-collector
```

### Supervisor 配置（备选）

#### 1. 安装 Supervisor

```bash
sudo apt-get install supervisor
```

#### 2. 创建配置

```bash
sudo nano /etc/supervisor/conf.d/hyperliquid-collector.conf
```

```ini
[program:hyperliquid-collector]
command = /opt/hyperliquid-collector/.venv/bin/python /opt/hyperliquid-collector/src/main.py
directory = /opt/hyperliquid-collector
user = hyperliquid
autostart = true
autorestart = true
startsecs = 10
stopwaitsecs = 30
stdout_logfile = /var/log/hyperliquid-collector/collector.log
stderr_logfile = /var/log/hyperliquid-collector/error.log
environment = PATH="/opt/hyperliquid-collector/.venv/bin"
```

#### 3. 管理服务

```bash
# 重载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start hyperliquid-collector

# 查看状态
sudo supervisorctl status hyperliquid-collector

# 重启服务
sudo supervisorctl restart hyperliquid-collector
```

## 监控和告警

### 日志管理

#### 日志轮转配置

```bash
sudo nano /etc/logrotate.d/hyperliquid-collector
```

```
/var/log/hyperliquid-collector/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 hyperliquid hyperliquid
    sharedscripts
    postrotate
        systemctl reload hyperliquid-collector > /dev/null 2>&1 || true
    endscript
}
```

#### 日志查看命令

```bash
# 实时查看日志
tail -f /var/log/hyperliquid-collector/collector.log

# 搜索错误
grep "Error" /var/log/hyperliquid-collector/collector.log

# 查看最近 100 行
tail -n 100 /var/log/hyperliquid-collector/collector.log

# 查看特定时间的日志
grep "2025-11-20 14:" /var/log/hyperliquid-collector/collector.log
```

### 健康检查

创建健康检查脚本：

```bash
#!/bin/bash
# /opt/hyperliquid-collector/health_check.sh

PUSH_GATEWAY="http://localhost:9091"
JOB_NAME="hyperliquid_nvda"

# 检查进程是否运行
if pgrep -f "python.*main.py" > /dev/null; then
    echo "Process: OK"
else
    echo "Process: FAIL"
    exit 1
fi

# 检查最近是否有数据推送
LAST_PUSH=$(curl -s "${PUSH_GATEWAY}/metrics" | grep "push_time_seconds{job=\"${JOB_NAME}\"}" | awk '{print $2}')
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - ${LAST_PUSH%.*}))

if [ $TIME_DIFF -lt 300 ]; then
    echo "Data Push: OK (${TIME_DIFF}s ago)"
else
    echo "Data Push: FAIL (${TIME_DIFF}s ago)"
    exit 1
fi

echo "Health Check: PASS"
exit 0
```

设置定时健康检查：

```bash
# 添加到 crontab
crontab -e

# 每 5 分钟检查一次
*/5 * * * * /opt/hyperliquid-collector/health_check.sh >> /var/log/hyperliquid-collector/health.log 2>&1
```

### Prometheus 告警规则

在 Prometheus 中配置告警：

```yaml
# prometheus-alerts.yml
groups:
  - name: hyperliquid_nvda_alerts
    interval: 30s
    rules:
      # 数据采集中断告警
      - alert: HyperliquidDataStale
        expr: time() - push_time_seconds{job="hyperliquid_nvda"} > 300
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Hyperliquid NVDA 数据采集中断"
          description: "超过 5 分钟未收到新数据"

      # 价格异常告警
      - alert: HyperliquidPriceAnomaly
        expr: abs(hyperliquid_nvda_perp_ask - hyperliquid_nvda_perp_bid) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "NVDA 价格差异异常"
          description: "买卖价差超过 $10"

      # 资金费率异常告警
      - alert: HyperliquidFundingRateHigh
        expr: abs(hyperliquid_nvda_funding_rate) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "NVDA 资金费率异常"
          description: "资金费率超过 1%"
```

## 备份和恢复

### 配置备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/hyperliquid-collector"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份配置文件
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz \
    /opt/hyperliquid-collector/.env \
    /etc/systemd/system/hyperliquid-collector.service

# 备份代码（可选）
tar -czf $BACKUP_DIR/code_$TIMESTAMP.tar.gz \
    /opt/hyperliquid-collector/src

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
```

### 恢复配置

```bash
# 停止服务
sudo systemctl stop hyperliquid-collector

# 恢复配置
tar -xzf /backup/hyperliquid-collector/config_20251120_120000.tar.gz -C /

# 重启服务
sudo systemctl start hyperliquid-collector
```

## 性能优化

### 1. 网络优化

```bash
# 增加 TCP 连接超时
echo "net.ipv4.tcp_keepalive_time = 600" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_intvl = 60" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_probes = 3" | sudo tee -a /etc/sysctl.conf

# 应用设置
sudo sysctl -p
```

### 2. Python 优化

在 `.env` 中添加：

```bash
# Python 优化
PYTHONOPTIMIZE=1
PYTHONDONTWRITEBYTECODE=1
```

### 3. 采集间隔优化

根据需求调整采集频率：

```bash
# 高频监控（30秒）- 占用资源较多
FETCH_INTERVAL=30

# 标准监控（60秒）- 推荐
FETCH_INTERVAL=60

# 低频监控（300秒）- 节省资源
FETCH_INTERVAL=300
```

## 安全建议

### 1. 网络安全

```bash
# 限制 Push Gateway 访问
sudo ufw allow from 10.0.0.0/8 to any port 9091
sudo ufw deny 9091

# 只允许必要的出站连接
sudo ufw allow out 443/tcp  # HTTPS
sudo ufw allow out 80/tcp   # HTTP
```

### 2. 文件权限

```bash
# 设置严格的文件权限
chmod 600 /opt/hyperliquid-collector/.env
chmod 755 /opt/hyperliquid-collector/src/*.py
chown -R hyperliquid:hyperliquid /opt/hyperliquid-collector
```

### 3. 环境变量安全

不要在代码中硬编码敏感信息，始终使用环境变量。

```bash
# 不好的做法
PUSH_GATEWAY_URL="http://secret-gateway:9091"

# 好的做法
PUSH_GATEWAY_URL=${PUSH_GATEWAY_URL}
```

### 4. 定期更新

```bash
# 定期更新依赖
pip install --upgrade -r requirements.txt

# 检查安全漏洞
pip install safety
safety check
```

## 故障排除

### 常见问题检查清单

1. **服务无法启动**
   ```bash
   sudo systemctl status hyperliquid-collector
   sudo journalctl -u hyperliquid-collector -n 50
   ```

2. **网络连接问题**
   ```bash
   curl -I https://api.hyperliquid.xyz
   ping api.hyperliquid.xyz
   ```

3. **Push Gateway 连接失败**
   ```bash
   curl http://localhost:9091/metrics
   telnet localhost 9091
   ```

4. **内存不足**
   ```bash
   free -h
   top -p $(pgrep -f "python.*main.py")
   ```

5. **磁盘空间不足**
   ```bash
   df -h
   du -sh /var/log/hyperliquid-collector/*
   ```

## 维护建议

### 日常维护

- **每天**：检查日志是否有错误
- **每周**：查看服务运行状态和资源使用
- **每月**：更新依赖包，清理旧日志
- **每季度**：审查配置，优化性能

### 维护脚本

```bash
#!/bin/bash
# maintenance.sh

echo "=== Hyperliquid Collector Maintenance ==="

# 检查服务状态
echo "Service Status:"
systemctl status hyperliquid-collector --no-pager

# 检查磁盘使用
echo -e "\nDisk Usage:"
df -h /var/log/hyperliquid-collector

# 检查最近错误
echo -e "\nRecent Errors:"
grep -i "error" /var/log/hyperliquid-collector/collector.log | tail -5

# 检查 Push Gateway
echo -e "\nPush Gateway Status:"
curl -s http://localhost:9091/metrics | grep push_time_seconds

echo -e "\n=== Maintenance Check Complete ==="
```

---

**部署完成后，记得测试所有功能是否正常！**
