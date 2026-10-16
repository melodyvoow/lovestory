# GEMINI.md — Master Specification for "LoveStory;" (Final Edition)

> **AGENT DIRECTIVE:**
> Build **LoveStory;** for the Google DeepMind AI Hackathon (Track 1: Entertainment).
> We have 4 hours to build and deploy a complete web application on **Google Cloud Run**.
> **Architecture Rule:** Do NOT use Firebase or external SQL databases. Use a single FastAPI backend + responsive frontend + local `ffmpeg` inside one Docker container (`max-instances=1`, `no-cpu-throttling`), storing session/job state and media files in `/tmp/lovestory_jobs/{job_id}/` (with optional Google Cloud Storage bucket backup).

---

## 1. PRODUCT OVERVIEW & WOW POINT
- **Title:** LoveStory;
- **Subtitle:** *Choose the moment of love. The story doesn’t end here.*
- **Core Experience:**
  1. **Dynamic Gender Casting:** Player selects their gender at the start, locking a `cast_profile` (pairing with either **Ijun**, 29yo male photographer, or **Iseo**, 29yo female photographer) so all two-shots, over-the-shoulder shots, and close-ups match the player's identity.
  2. **3-Cut Prequel Video Intro ("The Photographer's Film Roll"):** Plays 3 short video clips (3–4s each) showing their first meeting under a shared umbrella and an old promise in the darkroom to write true feelings on the back of a favorite photo postcard before leaving far away.
  3. **2-Turn Rainy Cafe Gameplay ("10 Minutes Before Closing"):** Players optionally inspect 3 visual clues (`wet_sleeve`, `postcard`, `itinerary`) and interact across 2 dialogue turns (preset choices or free-text input).
  4. **THE WOW POINT — Flipping the Photo Postcard (`3D Card Flip`):** Throughout the game, the player only sees the front/corner of the photo postcard on the table. When Turn 2 ends and the ending is locked, the photo postcard flips over on screen with a smooth 3D CSS animation, revealing a **personalized handwritten confession & P.S. note dynamically written by `gemini-4-argon`** that directly references the exact clues the player noticed and the exact words the player spoke.
  5. **Systematic 5-Cut Short Drama MP4:** Locks `play_log_snapshot` and runs: **5-Cut Continuity Plan (`gemini-4-argon` + Verification Loop) → 5 High-Consistency Storyboards (`gemini-nano-banana-2.1`) + Instant Preview MP4 → Cut-by-Cut 3–10s Video Clips (`gemini-omni-1.1-flash`) → Final FFmpeg Concatenated Master MP4** (ending with the flipped handwritten postcard in Cut 5).

---

## 2. UI / UX LAYOUT DIRECTIVE (CLEAN IMMERSION + TOGGLE MODAL)
- **Pure Service View During Gameplay:** Keep the main interface 100% clean, cinematic, and emotionally immersive (centered 9:16 vertical short-drama stage on a dark cinema backdrop). Do NOT clutter the gameplay screen with debug logs or judge badges.
- **Post-Ending Storyboard Darkroom View:** Only after Turn 2 ends (alongside the 3D Postcard Flip), reveal the **5-Cut Storyboard Filmstrip** developing in real time as `preview.mp4` and `master.mp4` compile.
- **Top-Right Judge Modal (`[🎬 Studio & Architecture]` Button):** Place a sleek button in the top-right header that opens a modal containing:
  1. An interactive HTML/SVG Architecture & Pipeline Diagram (as recommended in the hackathon builder guide).
  2. Live `gemini-4-argon` Continuity Verification Loop logs (showing schema checks, `cast_profile` enforcement, `observed_clues` grounding, and self-correction status).

---

## 3. GOOGLE AI MODELS & STRICT API RULES (INTERACTIONS API)
Use `google-genai` SDK (`>= 2.3.0`) and `client.interactions.create`.
1. **`gemini-4-argon`**: Lead Acting Brain, Handwritten Postcard Writer, 5-Cut Continuity Planner, and Continuity Validator.
   - **STRICT RULE:** NEVER pass deprecated parameters (`temperature`, `top_p`, `top_k`, `thinking_budget`, `cached_content`). ONLY use `generation_config={"thinking_level": "medium"}` (for turn dialogue) or `{"thinking_level": "high"}` (for 5-cut continuity planning & validation).
2. **`gemini-nano-banana-2.1`** (fallback: `gemini-3.1-flash-lite-image`): Generates consistent 9:16 storyboard keyframes using `cast_profile`.
3. **`gemini-omni-1.1-flash`**: Renders each storyboard keyframe into a 3–5s video clip (up to 10s for Cut 3 dialogue) with `background=True` and synchronized rain/ambient sound.

---

## 4. DYNAMIC GENDER CASTING (`cast_profile`)
Lock in session state upon selection and inject into every image/video prompt:
- **Mode A (`player_gender = "female"`):**
  - `partner_name`: `"Ijun"` (이준)
  - `partner_visual`: `"Ijun, 29-year-old handsome Korean male photographer, warm deep expressive eyes, natural comma hair, wearing a dark brown trench coat with a visibly damp left shoulder over a cream knit sweater"`
  - `player_visual`: `"27-year-old Korean female protagonist, soft expressive eyes, natural long dark hair, wearing a warm ivory wool coat"`
- **Mode B (`player_gender = "male"`):**
  - `partner_name`: `"Iseo"` (이서)
  - `partner_visual`: `"Iseo, 29-year-old beautiful Korean female photographer, gentle wistful eyes, soft wavy dark hair, wearing a classic beige trench coat with a visibly damp left shoulder over a warm knit top"`
  - `player_visual`: `"28-year-old Korean male protagonist, clean dandy hairstyle, gentle gaze, wearing a charcoal wool coat over a black turtleneck"`
- **Global Style Suffix:** `"Cinematic K-drama aesthetic, shot on ARRI Alexa, 35mm lens, shallow depth of field, warm tungsten cafe lighting contrasting with rainy night window reflections, photorealistic, 4K, 9:16 vertical composition."`

---

## 5. PREQUEL VIDEO INTRO (3 CUTS, 3–4s EACH, SKIPPABLE)
Provide a helper script/endpoint to pre-generate and cache static prequel clips under `static/prequel/{mode}/cut1.mp4..cut3.mp4` (and fallback keyframes):
- **Cut 1 (First Rain):** Two-shot under a single transparent umbrella on the rainy day they first met; partner holds a vintage camera looking warmly at the player. Subtitle: *"처음 우산을 나눠 썼던 날부터, 내 렌즈가 멈추는 곳은 늘 너였다."*
- **Cut 2 (The Darkroom Promise):** Warm darkroom close-up; partner holds their favorite photo postcard and a fountain pen, hesitating to write on the back. Subtitle: *"언젠가 멀리 떠나게 되는 날, 제일 아끼는 사진 뒤에 진짜 마음을 적어 주겠다고 했었지."*
- **Cut 3 (Tonight, 10 Minutes Before Closing):** Entering the rainy cafe tonight; partner's left shoulder is wet from tilting the umbrella, wiping the player's chair first. Subtitle: *"그리고 내일, 나는 긴 촬영을 떠난다. 오늘 밤 우리는 어떤 마지막 장면을 남기게 될까?"*

---

## 6. MAIN CAFE SCENARIO, 2-TURN ACTING & POSTCARD FLIP
- **Goal:** Confess true feelings and hand over the photo postcard before leaving tomorrow morning.
- **Obstacle:** Fears making the player feel obligated to wait during the long overseas assignment.
- **Opening Line:** `"비 많이 오네… 오늘은 조금 일찍 가봐야 할 것 같아."`
- **3 Optional Clues:**
  1. `wet_sleeve` (젖은 소매): Damp left shoulder from tilting the umbrella toward the player.
  2. `postcard` (만지작거리는 엽서): The darkroom photo print on the table; partner keeps touching its corner.
  3. `itinerary` (여행 일정표): Flight schedule on the table (render a crisp UI overlay: `Departure: Tomorrow 09:30 AM`).
- **State Separation:** Keep `observed_clues` separate from `confirmed_facts`.
- **Turn 2 Resolution & Handwritten Postcard Generation:**
  After Turn 2 input, `gemini-4-argon` outputs:
  1. `ending_type`: `FEELINGS_CONFIRMED` (엽서를 건네며 마음 확인) | `PROMISE_LEFT` (재회의 약속을 남김) | `UNSPOKEN_PARTING` (배려 속에 엽서를 간직한 채 인사).
  2. `partner_final_dialogue` & `physical_action`.
  3. `postcard_back`:
     - `handwritten_body_kr` / `handwritten_body_en`: 2–3 emotional sentences written on the back of the photo postcard matching the story.
     - `ps_note_kr` / `ps_note_en`: A specific P.S. line reacting to what the player noticed (`observed_clues`) and said in Turns 1–2 (e.g., thanking them for noticing the wet sleeve or answering their exact words).
  Lock all of this into an immutable `play_log_snapshot` and trigger the 3D Postcard Flip UI immediately.

---

## 7. 5-CUT VIDEO PIPELINE & AUTONOMOUS VERIFICATION LOOP
Run asynchronously (`idle -> planning -> storyboarding -> rendering_clips -> concatenating -> completed`) keyed by `sha256(play_log_snapshot)`:
1. **5-Cut Continuity Plan (`gemini-4-argon`, `thinking_level="high"`):**
   - `Cut 1 (3–4s)`: Prequel umbrella echo or rainy cafe two-shot intro.
   - `Cut 2 (3–4s)`: Close-up insert of the clue actually present in `observed_clues` (fallback: wet sleeve/rain).
   - `Cut 3 (5–10s)`: Over-the-shoulder or medium two-shot of the pivotal dialogue and emotional reaction (duration 5–10s based on line length).
   - `Cut 4 (4–5s, Climax)`: One decisive physical action matching `ending_type` (hands touching as the photo postcard is handed across the table, or slipping it into the coat pocket).
   - `Cut 5 (3–4s, Epilogue + Postcard Back)`: Lingering final shot transitioning to the flipped handwritten photo postcard (`postcard_back.handwritten_body_kr` + `ps_note_kr`).
2. **Verification Loop:** Check JSON schema, `cast_profile` inclusion in all cuts, zero un-clicked clues in Cut 2, and `3 <= duration_sec <= 10`. If invalid, send the error back to `gemini-4-argon` to self-correct (up to 2 retries) and save logs in `verification_log`.
3. **Storyboards & Instant Preview MP4 (`gemini-nano-banana-2.1` + FFmpeg):** Generate the 5 keyframes, render a styled image card for the handwritten postcard back, and immediately compile `preview.mp4` (with subtitles and gentle zoom) so a complete video is downloadable within seconds.
4. **Omni Video Clips (`gemini-omni-1.1-flash`) & Master MP4:** Convert the storyboard cuts (prioritizing Cut 4 Climax and Cut 3 Dialogue) into 3–10s video clips (`background=True`), then stitch all 5 cuts + subtitles + final handwritten postcard reveal via FFmpeg into `master.mp4` (substituting any timed-out cut with its animated storyboard clip so compilation never fails).