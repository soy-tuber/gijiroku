import streamlit as st
import time
from backend import MeetingAssistant

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="AI議事録",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. デザイン・CSS設定 ---
st.markdown("""
<style>
    /* 全体の余白調整 */
    .block-container {
        padding-top: 2rem;
    }
    /* サマリボックスのデザイン（画像の赤枠・グレー背景風） */
    .summary-box {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        border-top: 5px solid #ff4b4b; /* 上部にアクセントカラー */
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .summary-box h3 {
        color: #333;
        margin-bottom: 20px;
        font-size: 1.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .summary-box h4 {
        color: #555;
        margin-top: 15px;
        margin-bottom: 10px;
        font-size: 1.1rem;
        border-bottom: 1px dashed #ccc;
        padding-bottom: 5px;
    }
    .summary-box ul {
        margin-bottom: 15px;
        color: #444;
    }
    .summary-box li {
        margin-bottom: 5px;
        line-height: 1.6;
    }
    /* ステップアイコン */
    .step-icon {
        font-size: 2.5rem;
        margin-bottom: 5px;
        display: block;
    }
    /* ヘッダーボタンの右寄せ */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. バックエンド初期化 ---
if "assistant" not in st.session_state:
    try:
        st.session_state.assistant = MeetingAssistant()
    except Exception as e:
        st.error(f"起動エラー: {e}")

# --- 4. ヘッダーエリア ---
col_h1, col_h2 = st.columns([6, 4])

with col_h1:
    st.title("AI議事録")

with col_h2:
    # 右上のメニューボタン（ダミー）
    c1, c2 = st.columns(2)
    with c1:
        st.button("✨ リアルタイム録音・録画", key="btn_realtime", help="現在は音声のみ対応")
    with c2:
        st.button("📂 録音・録画ファイル作成", key="btn_file", type="primary")

st.markdown("---")

# --- 5. フィルターバー（UIのみ再現） ---
# 実際の機能は持たせず、雰囲気のために配置
cols = st.columns([2, 2, 2, 1.5, 1.5, 3])
with cols[0]: st.date_input("日付", label_visibility="collapsed")
with cols[1]: st.selectbox("会議名", ["会議名から絞る"], label_visibility="collapsed")
with cols[2]: st.text_input("検索", placeholder="AND検索", label_visibility="collapsed")
with cols[3]: st.button("👥 参加者", use_container_width=True)
with cols[4]: st.button("🖊️ 作成者", use_container_width=True)
with cols[5]: st.text_input("内容検索", placeholder="内容で検索", label_visibility="collapsed")

st.write("") 

# --- 6. メイン機能エリア ---

# A. 入力エリア (録音 or アップロード)
st.subheader("① 音声入力")
tab_mic, tab_file = st.tabs(["🎤 マイクで録音", "📂 ファイルをアップロード"])

audio_data = None

with tab_mic:
    st.write("ボタンを押して発言してください。録音停止ボタンで確定します。")
    audio_val = st.audio_input("録音開始") # Streamlit 1.40+ の新機能
    if audio_val:
        audio_data = audio_val.read()

with tab_file:
    uploaded_file = st.file_uploader("音声/動画ファイル (wav, mp3, m4a, mp4)", type=["wav", "mp3", "m4a", "mp4"])
    if uploaded_file:
        audio_data = uploaded_file.read()

# B. 生成実行ボタン
if audio_data is not None:
    st.info("音声データがセットされました。")
    
    # 既に結果があり、かつ新しいオーディオがセットされた場合はリセットを促すなどの制御も可能ですが、
    # ここではシンプルに上書き実行できるようにします。
    if st.button("② AI議事録を生成する (Gemini 2.5)", type="primary", use_container_width=True):
        with st.spinner("AIが音声を分析中... (話者分離・要約・ToDo抽出)"):
            try:
                # バックエンド呼び出し
                result = st.session_state.assistant.process_audio(audio_data)
                st.session_state.result = result
                st.toast("議事録の生成が完了しました！", icon="🎉")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# C. 結果表示エリア
if "result" in st.session_state:
    res = st.session_state.result
    
    st.divider()
    st.subheader("③ 議事録・全体サマリ")

    # リスト表示用のヘルパー関数（空リスト対策）
    def format_list(items):
        if not items:
            return "<li><span style='color: #999;'>（特になし）</span></li>"
        return ''.join([f'<li>{item}</li>' for item in items])

    # サマリボックス（HTML表示）
    st.markdown(f"""
    <div class="summary-box">
        <h3>📄 {res.title}</h3>
        <h4>✅ 主な協議事項・決定事項</h4>
        <ul>
            {format_list(res.decisions)}
        </ul>
        <h4>🚀 ToDo・残課題</h4>
        <ul>
            {format_list(res.todos)}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # テキストデータの作成（ダウンロード用）
    dl_str = f"会議タイトル: {res.title}\n"
    dl_str += f"作成日: {time.strftime('%Y-%m-%d')}\n\n"
    dl_str += "【決定事項】\n" + ("\n".join([f"- {i}" for i in res.decisions]) if res.decisions else "なし") + "\n\n"
    dl_str += "【ToDo】\n" + ("\n".join([f"- {i}" for i in res.todos]) if res.todos else "なし") + "\n\n"
    dl_str += "【文字起こし】\n"
    for seg in res.transcript:
        dl_str += f"[{seg.speaker}] {seg.text}\n"

    # ダウンロードボタン
    st.download_button(
        label="📥 テキストファイルで保存",
        data=dl_str,
        file_name=f"gijiroku_{int(time.time())}.txt",
        mime="text/plain"
    )

    # 詳細な文字起こし表示
    with st.expander("💬 詳細な文字起こし (話者分離済み)", expanded=True):
        for segment in res.transcript:
            with st.chat_message(segment.speaker, avatar="👤"):
                st.markdown(f"**{segment.speaker}**")
                st.write(segment.text)

# --- 7. 空の状態のガイド（結果がない時だけ表示） ---
if "result" not in st.session_state and audio_data is None:
    st.write("")
    st.write("")
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>音声または動画ファイルをアップロードするか、マイクで録音して<br>
            <b>「AI議事録を生成する」</b>ボタンを押してください。</p>
        </div>
        """, unsafe_allow_html=True)