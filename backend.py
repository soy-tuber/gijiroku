import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む（APIキー管理）
load_dotenv()

# --- 出力データの構造定義 (Pydantic) ---
# これにより、Geminiからの出力をJSONとして確実にパースできます
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
        # APIキーは環境変数 GOOGLE_API_KEY から自動取得、またはここで直接指定
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEYが設定されていません。")
        
        self.client = genai.Client(api_key=api_key)
        # ユーザー指定のモデル
        self.model_name = "gemini-2.5-flash" 

    def process_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> MeetingSummary:
        """
        音声データを受け取り、文字起こしと要約を生成して返す
        """
        
        # プロンプトの作成
        prompt = """
        あなたはプロフェッショナルな議事録作成AIです。
        提供された会議の音声データを分析し、以下の情報を生成してください。

        1. **会議タイトル**: 内容に即した簡潔なタイトル。
        2. **決定事項**: 会議で決まったこと。
        3. **ToDo・残課題**: 今後のアクションアイテムと担当者。
        4. **文字起こし**: 話者を識別(Speaker A, B...)し、発言内容を正確に記述してください。
           - 文脈から名前がわかる場合は、'Speaker A'の代わりにその名前を使用してください。
           - 'えー'や'あー'などのフィラーは除去して整えてください。
        """

        try:
            # Gemini 2.5 Flash へのリクエスト
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
                    response_schema=MeetingSummary, # Pydanticモデルをスキーマとして渡す
                    temperature=0.3, # 事実に忠実にするため低めに設定
                )
            )

            # Pydanticモデルとしてパースされた結果を返す
            if response.parsed:
                 return response.parsed
            else:
                 raise RuntimeError("Geminiからのレスポンスのパースに失敗しました。")

        except Exception as e:
            raise RuntimeError(f"AI処理中にエラーが発生しました: {str(e)}")