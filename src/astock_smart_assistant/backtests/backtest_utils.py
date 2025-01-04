from typing import Dict, Any
import pandas as pd

def calculate_performance_metrics(results: Dict[str, Any]) -> pd.DataFrame:
    """
    计算回测性能指标
    
    Args:
        results: 回测结果字典
        
    Returns:
        pd.DataFrame: 包含各项性能指标的DataFrame
    """
    metrics = {
        '总收益率': results['stats']['total_return'] * 100,
        'Sharpe比率': results['stats']['sharpe_ratio'],
        '最大回撤': results['stats']['max_drawdown'] * 100,
        '交易次数': results['stats']['total_trades'],
        '胜率': results['stats']['win_rate'] * 100,
        '平均收益': results['stats']['avg_trade_return'] * 100
    }
    return pd.DataFrame(metrics.items(), columns=['指标', '数值'])

def format_trade_records(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    格式化交易记录
    
    Args:
        trades_df: 原始交易记录DataFrame
        
    Returns:
        pd.DataFrame: 格式化后的交易记录
    """
    trades_df = trades_df.copy()
    trades_df['Return'] = trades_df['Return'] * 100
    return trades_df.rename(columns={
        'Entry Time': '买入时间',
        'Exit Time': '卖出时间',
        'Entry Price': '买入价格',
        'Exit Price': '卖出价格',
        'Return': '收益率(%)'
    }) 