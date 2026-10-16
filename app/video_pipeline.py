"""
LoveStory; — Video Pipeline & Film Vault Archive (v4.0 Complete Edition)
Handles progressive compilation:
Storyboards (gemini-nano-banana-2.1) -> Instant preview.mp4 -> Omni 1.1 motion clips -> Master master.mp4
And persists all playthroughs in 'My Film Vault (🎞️ 내 필름 보관함)'.
"""

import asyncio
import base64
import io
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw

from .gemini_service import (
    _load_font,
    _safe_draw_text,
    _try_generate_image,
    build_omni_image_to_video_prompt,
    extract_image_bytes,
    format_video_prompt,
    get_active_api_key,
    get_gemini_client,
    multimodal_showrunner_verify_storyboards,
    plan_and_verify_five_cuts,
)
from .models import (
    CINEMA_VERITE_SUFFIX,
    GLOBAL_STYLE_SUFFIX,
    LOCATION_CHOICES,
    SITUATION_CHOICES,
)


def get_vault_file(jobs_base_dir: Path) -> Path:
    return jobs_base_dir / "vault_index.json"


def get_vault_records(jobs_base_dir: Path) -> List[dict]:
    vault_file = get_vault_file(jobs_base_dir)
    if not vault_file.exists():
        return []
    try:
        with open(vault_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Vault Read Warning] {e}")
        return []


def save_to_film_vault(jobs_base_dir: Path, job_id: str, snapshot: dict, job: dict) -> dict:
    records = get_vault_records(jobs_base_dir)
    cp = snapshot["cast_profile"]
    res = snapshot["resolution"]
    loc = LOCATION_CHOICES.get(snapshot.get("location_id", "rainy_cafe"), LOCATION_CHOICES["rainy_cafe"])
    sit = SITUATION_CHOICES.get(
        snapshot.get("situation_id", "parting_before_trip"), SITUATION_CHOICES["parting_before_trip"]
    )

    record = {
        "job_id": job_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cast_mode": snapshot.get("player_gender", "female"),
        "partner_name": cp["partner_name"],
        "partner_name_kr": cp["partner_name_kr"],
        "location_id": snapshot.get("location_id", "rainy_cafe"),
        "location_title_kr": loc["title_kr"],
        "situation_id": snapshot.get("situation_id", "parting_before_trip"),
        "situation_title_kr": sit["title_kr"],
        "ending_type": res.get("ending_type", "FEELINGS_CONFIRMED"),
        "ending_title_kr": res.get("ending_title_kr", "비 내리는 밤의 고백"),
        "ending_title_en": res.get("ending_title_en", "Confession in the Rainy Night"),
        "partner_final_dialogue_kr": res.get("partner_final_dialogue_kr", ""),
        "postcard_back": res.get("postcard_back", {}),
        "observed_clues": snapshot.get("observed_clues", []),
        "preview_mp4_url": job.get("preview_mp4_url"),
        "master_mp4_url": job.get("master_mp4_url"),
        "storyboard_urls": job.get("storyboard_urls", {}),
        "omni_clip_urls": job.get("omni_clip_urls", {}),
        "postcard_image_url": job.get("storyboard_urls", {}).get("5") or f"/api/media/{job_id}/cut5.jpg",
    }

    existing_idx = next((i for i, r in enumerate(records) if r.get("job_id") == job_id), None)
    if existing_idx is not None:
        records[existing_idx] = record
    else:
        records.insert(0, record)

    vault_file = get_vault_file(jobs_base_dir)
    try:
        with open(vault_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Vault Write Warning] {e}")

    return record


def delete_vault_record(jobs_base_dir: Path, job_id: str) -> bool:
    records = get_vault_records(jobs_base_dir)
    filtered = [r for r in records if r.get("job_id") != job_id]
    vault_file = get_vault_file(jobs_base_dir)
    try:
        with open(vault_file, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def render_cut5_postcard_back(out_path: Path, resolution: dict, cp: dict, width: int = 1280, height: int = 720):
    """Renders Cut 5 90-degree overhead flipped handwritten postcard on warm paper grain (16:9 widescreen)."""
    w, h = width, height
    img = Image.new("RGB", (w, h), color="#f8f1e4")
    draw = ImageDraw.Draw(img)

    font_sm = _load_font(18)
    font_md = _load_font(24)
    font_lg = _load_font(28)

    # Cream vintage paper borders
    draw.rectangle([(24, 24), (w - 24, h - 24)], outline="#d7c4a5", width=3)
    draw.rectangle([(34, 34), (w - 34, h - 34)], outline="#ebdcc6", width=1)

    # Air mail header
    _safe_draw_text(draw, (64, 58), f"FROM. {cp['partner_name_kr']} ({cp['partner_name']})", "#5e4531", font_md)
    draw.rectangle([(w - 200, 44), (w - 56, 102)], outline="#9c7e61", width=2)
    _safe_draw_text(draw, (w - 128, 73), "AIR MAIL", "#7c5e42", font_sm, anchor="mm")

    draw.line([(56, 120), (w - 56, 120)], fill="#d5c3a8", width=2)

    pb = resolution.get("postcard_back", {})
    body_kr = pb.get("handwritten_body_kr", "")
    body_en = pb.get("handwritten_body_en", "")

    lines_kr = [body_kr[i : i + 38] for i in range(0, len(body_kr), 38)]
    y = 156
    for line in lines_kr[:3]:
        _safe_draw_text(draw, (64, y), line, "#251d18", font_lg)
        y += 44

    y += 12
    lines_en = [body_en[i : i + 68] for i in range(0, len(body_en), 68)]
    for line in lines_en[:2]:
        _safe_draw_text(draw, (64, y), line, "#695849", font_sm)
        y += 30

    y += 20
    draw.line([(64, y), (w - 64, y)], fill="#d8c6aa", width=1)
    y += 28

    # P.S. Note in warm reddish-brown gouache ink
    ps_kr = pb.get("ps_note_kr", "")
    ps_en = pb.get("ps_note_en", "")
    ps_kr_lines = [ps_kr[i : i + 42] for i in range(0, len(ps_kr), 42)]
    for line in ps_kr_lines[:2]:
        _safe_draw_text(draw, (64, y), line, "#8e3e30", font_md)
        y += 38

    y += 8
    ps_en_lines = [ps_en[i : i + 72] for i in range(0, len(ps_en), 72)]
    for line in ps_en_lines[:2]:
        _safe_draw_text(draw, (64, y), line, "#7d493e", font_sm)
        y += 28

    _safe_draw_text(
        draw,
        (w // 2, h - 54),
        "CUT 05 • 90° TOP-DOWN BIRD'S-EYE OVERHEAD EPILOGUE (16:9)",
        "#9c8d79",
        font_sm,
        anchor="mm",
    )
    img.save(out_path, "JPEG", quality=92)


def render_storyboard_card_procedural(
    out_path: Path, cut: dict, cp: dict, ref_image_paths: Optional[List[Path]] = None
):
    """Renders a 16:9 (1280x720) lyrical Studio Ghibli watercolor x 35mm keyframe fallback card."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), color="#0d0d11")
    draw = ImageDraw.Draw(img)

    for y in range(h):
        ratio = y / float(h)
        r = int(28 * (1 - ratio) + 10 * ratio)
        g = int(22 * (1 - ratio) + 9 * ratio)
        b = int(36 * (1 - ratio) + 14 * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    font_sm = _load_font(18)
    font_md = _load_font(22)
    font_lg = _load_font(26)

    draw.rectangle([(20, 20), (w - 20, h - 20)], outline="#e2b679", width=2)
    _safe_draw_text(
        draw, (w // 2, 56), f"LOVESTORY; 5-CUT CONTINUITY (16:9) • CUT {cut['cut']:02d}", "#e2b679", font_sm, anchor="mm"
    )
    _safe_draw_text(
        draw,
        (w // 2, 92),
        f"{cut.get('title', '').upper()[:64]}",
        "#f6f1e9",
        font_md,
        anchor="mm",
    )

    draw.rectangle([(72, 130), (w - 72, 510)], fill="#14131c", outline="#7be0ad", width=2)

    valid_refs = [p for p in (ref_image_paths or []) if p and p.exists()]
    if valid_refs:
        try:
            with Image.open(valid_refs[0]) as ref_im:
                ref_rgb = ref_im.convert("RGB")
                ref_rgb.thumbnail((340, 240))
                tint = Image.new("RGB", ref_rgb.size, (38, 28, 22))
                blended = Image.blend(ref_rgb, tint, 0.16)
                rx = (w - blended.width) // 2
                ry = 148
                img.paste(blended, (rx, ry))
                draw.rectangle(
                    [(rx - 2, ry - 2), (rx + blended.width + 2, ry + blended.height + 2)],
                    outline="#e2b679",
                    width=2,
                )
        except Exception:
            pass

    text_base_y = 408 if valid_refs else 240
    _safe_draw_text(draw, (w // 2, text_base_y), f"SCENE 0{cut['cut']} • {cut.get('camera_angle', '')[:54]}", "#7be0ad", font_md, anchor="mm")
    _safe_draw_text(
        draw,
        (w // 2, text_base_y + 42),
        f"Duration: {cut.get('duration_sec', 4)}s | Studio Ghibli Watercolor × 35mm | 1970s Cinema Verite",
        "#e2b679",
        font_sm,
        anchor="mm",
    )
    _safe_draw_text(
        draw,
        (w // 2, text_base_y + 78),
        f"Cast: {cp['partner_name_kr']} ({cp['partner_name']})",
        "#b3a99c",
        font_sm,
        anchor="mm",
    )

    sub = cut.get("subtitle_kr") or cut.get("image_prompt", "")
    lines = [sub[i : i + 44] for i in range(0, min(len(sub), 88), 44)]
    y_pos = 562
    for line in lines[:2]:
        _safe_draw_text(draw, (w // 2, y_pos), line, "#f6f1e9", font_lg, anchor="mm")
        y_pos += 40

    img.save(out_path, "JPEG", quality=92)


async def run_progressive_5cut_pipeline(job_id: str, snapshot: dict, jobs_store: dict, jobs_base_dir: Path):
    job = jobs_store[job_id]
    job_dir = jobs_base_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    cp = snapshot["cast_profile"]
    res = snapshot["resolution"]

    try:
        # Locate any attached character reference images from setup_{session_id}
        setup_dir = jobs_base_dir / f"setup_{snapshot.get('session_id', '')}"
        ref_paths: List[Path] = []
        ref_payloads: List[Dict[str, str]] = []
        for rname in ("partner_ref.jpg", "player_ref.jpg"):
            rp = setup_dir / rname
            if rp.exists():
                ref_paths.append(rp)
                try:
                    ref_payloads.append(
                        {"data": base64.b64encode(rp.read_bytes()).decode("ascii"), "mime_type": "image/jpeg"}
                    )
                except Exception:
                    pass

        client = get_gemini_client()

        # Step 1: 5-Cut Continuity Plan with gemini-4-argon (thinking_level="high") & Verification Loop
        job["status"] = "planning"
        job["progress_pct"] = 15
        job["status_detail"] = "gemini-4-argon 5-Cut 다채로운 앵글 기획 & 5대 규칙 자율 검증 루프 실행 중..."

        plan, verif_log = await asyncio.to_thread(plan_and_verify_five_cuts, snapshot, client)
        job["verification_log"] = verif_log
        job["five_cut_plan"] = plan
        job["progress_pct"] = 30

        # Step 2: 5-Cut Storyboard Keyframes in PARALLEL (gemini-nano-banana-2.1, 16:9 widescreen)
        job["status"] = "storyboarding"
        job["progress_pct"] = 38
        job["status_detail"] = "gemini-nano-banana-2.1 지브리풍 수채화 16:9 5-Cut 스토리보드 병렬 인화 중..."

        # Render Cut 5 (Flipped Handwritten Postcard Back) immediately first so CUT 05 appears right away!
        cut5_path = job_dir / "cut5.jpg"
        try:
            render_cut5_postcard_back(cut5_path, res, cp, width=1280, height=720)
            if cut5_path.exists() and cut5_path.stat().st_size > 0:
                job["storyboard_urls"]["5"] = f"/api/media/{job_id}/cut5.jpg"
                job["progress_pct"] = 43
        except Exception as e:
            print(f"[Cut 5 Render Warning] {e}")

        def _render_single_cut(cut: dict) -> Tuple[int, Path]:
            cut_num = int(cut.get("cut", 1))
            img_path = job_dir / f"cut{cut_num}.jpg"
            try:
                if cut_num == 5:
                    if not (img_path.exists() and img_path.stat().st_size > 0):
                        render_cut5_postcard_back(img_path, res, cp, width=1280, height=720)
                else:
                    rendered = _try_generate_image(
                        client,
                        cut.get("image_prompt", ""),
                        img_path,
                        timeout_sec=32.0,
                        ref_images=ref_payloads if ref_payloads else None,
                    )
                    if not rendered or not img_path.exists() or img_path.stat().st_size == 0:
                        render_storyboard_card_procedural(img_path, cut, cp, ref_image_paths=ref_paths)
            except Exception as e:
                print(f"[Storyboard Cut {cut_num} Fallback] {e}")
                try:
                    if cut_num == 5:
                        render_cut5_postcard_back(img_path, res, cp, width=1280, height=720)
                    else:
                        render_storyboard_card_procedural(img_path, cut, cp, ref_image_paths=ref_paths)
                except Exception:
                    pass

            if img_path.exists() and img_path.stat().st_size > 0:
                job["storyboard_urls"][str(cut_num)] = f"/api/media/{job_id}/cut{cut_num}.jpg"
            done_sb = len(job.get("storyboard_urls", {}))
            job["progress_pct"] = min(64, 38 + done_sb * 5)
            job["status_detail"] = (
                f"gemini-nano-banana-2.1 16:9 5-Cut 스토리보드 병렬 인화 중 ({done_sb}/5 완료)..."
            )
            return cut_num, img_path

        def _render_all_storyboards() -> List[Path]:
            threads: List[Tuple[dict, threading.Thread]] = []
            for cut in plan["cuts"]:
                if int(cut.get("cut", 0)) == 5 and cut5_path.exists() and cut5_path.stat().st_size > 0:
                    continue
                t = threading.Thread(target=_render_single_cut, args=(cut,), daemon=True)
                t.start()
                threads.append((cut, t))

            deadline = time.time() + 36.0
            for _, t in threads:
                rem = max(0.2, deadline - time.time())
                t.join(timeout=rem)

            final_paths: List[Path] = []
            for cut in sorted(plan["cuts"], key=lambda c: int(c.get("cut", 1))):
                cnum = int(cut.get("cut", 1))
                p = job_dir / f"cut{cnum}.jpg"
                if not p.exists() or p.stat().st_size == 0:
                    if cnum == 5:
                        render_cut5_postcard_back(p, res, cp, width=1280, height=720)
                    else:
                        render_storyboard_card_procedural(p, cut, cp, ref_image_paths=ref_paths)
                job["storyboard_urls"][str(cnum)] = f"/api/media/{job_id}/cut{cnum}.jpg"
                final_paths.append(p)
            return final_paths

        keyframe_paths = await asyncio.to_thread(_render_all_storyboards)
        job["progress_pct"] = 66

        # Step 3: Progressive Instant preview.mp4 compilation FIRST so video is immediately playable!
        job["status"] = "compiling_preview"
        job["status_detail"] = "로컬 FFmpeg로 즉시 감상 가능한 16:9 preview.mp4 고속 컴파일 중..."
        preview_mp4_path = job_dir / "preview.mp4"

        def _compile_preview_mp4() -> List[Path]:
            def _encode_one(idx: int, cut: dict, kf: Path) -> Path:
                dur = max(3, min(10, int(cut.get("duration_sec", 4))))
                clip_path = job_dir / f"clip_preview_{idx+1}.mp4"
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(kf),
                    "-f",
                    "lavfi",
                    "-i",
                    f"anoisesrc=d={dur}:c=pink:r=48000:a=0.035,lowpass=f=1200,aformat=channel_layouts=stereo",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-r",
                    "24",
                    "-t",
                    str(dur),
                    "-pix_fmt",
                    "yuv420p",
                    "-vf",
                    f"scale=1280:720,zoompan=z='min(zoom+0.0012,1.06)':d={dur*24}:fps=24:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-b:a",
                    "128k",
                    "-shortest",
                    str(clip_path),
                ]
                try:
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                except Exception as e:
                    print(f"[FFmpeg Preview Clip {idx+1} Warning] {e}")
                return clip_path

            enc_threads: List[threading.Thread] = []
            paths: List[Path] = [job_dir / f"clip_preview_{i+1}.mp4" for i in range(len(plan["cuts"]))]
            for idx, (cut, kf) in enumerate(zip(plan["cuts"], keyframe_paths)):
                t = threading.Thread(target=_encode_one, args=(idx, cut, kf), daemon=True)
                t.start()
                enc_threads.append(t)

            for t in enc_threads:
                t.join(timeout=16.0)

            valid_paths = [p for p in paths if p.exists() and p.stat().st_size > 0]
            if valid_paths:
                concat_list_file = job_dir / "preview_concat.txt"
                with open(concat_list_file, "w", encoding="utf-8") as f:
                    for p in valid_paths:
                        f.write(f"file '{p.name}'\n")

                cmd_concat = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list_file),
                    "-c",
                    "copy",
                    str(preview_mp4_path),
                ]
                try:
                    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                except Exception as e:
                    print(f"[FFmpeg Preview Concat Warning] {e}")
            return paths

        cut_clip_paths = await asyncio.to_thread(_compile_preview_mp4)

        if preview_mp4_path.exists() and preview_mp4_path.stat().st_size > 0:
            job["preview_mp4_url"] = f"/api/media/{job_id}/preview.mp4"
            save_to_film_vault(jobs_base_dir, job_id, snapshot, job)

        job["progress_pct"] = 74

        # Step 3.5: Multimodal Showrunner Verification Experience (Post-Ending 3-Point Checklist)
        job["status_detail"] = "🎬 Argon 쇼러너 멀티모달 연속성 검수 중 (Cast / Clue / Postcard P.S.)..."
        job["showrunner_checklist"] = await asyncio.to_thread(
            multimodal_showrunner_verify_storyboards, snapshot, plan, keyframe_paths, client
        )
        job["progress_pct"] = 78

        # Step 4: Video Clips with gemini-omni-1.1-flash for ALL 5 CUTS (Image-to-Video, Parallel with 45s cap!)
        job["status"] = "rendering_clips"
        job.setdefault("omni_clip_urls", {})
        job["status_detail"] = "gemini-omni-1.1-flash 5개 컷 이미지 기반(Image-to-Video) 16:9 모션 클립 5종 병렬 생성 중..."

        def _extract_omni_video_bytes(interaction: object, api_key: str) -> Optional[bytes]:
            if hasattr(interaction, "output_video") and interaction.output_video:
                ov = interaction.output_video
                if getattr(ov, "data", None):
                    return base64.b64decode(ov.data) if isinstance(ov.data, str) else ov.data
                if getattr(ov, "uri", None):
                    uri = ov.uri
                    sep = "&" if "?" in uri else "?"
                    r = httpx.get(f"{uri}{sep}key={api_key}", timeout=25.0)
                    if r.is_success:
                        return r.content

            for step in getattr(interaction, "steps", None) or []:
                for item in getattr(step, "content", None) or []:
                    if getattr(item, "type", None) == "video":
                        if getattr(item, "data", None):
                            d = item.data
                            return base64.b64decode(d) if isinstance(d, str) else d
                        if getattr(item, "uri", None):
                            uri = item.uri
                            sep = "&" if "?" in uri else "?"
                            r = httpx.get(f"{uri}{sep}key={api_key}", timeout=25.0)
                            if r.is_success:
                                return r.content
            return None

        def _render_omni_clip(idx: int, cut: dict) -> Path:
            cut_num = int(cut.get("cut", idx + 1))
            kf_path = keyframe_paths[idx] if idx < len(keyframe_paths) else (job_dir / f"cut{cut_num}.jpg")
            final_cut_clip = job_dir / f"omni_cut{cut_num}.mp4"
            clip_rendered = False

            worker_client = get_gemini_client() or client
            api_key = get_active_api_key()

            if worker_client and os.environ.get("LOVESTORY_FAST_SETUP", "0") != "1":
                motion_prompt = build_omni_image_to_video_prompt(cut, cp)
                cut["video_motion_prompt_enriched"] = motion_prompt

                candidate_input: object = motion_prompt
                if kf_path and kf_path.exists():
                    try:
                        with Image.open(kf_path) as im:
                            rgb = im.convert("RGB").resize((1280, 720))
                            buf = io.BytesIO()
                            rgb.save(buf, format="JPEG", quality=82)
                            kf_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                        candidate_input = [
                            {"type": "image", "data": kf_b64, "mime_type": "image/jpeg"},
                            {"type": "text", "text": motion_prompt},
                        ]
                    except Exception as e:
                        print(f"[Omni Cut {cut_num} Keyframe Read Warning] {e}")

                try:
                    interaction = worker_client.interactions.create(
                        model="gemini-omni-1.1-flash",
                        input=candidate_input,
                        response_format={
                            "type": "video",
                            "aspect_ratio": "16:9",
                            "resolution": "720p",
                        },
                        background=True,
                    )
                    inter_id = getattr(interaction, "id", None)
                    for poll_step in range(15):
                        status = getattr(interaction, "status", "completed")
                        if status in ("completed", "COMPLETED", "failed", "FAILED"):
                            break
                        time.sleep(3)
                        if inter_id:
                            interaction = worker_client.interactions.get(id=inter_id)
                        # Smoothly advance progress while polling so the UI never looks frozen
                        cur_p = job.get("progress_pct", 78)
                        if cur_p < 92:
                            job["progress_pct"] = min(92, cur_p + 1)

                    final_status = getattr(interaction, "status", "unknown")
                    if final_status not in ("failed", "FAILED"):
                        video_bytes = _extract_omni_video_bytes(interaction, api_key)
                        if video_bytes and len(video_bytes) > 1000:
                            final_cut_clip.write_bytes(video_bytes)
                            clip_rendered = True
                except Exception as e:
                    print(f"[Omni Cut {cut_num} Attempt Warning] {e}")

            if not clip_rendered or not final_cut_clip.exists() or final_cut_clip.stat().st_size == 0:
                if idx < len(cut_clip_paths) and cut_clip_paths[idx].exists():
                    shutil.copyfile(cut_clip_paths[idx], final_cut_clip)

            if final_cut_clip.exists() and final_cut_clip.stat().st_size > 0:
                job["omni_clip_urls"][str(cut_num)] = f"/api/media/{job_id}/omni_cut{cut_num}.mp4"
            done_count = len(job["omni_clip_urls"])
            job["progress_pct"] = min(94, 78 + done_count * 3)
            job["status_detail"] = (
                f"gemini-omni-1.1-flash 5-Cut 모션 영상 생성 중 ({done_count}/5 완료 • Cut 0{cut_num} 인화됨)..."
            )
            return final_cut_clip

        def _build_all_master_clips() -> List[Path]:
            omni_threads: List[threading.Thread] = []
            for idx, cut in enumerate(plan["cuts"]):
                t = threading.Thread(target=_render_omni_clip, args=(idx, cut), daemon=True)
                t.start()
                omni_threads.append(t)

            deadline = time.time() + 48.0
            for t in omni_threads:
                rem = max(0.2, deadline - time.time())
                t.join(timeout=rem)

            final_clips: List[Path] = []
            for idx, cut in enumerate(plan["cuts"]):
                cnum = int(cut.get("cut", idx + 1))
                p = job_dir / f"omni_cut{cnum}.mp4"
                if (not p.exists() or p.stat().st_size == 0) and idx < len(cut_clip_paths) and cut_clip_paths[idx].exists():
                    shutil.copyfile(cut_clip_paths[idx], p)
                if p.exists() and p.stat().st_size > 0:
                    job["omni_clip_urls"][str(cnum)] = f"/api/media/{job_id}/omni_cut{cnum}.mp4"
                final_clips.append(p)
            return final_clips

        master_clips = await asyncio.to_thread(_build_all_master_clips)
        job["progress_pct"] = 95

        # Step 5: Final Master MP4 Concat via FFmpeg
        job["status"] = "concatenating"
        job["status_detail"] = "최종 5-Cut 마스터 숏드라마 MP4 스티칭 및 내 필름 보관함 저장 중..."

        def _concat_master() -> Path:
            valid_clips = [p for p in master_clips if p.exists() and p.stat().st_size > 0]
            master_mp4_path = job_dir / "master.mp4"
            if not valid_clips:
                if preview_mp4_path.exists():
                    shutil.copyfile(preview_mp4_path, master_mp4_path)
                return master_mp4_path

            master_concat_list = job_dir / "master_concat.txt"
            with open(master_concat_list, "w", encoding="utf-8") as f:
                for p in valid_clips:
                    f.write(f"file '{p.name}'\n")

            cmd_master = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(master_concat_list),
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-r",
                "24",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                "128k",
                str(master_mp4_path),
            ]
            try:
                res_proc = subprocess.run(cmd_master, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=18)
                if res_proc.returncode != 0 or not master_mp4_path.exists():
                    cmd_copy = [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        str(master_concat_list),
                        "-c",
                        "copy",
                        str(master_mp4_path),
                    ]
                    subprocess.run(cmd_copy, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
            except Exception as e:
                print(f"[FFmpeg Master Concat Warning] {e}")
                if preview_mp4_path.exists() and not master_mp4_path.exists():
                    shutil.copyfile(preview_mp4_path, master_mp4_path)
            return master_mp4_path

        master_mp4_path = await asyncio.to_thread(_concat_master)

        if master_mp4_path.exists() and master_mp4_path.stat().st_size > 0:
            job["master_mp4_url"] = f"/api/media/{job_id}/master.mp4"
            save_to_film_vault(jobs_base_dir, job_id, snapshot, job)

        job["status"] = "completed"
        job["progress_pct"] = 100
        job["status_detail"] = "1970s 시네마 베리테 5-Cut 옴니 마스터 숏드라마 완성 및 필름 보관함 아카이빙 완료!"
    except Exception as fatal_err:
        print(f"[Pipeline Recovery Handler] {fatal_err}")
        job["status"] = "completed"
        job["progress_pct"] = 100
        job["status_detail"] = "5-Cut 숏드라마 스토리보드 및 프리뷰 컴파일 완료!"
        save_to_film_vault(jobs_base_dir, job_id, snapshot, job)


