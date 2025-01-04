from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import numpy as np

class IndicatorType(Enum):
    """指标类型"""
    POSITIVE = "positive"  # 利好信号
    NEGATIVE = "negative"  # 利空信号

@dataclass
class StrategyIndicator:
    """策略分析指标"""
    score: float  # 指标得分
    reason: str   # 指标说明
    indicator_type: IndicatorType  # 指标类型

@dataclass
class Signal:
    """交易信号"""
    timestamp: str
    action: str  # 'buy' or 'sell'
    reason: str
    strength: float  # 0-1之间的信号强度
    entry_time: Optional[str] = None  # 新增字段，记录买入时间

@dataclass
class StrategyMetrics:
    """策略指标"""
    score: float  # 策略总得分
    support_level: float  # 支撑位
    resistance_level: float  # 压力位
    volume_strength: float  # 量能强度
    price_strength: float  # 价格强度
    additional_metrics: Dict[str, Any]  # 策略特有的其他指标

@dataclass
class AnalysisResult:
    """分析结果"""
    signal: Optional[Signal]  # 交易信号
    metrics: StrategyMetrics  # 策略指标
    debug_info: Dict[str, Any]  # 调试信息

class BaseStrategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass
    
    @property
    @abstractmethod
    def required_windows(self) -> int:
        """策略所需的最小数据窗口"""
        pass
    
    @property
    @abstractmethod
    def required_fields(self) -> List[str]:
        """策略所需的数据字段"""
        pass
    
    @abstractmethod
    def analyze(self,
               timestamp: str,
               open_prices: np.ndarray,
               high_prices: np.ndarray,
               low_prices: np.ndarray,
               close_prices: np.ndarray,
               volumes: np.ndarray,
               position: int = -1,
               **kwargs) -> Optional[AnalysisResult]:
        """
        分析单个时间点的市场状态
        
        Args:
            timestamp: 时间戳
            open_prices: 开盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列
            close_prices: 收盘价序列
            volumes: 成交量序列
            position: 分析位置，默认-1表示最新数据
            **kwargs: 额外参数
            
        Returns:
            AnalysisResult: 分析结果
        """
        pass
    
    @abstractmethod
    def should_entry(self, analysis_result: AnalysisResult) -> bool:
        """判断是否应该入场"""
        pass
    
    @abstractmethod
    def should_exit(self, analysis_result: AnalysisResult) -> bool:
        """判断是否应该出场"""
        pass 