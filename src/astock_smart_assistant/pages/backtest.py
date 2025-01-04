import streamlit as st
from astock_smart_assistant.strategies.volume_price_strategy import VolumePriceStrategy
from astock_smart_assistant.backtests.backtest_runner import run_backtest
import pandas as pd

def show_backtest():
    st.set_page_config(
        page_title="策略回测",
        page_icon="📈",
        layout="wide"
    )
    
    # 添加返回首页按钮
    if st.button("返回首页", key="home_btn"):
        st.switch_page("src/astock_smart_assistant/pages/home.py")
    
    st.title("📈 策略回测系统")
    
    # 创建侧边栏用于参数设置
    with st.sidebar:
        st.header("回测参数设置")
        
        # 股票代码输入
        stock_code = st.text_input(
            "股票代码",
            value="000001",
            help="输入6位股票代码"
        )
        
        # 策略选择（目前只有一个策略）
        strategy_type = st.selectbox(
            "选择策略",
            ["量价关系策略"],
            index=0
        )
        
        # 回测参数
        score_threshold = st.slider(
            "入场得分阈值",
            min_value=0,
            max_value=100,
            value=70
        )
        
        # 运行回测按钮
        run_button = st.button("运行回测", use_container_width=True)
    
    # 主界面
    if run_button:
        with st.spinner("正在进行回测..."):
            # 创建策略实例
            strategy = VolumePriceStrategy()
            
            # 运行回测
            results = run_backtest(stock_code, strategy)
            
            # 显示回测结果
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.plotly_chart(results['figure'], use_container_width=True)
            
            with col2:
                st.markdown("### 策略绩效")
                metrics_df = pd.DataFrame({
                    '指标': [
                        '总收益率',
                        'Sharpe比率',
                        '最大回撤',
                        '交易次数',
                        '胜率',
                        '平均收益'
                    ],
                    '数值': [
                        f"{results['stats']['total_return']*100:.2f}%",
                        f"{results['stats']['sharpe_ratio']:.2f}",
                        f"{results['stats']['max_drawdown']*100:.2f}%",
                        f"{results['stats']['total_trades']}",
                        f"{results['stats']['win_rate']*100:.2f}%",
                        f"{results['stats']['avg_trade_return']*100:.2f}%"
                    ]
                })
                st.table(metrics_df)
            
            # 显示交易记录
            st.markdown("### 交易记录")
            trades_df = results['trades'].records_readable.copy()
            trades_df['Return'] = trades_df['Return'] * 100
            trades_df = trades_df.rename(columns={
                'Entry Timestamp': '买入时间',
                'Exit Timestamp': '卖出时间',
                'Avg Entry Price': '买入价格',
                'Avg Exit Price': '卖出价格',
                'Return': '收益率(%)'
            })
            st.dataframe(trades_df, use_container_width=True)

if __name__ == "__main__":
    show_backtest() 