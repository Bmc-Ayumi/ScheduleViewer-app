import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import load_and_process_csv, get_date_range, get_japanese_holidays
import calendar
import streamlit.components.v1 as components

st.set_page_config(page_title="スケジュール管理", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.selected_date_details = None

uploaded_file = st.file_uploader("スケジュールCSVをアップロード", type=['csv'])

if uploaded_file is not None:
    try:
        st.session_state.df = load_and_process_csv(uploaded_file)
        st.success("ファイルを読み込みました")
    except Exception as e:
        st.error(f"エラー: {str(e)}")

if st.session_state.df is not None:
    with st.sidebar:
        st.header("表示設定")

        # オーナー選択
        all_owners = sorted(st.session_state.df['Owner'].unique())
        selected_owner = st.radio("表示する担当者を選択", all_owners)
        selected_owners = [selected_owner]

        # 日付を取得
        min_date = st.session_state.df['date'].min()
        max_date = st.session_state.df['date'].max()

        # 月選択なしで最初の月の初日をselected_dateとして設定
        selected_date = min_date.replace(day=1)

    # 日付範囲の取得（月次表示用）
    start_date = selected_date.replace(day=1)
    if selected_date.month == 12:
        end_date = selected_date.replace(
            year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = selected_date.replace(month=selected_date.month + 1,
                                         day=1) - timedelta(days=1)

    # データのフィルタリング
    filtered_df = st.session_state.df[
        (st.session_state.df['Owner'].isin(selected_owners))
        & (st.session_state.df['date'] >= start_date) &
        (st.session_state.df['date'] <= end_date)]

    # 月次表示
    st.header(f"📅 カレンダー一覧 《{selected_owner}》")

    # スクレイピングされている全ての月のカレンダーを表示
    months_to_display = pd.date_range(start=min_date.replace(day=1),
                                      end=max_date.replace(day=1),
                                      freq='MS')

    # カレンダーを横に並べるHTMLを作成
    html_calendar_list = """
    <style>
        .calendar-container {
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
            gap: 10px;
            width: 100%;
        }
        .month-calendar {
            flex: 1 1 450px; /* カレンダーの幅をフレキシブルに */
            min-width: 380px;
            max-width: 600px;
            margin-bottom: 20px;
        }
        .month-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
            text-align: center;
        }
        .calendar-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .calendar-table th, .calendar-table td {
            border: 1px solid #000;
            padding: 4px;
            text-align: center;
            height: 50px;
        }
        .calendar-table th {
            height: auto;
            text-align: center;
        }
        .calendar-table th:nth-child(-n+5) {  /* 月～金 */
            background-color: #FFFFFF;
        }
        .calendar-table th:nth-child(6) {  /* 土曜日 */
            background-color: #E6F3FF;
        }
        .calendar-table th:nth-child(7) {  /* 日曜日 */
            background-color: #FFE6E6;
        }
        .calendar-table td:nth-child(6) .date-number span {  /* 土曜日の数字 */
            color: #0000FF;  /* 青色 */
        }
        .calendar-table td:nth-child(7) .date-number span {  /* 日曜日の数字 */
            color: #FF0000;  /* 赤色 */
        }
        /* 祝日のスタイル */
        .holiday-date {
            color: #FF0000 !important;  /* 祝日の日付は赤色 */
        }
        .calendar-cell {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .date-number {
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2px;
            border-bottom: 1px solid #000;
            width: 100%;
            padding-bottom: 2px;
        }
        .holiday-text {
            color: #FF0000;
            font-size: 0.85em;
            text-align: right;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 70%;
        }
        .am-pm-container {
            display: flex;
            flex-direction: row;
            height: 100%;
            flex-grow: 1;
        }
        .am-container, .pm-container {
            flex: 1;
            padding: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .am-container {
            border-right: 1px solid #000;
        }
        .am-holiday {
            background-color: #FFE4E4;
        }
        .pm-holiday {
            background-color: #FFE4E4;
        }
        .availability-mark {
            font-weight: bold;
            font-size: 1.2em;
        }
    </style>
    <div class="calendar-container">
    """

    # 各月のカレンダーを追加
    for month_date in months_to_display:
        month_title = month_date.strftime('%Y年%m月')

        # 各月のカレンダーを作成
        cal = calendar.monthcalendar(month_date.year, month_date.month)

        # 当月の祝日情報を取得
        holidays = get_japanese_holidays(month_date.year, month_date.month)

        # 月のカレンダーのHTMLを作成
        html_calendar_list += f'<div class="month-calendar"><div class="month-title">{month_title}</div>'
        html_calendar_list += '<table class="calendar-table"><tr>'

        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        for weekday in weekdays:
            html_calendar_list += f"<th>{weekday}</th>"
        html_calendar_list += "</tr>"

        for week in cal:
            html_calendar_list += "<tr>"
            for day in week:
                if day == 0:
                    html_calendar_list += "<td></td>"
                else:
                    current_date = month_date.replace(day=day)
                    is_holiday = day in holidays
                    holiday_name = holidays.get(day, '')
                    daily_events = filtered_df[(
                        filtered_df['Start'].dt.date == current_date)]

                    # 休日判定と休暇種類の取得
                    # 全月データから指定日付のみを抽出（filtered_dfではなくst.session_state.dfを使用）
                    date_events = st.session_state.df[
                        (st.session_state.df['date'] == current_date.date())
                        & (st.session_state.df['Owner'].isin(selected_owners))]
                    holiday_events = date_events[
                        date_events['Subject'].str.contains('休日|振休|代休|有休',
                                                            na=False)]
                    is_am_holiday = False
                    is_pm_holiday = False
                    holiday_type = ''
                    has_holiday_keyword = False

                    if not holiday_events.empty:
                        for _, event in holiday_events.iterrows():
                            start_hour = event['Start'].hour
                            end_hour = event['End'].hour
                            subject = event['Subject']

                            # 「休日」キーワードがあれば終日×にする
                            if '休日' in subject:
                                is_am_holiday = True
                                is_pm_holiday = True
                                has_holiday_keyword = True
                                holiday_type = "休日"
                                continue

                            # 休日キーワードがない場合は通常の午前/午後休判定
                            if not has_holiday_keyword:
                                # 午前休の場合（開始時刻が午前で終了時刻が12時以前）
                                if start_hour < 12 and end_hour <= 12:
                                    is_am_holiday = True
                                # 午後休の場合（開始時刻が12時以降）
                                elif start_hour >= 12:
                                    is_pm_holiday = True
                                # 全日休の場合
                                elif start_hour < 12 and end_hour > 12:
                                    is_am_holiday = True
                                    is_pm_holiday = True

                                # AMかPMの判定
                                time_prefix = ""
                                if start_hour >= 12:
                                    time_prefix = "PM"
                                elif end_hour <= 12:
                                    time_prefix = "AM"

                                # 休暇種類の判定
                                if '振休' in subject:
                                    holiday_type = f"{time_prefix}振休" if time_prefix else "振休"
                                elif '代休' in subject:
                                    holiday_type = f"{time_prefix}代休" if time_prefix else "代休"
                                elif '有休' in subject:
                                    holiday_type = f"{time_prefix}有休" if time_prefix else "有休"

                    # 現調・現場の予定を抽出（全月データから）
                    date_events['Subject'] = date_events['Subject'].astype(
                        str).str.replace('\u3000', ' ').str.strip()
                    site_events = date_events[
                        date_events['Subject'].str.contains('現場', na=False)]

                    # AM/PMの空き時間チェック
                    def check_availability(events, start_hour, end_hour,
                                           is_holiday, current_date):
                        today = datetime.now().date()
                        # Timestamp型をdate型に変換
                        if hasattr(current_date, 'date'):
                            current_date = current_date.date()

                        # 祝日や休日の場合は「×」を表示
                        if is_holiday:
                            return "×"

                        # 今日から60日以上後の日付は「-」を表示
                        if (current_date - today).days > 60:
                            return "-"
                        # 今日より前の日付は「-」を表示
                        if current_date < today:
                            return "-"

                        if events.empty:
                            return "○"

                        time_slots = []
                        for _, event in events.iterrows():
                            event_start = max(event['Start'].hour, start_hour)
                            event_end = min(event['End'].hour, end_hour)
                            time_slots.append((event_start, event_end))

                        # 最大の空き時間を計算
                        max_free_time = 0
                        current_time = start_hour
                        time_slots.sort()

                        for slot_start, slot_end in time_slots:
                            free_time = slot_start - current_time
                            max_free_time = max(max_free_time, free_time)
                            current_time = slot_end

                        free_time = end_hour - current_time
                        max_free_time = max(max_free_time, free_time)

                        if max_free_time >= 3:
                            return "○"
                        elif max_free_time >= 2:
                            return "△"
                        else:
                            return "×"

                    am_mark = "×" if is_am_holiday else check_availability(
                        site_events, 9, 12, is_am_holiday, current_date)
                    pm_mark = "×" if is_pm_holiday else check_availability(
                        site_events, 13, 17, is_pm_holiday, current_date)

                    html_calendar_list += '<td><div class="calendar-cell">'

                    # 祝日と休暇の表示を処理
                    date_class = ""
                    if current_date.weekday() == 6 or is_holiday:  # 日曜日または祝日
                        date_class = ' style="color: #FF0000;"'

                    if holiday_type and holiday_name:
                        # 祝日と休暇の両方がある場合
                        holiday_span = f'<span class="holiday-text">{holiday_type}, {holiday_name}</span>'
                        html_calendar_list += f'<div class="date-number"><span{date_class}>{day}</span>{holiday_span}</div>'
                    elif holiday_type:
                        # 休暇のみの場合
                        holiday_span = f'<span class="holiday-text">{holiday_type}</span>'
                        html_calendar_list += f'<div class="date-number"><span{date_class}>{day}</span>{holiday_span}</div>'
                    elif holiday_name:
                        # 祝日のみの場合
                        holiday_span = f'<span class="holiday-text">{holiday_name}</span>'
                        html_calendar_list += f'<div class="date-number"><span{date_class}>{day}</span>{holiday_span}</div>'
                    else:
                        # 何もない場合
                        html_calendar_list += f'<div class="date-number"><span{date_class}>{day}</span></div>'

                    html_calendar_list += '<div class="am-pm-container">'

                    # AM表示部分
                    am_class = " am-holiday" if is_am_holiday else ""
                    html_calendar_list += f'<div class="am-container{am_class}"><span class="availability-mark">{am_mark}</span></div>'

                    # PM表示部分
                    pm_class = " pm-holiday" if is_pm_holiday else ""
                    html_calendar_list += f'<div class="pm-container{pm_class}"><span class="availability-mark">{pm_mark}</span></div>'
                    html_calendar_list += '</div></div></td>'
            html_calendar_list += "</tr>"
        html_calendar_list += "</table></div>"

    html_calendar_list += "</div>"

    # 一覧モードのHTMLを表示
    st.components.v1.html(html_calendar_list, height=1200, scrolling=True)

    # 日付詳細の表示（クリックイベントの処理）
    if st.session_state.selected_date_details:
        detail_date = datetime.strptime(st.session_state.selected_date_details,
                                        '%Y-%m-%d').date()
        detail_events = filtered_df[filtered_df['date'] == detail_date]

        st.subheader(f"{detail_date.strftime('%Y年%m月%d日')}のスケジュール")
        for _, event in detail_events.iterrows():
            time_str = f"{event['Start'].strftime('%H:%M')} - {event['End'].strftime('%H:%M')}"
            st.write(f"- {time_str} {event['Subject']}")

else:
    st.info("CSVファイルをアップロードしてください")

