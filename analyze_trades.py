"""
交易统计分析工具
"""
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage.trade_recorder import TradeRecorder
from datetime import datetime
from decimal import Decimal


def print_summary(summary):
    """打印交易汇总"""
    print("\n" + "="*60)
    print("交易汇总统计")
    print("="*60 + "\n")

    print(f"总交易次数: {summary['total_trades']}")
    print(f"  买入次数: {summary['buy_trades']}")
    print(f"  卖出次数: {summary['sell_trades']}")
    print(f"总交易量: {summary['total_volume']:.6f}")
    print(f"总盈利: {summary['total_profit']:.2f} USDT")
    print(f"总亏损: {summary['total_loss']:.2f} USDT")
    print(f"净盈利: {summary['net_profit']:.2f} USDT")

    # 胜率计算
    if summary['total_trades'] > 0:
        win_rate = (summary['sell_trades'] / summary['total_trades']) * 100
        print(f"胜率: {win_rate:.2f}%")

    # 平均盈利
    if summary['total_trades'] > 0:
        avg_profit = summary['net_profit'] / summary['total_trades']
        print(f"平均每笔盈利: {avg_profit:.2f} USDT")

    print()


def print_detailed_trades(trades, limit=20):
    """打印详细交易记录"""
    print("\n" + "="*60)
    print(f"最近 {limit} 笔交易记录")
    print("="*60 + "\n")

    if not trades:
        print("暂无交易记录")
        return

    print(f"{'时间':<20} {'类型':<6} {'网格ID':<12} {'价格':<12} {'数量':<12} {'盈利':<12}")
    print("-"*80)

    for trade in trades[:limit]:
        timestamp = trade.get('timestamp', '')[:19]
        trade_type = trade.get('type', '')
        grid_id = trade.get('grid_id', '')
        price = trade.get('price', 0)
        amount = trade.get('amount', 0)
        profit = trade.get('profit', 0)

        print(f"{timestamp:<20} {trade_type:<6} {grid_id:<12} {price:<12.2f} {amount:<12.6f} {profit:<12.2f}")

    print()


def analyze_trades(trades):
    """分析交易数据"""
    if not trades:
        return None

    analysis = {
        'avg_buy_price': 0,
        'avg_sell_price': 0,
        'buy_count': 0,
        'sell_count': 0,
        'total_buy_amount': 0,
        'total_sell_amount': 0,
        'max_profit': 0,
        'max_loss': 0,
        'profitable_trades': 0,
        'loss_trades': 0
    }

    for trade in trades:
        if trade.get('type') == 'buy':
            analysis['buy_count'] += 1
            analysis['total_buy_amount'] += trade.get('amount', 0)
            analysis['avg_buy_price'] += trade.get('price', 0)
        else:
            analysis['sell_count'] += 1
            analysis['total_sell_amount'] += trade.get('amount', 0)
            analysis['avg_sell_price'] += trade.get('price', 0)

        profit = trade.get('profit', 0)
        if profit > 0:
            analysis['profitable_trades'] += 1
            analysis['max_profit'] = max(analysis['max_profit'], profit)
        elif profit < 0:
            analysis['loss_trades'] += 1
            analysis['max_loss'] = max(analysis['max_loss'], abs(profit))

    # 计算平均价格
    if analysis['buy_count'] > 0:
        analysis['avg_buy_price'] /= analysis['buy_count']
    if analysis['sell_count'] > 0:
        analysis['avg_sell_price'] /= analysis['sell_count']

    return analysis


def main():
    """主函数"""
    print("="*60)
    print("币安对冲网格 - 交易统计分析")
    print("="*60 + "\n")

    # 初始化交易记录器
    recorder = TradeRecorder("data")

    # 加载交易记录
    trades = recorder.load_trades(limit=1000)

    if not trades:
        print("暂无交易记录，请先运行策略")
        return

    # 显示交易汇总
    summary = recorder.get_trade_summary()
    print_summary(summary)

    # 显示详细交易
    print_detailed_trades(trades, limit=20)

    # 交易分析
    print("\n" + "="*60)
    print("交易分析")
    print("="*60 + "\n")

    analysis = analyze_trades(trades)

    if analysis:
        print(f"平均买入价格: {analysis['avg_buy_price']:.2f}")
        print(f"平均卖出价格: {analysis['avg_sell_price']:.2f}")
        print(f"总买入数量: {analysis['total_buy_amount']:.6f}")
        print(f"总卖出数量: {analysis['total_sell_amount']:.6f}")
        print(f"最大单笔盈利: {analysis['max_profit']:.2f} USDT")
        print(f"最大单笔亏损: {analysis['max_loss']:.2f} USDT")
        print(f"盈利交易数: {analysis['profitable_trades']}")
        print(f"亏损交易数: {analysis['loss_trades']}")

        if analysis['profitable_trades'] + analysis['loss_trades'] > 0:
            win_rate = analysis['profitable_trades'] / (analysis['profitable_trades'] + analysis['loss_trades']) * 100
            print(f"盈亏交易胜率: {win_rate:.2f}%")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n分析已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
