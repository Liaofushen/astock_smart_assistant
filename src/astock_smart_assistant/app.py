import streamlit as st
from astock_smart_assistant.pages.home import show_home
from astock_smart_assistant.config.logging_config import setup_logging

def initialize_app():
    """
    初始化应用程序
    - 加载配置
    - 设置日志
    - 初始化数据连接等
    """
    # 加载配置
    
    # 设置日志
    setup_logging()
    
    # 设置页面配置
    st.set_page_config(
        page_title="A股智能助手",
        page_icon="📊",
        layout="wide"
    )
    
def main():
    """
    应用程序入口点
    """
    try:
        # 初始化应用
        initialize_app()
        
        # 显示首页
        show_home()
        
    except Exception as e:
        st.error(f"应用启动错误: {str(e)}")

if __name__ == "__main__":
    main() 