# 配置文件说明

## 配置文件路径

- 配置文件：`config/config.json`
- 示例文件：`config/config.example.json`

## 配置项详解

### exchange（交易所配置）

| 配置项 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| exchange | string | 交易所名称，目前支持binance | "binance" |
| api_key | string | 币安API Key | "your_api_key_here" |
| secret | string | 币安API Secret | "your_api_secret_here" |
| testnet | boolean | 是否使用测试网，实盘设为false | true/false |

**获取币安API密钥：**
1. 登录币安官网
2. 进入"API管理"
3. 创建API Key（需启用期货交易权限）
4. 设置IP白名单（推荐）

### strategy（策略配置）

| 配置项 | 类型 | 说明 | 默认值 | 建议范围 |
|--------|------|------|--------|----------|
| symbol | string | 交易对 | "BTC/USDT" | 币安支持的期货交易对 |
| investment | number | 初始资金(USDT) | 1000 | 根据账户余额设置 |
| position_ratio | number | 单次开仓比例 | 0.1 | 0.05-0.2 |
| leverage | number | 杠杆倍数 | 5 | 3-10 |
| up_threshold_type | string | 上轨阈值类型 | "atr" | "atr"或"fixed" |
| up_threshold | number | 上轨固定阈值 | 0.02 | 当type为fixed时生效 |
| up_atr_multiplier | number | 上轨ATR倍数 | 0.9 | 当type为atr时生效 |
| down_threshold_type | string | 下轨阈值类型 | "atr" | "atr"或"fixed" |
| down_threshold | number | 下轨固定阈值 | 0.02 | 当type为fixed时生效 |
| down_atr_multiplier | number | 下轨ATR倍数 | 0.9 | 当type为atr时生效 |
| stop_loss_type | string | 止损类型 | "atr" | "atr"或"fixed" |
| stop_loss_ratio | number | 止损固定比例 | 0.05 | 当type为fixed时生效 |
| stop_loss_atr_multiplier | number | 止损ATR倍数 | 1.5 | 当type为atr时生效 |
| atr_period | number | ATR周期 | 14 | 7-21 |
| atr_timeframe | string | K线周期 | "1h" | "15m", "1h", "4h" |
| max_daily_loss | number | 最大日亏损(USDT) | 100 | 根据风险承受能力 |
| max_daily_trades | number | 最大日交易次数 | 50 | 20-100 |
| max_positions | number | 最大持仓数 | 5 | 3-10 |

## 配置示例

### 测试网配置（新手推荐）

```json
{
    "exchange": {
        "exchange": "binance",
        "api_key": "你的测试网API Key",
        "secret": "你的测试网API Secret",
        "testnet": true
    },
    "strategy": {
        "symbol": "BTC/USDT",
        "investment": 1000,
        "position_ratio": 0.1,
        "leverage": 5,
        "up_threshold_type": "atr",
        "up_threshold": 0.02,
        "up_atr_multiplier": 0.9,
        "down_threshold_type": "atr",
        "down_threshold": 0.02,
        "down_atr_multiplier": 0.9,
        "stop_loss_type": "atr",
        "stop_loss_ratio": 0.05,
        "stop_loss_atr_multiplier": 1.5,
        "atr_period": 14,
        "atr_timeframe": "1h",
        "max_daily_loss": 100,
        "max_daily_trades": 50,
        "max_positions": 5
    }
}
```

### 实盘配置（保守策略）

```json
{
    "exchange": {
        "exchange": "binance",
        "api_key": "你的实盘API Key",
        "secret": "你的实盘API Secret",
        "testnet": false
    },
    "strategy": {
        "symbol": "BTC/USDT",
        "investment": 5000,
        "position_ratio": 0.05,
        "leverage": 3,
        "up_threshold_type": "atr",
        "up_threshold": 0.03,
        "up_atr_multiplier": 1.2,
        "down_threshold_type": "atr",
        "down_threshold": 0.03,
        "down_atr_multiplier": 1.2,
        "stop_loss_type": "atr",
        "stop_loss_ratio": 0.03,
        "stop_loss_atr_multiplier": 2.0,
        "atr_period": 21,
        "atr_timeframe": "1h",
        "max_daily_loss": 200,
        "max_daily_trades": 20,
        "max_positions": 3
    }
}
```

### 实盘配置（激进策略）

```json
{
    "exchange": {
        "exchange": "binance",
        "api_key": "你的实盘API Key",
        "secret": "你的实盘API Secret",
        "testnet": false
    },
    "strategy": {
        "symbol": "BTC/USDT",
        "investment": 2000,
        "position_ratio": 0.2,
        "leverage": 10,
        "up_threshold_type": "atr",
        "up_threshold": 0.015,
        "up_atr_multiplier": 0.7,
        "down_threshold_type": "atr",
        "down_threshold": 0.015,
        "down_atr_multiplier": 0.7,
        "stop_loss_type": "atr",
        "stop_loss_ratio": 0.02,
        "stop_loss_atr_multiplier": 1.2,
        "atr_period": 7,
        "atr_timeframe": "15m",
        "max_daily_loss": 300,
        "max_daily_trades": 80,
        "max_positions": 5
    }
}
```

## 阈值类型说明

### ATR类型（推荐）

- 使用ATR（平均真实波幅）指标动态计算阈值
- 能够适应市场波动，提高策略适应性
- 适合波动较大的市场

### Fixed类型

- 使用固定比例作为阈值
- 计算简单，易于理解
- 适合波动较小的市场

## 风险提示

1. **测试先行**：务必先在测试网充分测试
2. **资金管理**：不要使用全部资金进行交易
3. **杠杆控制**：新手建议使用低杠杆（3-5倍）
4. **止损设置**：必须设置止损，控制单笔亏损
5. **定期检查**：定期查看日志和Web界面，监控策略运行状态
6. **备份配置**：定期备份配置文件和交易日志

## 常见问题

### 1. 测试网如何获取API密钥？

访问币安测试网：https://testnet.binance.vision/
注册账户后在API管理中创建API密钥

### 2. 如何修改交易对？

修改 `strategy.symbol` 字段，例如：
- ETH/USDT
- SOL/USDT
- DOGE/USDT

### 3. 如何调整策略激进程度？

- **更激进**：增大leverage和position_ratio，减小atr_multiplier
- **更保守**：减小leverage和position_ratio，增大atr_multiplier

### 4. 如何查看配置是否生效？

启动程序后查看日志，会显示加载的配置信息
