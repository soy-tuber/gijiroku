import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# --- 出力データの構造定義 ---
class TranscriptSegment(BaseModel):
    speaker: str = Field(..., description="発話者の名前またはID (例: Speaker A)")
    text: str = Field(..., description="発話内容")

class MeetingSummary(BaseModel):
    title: str = Field(..., description="会議のタイトル案")
    decisions: List[str] = Field(..., description="決定事項のリスト")
    todos: List[str] = Field(..., description="ToDo・残課題のリスト (担当者含む)")
    transcript: List[TranscriptSegment] = Field(..., description="話者分離された文字起こし")

# --- バックエンドクラス ---
class MeetingAssistant:
    def __init__(self):
        self.api_key = None
        
        # Streamlit Cloud の Secrets からキーを探す
        # 設定されている可能性のあるキー名を順にチェック
        possible_keys = ["GEMINI_API_KEY", "GENAI_API_KEY", "GOOGLE_API_KEY"]
        
        for key in possible_keys:
            if key in st.secrets:
                self.api_key = st.secrets[key]
                break
        
        if not self.api_key:
            raise ValueError(
                "APIキーが見つかりません。Streamlit CloudのSecrets設定で "
                "'GEMINI_API_KEY' または 'GENAI_API_KEY' を設定してください。"
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash" 

    def process_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> MeetingSummary:
        prompt = """
        あなたはプロフェッショナルな議事録作成AIです。
        提供された会議の音声データを分析し、以下の情報を生成してください。

        1. **会議タイトル**: 内容に即した簡潔なタイトル。
        2. **決定事項**: 会議で決まったこと。
        3. **ToDo・残課題**: 今後のアクションアイテムと担当者。
        4. **文字起こし**: 話者を識別(Speaker A, B...)し、発言内容を正確に記述してください。
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MeetingSummary,
                    temperature=0.3,
                )
            )

            if response.parsed:
                 return response.parsed
            else:
                 raise RuntimeError("Geminiからのレスポンスのパースに失敗しました。")

        except Exception as e:
            # エラー内容を詳細に表示（デバッグ用）
            raise RuntimeError(f"AI処理中にエラー: {str(e)}")