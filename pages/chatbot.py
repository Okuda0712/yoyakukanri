import streamlit as st

st.title("採用サポートBot（チャットボット）")

# チャット履歴を保持するSession Stateの初期化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "こんにちは！面接日程についてのご質問にお答えします。気になる項目を選んでください。"}
    ]

# 過去のメッセージを画面に表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ユーザーがクリックできる選択肢（ボタン）の定義
st.write("---")
st.write("💬 **よくある質問（ボタンを選択）**")

col1, col2, col3 = st.columns(3)

# ボタンが押されたときの処理
user_input = None
if col1.button("日程を変更したい"):
    user_input = "日程を変更したい"
if col2.button("面接方法を知りたい"):
    user_input = "面接方法を知りたい"
if col3.button("担当者に相談したい"):
    user_input = "担当者に相談したい"

# 自由入力用のチャット欄
chat_input = st.chat_input("メッセージを入力…")

# ユーザーの入力を決定（ボタンかテキスト入力のどちらか）
if chat_input:
    user_input = chat_input

# ユーザーからの入力があった場合の処理
if user_input:
    # 1. ユーザーのメッセージを履歴に追加して表示
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # 2. ボット側の返信ロジック（質問に応じた回答）
    if "日程を変更したい" in user_input:
        bot_response = "予約画面の「日程を変更する」ボタンから、いつでも空いている日時に変更できます。変更後は自動でメールが再送信されます。"
    elif "面接方法を知りたい" in user_input:
        bot_response = "一次面接はオンライン（Zoom）で実施します。予約確定後に接続用のURLがメールで届きます。"
    elif "担当者に相談したい" in user_input:
        bot_response = "採用担当窓口（support@example.com）宛てに直接メールかお電話にてお問い合わせください。"
    else:
        bot_response = f"「{user_input}」ですね。詳細について確認いたしますので少々お待ちください。"

    # 3. ボットの返信を履歴に追加して表示
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.write(bot_response)
    
    # 画面を再描画して最新の履歴を反映
    st.rerun()