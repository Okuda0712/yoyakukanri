import datetime
import sqlite3
import streamlit as st


# 1. データベースの初期化
def init_db():
    conn = sqlite3.connect("sample.db")
    cursor = conn.cursor()
    cursor.execute("""
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


# 2. 指定した日付の空き時間と面接官情報（およびレコードID）を取得する関数
def get_available_slots(date_str):
    conn = sqlite3.connect("sample.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT id, start_time, Interviewer_name FROM reservations 
        WHERE date = ? AND (booking = 0 OR student_name IS NULL OR student_name = '')
        ORDER BY start_time ASC, Interviewer_name ASC
    """,
        (date_str,),
    ).fetchall()
    conn.close()

    # 一致する枠をリストで返す
    slots = []
    for row in rows:
        interviewer = row["Interviewer_name"] or "未割り当て"
        slots.append({
            "id": row["id"],
            "time": row["start_time"],
            "interviewer": interviewer,
            "display": f"{row['start_time']} （担当: {interviewer}）",
        })
    return slots


# 3. 予約を保存（IDをピンポイント指定して更新）する関数
def save_booking_by_id(reservation_id, name, email, job):
    conn = sqlite3.connect("sample.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE reservations 
        SET student_name = ?, email = ?, job_type = ?, booking = 1
        WHERE id = ?
    """,
        (name, email, job, reservation_id),
    )
    conn.commit()
    conn.close()


# 画面の初期設定
st.set_page_config(layout="wide", page_title="MeetSync 面接日程調整")

# メインコンテンツ
st.markdown("## 一次面接の日程を選択してください")
st.write(
    "カレンダーから日付を選ぶと、人事側が登録した空き時間が右側に表示されます。"
)

st.progress(66)
c1, c2, c3 = st.columns(3)
with c1:
    st.caption(" 1. ご案内確認")
with c2:
    st.caption(" **2. 日程を選ぶ** (現在地)")
with c3:
    st.caption(" 3. 予約完了")

st.write("")

with st.container(border=True):
    st.markdown("### 🏢 株式会社サンプル商事 ／ 一次面接（オンライン）")
    st.caption(
        "所要時間：約45分 ｜ 面接方法：Zoom（予約確定後に接続先をメールで送付）"
    )

st.write("")

left_col, right_col = st.columns(2)

with left_col:
    with st.container(border=True):
        st.subheader(" 👤 学生情報の入力")
        student_name = st.text_input(
            "お名前を入力してください", placeholder="例：山田 太郎"
        )
        email = st.text_input(
            "メールアドレスを入力してください",
            placeholder="例：example@mail.com",
        )

        job_types = [
            "総合職（営業・企画）",
            "エンジニア職",
            "デザイナー職",
            "事務職",
        ]
        selected_job = st.selectbox(
            "志望職種を選択してください", options=job_types
        )

        st.write("---")
        st.subheader(" 📅 日付と時間の選択")
        today = datetime.date.today()
        selected_date = st.date_input(
            "日付を選択",
            value=today,
            min_value=today,
            max_value=today + datetime.timedelta(days=60),
        )
        date_str = selected_date.strftime("%Y-%m-%d")

        st.write("---")
        st.write(" **空き時間を選択してください**")

        # データベースからこの日の空き時間・面接官枠を取得
        available_slots = get_available_slots(date_str)

        if available_slots:
            # radioで表示するテキストのリストを作成
            options_display = [s["display"] for s in available_slots]
            selected_display = st.radio(
                "時間帯", options=options_display, label_visibility="collapsed"
            )

            # 選択された表示名から対応する枠情報(IDや面接官名)を取得
            selected_slot = next(
                s for s in available_slots if s["display"] == selected_display
            )
        else:
            selected_slot = None
            st.warning(
                "⚠️"
                " この日の空き面接枠はありません。人事側で日程が登録されるのをお待ちいただくか、別の日付を選択してください。"
            )

with right_col:
    with st.container(border=True):
        st.subheader(" ✅ 選択内容の確認")
        st.write("以下の内容で間違いなければ、ボタンを押してください。")
        st.write("")

        if selected_slot:
            display_time = (
                f"{selected_slot['time']} (面接官:"
                f" {selected_slot['interviewer']})"
            )
        else:
            display_time = "選択中の枠なし"

        st.info(
            f"**【予約者名】**\n {student_name if student_name else '未入力'}\n\n"
            f"**【メールアドレス】**\n {email if email else '未入力'}\n\n"
            f"**【志望職種】**\n {selected_job}\n\n"
            f"**【選択中の日程】**\n {date_str} {display_time}"
        )

        st.write("")

        if st.button(
            "この日程で予約する", type="primary", use_container_width=True
        ):
            if not student_name or not email:
                st.warning(
                    "⚠️ お名前とメールアドレスの両方を入力してください！"
                )
            elif not selected_slot:
                st.warning("⚠️ 予約可能な時間枠を選択してください！")
            else:
                # 特定のレコードIDを使って予約（他の同刻枠には影響しない）
                save_booking_by_id(
                    selected_slot["id"], student_name, email, selected_job
                )
                st.success(
                    f"【予約完了】{student_name}さん、{date_str}"
                    f" {selected_slot['time']}（担当:"
                    f" {selected_slot['interviewer']}）で受け付けました！"
                )
                st.balloons()