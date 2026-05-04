import streamlit as st
from datetime import datetime
from google import genai
import pandas as pd

# --- 1. APIクライアントの設定 ---
# 404エラー（NOT_FOUND）を回避するため、最新モデルに対応した v1beta を使用します
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"],
    http_options={'api_version': 'v1beta'}
)

# --- 2. キャッシュ機能（API節約） ---
@st.cache_data(ttl=3600)
def get_fortune_result(issue, situation):
    # プロンプトの定義
    prompt = f"""
    あなたは論理的かつ直感的な「行動決定型占い師」です。
    ユーザーの現状を分析し、以下の3点のみを出力してください。

    【ユーザーの悩み】: {issue}
    【現在の状況】: {situation}

    出力形式厳守:
    ### 鑑定結果
    **【今の状態】**
    (ユーザーが言語化できていないモヤモヤを鋭く言語化)
    **【1つの警告】**
    (このまま動かなかった場合に起こる具体的リスクを1つ提示)
    **【1つの行動】**
    (今すぐできる極めて小さなアクションを提示)

    最後に必ず以下の定型文を添えてください。
    「この一歩が、あなたの運命を書き換える起点となります。」
    """
    
    # 404エラー対策のためモデル名の指定をシンプルに記述します
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    return response.text

# --- 3. ページ設定とUI ---
st.set_page_config(page_title="行動決定型占い", layout="centered")
st.title("🔮 行動決定型占い")
st.caption("迷いを「行動」に変える専門家が、あなたの次の一歩を導き出します。")

# セッション状態の初期化
if "history" not in st.session_state:
    st.session_state.history = []

# --- ユーザー認証風UI ---
if "user_id" not in st.session_state:
    user_id = st.text_input("ニックネーム（履歴保存用）", placeholder="例: user_01")
    if st.button("スタート"):
        if user_id:
            st.session_state.user_id = user_id
            st.rerun()
    st.stop()

st.sidebar.success(f"鑑定中: {st.session_state.user_id}")

# --- 入力エリア ---
st.subheader("あなたの状況を教えてください")
issue = st.text_area("1. 今、決断できずに止まっていることは？", placeholder="例: 転職するか今の会社に残るか迷っている")
situation = st.text_area("2. 現在の状況（短く）", placeholder="例: 3年以上同じ部署にいて成長を感じないが、給与は安定している")

# --- 占い実行 ---
if st.button("占う", type="primary"):
    if not issue or not situation:
        st.error("入力を完了させてから占ってください。")
    else:
        with st.spinner("運命の糸を読み解いています..."):
            try:
                # キャッシュ機能を通じた鑑定実行
                result = get_fortune_result(issue, situation)

                # 結果の表示
                st.markdown("---")
                st.markdown(result)
                
                # 履歴の保存
                log_data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": st.session_state.user_id,
                    "issue": issue,
                    "situation": situation,
                    "result": result
                }
                st.session_state.history.append(log_data)
                
                st.success("鑑定が完了しました。")
                st.markdown("---")
                st.info("※さらに深い分析はnote完全版で → [あなたのnoteリンク]")

            except Exception as e:
                st.error("現在、星の配置が乱れています（アクセス集中または設定エラー）。")
                # 管理者向けのデバッグ情報
                with st.expander("詳細なエラー原因を表示"):
                    st.code(e)
                st.warning("1分ほど待ってから再度お試しください。")

# --- 履歴の表示とダウンロード ---
if st.session_state.history:
    with st.expander("過去の鑑定履歴"):
        for entry in reversed(st.session_state.history):
            st.write(f"**{entry['date']}**")
            st.markdown(entry['result'])
            st.markdown("---")
    
    # 分析用CSVダウンロード
    df = pd.DataFrame(st.session_state.history)
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 鑑定履歴を保存 (CSV)",
        data=csv,
        file_name=f"fortune_log_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )
