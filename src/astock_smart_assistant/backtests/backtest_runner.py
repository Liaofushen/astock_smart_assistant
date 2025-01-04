import vectorbt as vbt
import akshare as ak
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from vectorbt.portfolio import enums as vbt_enums
from astock_smart_assistant.strategies.base_strategy import BaseStrategy
from astock_smart_assistant.strategies.volume_price_strategy import VolumePriceStrategy

def run_backtest(stock_code: str, strategy: BaseStrategy):
    # 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # 获取数据 - akshare 格式
    hist_data = ak.stock_zh_a_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
        adjust="qfq"
    )
    
    # 转换为标准格式
    hist_data = hist_data.rename(columns={
        '日期': 'datetime',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    })
    hist_data.set_index('datetime', inplace=True)
    hist_data.index = pd.to_datetime(hist_data.index)
    
    # 确保数据长度足够
    if len(hist_data) <= strategy.required_windows:
        raise ValueError(f"历史数据长度({len(hist_data)})小于策略所需窗口期({strategy.required_windows})")
    
    # 计算每个时间点的信号
    analysis_results = []
    entries = []
    exits = []
    
    holding_days = 0
    max_holding_days = 2  # 设置最大持仓天数

    for i in range(strategy.required_windows, len(hist_data)):
        try:
            # 获取截止到当前位置的所有历史数据
            window_data = {
                'timestamp': str(hist_data.index[i]),
                'open_prices': hist_data['open'].values[:i],
                'high_prices': hist_data['high'].values[:i],
                'low_prices': hist_data['low'].values[:i],
                'close_prices': hist_data['close'].values[:i],
                'volumes': hist_data['volume'].values[:i],
                'position': -1
            }
            
            # 检查数据长度
            if len(window_data['close_prices']) < strategy.required_windows:
                continue
                
            result = strategy.analyze(**window_data)
            analysis_results.append(result)
            
            # 处理买入信号
            if strategy.should_entry(result):
                if holding_days < max_holding_days:  # 只有在没有持仓时才买入
                    entries.append(True)
                    exits.append(False)
                    holding_days += 1
                    continue
                    
            # 处理卖出信号
            should_exit = (
                strategy.should_exit(result) or  # 策略建议卖出
                holding_days >= max_holding_days  # 或达到最大持仓天数
            )
            
            if holding_days > 0:  # 有持仓
                if should_exit:
                    entries.append(False)
                    exits.append(True)
                    holding_days = 0
                else:
                    holding_days += 1
                    entries.append(False)
                    exits.append(False)
            else:  # 无持仓
                entries.append(False)
                exits.append(False)
            
        except Exception as e:
            print(f"分析第 {i} 个数据点时出错: {str(e)}")
            analysis_results.append(None)
            continue
        
    entries = [False] * strategy.required_windows + entries
    exits = [False] * strategy.required_windows + exits
    padding = [0] * strategy.required_windows
    scores = padding + [r.metrics.score if r else 0 for r in analysis_results]
    volume_strengths = padding + [r.metrics.volume_strength if r else 0 for r in analysis_results]
    price_strengths = padding + [r.metrics.price_strength if r else 0 for r in analysis_results]
    supports = list(hist_data['low'].iloc[:strategy.required_windows]) + [r.metrics.support_level if r else hist_data['low'].iloc[i] for i, r in enumerate(analysis_results)]
    resistances = list(hist_data['high'].iloc[:strategy.required_windows]) + [r.metrics.resistance_level if r else hist_data['high'].iloc[i] for i, r in enumerate(analysis_results)]
    
    # 创建信号DataFrame
    # hist_data['signal'] = signals
    hist_data['score'] = scores
    hist_data['volume_strength'] = volume_strengths
    hist_data['price_strength'] = price_strengths
    hist_data['support'] = supports
    hist_data['resistance'] = resistances
    
    # 运行回测
    pf = vbt.Portfolio.from_signals(
        close=hist_data['close'],
        entries=entries,
        exits=exits,
        init_cash=10000,
        fees=0.0025,  # 0.25% 手续费
        freq='1D',    # 日线级别
        size=50,     # 每次买入时的资金利用率
        size_type=vbt_enums.SizeType.Percent,  # 按百分比控制仓位
        direction='longonly',  # 只做多
        entry_price=hist_data['close'],  # 买入使用收盘价
        exit_price=hist_data['open'],    # 卖出使用开盘价
    )
    
    # 生成图表
    fig = make_subplots(rows=4, cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.4, 0.2, 0.2, 0.2])

    # 添加K线图
    fig.add_trace(go.Candlestick(
        x=hist_data.index,
        open=hist_data['open'],
        high=hist_data['high'],
        low=hist_data['low'],
        close=hist_data['close'],
        name='K线'
    ), row=1, col=1)
    
    # 添加支撑压力位
    fig.add_trace(go.Scatter(
        x=hist_data.index,
        y=hist_data['support'],
        name='支撑位',
        line=dict(color='green', dash='dash')
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=hist_data.index,
        y=hist_data['resistance'],
        name='压力位',
        line=dict(color='red', dash='dash')
    ), row=1, col=1)

    # 添加成交量
    colors = ['red' if x >= 0 else 'green' for x in hist_data['close'].diff()]
    fig.add_trace(go.Bar(
        x=hist_data.index,
        y=hist_data['volume'],
        name='成交量',
        marker_color=colors
    ), row=2, col=1)
    
    # 添加策略得分
    fig.add_trace(go.Scatter(
        x=hist_data.index,
        y=hist_data['score'],
        name='策略得分',
        line=dict(color='purple')
    ), row=3, col=1)

    # 添加资金曲线
    fig.add_trace(go.Scatter(
        x=hist_data.index,
        y=pf.value(),
        name='资金曲线',
        line=dict(color='blue')
    ), row=4, col=1)

    # 标记交易点位
    for idx, trade in pf.trades.records_readable.iterrows():
        # 买入点
        fig.add_trace(go.Scatter(
            x=[trade['Entry Timestamp']],
            y=[trade['Avg Entry Price']],
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color='red'),
            name=f'买入 {trade["Avg Entry Price"]:.2f}'
        ), row=1, col=1)
        
        # 卖出点
        if not pd.isna(trade['Exit Timestamp']):
            fig.add_trace(go.Scatter(
                x=[trade['Exit Timestamp']],
                y=[trade['Avg Exit Price']],
                mode='markers',
                marker=dict(symbol='triangle-down', size=10, color='green'),
                name=f'卖出 {trade["Avg Exit Price"]:.2f}'
            ), row=1, col=1)

    # 更新布局，添加 x 轴设置
    fig.update_layout(
        title=f'{stock_code} 量价策略回测结果',
        xaxis_title='日期',
        yaxis_title='价格',
        height=1000,
        xaxis=dict(
            type='category',  # 使用分类型 x 轴
            rangeslider=dict(visible=False),  # 禁用范围滑块
            tickmode='auto',  # 自动调整刻度
            nticks=20,  # 控制显示的刻度数量
        ),
        xaxis2=dict(type='category'),  # 成交量图表的 x 轴
        xaxis3=dict(type='category'),  # 策略得分图表的 x 轴
        xaxis4=dict(type='category'),  # 资金曲线图表的 x 轴
    )

    # 计算策略统计指标
    stats = {
        'total_return': pf.total_return(),
        'sharpe_ratio': pf.sharpe_ratio(),
        'max_drawdown': pf.max_drawdown(),
        'total_trades': len(pf.trades.records),
        'win_rate': len(pf.trades.records[pf.trades.records['return'] > 0]) / len(pf.trades.records) if len(pf.trades.records) > 0 else 0,
        'avg_trade_return': pf.trades.records['return'].mean() if len(pf.trades.records) > 0 else 0
    }

    return {
        'stats': stats,
        'trades': pf.trades,
        'figure': fig,
        'daily_data': hist_data
    }

if __name__ == '__main__':
    # 创建策略实例
    strategy = VolumePriceStrategy()
    
    # 运行回测
    results = run_backtest('000001', strategy)
    print("\n策略统计指标:")
    for key, value in results['stats'].items():
        print(f"{key}: {value:.4f}")
    
    # 显示图表
    results['figure'].show() 