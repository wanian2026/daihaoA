# Mac 部署指南

## 1. 环境要求

- macOS 10.15 或更高版本
- Python 3.12+
- Git

## 2. 安装步骤

### 2.1 克隆项目

```bash
# 进入你的工作目录
cd ~/Documents

# 克隆项目
git clone https://github.com/wanian2026/daihaoA.git

# 进入项目目录
cd daihaoA
```

### 2.2 创建虚拟环境

```bash
# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 2.3 安装依赖

```bash
# 安装项目依赖
pip install -r requirements_minimal.txt
```

## 3. 配置文件

### 3.1 复制配置文件

```bash
cp config/config.example.json config/config.json
```

### 3.2 编辑配置文件

```bash
# 使用vim编辑配置
vim config/config.json

# 或者使用其他编辑器
open -e config/config.json
```

**重要配置项：**

```json
{
  "binance": {
    "api_key": "你的币安API Key",
    "api_secret": "你的币安API Secret"
  },
  "trading": {
    "leverage": 10,
    "position_ratio": 0.8,
    "min_position_ratio": 0.2
  },
  "web": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

## 4. 运行程序

### 4.1 启动策略

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动程序
python src/main.py
```

### 4.2 后台运行（推荐）

使用 nohup 在后台运行：

```bash
nohup python src/main.py > logs/app.log 2>&1 &

# 查看进程
ps aux | grep main.py

# 查看日志
tail -f logs/app.log

# 停止程序
pkill -f "python src/main.py"
```

### 4.3 使用 screen/tmux（推荐开发环境）

```bash
# 使用screen
screen -S trading
python src/main.py
# 按 Ctrl+A 然后按 D 分离会话
# 重新连接：screen -r trading

# 或使用tmux
tmux new -s trading
python src/main.py
# 按 Ctrl+B 然后按 D 分离会话
# 重新连接：tmux attach -t trading
```

## 5. 访问Web管理界面

启动程序后，在浏览器中打开：

```
http://localhost:8000
```

### Web界面功能：

- **实时监控**：查看当前价格、ATR、持仓信息、浮盈等
- **手动操作**：
  - 手动开多单
  - 手动开空单
  - 平仓所有持仓
  - 暂停/恢复策略
- **交易历史**：查看所有交易记录
- **实时日志**：查看策略运行日志

## 6. 查看日志

```bash
# 实时查看应用日志
tail -f logs/app.log

# 查看交易日志
tail -f logs/trading.log

# 查看最近100行日志
tail -n 100 logs/app.log
```

## 7. 常见问题

### 7.1 端口被占用

```bash
# 查看端口占用
lsof -i :8000

# 杀死占用进程
kill -9 <PID>
```

### 7.2 依赖安装失败

```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像源安装
pip install -r requirements_minimal.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 7.3 API权限问题

- 确保币安API Key有期货交易权限
- IP白名单设置正确
- 测试网络连接：
  ```bash
  python -c "import ccxt; print(ccxt.binance().fetch_balance())"
  ```

## 8. 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重启程序
pkill -f "python src/main.py"
source venv/bin/activate
nohup python src/main.py > logs/app.log 2>&1 &
```

## 9. 安全建议

1. **不要将包含真实API密钥的 config.json 提交到Git**
2. **设置合理的杠杆倍数**（建议10倍以下）
3. **设置止损和止盈**
4. **定期备份交易日志**
5. **监控账户余额变化**

## 10. 测试运行

在实盘运行前，建议：

1. 使用测试网进行测试
2. 小仓位测试策略
3. 观察日志输出，确认策略逻辑正确
4. 检查Web界面数据是否实时更新
