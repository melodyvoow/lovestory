"""
LoveStory; — Master FastAPI Application (v4.0 Complete Edition)
Google DeepMind AI Hackathon (Track 1: Entertainment)
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .gemini_service import (
    call_argon_turn1,
    call_argon_turn2,
    enrich_cast_profile_with_reference_images,
    generate_in_app_setup_and_prequel,
    get_active_api_key,
    get_gemini_client,
    synthesize_clues_with_argon,
)
from .models import (
    CAST_PROFILES,
    CLUES_CATALOG,
    LOCATION_CHOICES,
    SITUATION_CHOICES,
    CharacterAssetRequest,
    ClueRequest,
    ClueSynthesisRequest,
    StartSessionRequest,
    TurnRequest,
)
from .video_pipeline import (
    delete_vault_record,
    get_vault_records,
    run_progressive_5cut_pipeline,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
STATIC_DIR = BASE_DIR / "static"
PUBLIC_DIR = BASE_DIR / "public"

JOBS_BASE_DIR = Path(os.environ.get("LOVESTORY_STORAGE_DIR", "/tmp/lovestory_jobs"))
if not JOBS_BASE_DIR.exists():
    try:
        JOBS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        JOBS_BASE_DIR = BASE_DIR / "outputs" / "jobs"
        JOBS_BASE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="LoveStory; API",
    version="4.0.0",
    description="Choose the moment of love. The story doesn’t end here.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}
jobs: Dict[str, dict] = {}


@app.get("/api/health")
def health_check():
    key = get_active_api_key()
    masked = f"{key[:12]}...{key[-4:]}" if len(key) > 16 else "configured"
    return {
        "status": "ok",
        "service": "LoveStory; v4.0 Complete Edition",
        "api_key_configured": bool(key),
        "api_key_masked": masked,
        "storage_dir": str(JOBS_BASE_DIR),
        "vault_count": len(get_vault_records(JOBS_BASE_DIR)),
    }


@app.post("/api/character/asset")
def generate_character_asset_preview(req: CharacterAssetRequest):
    """
    Generates a Character Reference Asset Sheet (`character_sheet.jpg`) and extracts visual traits
    from attached partner/player reference images right inside Step 1 of Onboarding.
    """
    gender = req.player_gender if req.player_gender in ("female", "male") else "female"
    base_cp = dict(CAST_PROFILES[gender])
    asset_id = f"char_{int(time.time() * 1000)}"
    asset_dir = JOBS_BASE_DIR / asset_id

    client = get_gemini_client()
    updated_cp, _, _, sheet_url = enrich_cast_profile_with_reference_images(
        cp=base_cp,
        partner_ref_b64=req.partner_ref_image_b64,
        player_ref_b64=req.player_ref_image_b64,
        custom_note=req.custom_note,
        out_dir=asset_dir,
        client=client,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "cast_profile": updated_cp,
        "character_sheet_url": sheet_url,
        "partner_ref_url": updated_cp.get("partner_ref_url"),
        "player_ref_url": updated_cp.get("player_ref_url"),
        "extracted_summary_kr": updated_cp.get(
            "extracted_summary_kr",
            f"{updated_cp['partner_name_kr']} ({updated_cp['partner_name']}) 지브리 수채화 × 35mm 캐릭터 자산 시트가 생성되었습니다.",
        ),
    }


@app.post("/api/session/start")
def start_session(req: StartSessionRequest):
    """
    4-Step Dynamic Story Director Onboarding:
    1. Who am I & Who is my partner? (player_gender -> locks cast_profile + optional reference images)
    2. Where are we right now? (location_id)
    3. What is the moment between us? (situation_id)
    4. Initial Clue Focus (anchor_clue_id)
    Generates in-app setup still & 3-cut prequel keyframes via gemini-nano-banana-2.1.
    """
    gender = req.player_gender if req.player_gender in ("female", "male") else "female"
    base_cp = dict(CAST_PROFILES[gender])
    loc_id = req.location_id if req.location_id in LOCATION_CHOICES else "rainy_cafe"
    sit_id = req.situation_id if req.situation_id in SITUATION_CHOICES else "parting_before_trip"
    anchor_id = req.anchor_clue_id if req.anchor_clue_id in CLUES_CATALOG else "wet_sleeve"

    loc = dict(LOCATION_CHOICES[loc_id])
    sit = dict(SITUATION_CHOICES[sit_id])

    # Crisp itinerary badge tailored to location/situation
    if loc_id == "midnight_station":
        sit["itinerary_badge"] = "🚉 DEPARTURE: 05:30 AM PLATFORM 3"
    else:
        sit["itinerary_badge"] = "✈️ DEPARTURE: TOMORROW 09:30 AM"

    session_id = f"sess_{int(time.time() * 1000)}"
    session_out_dir = JOBS_BASE_DIR / f"setup_{session_id}"

    client = get_gemini_client()
    cp, ref_images_payload, saved_ref_paths, character_sheet_url = enrich_cast_profile_with_reference_images(
        cp=base_cp,
        partner_ref_b64=req.partner_ref_image_b64,
        player_ref_b64=req.player_ref_image_b64,
        custom_note=req.custom_note,
        out_dir=session_out_dir,
        client=client,
    )

    session_stub = {
        "cast_profile": cp,
        "location_id": loc_id,
        "situation_id": sit_id,
    }
    setup_still_url, prequel_clips = generate_in_app_setup_and_prequel(
        session_stub,
        session_out_dir,
        client=client,
        ref_images=ref_images_payload if ref_images_payload else None,
        ref_image_paths=saved_ref_paths if saved_ref_paths else None,
    )

    opening_line = sit["opening_lines"].get(gender, "비 많이 오네… 오늘은 조금 일찍 가봐야 할 것 같아.")
    first_history = {
        "speaker": cp["partner_name"],
        "text_kr": opening_line,
        "action_kr": f"{loc['time_str']} — 젖은 왼쪽 어깨를 가볍게 털며 맞은편에 조용히 마주 앉는다.",
    }

    session = {
        "session_id": session_id,
        "player_gender": gender,
        "cast_profile": cp,
        "location_id": loc_id,
        "location": loc,
        "situation_id": sit_id,
        "situation": sit,
        "anchor_clue_id": anchor_id,
        "setup_still_url": setup_still_url,
        "character_sheet_url": character_sheet_url,
        "dialogue_history": [first_history],
        "turn": 1,
        "observed_clues": [anchor_id],
        "confirmed_facts": [],
        "clue_synthesis": None,
        "heart_lock_status": "LOCKED",
    }
    sessions[session_id] = session

    preset_turn1 = sit.get(
        "preset_turn1",
        [
            "어깨가 많이 젖었네… 우산 나한테만 씌워준 거야?",
            f"오늘따라 왜 이렇게 서둘러? 아직 {loc['time_str'].split('(')[0].strip()}잖아.",
            "그 엽서… 암실에서 약속했던 그 사진이야?",
        ],
    )

    return {
        "session": session,
        "setup_still_url": setup_still_url,
        "character_sheet_url": character_sheet_url,
        "prequel_clips": prequel_clips,
        "clues_catalog": CLUES_CATALOG,
        "location": loc,
        "situation": sit,
        "preset_choices_turn1": preset_turn1,
    }


@app.post("/api/session/clue")
def inspect_clue(req: ClueRequest):
    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    clue = CLUES_CATALOG.get(req.clue_id)
    if not clue:
        raise HTTPException(status_code=400, detail="유효하지 않은 단서입니다.")

    if req.clue_id not in sess["observed_clues"]:
        sess["observed_clues"].append(req.clue_id)

    can_synthesize = len(sess["observed_clues"]) >= 2
    if can_synthesize and sess.get("heart_lock_status") == "LOCKED":
        sess["heart_lock_status"] = "READY_TO_SYNTHESIZE"

    return {
        "status": "ok",
        "clue": clue,
        "observed_clues": sess["observed_clues"],
        "confirmed_facts": sess["confirmed_facts"],
        "can_synthesize": can_synthesize,
        "heart_lock_status": sess.get("heart_lock_status", "LOCKED"),
    }


@app.post("/api/session/synthesize")
def synthesize_clues(req: ClueSynthesisRequest):
    """
    Player Clue Synthesis & Escape-Room Heart Lock Deduction (gemini-4-argon, thinking_level='high').
    Cross-references 2+ observed clues with prequel darkroom memory to unlock a Deduced Deep Line.
    """
    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    if len(sess.get("observed_clues", [])) < 2:
        raise HTTPException(status_code=400, detail="단서를 2개 이상 관찰해야 단서 조합 추론이 가능합니다.")

    client = get_gemini_client()
    synthesis = synthesize_clues_with_argon(sess, client=client)
    sess["clue_synthesis"] = synthesis
    sess["heart_lock_status"] = "KEY_FOUND"
    if "clue_synthesis_unlocked" not in sess["confirmed_facts"]:
        sess["confirmed_facts"].append("clue_synthesis_unlocked")

    return {
        "status": "ok",
        "synthesis": synthesis,
        "session": sess,
        "heart_lock_status": sess["heart_lock_status"],
    }


@app.post("/api/session/turn")
async def process_turn(req: TurnRequest, bg_tasks: BackgroundTasks):
    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    current_turn = sess["turn"]
    cp = sess["cast_profile"]
    player_input = req.player_input.strip()

    sess["dialogue_history"].append(
        {
            "speaker": "Player",
            "text_kr": player_input,
        }
    )

    client = get_gemini_client()

    # TURN 1 -> gemini-4-argon (thinking_level="medium")
    if current_turn == 1:
        t1_resp = call_argon_turn1(sess, player_input, client=client)

        sess["dialogue_history"].append(
            {
                "speaker": cp["partner_name"],
                "text_kr": t1_resp["partner_dialogue_kr"],
                "action_kr": t1_resp["subtle_cue_kr"],
                "argon_reasoning_trace": t1_resp.get("argon_reasoning_trace"),
            }
        )
        sess["turn"] = 2
        sess["heart_lock_status"] = t1_resp.get("heart_lock_status", "LOOSENING")

        return {
            "phase": "turn_2",
            "session": sess,
            "turn1_response": t1_resp,
        }

    # TURN 2 -> Final Resolution & Handwritten Postcard Generation
    resolution = call_argon_turn2(sess, player_input, client=client)
    sess["confirmed_facts"].append(f"ending:{resolution.get('ending_type', 'FEELINGS_CONFIRMED')}")
    sess["heart_lock_status"] = resolution.get("heart_lock_status", "UNLOCKED")

    # Lock immutable play_log_snapshot
    snapshot = {
        "session_id": sess["session_id"],
        "player_gender": sess["player_gender"],
        "cast_profile": cp,
        "location_id": sess.get("location_id", "rainy_cafe"),
        "situation_id": sess.get("situation_id", "parting_before_trip"),
        "dialogue_history": sess["dialogue_history"],
        "observed_clues": sess["observed_clues"],
        "confirmed_facts": sess["confirmed_facts"],
        "clue_synthesis": sess.get("clue_synthesis"),
        "resolution": resolution,
    }
    snapshot_bytes = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    snapshot_hash = hashlib.sha256(snapshot_bytes).hexdigest()
    job_id = f"job_{snapshot_hash[:12]}"

    job_dir = JOBS_BASE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    with open(job_dir / "snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    jobs[job_id] = {
        "job_id": job_id,
        "snapshot_hash": snapshot_hash,
        "status": "planning",
        "progress_pct": 10,
        "status_detail": "gemini-4-argon 5-Cut 시네마 베리테 기획 및 자율 연속성 검증 루프 시작...",
        "storyboard_urls": {},
        "preview_mp4_url": None,
        "master_mp4_url": None,
        "verification_log": [],
        "showrunner_checklist": None,
        "created_at": time.time(),
    }

    bg_tasks.add_task(run_progressive_5cut_pipeline, job_id, snapshot, jobs, JOBS_BASE_DIR)

    return {
        "phase": "ending_locked",
        "session": sess,
        "job_id": job_id,
        "snapshot_hash": snapshot_hash,
        "resolution": resolution,
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return job


@app.get("/api/media/{job_id}/{filename}")
def serve_job_media(job_id: str, filename: str):
    file_path = JOBS_BASE_DIR / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="미디어 파일을 찾을 수 없습니다.")
    media_type = "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)


# "MY FILM VAULT (🎞️ 내 필름 보관함)" Archive Endpoints
@app.get("/api/vault")
def get_film_vault():
    records = get_vault_records(JOBS_BASE_DIR)
    return {"total": len(records), "records": records}


@app.delete("/api/vault/{job_id}")
def remove_from_film_vault(job_id: str):
    ok = delete_vault_record(JOBS_BASE_DIR, job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="보관함 기록을 찾을 수 없습니다.")
    return {"status": "ok", "deleted_job_id": job_id}


@app.get("/LoveStory_Final_Master.html")
def serve_master_dashboard():
    for candidate in (
        BASE_DIR / "LoveStory_Final_Master.html",
        BASE_DIR.parent / "LoveStory_Final_Master.html",
        STATIC_DIR / "LoveStory_Final_Master.html",
    ):
        if candidate.exists():
            return FileResponse(candidate, media_type="text/html")
    raise HTTPException(status_code=404, detail="LoveStory_Final_Master.html not found")


# Mount static files cleanly so both /static/* and /* resolve to static/
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="root_static")
