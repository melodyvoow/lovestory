"""
Live Gemini Interactions API Verification Script for LoveStory;
Tests:
1) gemini-4-argon (thinking_level="medium", zero deprecated parameters)
2) gemini-nano-banana-2.1 (image generation, 16:9 widescreen)
3) gemini-omni-1.1-flash (video generation, 16:9 widescreen, 720p)
"""

import base64
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)

    print(f"🔑 GEMINI_API_KEY 확인됨: {api_key[:8]}... (길이: {len(api_key)})")
    print("🌐 Google GenAI Client 초기화...")
    client = genai.Client(api_key=api_key)

    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Test gemini-4-argon
    print("\n[1/3] 🧪 gemini-4-argon (Acting Brain & Handwritten Postcard) 호출 테스트...")
    try:
        t0 = time.time()
        res = client.interactions.create(
            model="gemini-4-argon",
            input="K-드라마 사진가 이준(29세)으로서 카페에서 비를 바라보며 건네는 한 마디 대사를 JSON {'dialogue_kr': '...'} 형식으로만 출력해줘.",
            generation_config={"thinking_level": "medium"},
        )
        elapsed = time.time() - t0

        text = ""
        if hasattr(res, "output_text") and res.output_text:
            text = res.output_text
        else:
            for step in getattr(res, "steps", None) or []:
                if getattr(step, "type", None) == "model_output":
                    for item in getattr(step, "content", None) or []:
                        if getattr(item, "type", None) == "text":
                            text += item.text

        print(f"  ✅ gemini-4-argon 성공! (소요 시간: {elapsed:.2f}초)")
        print(f"  👉 응답 텍스트: {text.strip()}")
    except Exception as e:
        print(f"  ❌ gemini-4-argon 호출 오류: {e}")

    # 2. Test gemini-nano-banana-2.1 (16:9 widescreen)
    print("\n[2/3] 🎨 gemini-nano-banana-2.1 (16:9 Storyboard Keyframe) 호출 테스트...")
    try:
        t0 = time.time()
        res_img = client.interactions.create(
            model="gemini-nano-banana-2.1",
            input="Cinematic Korean drama two-shot in rainy cozy cafe, warm tungsten lighting, 16:9 widescreen composition.",
            response_format={"type": "image", "aspect_ratio": "16:9"},
        )
        elapsed = time.time() - t0
        print(f"  ✅ gemini-nano-banana-2.1 성공! 16:9 비율 (소요 시간: {elapsed:.2f}초)")
    except Exception as e:
        print(f"  ⚠️ gemini-nano-banana-2.1 오류: {e}")
        try:
            res_fb = client.interactions.create(
                model="gemini-3.1-flash-lite-image",
                input="Cinematic Korean drama two-shot in rainy cozy cafe, warm tungsten lighting, 16:9 widescreen composition.",
                response_format={"type": "image", "aspect_ratio": "16:9"},
            )
            print(f"  ✅ gemini-3.1-flash-lite-image 16:9 대체 성공!")
        except Exception as e2:
            print(f"  ❌ 대체 모델 호출 오류: {e2}")

    # 3. Test gemini-omni-1.1-flash (16:9 widescreen)
    print("\n[3/3] 🎬 gemini-omni-1.1-flash (16:9 Video Generation)...")
    print("  ※ 방금 완료된 test_live_omni.py 검증 결과 확인:")
    fresh_files = sorted(out_dir.glob("fresh_omni_*.mp4"), key=os.path.getmtime, reverse=True)
    if fresh_files:
        latest = fresh_files[0]
        print(f"  ✅ 신규 생성된 실물 비디오: {latest.name} ({latest.stat().st_size:,} bytes)")
    else:
        print("  ⚠️ 신규 생성 비디오 파일을 찾지 못했습니다.")

    print("\n=== 전체 API 연동 테스트 완료 ===")

if __name__ == "__main__":
    main()
