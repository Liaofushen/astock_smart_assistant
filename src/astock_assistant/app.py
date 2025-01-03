import io

import akshare as ak
import pandas as pd
import streamlit as st
from astock_assistant.stock_detail import create_stock_charts
from astock_assistant.stock_screener import StockScreener

index_titles = [
    '股票代码',
    '股票名称',
    '推荐指数',
    '当前价格',
    '涨跌幅(%)',
    '预测最高价',
    '预测最低价',
    '预测波动(%)',
    '量比',
    '今开',
    '昨收',
    '涨速',
    '5分钟涨跌',
    '60日涨跌幅',
    '年初至今涨跌幅',
    '换手率',
    '总市值',
    '流通市值',
    '振幅',
]


def show_results():
    if st.session_state.results:
        # 创建DataFrame并设置正确的列名
        df = pd.DataFrame(st.session_state.results)

        df.columns = index_titles

        # 创建两列布局
        left_col, right_col = st.columns([0.3, 0.7])

        with left_col:
            st.subheader('推荐股票列表')

            # 创建表头
            cols = st.columns([1, 1.2, 0.8, 0.8, 0.8])
            cols[0].write('**股票代码**')
            cols[1].write('**股票名称**')
            cols[2].write('**推荐指数**')
            cols[3].write('**当前价格**')
            cols[4].write('**涨跌幅(%)**')

            # 显示每行数据，每个股票代码都是一个按钮
            for _, row in df.iterrows():
                cols = st.columns([1, 1.2, 0.8, 0.8, 0.8])

                # 股票代码作为按钮
                if cols[0].button(row['股票代码'], key=f"btn_{row['股票代码']}"):
                    st.session_state.selected_stock = row['股票代码']

                # 其他列正常显示
                cols[1].write(row['股票名称'])

                # 推荐指数带颜色
                score = row['推荐指数']
                color = 'red' if score >= 80 else 'orange' if score >= 70 else 'black'
                cols[2].markdown(
                    f"<span style='color: {color}'>{score:.0f}</span>",
                    unsafe_allow_html=True,
                )

                cols[3].write(f"{row['当前价格']:.2f}")

                # 涨跌幅带颜色
                change = row['涨跌幅(%)']
                color = 'red' if change > 0 else 'green' if change < 0 else 'black'
                cols[4].markdown(
                    f"<span style='color: {color}'>{change:.2f}%</span>",
                    unsafe_allow_html=True,
                )

            # 创建Excel二进制数据
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='选股结果')
                # 获取工作表
                worksheet = writer.sheets['选股结果']
                # 调整列宽
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception as e:
                            print(e)
                            pass
                    adjusted_width = max_length + 2
                    worksheet.column_dimensions[
                        column[0].column_letter
                    ].width = adjusted_width

            # 重置指针位置
            output.seek(0)

            # 添加下载按钮
            st.download_button(
                label='下载选股结果(Excel)',
                data=output.getvalue(),
                file_name='stock_recommendations.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

        with right_col:
            if st.session_state.selected_stock:
                show_stock_details(st.session_state.selected_stock)


def show_stock_details(stock_code):
    try:
        # 获取股票数据
        df = pd.DataFrame(st.session_state.results)
        df.columns = index_titles
        stock_info = df[df['股票代码'] == stock_code].iloc[0]

        st.write(f"### {stock_code} - {stock_info['股票名称']}")

        # 创建两列布局显示预测信息
        col1, col2 = st.columns(2)

        with col1:
            delta_pct = (stock_info['预测最高价'] / stock_info['当前价格'] - 1) * 100
            st.metric(
                label='预测最高价',
                value=f"¥{stock_info['预测最高价']:.2f}",
                delta=f'{delta_pct:.1f}%',
                delta_color='inverse',  # "normal"表示上涨红色，下跌绿色
            )

        with col2:
            delta_pct = (stock_info['预测最低价'] / stock_info['当前价格'] - 1) * 100
            st.metric(
                label='预测最低价',
                value=f"¥{stock_info['预测最低价']:.2f}",
                delta=f'{delta_pct:.1f}%',
                delta_color='inverse',  # "normal"表示上涨红色，下跌绿色
            )

        # 显示预测详情
        st.write('### 预测详情')
        details = pd.DataFrame(
            {
                '指标': ['预测波动幅度', '当前量比', '推荐指数'],
                '数值': [
                    f"{stock_info['预测波动(%)']}%",
                    f"{stock_info['量比']:.2f}",
                    f"{stock_info['推荐指数']:.0f}",
                ],
            }
        )
        st.table(details)

        # 显示市场指标
        st.write('### 市场指标')

        # 使用5列布局，创建类似表格的效果
        col1, col2, col3, col4, col5 = st.columns(5)

        # 第一行
        with col1:
            st.metric('今开', f"¥{stock_info['今开']:.2f}")
        with col2:
            st.metric('昨收', f"¥{stock_info['昨收']:.2f}")
        with col3:
            st.metric('涨速', f"{stock_info['涨速']}%")
        with col4:
            st.metric('振幅', f"{stock_info['振幅']}%")
        with col5:
            st.metric('换手率', f"{stock_info['换手率']}%")

        # 第二行
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric('5分钟涨跌', f"{stock_info['5分钟涨跌']}%")
        with col2:
            st.metric('60日涨跌幅', f"{stock_info['60日涨跌幅']}%")
        with col3:
            st.metric('年初至今涨跌幅', f"{stock_info['年初至今涨跌幅']}%")
        with col4:
            st.metric('总市值', format_market_value(stock_info['总市值']))
        with col5:
            st.metric('流通市值', format_market_value(stock_info['流通市值']))

        # 获取分时数据并显示图表
        hist_data = ak.stock_zh_a_hist(
            symbol=stock_code,
            period='daily',  # 改为日级别
            start_date=(pd.Timestamp.now() - pd.Timedelta(days=120)).strftime('%Y%m%d'),
            end_date=pd.Timestamp.now().strftime('%Y%m%d'),
            adjust='qfq',
        )

        if not hist_data.empty:
            charts = create_stock_charts(hist_data)
            st.plotly_chart(charts, use_container_width=True)

    except Exception as e:
        st.error(f'获取股票数据失败: {str(e)}')


# 格式化市值显示（转换为亿）
def format_market_value(value_float):
    try:
        if value_float >= 100000000000:  # 大于1000亿
            return f'{value_float/100000000:.0f}亿'
        else:
            return f'{value_float/100000000:.2f}亿'
    except Exception as e:
        print(e)
        return value_float


if __name__ == '__main__':
    st.set_page_config(page_title='stock analysis', layout='wide')

    # 初始化 session state
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'progress' not in st.session_state:
        st.session_state.progress = None

    if st.button('开始选股') or st.session_state.results is not None:
        if st.session_state.results is None:  # 只在第一次点击时执行选股
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total, message):
                progress = int(current * 100 / total)
                progress_bar.progress(progress)
                status_text.text(f'{message} ({progress}%)')

            with st.spinner('正在分析市场活跃股票，请稍候...'):
                screener = StockScreener()
                results = screener.screen_stocks(progress_callback=update_progress)
                st.session_state.results = results

            progress_bar.empty()
            status_text.empty()

        show_results()
