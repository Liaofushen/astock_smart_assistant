import akshare as ak
import pandas as pd
import talib
import numpy as np
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor

class StockScreener:
    def __init__(self):
        self.stock_data = None
        self.thread_lock = threading.Lock()

    def screen_stocks(self, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(0, 100, "正在获取市场数据...")
            
            # 获取活跃股票数据
            active_stocks = ak.stock_zh_a_spot_em()
            
            if progress_callback:
                progress_callback(10, 100, "正在筛选活跃股票...")
            
            # 基础过滤条件
            active_stocks = active_stocks[
                (active_stocks['代码'].str.startswith(('00', '60'))) &
                (~active_stocks['名称'].str.contains('ST')) &
                (active_stocks['最新价'].astype(float) >= 5) &
                (active_stocks['最新价'].astype(float) <= 100) &
                (active_stocks['换手率'].astype(float) >= 3) &
                (active_stocks['涨跌幅'].astype(float) > -5) &
                (active_stocks['量比'].astype(float) >= 1) &
                (active_stocks['市盈率-动态'].astype(float) > 0) &
                (active_stocks['市盈率-动态'].astype(float) < 100) &
                (active_stocks['振幅'].astype(float) >= 2)
            ]
            
            if progress_callback:
                progress_callback(20, 100, "正在排序股票...")
            
            # 将所有需要的指标转换为百分位数排名
            active_stocks['换手率排名'] = active_stocks['换手率'].astype(float).rank(pct=True)
            active_stocks['成交额排名'] = active_stocks['成交额'].astype(float).rank(pct=True)
            active_stocks['量比排名'] = active_stocks['量比'].astype(float).rank(pct=True)
            active_stocks['涨速排名'] = active_stocks['涨速'].astype(float).rank(pct=True)
            active_stocks['五分钟涨跌排名'] = active_stocks['5分钟涨跌'].astype(float).rank(pct=True)
            
            # 计算综合得分（加权）
            active_stocks['排序得分'] = (
                active_stocks['换手率排名'] * 0.3 +  # 降低换手率权重
                active_stocks['成交额排名'] * 0.2 +  # 降低成交额权重
                active_stocks['量比排名'] * 0.2 +    # 加入量比指标
                active_stocks['涨速排名'] * 0.2 +    # 加入涨速指标
                active_stocks['五分钟涨跌排名'] * 0.1  # 加入短期趋势指标
            )
            
            # 按得分降序排序并选取前300只股票
            active_stocks = active_stocks.sort_values(
                by='排序得分',
                ascending=False
            ).head(300)
            
            results = []
            total_stocks = len(active_stocks)
            
            # 使用线程池处理股票分析
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self._process_single_stock, stock): i 
                          for i, (_, stock) in enumerate(active_stocks.iterrows())}
                
                for future in concurrent.futures.as_completed(futures):
                    if progress_callback:
                        current = futures[future] + 1
                        progress = 20 + int(current * 80 / total_stocks)
                        progress_callback(progress, 100, f"正在分析第 {current}/{total_stocks} 支股票...")
                    
                    result = future.result()
                    if result:
                        results.append(result)
            
            # 过滤并排序结果
            valid_results = [r for r in results if r is not None]
            valid_results.sort(key=lambda x: x[2], reverse=True)  # 按推荐指数排序
            
            # 对排序后的股票进行二次筛选
            # active_stocks = active_stocks[
            #     # 确保近期走势相对稳定
            #     (active_stocks['60日涨跌幅'].astype(float) > -30) &  # 去除长期下跌过猛的股票
            #     # (active_stocks['60日涨跌幅'].astype(float) < 100) &  # 去除前期涨幅过大的股票
                
            #     # 确保合理的市值范围
            #     (active_stocks['流通市值'].astype(float) >= 20e8) &  # 流通市值大于20亿
            #     (active_stocks['流通市值'].astype(float) <= 1000e8)  # 流通市值小于1000亿
            # ]
            
            return valid_results
            
        except Exception as e:
            print(f"获取股票数据时出错: {str(e)}")
            return []

    def _calculate_score(self, df, stock_code=None, stock_name=None, price_prediction=None):
        try:
            if len(df) < 20:  # 确保至少有20天数据
                return 0
            
            df = df.copy()
            
            required_columns = ['收盘', '开盘', '最高', '最低', '成交量']
            if not all(col in df.columns for col in required_columns):
                print(f"缺少必要的列: {df.columns}")
                return 0
            
            # 转换数据类型并检查
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)  # 确保转换为浮点数
            
            # 打印数据类型以调试
            # print(f"数据类型检查: {df[required_columns].dtypes}")
            
            close = df['收盘'].values
            open_price = df['开盘'].values
            high = df['最高'].values
            low = df['最低'].values
            volume = df['成交量'].values
            
            # 确保所有数组都是浮点数
            close = close.astype(float)
            open_price = open_price.astype(float)
            high = high.astype(float)
            low = low.astype(float)
            volume = volume.astype(float)
            
            score = 0
            positive_signals = {}  # 使用字典记录得分和文本
            negative_signals = {}
            
            # 1. 量价趋势分析 (40分)
            # 计算5日、10日均线
            ma5 = talib.SMA(close, timeperiod=5)
            ma10 = talib.SMA(close, timeperiod=10)
            vol_ma5 = talib.SMA(volume, timeperiod=5)
            
            # 判断均线多头排列
            if ma5[-1] > ma10[-1] and ma5[-2] > ma10[-2]:
                positive_signals['均线多头排列'] = 15  # 均线多头排列
                
                # 检查是否是上升趋势中的回调
                if close[-1] < ma5[-1] and close[-1] > ma10[-1]:
                    positive_signals['回调到支撑位'] = 10  # 回调到支撑位
            
            # 2. 量价配合分析 (40分)
            # 计算最近5天的量价关系
            for i in range(-5, 0):
                price_change = (close[i] - close[i-1]) / close[i-1]
                vol_change = volume[i] / vol_ma5[i]
                
                # 上涨放量
                if price_change > 0 and vol_change > 1.2:
                    positive_signals['上涨放量'] = 8
                # 下跌缩量
                elif price_change < 0 and vol_change < 0.8:
                    positive_signals['下跌缩量'] = 5
                # 下跌放量（卖压大）
                elif price_change < 0 and vol_change > 1.5:
                    negative_signals['下跌放量'] = 10
            
            # 3. 承接力度分析 (20分)
            for i in range(-5, -1):  # 使用更多的历史数据
                body = abs(close[i] - open_price[i])
                upper_shadow = high[i] - max(open_price[i], close[i])
                lower_shadow = min(open_price[i], close[i]) - low[i]
                
                # 设置影线长度的阈值
                shadow_threshold = 0.1 * body  # 影线长度至少为实体的10%

                # 上涨中的承接
                if close[i] > open_price[i]:
                    # 实体大于上影线，说明上涨承接好
                    if body > upper_shadow * 2 and upper_shadow > shadow_threshold:
                        positive_signals['上涨承接好'] = positive_signals.get('上涨承接好', 0) + 7
                    # 下影线长，说明有资金承接
                    if lower_shadow > body and lower_shadow > shadow_threshold:
                        positive_signals['资金承接'] = positive_signals.get('资金承接', 0) + 5
                
                # 下跌中的承接
                else:
                    # 下影线长于实体，说明有承接
                    if lower_shadow > body * 1.5 and lower_shadow > shadow_threshold:
                        positive_signals['下影线承接'] = positive_signals.get('下影线承接', 0) + 6
                    # 上影线过长，说明上方压力大
                    if upper_shadow > body * 2 and upper_shadow > shadow_threshold:
                        negative_signals['上方压力大'] = negative_signals.get('上方压力大', 0) + 5
            
            # 4. 风险控制（减分项）
            # 连续大阴线
            recent_changes = [(close[i] - open_price[i])/open_price[i] for i in range(-3, 0)]
            if all(change < -0.02 for change in recent_changes):
                negative_signals['连续大阴线'] = 20  # 连续大阴线，严重警告
            
            # 计算最终得分
            base_score = sum(positive_signals.values()) - sum(negative_signals.values())
            
            # 根据信号数量增加权重
            boost_factor = min(1.5, 1 + len(positive_signals) * 0.1)
            penalty_factor = min(2.0, 1 + len(negative_signals) * 0.2)
            
            final_score = base_score * boost_factor - sum(negative_signals.values()) * penalty_factor
            score = max(0, min(100, final_score))
            
            # 打印详细信息
            if score >= 60:
                p_str = "+".join([f"{k}({v})" for k, v in positive_signals.items()])
                n_str = "+".join([f"{k}({v})" for k, v in negative_signals.items()])
                print(f"股票 {stock_code} ({stock_name}) 得分: {score:.2f} 正向信号: {p_str} 负向信号: {n_str}")
            
            return score
            
        except Exception as e:
            print(f"计算得分时出错: {str(e)}")
            return 0

    def _predict_next_day_price(self, df):
        try:
            df = df.copy()
            
            # 获取最近的价格数据
            latest_close = df['收盘'].iloc[-1]
            latest_high = df['最高'].iloc[-1]
            latest_low = df['最低'].iloc[-1]
            latest_volume = df['成交量'].iloc[-1]
            
            # 计算最近5天的数据
            avg_volume = df['成交量'].rolling(5).mean().iloc[-1]
            avg_range = (df['最高'] - df['最低']).rolling(5).mean().iloc[-1]
            
            # 计算支撑和压力位
            support_level = min(df['最低'].iloc[-5:])
            resistance_level = max(df['最高'].iloc[-5:])
            
            # 计算量能强度
            volume_strength = latest_volume / avg_volume
            
            # 预测范围基于支撑位和压力位
            if volume_strength > 1.2:  # 放量
                high_pred = min(resistance_level * 1.05, latest_close * 1.1)  # 突破压力位
                low_pred = max(support_level, latest_close * 0.97)  # 较强支撑
            else:  # 缩量
                high_pred = min(resistance_level, latest_close * 1.05)  # 压力位限制
                low_pred = max(support_level * 0.98, latest_close * 0.95)  # 可能继续回调
            
            # 计算预测波动幅度
            pred_range = (high_pred - low_pred) / latest_close * 100
            
            return {
                '预测最高价': round(high_pred, 2),
                '预测最低价': round(low_pred, 2),
                '预测幅度': round(pred_range, 2),
                '成交量比': round(volume_strength, 2)
            }
            
        except Exception as e:
            print(f"预测价格时出错: {str(e)}")
            return None

    def _process_single_stock(self, stock):
        try:
            stock_code = stock['代码']
            stock_name = stock['名称']
            current_price = float(stock['最新价'])
            change_pct = float(stock['涨跌幅'])
            
            # 修改为获取日K线数据
            hist_data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",  # 改为日级别
                start_date=(pd.Timestamp.now() - pd.Timedelta(days=120)).strftime("%Y%m%d"),  # 获取更长时间的历史数据
                end_date=pd.Timestamp.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if hist_data.empty:
                return None
                
            # 先进行价格预测
            price_prediction = self._predict_next_day_price(hist_data)
            
            # 计算技术指标得分，并传入价格预测结果
            score = self._calculate_score(hist_data, stock_code, stock_name, price_prediction)
            
            if score > 0:
                # 把 stock 放在最前面
                result = [stock_code, stock_name, score, current_price, change_pct]
                
                if price_prediction:
                    result.extend([
                        price_prediction['预测最高价'],
                        price_prediction['预测最低价'],
                        price_prediction['预测幅度'],
                        price_prediction['成交量比']
                    ])
                else:
                    result.extend([0, 0, 0, 0])
                
                result.append(stock['今开'])
                result.append(stock['昨收'])
                result.append(stock['涨速'])
                result.append(stock['5分钟涨跌'])
                result.append(stock['60日涨跌幅'])
                result.append(stock['年初至今涨跌幅'])
                result.append(stock['换手率'])
                result.append(stock['总市值'])
                result.append(stock['流通市值'])
                result.append(stock['振幅'])
                return result
            return None
            
        except Exception as e:
            print(f"处理股票 {stock_code} 时出错: {str(e)}")
            return None