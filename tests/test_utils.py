import pytest
from astock_assistant.stock_screener import StockScreener

@pytest.fixture
def stock_screener():
    """创建 StockScreener 实例的 fixture"""
    return StockScreener()

def test_stock_screener_initialization(stock_screener):
    """测试 StockScreener 初始化"""
    assert stock_screener is not None
