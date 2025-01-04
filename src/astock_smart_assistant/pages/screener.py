import streamlit as st

def show_screener():
    st.set_page_config(
        page_title="智能选股",
        page_icon="🔍",
        layout="wide"
    )
    
    # 添加返回首页按钮
    if st.button("返回首页", key="home_btn"):
        st.switch_page("src/astock_smart_assistant/pages/home.py")
        
    st.title("🔍 智能选股系统")
    
    # 其余代码保持不变...

if __name__ == '__main__':
    show_screener() 