#python -m streamlit run interviewer_date_1.py

import streamlit as st
import pandas as pd
import datetime
from streamlit_calendar import calendar
import sqlite3
import os

DEBUGMODE = False

# --- データベース接続設定 ---
def get_db_connection():
    # プログラムと同じ場所にある sample.db に接続する
    conn = sqlite3.connect("sample.db")
    # カラム名でアクセスできるようにする
    conn.row_factory = sqlite3.Row
    return conn

# --- 初期テーブル作成（初回のみ・データは消えない安全な設定） ---
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            Interviewer_name TEXT,
            email TEXT,
            job_type TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            booking INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- DBからデータを読み込んで st.session_state.date にセットする関数（安全対策版） ---
def load_data_to_session():
    st.session_state.date = {}
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM reservations").fetchall()
    
    for row in rows:
        # データのキー（列名）が存在するか安全にチェック
        keys = row.keys()
        d = row["date"] if "date" in keys else None
        if not d:
            continue
            
        start = row["start_time"] if "start_time" in keys and row["start_time"] else None
        end = row["end_time"] if "end_time" in keys and row["end_time"] else "00:00"
        booking = row["booking"] if "booking" in keys and row["booking"] is not None else 0
        interviewer_name = row["Interviewer_name"] if "Interviewer_name" in keys and row["Interviewer_name"] else None
        
        # 古いデータなどで start_time がないものはスキップ
        if not start:
            continue
            
        if d not in st.session_state.date:
            st.session_state.date[d] = []
        st.session_state.date[d].append({
            "start": start, 
            "end": end, 
            "booking": booking,
            "interviewer_name": interviewer_name
        })
    conn.close()

# --- 初回起動時のデータ読み込み ---
if "date" not in st.session_state:
    load_data_to_session()

# --- 開始時間が昇順になるようにソート ---
def DateSort(Da):#"yyyy-mm-dd"
    st.session_state.date[Da].sort(key=lambda x: datetime.datetime.strptime(x['start'], "%H:%M"))
    print(st.session_state.date[Da])


# --- 開始時間をもとに終了時間(+30分)を求める ---
def Calc_FinishTime(start_time):
    hh,mm = None,None
    hh,mm = map(int,start_time.split(":"))
    mm = mm+30
    if mm >= 60:
        mm = mm-60
        hh = hh + 1
        if hh == 24:
            hh = 0
    return f"{hh:02}:{mm:02}"

# --- タイトル ---
st.header("面接官日程設定")
st.divider()

# --- データベースに基づきカレンダーに表示するイベント（予定）のリストを設定 ---
def CalendarEvents_set():
    calendar_events = []
    for key_date,row_date in st.session_state.date.items():#日付の数だけ繰り返す
        IsVacantExist = False
        for row_time in st.session_state.date[str(key_date)]:#上記日付内の時間枠数だけ繰り返す
            if IsVacantExist == True:
                break
            if row_time["booking"] == 0:
                IsVacantExist = True
        if IsVacantExist == True:
            title = "空席あり"
            color = "#2130DA52"
        else:
            title = "満席"
            color = "#EC1118"
        calendar_events.append({"title":title,
                                "start":key_date,
                                "end":key_date,
                                "backgroundColor":color})
    return calendar_events

# --- 【データベースの中身確認用】 ---
if DEBUGMODE:
    with st.expander("🔍 現在のデータベースの中身（確認用）"):
        conn = get_db_connection()
        df_all = pd.read_sql_query("SELECT * FROM reservations", conn)
        st.dataframe(df_all)
        conn.close()
        de = st.text_input("削除するid")
        if st.button("上記行を削除"):
            # --- DBから削除 ---
            conn = get_db_connection()
            conn.execute("DELETE FROM reservations WHERE id=?",
                        (de,)
                        )
            conn.commit()
            conn.close()
            load_data_to_session()
            st.rerun()


# --- カレンダーの描画 ---
custom_calendar = calendar(
    events=CalendarEvents_set(),
    options={
        "editable": True,
        "selectable": True,
        "initialView": "dayGridMonth", # 初期表示（月間）
        },
    key="calendar"
)


# --- 選択中の日付の詳細な時間枠の表示および時間枠追加 ---

flame = {"時間":[],"予約状況":[],"担当面接官":[]}#表の定義
#選択日付を定義(初期値は"0000-00-00")
if "selected_date" not in st.session_state:
    st.session_state.selected_date = "0000-00-00"
if custom_calendar.get("dateClick"):#いずれかの日付が選択されていたら
    #選択中の日付を識別
    st.session_state.selected_date = custom_calendar["dateClick"]["date"][0:10]
    #日本時間に調整するため1日繰り上げる
    dt = datetime.datetime.strptime(st.session_state.selected_date, "%Y-%m-%d")
    next_dt = dt + datetime.timedelta(days=1)
    st.session_state.selected_date = next_dt.strftime("%Y-%m-%d")

#選択日付を配列に格納する変数の定義（テキストとして表示するのに使う）
if "sd" not in st.session_state:
    st.session_state.sd = None
if custom_calendar.get("dateClick"):#いずれかの日付が選択されていたら
    st.session_state.sd = st.session_state.selected_date.split("-")

col1, col2 = st.columns(2)#左右分割

# --- 面接枠の表 ---
with col1:#左側
    with st.container(border=True):#枠の描画
        if st.session_state.selected_date != "0000-00-00":#選択された日付が初期値でなければ＝何かしら日付が選択されていたら
            #1行ごとの時間及び予約状況を表示する
            st.subheader(f"{st.session_state.sd[0]}年{st.session_state.sd[1]}月{st.session_state.sd[2]}日の面接枠")
            if st.session_state.selected_date in st.session_state.date:#選択された日付がdateリストに存在したら
                DateSort(st.session_state.selected_date)
                for row_time in st.session_state.date[str(st.session_state.selected_date)]:#選択した日付のdateリストの要素数(面接枠の数)だけ繰り返し総当たりする
                    #時間枠列
                    flame["時間"].append(row_time["start"]+"~"+row_time["end"])
                    #予約状況列
                    if row_time["booking"] == 0:
                        flame["予約状況"].append("予約可")
                    else:
                        flame["予約状況"].append("学生予約済")
                    #担当面接官列
                    if row_time["interviewer_name"] == "" or row_time["interviewer_name"] == None:
                        flame["担当面接官"].append("ー")
                    else:
                        flame["担当面接官"].append(row_time["interviewer_name"])
            else:
                flame = {"時間":["面接枠なし"],"予約状況":["ー"],"担当面接官":["ー"]}
            #表の描画
            dt = pd.DataFrame(flame)
            st.dataframe(dt)


# --- サイドバーで面接官名を指定 ---
st.sidebar.header("ログイン・面接官設定")
imput_interviewer_name = st.sidebar.text_input("面接官のお名前を入力してください", value="面接官A")

        
#枠追加のデータベース処理
def InterviewerDateAdd():
    # --- DBへ追加 ---
    conn = get_db_connection()
    conn.execute("INSERT INTO reservations (date, start_time, end_time, booking, Interviewer_name) VALUES (?, ?, ?, 0, ?)",
                    (st.session_state.selected_date, TimesSlect, Calc_FinishTime(TimesSlect),imput_interviewer_name))
    conn.commit()
    conn.close()
    load_data_to_session()
    DateSort(st.session_state.selected_date)
    st.rerun()
# --- 日程/面接枠の追加 ---
with col2:#左側
    with st.container(border=True):#枠の描画
        if st.session_state.selected_date != "0000-00-00":#選択された日付が初期値でなければ＝何かしら日付が選択されていたら
            st.subheader("面接枠の追加")
            tf = []#追加する面接枠の選択肢を一時的に格納する変数
            dt = []#削除する面接枠の選択肢を一時的に格納する変数
            #追加枠の選択肢の定義(30分刻み)
            for hh in range(24):
                for mm in range(2):
                    tf.append(f"{hh:02}:{(mm*30):02}")
            
            #面接枠追加の項目
            TimesSlect = st.selectbox('時間枠を選択してください',tf)
            st.success(f"選択された日時: {st.session_state.sd[0]}年{st.session_state.sd[1]}月{st.session_state.sd[2]}日 {TimesSlect}~{Calc_FinishTime(TimesSlect)}")
            #日程追加ボタンが押された場合の処理
            if st.button("上記内容で面接枠を追加する"):
                Is_InterviewerEmpty = not imput_interviewer_name
                if st.session_state.selected_date in st.session_state.date:#もし選択日に既存の面接枠があったら
                    #エラー処理
                    for i in range(len(st.session_state.date[st.session_state.selected_date])):#日付内の既存枠数だけ繰り返す(追加枠が既存枠に既にないか探すために総当たりする)
                        Is_ExistTime = st.session_state.date[st.session_state.selected_date][i]["start"] == TimesSlect
                        Is_ExistInterviewer = st.session_state.date[st.session_state.selected_date][i]["interviewer_name"] == imput_interviewer_name
                        if Is_InterviewerEmpty:
                            st.error(":red[左記サイドバーに担当面接官の名前を記入してください]")
                            break
                        if Is_ExistTime and Is_ExistInterviewer:
                            st.error(":red[この面接枠は既に登録されています]")
                            break

                    #選択枠の追加(既存の面接枠がある日付に面接枠を追加)
                    else:
                        InterviewerDateAdd()
                #選択枠の追加(既存の面接枠がない日付に新規追加)
                else:
                    if Is_InterviewerEmpty:
                        st.error(":red[左記サイドバーに担当面接官の名前を記入してください]")
                    else:
                        InterviewerDateAdd()
            
            #面接枠削除の項目(選択中の日付に面接枠が設定されている場合のみ表示)
            if st.session_state.selected_date in st.session_state.date:
                st.divider()
                st.subheader("面接枠の削除")
                #削除枠の選択肢の定義(既存の面接枠)
                for time_row in st.session_state.date[st.session_state.selected_date]:
                    if not time_row["start"] in dt:
                        dt.append(time_row["start"])
                DeleteSlect = st.selectbox('時間枠を選択してください',dt)
                if DeleteSlect != None:
                    st.success(f"選択された日時: {st.session_state.sd[0]}年{st.session_state.sd[1]}月{st.session_state.sd[2]}日 {DeleteSlect}~{Calc_FinishTime(DeleteSlect)}")
                #面接枠削除ボタンを押した際の処理
                if st.button("上記内容で面接枠を削除する"):
                    for i in range(len(st.session_state.date[st.session_state.selected_date])):#削除枠の位置を探すために総当たりする                            
                        Is_ExistTime = st.session_state.date[st.session_state.selected_date][i]["start"] == DeleteSlect
                        Is_Booking = st.session_state.date[st.session_state.selected_date][i]["booking"] == 1
                        Is_ExistInterviewer = st.session_state.date[st.session_state.selected_date][i]["interviewer_name"] == imput_interviewer_name
                        Is_NoneInterviewer = st.session_state.date[st.session_state.selected_date][i]["interviewer_name"] == "" or st.session_state.date[st.session_state.selected_date][i]["interviewer_name"] == None
                        
                        if Is_ExistTime and Is_ExistInterviewer:#時間と担当面接官名が一致すれば
                            #予約済みの枠を削除しようとした場合のエラー処理
                            if Is_Booking:
                                st.error(":red[この面接枠は予約されているため削除できません]")
                                break
                            #選択した枠を削除する
                            else:
                                # --- DBから削除 ---
                                conn = get_db_connection()
                                conn.execute("DELETE FROM reservations WHERE date=? AND start_time=? AND Interviewer_name=?",
                                                (st.session_state.selected_date, DeleteSlect,imput_interviewer_name))
                                conn.commit()
                                conn.close()
                                load_data_to_session()
                                st.rerun()
                                break
                        #時間が一致してかつ担当面接官がいない場合削除する
                        if Is_ExistTime and Is_NoneInterviewer:
                            conn = get_db_connection()
                            conn.execute("DELETE FROM reservations WHERE date=? AND start_time=?",
                                            (st.session_state.selected_date, DeleteSlect))
                            conn.commit()
                            conn.close()
                            load_data_to_session()
                            st.rerun()
                            break
                    #見つからなかった場合
                    else:
                        st.error(":red[指定された日時および該当面接官名を満たす項目が見つかりませんでした。入力内容を確認してください]")