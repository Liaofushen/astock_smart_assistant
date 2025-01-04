import streamlit as st
from pathlib import Path

def show_home():
    st.set_page_config(
        page_title="A股智能助手",
        page_icon="📊",
        layout="wide"
    )
    
    # 标题和简介
    st.title("📊 A股智能助手")
    st.markdown("""
    ### 功能介绍
    这是一个基于量价关系分析的智能选股和回测系统。通过分析股票的量价关系、趋势和支撑位，
    帮助投资者发现潜在的交易机会。
    """)
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 智能选股")
        st.markdown("""
        - 基于量价关系分析
        - 多维度技术指标
        - 实时市场数据
        - 个股详细分析
        """)
        if st.button("进入选股器", key="screener_btn", use_container_width=True):
            st.switch_page("src/astock_smart_assistant/pages/screener.py")
            
    with col2:
        st.markdown("### 📈 策略回测")
        st.markdown("""
        - 历史数据回测
        - 多策略对比
        - 绩效分析
        - 参数优化
        """)
        if st.button("进入回测系统", key="backtest_btn", use_container_width=True):
            st.switch_page("src/astock_smart_assistant/pages/backtest.py")
    
    # 添加系统信息
    st.markdown("---")
    st.markdown("### 📊 系统状态")
    
    # 创建三列显示系统信息
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric(
            label="数据更新时间",
            value="实时更新"
        )
    
    with status_col2:
        st.metric(
            label="可用策略数量",
            value="1"
        )
    
    with status_col3:
        st.metric(
            label="系统状态",
            value="正常运行"
        )

if __name__ == "__main__":
    show_home() 