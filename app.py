import streamlit as st

# 各ページオブジェクトを定義（title で表示名を自由に変更可能）
page_1 = st.Page("pages/chatbot.py", title="チャットボット", icon="🤖")
page_2 = st.Page("pages/gakusei.py", title="学生一覧", icon="🎓")
page_3 = st.Page("pages/interviewer_date.py", title="面接枠の日程の設定", icon="📅")
page_4 = st.Page("pages/reservation_status.py", title="予約状況", icon="📊")

# ナビゲーションの構築
pg = st.navigation([page_1, page_2, page_3, page_4])
pg.run()