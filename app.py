import streamlit as st
import time
from backend import MeetingAssistant  # 作成したbackend.pyをインポート

# --- ページ設定 ---
st.set_page_config(page_title="AI議事録", layout="wide")

# --- CSS (前回のスタイルを適用) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .summary-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #d6d6d6;
        margin-bottom: 20px;
    }
    .transcript-box {
        border-left: 3px solid #ff4b4b;
        padding-left: 15px;
        margin-bottom: 10px;
    }
    .speaker-label {
        font-weight: bold;
        font-size: 0.9em;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# --- バックエンドの初期化 ---
if "assistant" not in st.session_state:
    try:
        st.session_state.assistant = MeetingAssistant()
        st.toast("AIエンジンの準備完了 (Gemini 2.5 Flash)", icon="✅")
    except Exception as e:
        st.error(f"初期化エラー: {e}")

# --- UI構築 ---

st.title("AI議事録 - リアルタイム対応版")

# 1. 録音・アップロードエリア (画像の①に対応)
st.subheader("① 録音・録画をアップロード")
tab1, tab2 = st.tabs(["🎤 マイクで録音", "📂 ファイルアップロード"])

audio_data = None

with tab1:
    # Streamlit標準のマイク入力 (ブラウザで録音可能)
    audio_val = st.audio_input("録音を開始")
    if audio_val:
        audio_data = audio_val.read()

with tab2:
    uploaded_file = st.file_uploader("音声/動画ファイルをアップロード", type=["wav", "mp3", "m4a", "mp4"])
    if uploaded_file:
        audio_data = uploaded_file.read()

# 2. 処理実行ボタン
if audio_data is not None:
    st.info("音声データがセットされました。AI処理を開始できます。")
    
    if st.button("② AI議事録を生成 (Gemini 2.5 Flash)", type="primary"):
        with st.spinner("AIが音声を分析中... 話者を分離し、要約を作成しています..."):
            try:
                # バックエンド呼び出し
                result = st.session_state.assistant.process_audio(audio_data)
                st.session_state.result = result # 結果を保存
                st.success("生成完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- 結果表示エリア (画像の②、③に対応) ---
if "result" in st.session_state:
    res = st.session_state.result
    
    st.divider()
    
    # 3. 議事録・全体サマリ (画像の③に対応)
    st.subheader("③ 議事録・全体サマリ")
    
    # 赤枠で囲まれたサマリ風のデザイン
    st.markdown(f"""
    <div class="summary-box">
        <h3>📄 {res.title}</h3>
        <h4>✅ 主な協議事項・決定事項</h4>
        <ul>
            {''.join([f'<li>{item}</li>' for item in res.decisions])}
        </ul>
        <h4>🚀 ToDo・残課題</h4>
        <ul>
            {''.join([f'<li>{item}</li>' for item in res.todos])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # 4. 文字起こし・話者分離 (画像の②に対応)
    with st.expander("詳細な文字起こし (話者分離済み)", expanded=True):
        for segment in res.transcript:
            # チャット風の表示
            with st.chat_message(name=segment.speaker, avatar="👤"):
                st.write(f"**{segment.speaker}**: {segment.text}")
                # 画像②のような矢印の可視化は複雑なため、ここではチャット形式で分かりやすく表現