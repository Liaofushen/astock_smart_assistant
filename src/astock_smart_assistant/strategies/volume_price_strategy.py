from dataclasses import dataclass
from enum import Enum
import numpy as np
import talib
from typing import List, Dict, Optional, Any
from astock_smart_assistant.strategies.base_strategy import (
    BaseStrategy, Signal, StrategyMetrics, AnalysisResult,
    IndicatorType, StrategyIndicator
)

class VolumePriceStrategy(BaseStrategy):
    """量价关系分析策略"""
    
    @property
    def name(self) -> str:
        return "量价关系策略"
    
    @property
    def description(self) -> str:
        return "基于量价关系、趋势和支撑位的交易策略"
    
    @property
    def required_windows(self) -> int:
        return 30
    
    @property
    def required_fields(self) -> List[str]:
        return ['open', 'high', 'low', 'close', 'volume']
    
    def analyze(self,
               timestamp: str,
               open_prices: np.ndarray,
               high_prices: np.ndarray,
               low_prices: np.ndarray,
               close_prices: np.ndarray,
               volumes: np.ndarray,
               position: int = -1,
               **kwargs) -> Optional[AnalysisResult]:
        try:
            if len(close_prices) < self.required_windows:
                return None
            
            # 确保数据类型为 float64
            open_prices = np.array(open_prices, dtype=np.float64)
            high_prices = np.array(high_prices, dtype=np.float64)
            low_prices = np.array(low_prices, dtype=np.float64)
            close_prices = np.array(close_prices, dtype=np.float64)
            volumes = np.array(volumes, dtype=np.float64)
                
            # 1. 计算技术指标
            ma5 = talib.SMA(close_prices, timeperiod=5)
            ma10 = talib.SMA(close_prices, timeperiod=10)
            vol_ma5 = talib.SMA(volumes, timeperiod=5)
            
            # 2. 分析各个维度
            # trend_signals = self._analyze_trend(ma5, ma10, close_prices, position)
            volume_signals = self._analyze_volume_price(close_prices, volumes, vol_ma5, position)
            # support_signals = self._analyze_support(open_prices, high_prices, low_prices, close_prices, position)
            
            # 3. 计算支撑压力位
            support_level = self._calculate_support(low_prices, close_prices, position)
            resistance_level = self._calculate_resistance(high_prices, close_prices, position)
            
            # 4. 汇总信号
            all_signals = []
            # all_signals.extend(trend_signals)
            all_signals.extend(volume_signals)
            # all_signals.extend(support_signals)
            
            # 计算总分
            total_score = self._calculate_final_score(all_signals)
            
            # 5. 生成交易信号
            signal = None
            if total_score >= 70:
                signal = Signal(
                    timestamp=timestamp,
                    action='buy',
                    reason=f"策略得分: {total_score:.2f}",
                    strength=min(1.0, total_score/100),
                    entry_time=timestamp
                )
            
            # 6. 生成指标
            metrics = StrategyMetrics(
                score=total_score,
                support_level=support_level,
                resistance_level=resistance_level,
                volume_strength=volumes[position] / vol_ma5[position],
                price_strength=(close_prices[position] - ma5[position]) / ma5[position],
                additional_metrics={
                    # 'trend_score': sum(s.score for s in trend_signals if s.indicator_type == IndicatorType.POSITIVE),
                    'volume_score': sum(s.score for s in volume_signals if s.indicator_type == IndicatorType.POSITIVE),
                    # 'support_score': sum(s.score for s in support_signals if s.indicator_type == IndicatorType.POSITIVE)
                }
            )
            
            # 7. 调试信息
            debug_info = {
                'signals': [{'reason': s.reason, 'score': s.score, 'type': s.indicator_type.value} for s in all_signals],
                'ma5': ma5[position],
                'ma10': ma10[position],
                'vol_ma5': vol_ma5[position]
            }
            
            return AnalysisResult(signal, metrics, debug_info)
            
        except Exception as e:
            print(f"策略分析错误: {str(e)}")
            return None
    
    def should_entry(self, analysis_result: AnalysisResult) -> bool:
        """判断是否应该入场"""
        if not analysis_result:
            return False
        return analysis_result.metrics.score >= 70
    def should_exit(self, analysis_result: AnalysisResult) -> bool:
        """判断是否应该出场"""
        if not analysis_result:
            return True
        return analysis_result.metrics.score < 70
        
    def _calculate_holding_days(self, entry_time: str, current_time: str) -> int:
        """计算持仓天数"""
        from datetime import datetime
        entry_dt = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
        current_dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        return (current_dt - entry_dt).days
    
    def _analyze_trend(self, ma5, ma10, close, position) -> List[StrategyIndicator]:
        """分析均线趋势"""
        signals = []
        
        # 检查当日是否发生金叉或死叉
        today_cross = None
        if ma5[position] > ma10[position] and ma5[position-1] < ma10[position-1]:
            today_cross = "金叉"
        elif ma5[position] < ma10[position] and ma5[position-1] > ma10[position-1]:
            today_cross = "死叉"
        
        # 均线多头排列
        if ma5[position] > ma10[position]:
            if today_cross == "金叉":
                signals.append(StrategyIndicator(25, "当日金叉转多头", IndicatorType.POSITIVE))
            else:
                signals.append(StrategyIndicator(15, "均线多头排列", IndicatorType.POSITIVE))
            
            # 回调到支撑位
            if close[position] < ma5[position] and close[position] > ma10[position]:
                signals.append(StrategyIndicator(
                    15 if today_cross == "金叉" else 10, 
                    "当日金叉回调买点" if today_cross == "金叉" else "回调到支撑位",
                    IndicatorType.POSITIVE
                ))
                
        # 均线空头排列
        else:
            if today_cross == "死叉":
                signals.append(StrategyIndicator(25, "当日死叉转空头", IndicatorType.NEGATIVE))
            else:
                signals.append(StrategyIndicator(15, "均线空头排列", IndicatorType.NEGATIVE))
            
            # 反弹到阻力位
            if close[position] > ma5[position] and close[position] < ma10[position]:
                signals.append(StrategyIndicator(
                    15 if today_cross == "死叉" else 10,
                    "当日死叉反弹卖点" if today_cross == "死叉" else "反弹到阻力位",
                    IndicatorType.NEGATIVE
                ))
                
        return signals
    
    def _analyze_volume_price(self, close, volume, vol_ma5, position) -> List[StrategyIndicator]:
        """分析最新一天的量价关系"""
        signals = []
        
        # 计算价格和成交量变化
        price_change = (close[position] - close[position-1]) / close[position-1]
        vol_change = volume[position] / vol_ma5[position]  # 相对于5日均量
        vol_change_today = volume[position] / volume[position-1]  # 相对于前一天
        
        # 价格变化幅度分类
        is_big_up = price_change > 0.03
        is_small_up = 0 < price_change <= 0.03
        is_big_down = price_change < -0.03
        is_small_down = -0.03 <= price_change < 0
        
        # 成交量变化分类
        is_huge_vol = vol_change > 2 or vol_change_today > 2  # 巨量
        is_big_vol = 1.2 < vol_change <= 2 or 1.2 < vol_change_today <= 2  # 放量
        is_normal_vol = 0.8 <= vol_change <= 1.2 and 0.8 <= vol_change_today <= 1.2  # 正常量
        is_small_vol = vol_change < 0.8 and vol_change_today < 0.8  # 缩量
        
        # 上涨情况细分
        if is_big_up:
            if is_huge_vol:
                signals.append(StrategyIndicator(25, "大幅上涨巨量，可能是重大利好或炒作", IndicatorType.POSITIVE))
            elif is_big_vol:
                signals.append(StrategyIndicator(20, "大幅上涨放量，上升趋势确立", IndicatorType.POSITIVE))
            elif is_normal_vol:
                signals.append(StrategyIndicator(15, "大幅上涨量能正常，走势稳健", IndicatorType.POSITIVE))
            elif is_small_vol:
                signals.append(StrategyIndicator(5, "大幅上涨量能不足，上涨持续性存疑", IndicatorType.NEGATIVE))
        
        elif is_small_up:
            if is_huge_vol:
                signals.append(StrategyIndicator(10, "小幅上涨巨量，可能是筹码集中", IndicatorType.NEGATIVE))
            elif is_big_vol:
                signals.append(StrategyIndicator(15, "小幅上涨放量，上升动能在积聚", IndicatorType.POSITIVE))
            elif is_normal_vol:
                signals.append(StrategyIndicator(10, "小幅上涨量能正常，走势平稳", IndicatorType.POSITIVE))
            elif is_small_vol:
                signals.append(StrategyIndicator(5, "小幅上涨量能萎缩，上涨乏力", IndicatorType.NEGATIVE))
        
        # 下跌情况细分
        elif is_big_down:
            if is_huge_vol:
                signals.append(StrategyIndicator(25, "大幅下跌巨量，可能是重大利空或恐慌性抛售", IndicatorType.NEGATIVE))
            elif is_big_vol:
                signals.append(StrategyIndicator(20, "大幅下跌放量，下跌趋势确立", IndicatorType.NEGATIVE))
            elif is_normal_vol:
                signals.append(StrategyIndicator(15, "大幅下跌量能正常，走势承压", IndicatorType.NEGATIVE))
            elif is_small_vol:
                signals.append(StrategyIndicator(10, "大幅下跌量能萎缩，可能是下跌末期", IndicatorType.POSITIVE))
        
        elif is_small_down:
            if is_huge_vol:
                signals.append(StrategyIndicator(15, "小幅下跌巨量，可能是主力洗盘", IndicatorType.POSITIVE))
            elif is_big_vol:
                signals.append(StrategyIndicator(15, "小幅下跌放量，需警惕加速下跌", IndicatorType.NEGATIVE))
            elif is_normal_vol:
                signals.append(StrategyIndicator(10, "小幅下跌量能正常，走势平稳", IndicatorType.NEGATIVE))
            elif is_small_vol:
                signals.append(StrategyIndicator(5, "小幅下跌量能萎缩，观望气氛浓厚", IndicatorType.POSITIVE))
                
        return signals
    
    def _analyze_support(self, open_price, high, low, close, position) -> List[StrategyIndicator]:
        """分析最新一天的支撑和压力"""
        signals = []
        
        # 只分析最后一天的K线形态
        body = abs(close[position] - open_price[position])
        upper_shadow = high[position] - max(open_price[position], close[position])
        lower_shadow = min(open_price[position], close[position]) - low[position]
        
        if close[position] > open_price[position]:  # 阳线
            if body > upper_shadow * 2:
                signals.append(StrategyIndicator(15, "当日强势上涨", IndicatorType.POSITIVE))
            if lower_shadow > body:
                signals.append(StrategyIndicator(12, "当日下方获得支撑", IndicatorType.POSITIVE))
        else:  # 阴线
            if lower_shadow > body * 1.5:
                # signals.append(StrategyIndicator(14, "当日下方承接强", IndicatorType.POSITIVE))
                pass
            if upper_shadow > body * 2:
                signals.append(StrategyIndicator(12, "当日上方压力大", IndicatorType.NEGATIVE))
            if body > (high[position] - low[position]) * 0.7:
                signals.append(StrategyIndicator(20, "当日跌幅过大", IndicatorType.NEGATIVE))
                
        return signals
    
    def _calculate_support(self, low, close, position):
        """计算支撑位"""
        return min(low[position-5:position])
    
    def _calculate_resistance(self, high, close, position):
        """计算压力位"""
        return max(high[position-5:position])
    
    def _calculate_final_score(self, signals: List[StrategyIndicator]) -> float:
        """计算最终得分"""
        # 分别计算正面和负面信号的总分
        positive_sum = sum(signal.score for signal in signals if signal.indicator_type == IndicatorType.POSITIVE)
        negative_sum = sum(signal.score for signal in signals if signal.indicator_type == IndicatorType.NEGATIVE)
        
        # 计算信号的总数量
        positive_count = sum(1 for signal in signals if signal.indicator_type == IndicatorType.POSITIVE)
        negative_count = sum(1 for signal in signals if signal.indicator_type == IndicatorType.NEGATIVE)
        
        # 基础分数计算
        base_score = 50  # 基准分数
        
        # 根据正负信号的强度调整分数
        if positive_sum > 0 or negative_sum > 0:
            # 计算正负信号的权重
            total_signals = positive_sum + negative_sum
            if total_signals > 0:
                score_adjustment = (positive_sum - negative_sum) / total_signals * 50
                final_score = base_score + score_adjustment
            else:
                final_score = base_score
        else:
            final_score = base_score
            
        # 确保分数在0-100之间
        return max(0, min(100, final_score)) 