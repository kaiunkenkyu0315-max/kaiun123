import streamlit as st
from datetime import datetime
from google import genai
import pandas as pd # 履歴管理用

# 1. APIクライアントの設定
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"],
    http_options={'api_version': 'v1'}
)

# --- キャッシュ機能の追加 ---
# 悩み(issue)と状況(situation)が全く同じなら、1時間はAPIを叩かず前回の結果を返します
@st.cache_data(ttl=3600)
def get_fortune_result(issue, situation):
    prompt = f"""
    あなたは凄腕の占い師です。以下の悩みを持つユーザーに対して、
    専門的な知見（占星術や心理学など）を交えつつ、以下の3点を鑑定してください。

    【ユーザーの悩み】: {issue}
    【現在の状況】: {situation}

    出力形式:
    ### 鑑定結果
    **【今の状態】**
    (ここに鑑定結果)
    **【1つの警告】**
    (ここに厳しい警告)
    **【1つの行動】**
    (今日からできる具体的な一歩)
    """
    
    # 生成の実行
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt,
        config={'api_version': 'v1beta'} # エラーが出る場合はここを試
    )
    return response.text

st.set_page_config(page_title="行動決定型占い", layout="centered")
st.title("🔮 迷いを行動に変える 無料占い")

# セッション状態の初期化
if "history" not in st.session_state:
    st.session_state.history = []

# --- ユーザー認証風UI ---
if "user_id" not in st.session_state:
    user_id = st.text_input("ニックネーム（履歴保存用）", placeholder="例: tanaka_01")
    if st.button("スタート"):
        if user_id:
            st.session_state.user_id = user_id
            st.rerun()
    st.stop()

st.sidebar.success(f"鑑定中: {st.session_state.user_id}")

# --- 入力エリア ---
st.subheader("あなたの状況を教えてください")
issue = st.text_area("1. 今、決断できずに止まっていること", height=100)
situation = st.text_area("2. 現在の状況（短く）", height=80)

# --- 占い実行 ---
if st.button("占う", type="primary"):
    if not issue or not situation:
        st.error("悩みを入力してください")
    else:
        with st.spinner("AIが運命を読み解いています..."):
            try:
                # キャッシュ化した関数を呼び出し
                result = get_fortune_result(issue, situation)

                # 結果の表示
                st.markdown(result)
                
                # --- 履歴の保存 ---
                log_data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": st.session_state.user_id,
                    "issue": issue,
                    "situation": situation,
                    "result": result
                }
                st.session_state.history.append(log_data)
                
                st.success("鑑定が完了しました！")
                st.markdown("---")
                st.markdown("※さらに深い分析はnote完全版で → [noteリンク]")

            except Exception as e:
                st.error(f"占い中にエラーが発生しました。")
                st.info(f"詳細な原因: {e}")
                st.warning("1分ほど待ってから再度お試しください。")

# --- 履歴の表示 ---
if st.session_state.history:
    with st.expander("過去の鑑定履歴（あなたのみ表示）"):
        for entry in reversed(st.session_state.history):
            st.write(f"**{entry['date']}**")
            st.write(entry['result'])
            st.markdown("---")
    
    df = pd.DataFrame(st.session_state.history)
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 分析用データをダウンロード",
        data=csv,
        file_name=f"uranai_history_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )
