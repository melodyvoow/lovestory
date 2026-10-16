"""
Fresh Live Test for gemini-omni-1.1-flash video generation
Aspect ratio: 16:9
"""

import base64
import os
import sys
import time
from pathlib import Path
import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 없습니다.")
        sys.exit(1)

    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"fresh_omni_{int(time.time())}.mp4"

    print(f"🎬 gemini-omni-1.1-flash 신규 비디오 생성 테스트 시작...")
    print(f"📐 규격: 16:9 widescreen, 720p, background=True")
    client = genai.Client(api_key=api_key)

    prompt = (
        "Cinematic slow-motion shot, 16:9 widescreen: A 29-year-old Korean male photographer's hand gently "
        "sliding a vintage photo postcard across a rain-streaked wooden table in a warm tungsten-lit cafe at night. "
        "Steam rising from a coffee cup, soft rain reflections in the background."
    )

    t0 = time.time()
    try:
        interaction = client.interactions.create(
            model="gemini-omni-1.1-flash",
            input=prompt,
            response_format={
                "type": "video",
                "aspect_ratio": "16:9",
                "resolution": "720p",
            },
            background=True,
        )
        inter_id = getattr(interaction, "id", None)
        init_status = getattr(interaction, "status", "unknown")
        print(f"  🚀 작업 접수 완료! ID: {inter_id} (초기 상태: {init_status})")

        # Polling
        for attempt in range(1, 40):
            status = getattr(interaction, "status", "completed")
            print(f"  ⏳ [{attempt * 5}s] 폴링 중... 상태: {status}")
            if status in ("completed", "COMPLETED", "failed", "FAILED"):
                break
            time.sleep(5)
            interaction = client.interactions.get(id=inter_id)

        final_status = getattr(interaction, "status", "unknown")
        print(f"  🏁 최종 처리 상태: {final_status}")

        if final_status in ("failed", "FAILED"):
            print(f"  ❌ 영상 생성 실패: {interaction}")
            return False

        # Extract video bytes
        video_bytes = None

        # 1. Check output_video data
        if hasattr(interaction, "output_video") and interaction.output_video:
            ov = interaction.output_video
            if getattr(ov, "data", None):
                video_bytes = base64.b64decode(ov.data) if isinstance(ov.data, str) else ov.data
            elif getattr(ov, "uri", None):
                uri = ov.uri
                print(f"  📥 URI로부터 비디오 다운로드 중: {uri}")
                # Download via Files API
                sep = "&" if "?" in uri else "?"
                dl_url = f"{uri}{sep}key={api_key}"
                r = httpx.get(dl_url, timeout=60.0)
                if r.is_success:
                    video_bytes = r.content

        # 2. Check steps array
        if not video_bytes:
            for step in getattr(interaction, "steps", None) or []:
                for item in getattr(step, "content", None) or []:
                    if getattr(item, "type", None) == "video":
                        if getattr(item, "data", None):
                            d = item.data
                            video_bytes = base64.b64decode(d) if isinstance(d, str) else d
                            break
                        elif getattr(item, "uri", None):
                            uri = item.uri
                            sep = "&" if "?" in uri else "?"
                            dl_url = f"{uri}{sep}key={api_key}"
                            r = httpx.get(dl_url, timeout=60.0)
                            if r.is_success:
                                video_bytes = r.content
                                break

        if video_bytes and len(video_bytes) > 1000:
            out_file.write_bytes(video_bytes)
            elapsed = time.time() - t0
            print(f"\n✅ gemini-omni-1.1-flash 신규 영상 생성 성공!")
            print(f"  📁 저장 파일: {out_file}")
            print(f"  📊 파일 크기: {len(video_bytes):,} bytes ({len(video_bytes)/1024/1024:.2f} MB)")
            print(f"  ⏱️ 총 소요 시간: {elapsed:.1f}초")
            return True
        else:
            print(f"  ⚠️ 영상 데이터 바이트를 추출하지 못했습니다. Raw 응답: {interaction}")
            return False

    except Exception as e:
        print(f"  ❌ Omni 생성 중 예외 발생: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
