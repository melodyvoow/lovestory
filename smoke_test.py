"""
Step 0 · LoveStory; 현장 스모크 테스트 스크립트
1) gemini-4-argon (Interactions API + thinking_level="low", deprecated 파라미터 제외)
2) gemini-nano-banana-2.1 (기본/인서트 이미지 생성 확인)
3) gemini-omni-1.1-flash (비디오 생성 / background=True 호출 및 상태 조회 확인)

실행 방법:
  export GEMINI_API_KEY="AIza..."
  python3 smoke_test.py            # Argon + Nano Banana 빠른 확인
  python3 smoke_test.py --omni     # Omni 백그라운드 영상 생성까지 포함해 확인
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()


def extract_text_from_interaction(interaction) -> str:
    """Interactions API 응답에서 텍스트 추출"""
    if hasattr(interaction, "output_text") and interaction.output_text:
        return interaction.output_text
    texts = []
    steps = getattr(interaction, "steps", None) or []
    for step in steps:
        if getattr(step, "type", None) == "model_output":
            for item in getattr(step, "content", None) or []:
                if getattr(item, "type", None) == "text" and getattr(item, "text", None):
                    texts.append(item.text)
    return "\n".join(texts).strip()


def extract_image_bytes(interaction) -> bytes | None:
    """Interactions API 응답에서 이미지 바이트 추출"""
    if hasattr(interaction, "output_image") and interaction.output_image:
        data = getattr(interaction.output_image, "data", None)
        if data:
            return base64.b64decode(data) if isinstance(data, str) else data

    steps = getattr(interaction, "steps", None) or []
    for step in steps:
        for item in getattr(step, "content", None) or []:
            if getattr(item, "type", None) == "image" and getattr(item, "data", None):
                data = item.data
                return base64.b64decode(data) if isinstance(data, str) else data
    return None


def test_argon(client: genai.Client) -> bool:
    print("\n[1/3] 🧪 Testing gemini-4-argon (Interactions API, thinking_level='low')...")
    try:
        # CRITICAL RULE: Never pass temperature, top_p, top_k, thinking_budget to gemini-4-argon
        res = client.interactions.create(
            model="gemini-4-argon",
            input="이준(29세 사진가, 내일 출국)이 카페에서 첫 마디로 '오늘은 조금 일찍 가봐야 할 것 같아.'라고 말한 상황을 한 줄 JSON {\"status\":\"ok\",\"character\":\"이준\"} 으로만 답해줘.",
            generation_config={"thinking_level": "low"},
        )
        text = extract_text_from_interaction(res)
        print(f"  ✅ gemini-4-argon 성공! (interaction_id={getattr(res, 'id', 'N/A')})")
        print(f"  👉 응답: {text[:200]}")
        return True
    except Exception as e:
        print(f"  ❌ gemini-4-argon 실패: {e}")
        return False


def test_nano_banana(client: genai.Client, out_dir: Path) -> bool:
    print("\n[2/3] 🎨 Testing gemini-nano-banana-2.1 (Image Generation)...")
    for model_name in ["gemini-nano-banana-2.1", "gemini-3.1-flash-lite-image"]:
        try:
            res = client.interactions.create(
                model=model_name,
                input="Warm cinematic Korean drama style illustration, rainy night cozy cafe window, a wet umbrella leaning by a wooden chair, soft warm lighting, 9:16 vertical aspect ratio, no text.",
                response_format={"type": "image", "aspect_ratio": "9:16"},
            )
            img_bytes = extract_image_bytes(res)
            if img_bytes:
                out_path = out_dir / "smoke_cafe.jpg"
                out_path.write_bytes(img_bytes)
                print(f"  ✅ {model_name} 성공! 저장 위치: {out_path} ({len(img_bytes)} bytes)")
                return True
            print(f"  ⚠️ {model_name} 응답에 이미지 바이트가 없습니다: {res}")
        except Exception as e:
            print(f"  ⚠️ {model_name} 호출 오류: {e}")
    return False


def test_omni(client: genai.Client, out_dir: Path) -> bool:
    print("\n[3/3] 🎬 Testing gemini-omni-1.1-flash (Video Generation, background=True)...")
    try:
        interaction = client.interactions.create(
            model="gemini-omni-1.1-flash",
            input="Close-up cinematic shot of a man's hand gently sliding a vintage postcard across a warm wooden cafe table on a rainy night, 9:16 vertical.",
            response_format={
                "type": "video",
                "aspect_ratio": "9:16",
                "resolution": "720p",
            },
            background=True,
        )
        inter_id = getattr(interaction, "id", None)
        print(f"  🚀 Omni 작업 시작됨! id={inter_id}, 초기 status={getattr(interaction, 'status', 'N/A')}")

        # Poll until completed if background=True returned in-progress status
        for attempt in range(40):
            status = getattr(interaction, "status", "completed")
            if status in ("completed", "COMPLETED", "failed", "FAILED"):
                break
            time.sleep(5)
            interaction = client.interactions.get(id=inter_id)
            print(f"  ⏳ 폴링 중 ({attempt + 1})... status={getattr(interaction, 'status', 'N/A')}")

        video_b64 = None
        if hasattr(interaction, "output_video") and interaction.output_video:
            video_b64 = getattr(interaction.output_video, "data", None)

        if not video_b64:
            for step in getattr(interaction, "steps", None) or []:
                for item in getattr(step, "content", None) or []:
                    if getattr(item, "type", None) == "video" and getattr(item, "data", None):
                        video_b64 = item.data

        if video_b64:
            out_path = out_dir / "smoke_omni.mp4"
            out_path.write_bytes(base64.b64decode(video_b64))
            print(f"  ✅ gemini-omni-1.1-flash 성공! 저장 위치: {out_path}")
            return True

        print(f"  ⚠️ 완료되었으나 video data 필드를 찾지 못했습니다: {interaction}")
        return False
    except Exception as e:
        print(f"  ❌ gemini-omni-1.1-flash 실패: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--omni", action="store_true", help="Omni 영상 생성 테스트 포함")
    parser.add_argument("--only-omni", action="store_true", help="Omni 영상 생성만 단독 테스트")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. .env 파일 또는 환경변수를 확인해 주세요.")
        sys.exit(1)

    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== LoveStory; Step 0 Smoke Test (google-genai v{genai.__version__}) ===")
    client = genai.Client(api_key=api_key)

    if args.only_omni:
        ok_omni = test_omni(client, out_dir)
        print("\n=== 요약 ===")
        print(f"• gemini-omni-1.1-flash: {'PASS' if ok_omni else 'FAIL'}")
        return

    ok_argon = test_argon(client)
    ok_image = test_nano_banana(client, out_dir)
    ok_omni = True
    if args.omni:
        ok_omni = test_omni(client, out_dir)
    else:
        print("\n[3/3] ⏭️ Omni 테스트는 --omni 옵션 지정 시 실행됩니다.")

    print("\n=== 요약 ===")
    print(f"• gemini-4-argon       : {'PASS' if ok_argon else 'FAIL'}")
    print(f"• gemini-nano-banana   : {'PASS' if ok_image else 'FAIL'}")
    if args.omni:
        print(f"• gemini-omni-1.1-flash: {'PASS' if ok_omni else 'FAIL'}")


if __name__ == "__main__":
    main()
