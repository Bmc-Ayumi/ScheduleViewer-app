import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import jpholiday

def get_japanese_holidays(year, month):
    """指定された年月の日本の祝日を取得する"""
    holidays = {}
    for day in range(1, 32):
        try:
            date = datetime(year, month, day).date()
            holiday_name = jpholiday.is_holiday_name(date)
            if holiday_name:
                holidays[day] = holiday_name
        except ValueError:
            # 無効な日付（例：2月30日）は無視
            pass
    return holidays

def load_and_process_csv(file):
    """CSVファイルを読み込み、データを処理する"""
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')

        # Convert Start and End to datetime
        df['Start'] = pd.to_datetime(df['Start'])
        df['End'] = pd.to_datetime(df['End'])

        # Extract date and time components
        df['date'] = df['Start'].dt.date
        df['start_time'] = df['Start'].dt.time
        df['end_time'] = df['End'].dt.time

        # Sort by date and start time
        df = df.sort_values(['date', 'start_time'])

        return df
    except Exception as e:
        raise Exception(f"CSVファイルの処理中にエラーが発生しました: {str(e)}")

def get_date_range(selected_date, view_mode):
    """選択された日付と表示モードに基づいて日付範囲を取得する"""
    if isinstance(selected_date, datetime):
        selected_date = selected_date.date()

    if view_mode == "日次":
        start_date = selected_date
        end_date = selected_date
    elif view_mode == "週次":
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
    else:  # 月次
        start_date = selected_date.replace(day=1)
        if selected_date.month == 12:
            end_date = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)

    return start_date, end_date

def filter_data_by_date(df, start_date, end_date):
    """指定された日付範囲でデータをフィルタリングする"""
    return df[
        (df['date'] >= start_date) &
        (df['date'] <= end_date)
    ]