import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import talib
import numpy as np

def calculate_kdj(df, n=9, m1=3, m2=3):
    df = df.copy()
    
    low_list = df['最低'].rolling(n).min()
    high_list = df['最高'].rolling(n).max()
    
    rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
    
    df['K'] = pd.DataFrame(rsv).ewm(com=m1-1).mean()
    df['D'] = pd.DataFrame(df['K']).ewm(com=m2-1).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df

def create_stock_charts(df):
    # 确保数据类型正确
    df['收盘'] = pd.to_numeric(df['收盘'])
    df['开盘'] = pd.to_numeric(df['开盘'])
    df['最高'] = pd.to_numeric(df['最高'])
    df['最低'] = pd.to_numeric(df['最低'])
    df['成交量'] = pd.to_numeric(df['成交量'])
    
    # 设置时间索引
    df.index = pd.to_datetime(df['时间'])
    df.index = df.index.tz_localize('Asia/Shanghai')  # 添加这行，确保时区正确
    
    # 计算MACD
    typical_price = (df['最高'].values + df['最低'].values + df['收盘'].values) / 3
    macd, signal, hist = talib.MACD(typical_price, 
                                   fastperiod=12,
                                   slowperiod=26,
                                   signalperiod=9)
    
    # 计算KDJ
    df = calculate_kdj(df)
    
    # 找到MACD和KDJ都开始有效的位置
    macd_valid_index = np.where(~np.isnan(macd))[0][0]
    kdj_valid_index = df.index[df['K'].notna()][0]  # 找到第一个非空的KDJ值
    
    # 使用最晚的起始位置，确保所有指标都有效
    valid_index = max(macd_valid_index, df.index.get_loc(kdj_valid_index))
    
    # 所有数据都从这个位置开始展示
    df = df.iloc[valid_index:]
    macd = macd[valid_index:]
    signal = signal[valid_index:]
    hist = hist[valid_index:]
    
    # 创建子图，修改行数和高度比例
    fig = make_subplots(
        rows=4, cols=1,  # 改为4行以容纳K线、成交量、MACD和KDJ
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.4, 0.2, 0.2, 0.2],  # 调整每个子图的高度比例
        specs=[[{"secondary_y": False}],  # K线图不需要副Y轴
               [{"secondary_y": False}],  # 成交量图
               [{"secondary_y": False}],  # MACD
               [{"secondary_y": False}]]   # KDJ
    )
    
    # 添加K线图（在第一行）
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['开盘'],
            high=df['最高'],
            low=df['最低'],
            close=df['收盘'],
            name='K线',
            increasing_line_color='red',
            decreasing_line_color='green'
        ),
        row=1, col=1
    )
    
    # 添加成交量图（在第二行）
    colors = ['red' if row['收盘'] >= row['开盘'] else 'green' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['成交量'],
            name='成交量',
            marker_color=colors,
            opacity=0.3
        ),
        row=2, col=1
    )
    
    # MACD图（在第三行）
    fig.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=hist,
            name='MACD Hist',
            marker_color=['red' if val >= 0 else 'green' for val in hist]
        ),
        row=3, col=1
    )
    
    # KDJ图（在第四行）
    fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K', line=dict(color='blue')), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['D'], name='D', line=dict(color='orange')), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['J'], name='J', line=dict(color='purple')), row=4, col=1)
    
    # 更新布局
    fig.update_layout(
        height=1000,
        title_text="60分钟K线图表",
        showlegend=True,
        xaxis4_rangeslider_visible=True
    )
    
    # 设置X轴为类别类型
    fig.update_xaxes(
        rangeslider_visible=False,
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        type='category',
        tickformat='%Y-%m-%d %H:%M',
        dtick=10
    )
    
    # 更新Y轴标题
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="KDJ", row=4, col=1)
    
    # 统一设置Y轴格式
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        showline=True,
        linewidth=1,
        linecolor='Grey'
    )
    
    return fig