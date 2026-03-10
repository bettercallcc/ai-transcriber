import streamlit as st
try:
    import whisper
except ImportError:
    st.error("❌ 找不到 `openai-whisper` 模組。請確認您的 GitHub 倉庫中是否有 `requirements.txt` 且內容包含 `openai-whisper`。")
    st.info("💡 提示：如果剛上傳檔案，Streamlit Cloud 可能還在背景安裝套件，請稍等 1-2 分鐘並重新整理。")
    st.stop()
import os
import time
import subprocess

# 頁面配置
st.set_page_config(page_title="AI 音檔轉文字系統", page_icon="🎙️", layout="centered")

# CSS 樣式美化
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #6366f1; color: white; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #6366f1, #a855f7); }
    </style>
    """, unsafe_allow_html=True)

st.title("🎙️ AI 音檔轉文字系統")
st.subheader("高精準繁體中文逐字稿產出")

# 側邊欄說明
with st.sidebar:
    st.info("💡 **提示**：轉錄速度取決於伺服器效能，大型音檔請耐心等候。")
    st.write("---")
    st.write("🌐 **版本資訊**：雲端發布版 v1.3")

# 自動偵測本地 ffmpeg (僅在本地執行時生效)
local_ffmpeg_bin = os.path.join(os.getcwd(), "ffmpeg-8.0.1-essentials_build", "bin")
if os.path.exists(local_ffmpeg_bin):
    if local_ffmpeg_bin not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + local_ffmpeg_bin

# 檔案上傳
uploaded_file = st.file_uploader("請上傳音檔 (MP3, WAV, M4A...)", type=["mp3", "wav", "m4a", "flac", "aac"])

if uploaded_file is not None:
    st.success(f"已選取檔案：{uploaded_file.name}")
    
    if st.button("🚀 開始轉錄"):
        # 建立暫存檔處理
        temp_dir = "temp_uploads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            # --- 步驟 1：載入模型 ---
            status_placeholder.info("🔄 正在準備 AI 模型，請稍候...")
            progress_bar.progress(20)
            model = whisper.load_model("base")
            progress_bar.progress(40)
            
            # --- 步驟 2：執行轉錄 ---
            status_placeholder.info("🎙️ 正在進行轉錄... 這可能需要幾分鐘時間。")
            progress_bar.progress(60)
            
            result = model.transcribe(
                file_path, 
                language="zh", 
                initial_prompt="以下是繁體中文的逐字稿。",
                verbose=False
            )
            
            progress_bar.progress(90)
            text = result["text"]
            
            # --- 步驟 3：產出結果 ---
            status_placeholder.success("🎊 轉錄完成！")
            progress_bar.progress(100)
            
            # 準備 HTML 內容
            file_title = os.path.splitext(uploaded_file.name)[0]
            html_report = f"""
            <!DOCTYPE html>
            <html lang="zh-TW">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Microsoft JhengHei', sans-serif; line-height: 1.8; color: #333; max-width: 900px; margin: 40px auto; padding: 20px; background: #f9f9f9; }}
                    .container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                    h1 {{ color: #4f46e5; border-bottom: 3px solid #6366f1; padding-bottom: 15px; margin-bottom: 30px; }}
                    .info {{ display: flex; gap: 20px; color: #666; font-size: 0.9em; margin-bottom: 30px; background: #f0f4ff; padding: 15px; border-radius: 8px; }}
                    .content {{ white-space: pre-wrap; font-size: 1.1em; letter-spacing: 0.5px; text-align: justify; }}
                    .footer {{ margin-top: 50px; text-align: center; font-size: 0.8em; color: #999; border-top: 1px solid #eee; padding-top: 20px; }}
                </style>
                <title>{file_title} - AI 逐字稿報告</title>
            </head>
            <body>
                <div class="container">
                    <h1>🎙️ 音檔轉文字逐字稿</h1>
                    <div class="info">
                        <span>📄 檔案：{uploaded_file.name}</span>
                        <span>📅 日期：{time.strftime("%Y-%m-%d %H:%M")}</span>
                    </div>
                    <div class="content">{text}</div>
                    <div class="footer">由 AI 音檔轉文字系統 自動生成</div>
                </div>
            </body>
            </html>
            """
            
            # 顯示結果預覽
            st.markdown("### 📝 逐字稿預覽")
            st.text_area("轉錄內容", value=text, height=300)
            
            # 提供下載
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 下載純文字 (.txt)",
                    data=text,
                    file_name=f"{file_title}.txt",
                    mime="text/plain"
                )
            with col2:
                st.download_button(
                    label="✨ 下載精美報表 (.html)",
                    data=html_report,
                    file_name=f"{file_title}.html",
                    mime="text/html"
                )
            
            # 本地同步儲存 (僅限本地執行)
            try:
                output_txt = os.path.join(os.getcwd(), f"{file_title}.txt")
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write(text)
            except: pass

        except Exception as e:
            st.error(f"發生錯誤：{str(e)}")
        finally:
            # 清理暫存檔案 (選填)
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except: pass
else:
    st.write("👆 請選取一個音檔開始吧！")
