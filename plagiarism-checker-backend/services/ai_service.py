import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def evaluate_plagiarism_with_gemini(student_text: str, source_text: str) -> dict:
    """Gọi Gemini để chấm điểm đạo văn"""
    if not client: raise Exception("Server chưa được cấu hình API Key của Google.")
    
    prompt = f"""
    Bạn là một chuyên gia kiểm định đạo văn học thuật nghiêm khắc.
    ĐOẠN VĂN CỦA SINH VIÊN: "{student_text}"
    NGUỒN DỮ LIỆU GỐC: "{source_text}"
    
    Quy tắc phân loại:
    - EXACT_MATCH: Sao chép y nguyên hoặc chỉ thay đổi rất ít từ ngữ (giống >= 85%).
    - PARAPHRASED: Xào nấu từ ngữ (đạo ý), nhưng nội dung cốt lõi vẫn lấy từ gốc (giống từ 50% - 84%).
    - SAFE: Hai đoạn văn không liên quan (giống < 50%).
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite', contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1, response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "similarity_score": {"type": "NUMBER"},
                        "match_type": {"type": "STRING", "enum": ["EXACT_MATCH", "PARAPHRASED", "SAFE"]}
                    },
                    "required": ["similarity_score", "match_type"]
                },
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Lỗi Gemini: {str(e)}")
        raise e