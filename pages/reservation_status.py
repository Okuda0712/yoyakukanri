from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib
import sqlite3

import streamlit as st

# 1. 画面の初期設定
st.set_page_config(
    page_title="予約状況一覧 | MeetSync 人事管理",
    page_icon="🗓",
    layout="wide",
)

# ------------------------------------------------------------
# 見た目をリッチにするカスタムCSS
# ------------------------------------------------------------
st.markdown(
    """
<style>
    .main { background-color: #F8F9FA; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# データベース接続関数（student_name が入っているデータだけ取得する）
# ------------------------------------------------------------
def get_reservations():
    try:
        conn = sqlite3.connect("sample.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, student_name, Interviewer_name, email, job_type, date, start_time 
            FROM reservations 
            WHERE student_name IS NOT NULL AND student_name != ''
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


# 実際のメール送信関数
def send_reminder_email(to_email, subject, body):
    FROM_EMAIL = "your_email@gmail.com"
    APP_PASSWORD = "xxxx xxxx xxxx xxxx"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(FROM_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False


# ------------------------------------------------------------
# メイン処理
# ------------------------------------------------------------
students = []
for row in get_reservations():
    students.append({
        "id": row[0],
        "name": row[1],
        "interviewer": row[2] or "未割り当て",
        "email": row[3],
        "role": row[4] or "未選択",
        "datetime": f"{row[5]} {row[6]}",
    })

st.markdown("## 📊 採用面接 予約状況ダッシュボード")

# サマリー
col1, col2, col3 = st.columns(3)
col1.metric("総予約数", f"{len(students)} 名")
col2.metric("予約確定済み", f"{len(students)} 名")
col3.metric("未予約", "0 名")

st.write("")

# 検索とソートの入力エリア
c_search, c_sort = st.columns([2, 1])
with c_search:
    search_text = st.text_input("🔍 学生名で検索")
with c_sort:
    sort_key = st.selectbox(
        "⇅ ソート（並び替え）",
        ["指定なし", "面接官名", "志望職種", "面接日時"],
    )

# 検索フィルタリング
filtered = [s for s in students if not search_text or search_text in s["name"]]

# ソート処理
if sort_key == "面接官名":
    filtered = sorted(filtered, key=lambda x: x["interviewer"])
elif sort_key == "志望職種":
    filtered = sorted(filtered, key=lambda x: x["role"])
elif sort_key == "面接日時":
    filtered = sorted(filtered, key=lambda x: x["datetime"])

with st.container(border=True):
    col_widths = [1.5, 1.5, 2.0, 1.5, 1.5, 1.2]

    header = st.columns(col_widths)
    for c, label in zip(
        header,
        [
            "学生名",
            "面接官名",
            "メールアドレス",
            "志望職種",
            "面接日時",
            "アクション",
        ],
    ):
        c.markdown(f"**{label}**")

    st.divider()

    if not filtered:
        st.info("現在、条件に一致する予約はありません。")
    else:
        for s in filtered:
            row = st.columns(col_widths)
            row[0].write(s["name"])
            row[1].write(s["interviewer"])
            row[2].write(s["email"] or "未登録")
            row[3].write(s["role"])
            row[4].write(s["datetime"])
            if row[5].button(
                "📧 催促メール", key=f"btn_{s['id']}", type="primary"
            ):
                st.session_state["target_student"] = s
                st.rerun()

# メール送信プレビュー
if "target_student" in st.session_state:
    s = st.session_state["target_student"]
    st.divider()
    with st.container(border=True):
        st.subheader(f"📨 {s['name']} 様へのリマインドメール")
        sub = st.text_input("件名", value="【MeetSync】面接に関するリマインド")
        body = st.text_area(
            "本文",
            value=(
                f"{s['name']} 様\n\nお世話になっております。\n{s['datetime']}からの面接にてお待ちしております。"
            ),
            height=150,
        )

        c1, c2 = st.columns([1, 4])
        if c1.button("送信実行"):
            if send_reminder_email(s["email"], sub, body):
                st.success("送信完了！")
                del st.session_state["target_student"]
                st.rerun()
            else:
                st.error("送信失敗：設定を確認してください")
        if c2.button("キャンセル"):
            del st.session_state["target_student"]
            st.rerun()