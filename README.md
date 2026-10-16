# LoveStory; — Interactive K-Drama & Autonomous Short-Drama Director
> *"Choose the moment of love. The story doesn’t end here."*  
> **Google DeepMind AI Hackathon (Track 1: Gemini 4 Argon in Entertainment)**

---

## 🌐 Google Cloud Deployment & Links
- **Google Cloud Project ID:** `h2gdm-hack26icn-2725`
- **Google Cloud Run Console:** [https://console.cloud.google.com/run?project=h2gdm-hack26icn-2725](https://console.cloud.google.com/run?project=h2gdm-hack26icn-2725)
- **Google Cloud Dashboard:** [https://console.cloud.google.com/home/dashboard?project=h2gdm-hack26icn-2725](https://console.cloud.google.com/home/dashboard?project=h2gdm-hack26icn-2725)
- **Public GitHub Repository:** [https://github.com/melodyvoow/lovestory](https://github.com/melodyvoow/lovestory)

---

## 1. Project Overview (One-Line Pitch)
**LoveStory;** is an AI-native interactive K-drama web application where players step into a rainy Seoul café 10 minutes before closing, uncover subtle visual clues, converse with an unscripted photographer partner powered by **`gemini-4-argon`**, reveal a personalized 3D handwritten photo postcard, and watch their exact playthrough autonomously compile into a **5-cut vertical short-drama film (`9:16 MP4`)** using **`gemini-nano-banana-2.1`** and **`gemini-omni-1.1-flash`**.

---

## 2. Problem & Impact (Why Entertainment Needs This)
- **The Problem:** Traditional interactive narrative games (FMVs and visual novels) force players and creators into a painful trade-off: choose **pre-recorded video** with rigid, pre-scripted branching, or choose **free-form LLM chat** with static avatars and zero cinematic payoff. Meanwhile, existing generative video workflows suffer from character drift, hallucinated props, and broken scene continuity across multi-shot sequences.
- **Our Solution & Impact:** **LoveStory;** bridges interactive storytelling and generative filmmaking. Using **`gemini-4-argon`** as both the real-time **Lead Acting Brain** and the **Autonomous Showrunner / Continuity Director**, every subtle clue a player inspects and every word they speak is grounded into an immutable `play_log_snapshot`, verified through a deterministic **Continuity Verification Loop**, and rendered into a shareable K-drama short film where character identities, wardrobe, observed props, and emotional arcs remain 100% consistent.

---

## 3. Core Experience & "Wow" Moments
1. **Dynamic Gender Casting (`cast_profile`):** At the start, players choose their protagonist identity, locking a unified visual casting sheet paired with either **Ijun** (29yo male photographer) or **Iseo** (29yo female photographer) that persists across every two-shot, over-the-shoulder shot, and close-up.
2. **3-Cut Prequel Video Intro ("The Photographer's Film Roll"):** Sets the emotional stakes with 3 short prequel cuts—their first meeting under a shared umbrella in the rain, an old darkroom promise to write true feelings on the back of a favorite photo postcard before leaving far away, and entering the café tonight 10 minutes before closing.
3. **2-Turn Rainy Café Gameplay & Clue Grounding:** Players optionally inspect 3 environmental clues on stage—**`wet_sleeve`** (damp left shoulder from tilting the umbrella toward the player), **`postcard`** (the darkroom photo print being nervously touched), and **`itinerary`** (a tomorrow `09:30 AM` departure schedule)—while conversing freely or via curated dialogue choices across 2 intense turns.
4. **THE WOW POINT — 3D Handwritten Photo Postcard Flip:** Throughout gameplay, only the front corner of the photo postcard is visible. When Turn 2 resolves into one of three distinct endings (`FEELINGS_CONFIRMED`, `PROMISE_LEFT`, or `UNSPOKEN_PARTING`), the postcard flips over with a smooth 3D CSS animation to reveal a **bilingual handwritten confession and personalized `P.S.` note** dynamically authored by `gemini-4-argon`, directly referencing the exact clues the player noticed and the exact words they spoke.
5. **Post-Ending Darkroom & 5-Cut Short-Drama MP4 Compilation:** Alongside the postcard flip, a **5-Cut Storyboard Filmstrip** develops in real time. An instant `preview.mp4` is compiled within seconds, followed by a fully voiced/ambient `master.mp4` stitched from `gemini-omni-1.1-flash` video clips ending on the flipped handwritten postcard.

---

## 4. How We Use Google AI Models (Interactions API)

Built on the `google-genai` SDK (`>= 2.3.0`) using `client.interactions.create`:

| Role in Application | Model ID | Key Configuration & Responsibility |
| :--- | :--- | :--- |
| **Lead Acting Brain & Handwritten Postcard Writer** | `gemini-4-argon` | `thinking_level="medium"` via Interactions API. Roleplays Ijun/Iseo in real time, tracks `observed_clues` vs. `confirmed_facts`, determines the ending branch, and writes the personalized handwritten postcard + `P.S.` note. |
| **5-Cut Continuity Planner & Self-Correcting Validator** | `gemini-4-argon` | `thinking_level="high"` via Interactions API. Synthesizes `play_log_snapshot` into a 5-cut directorial plan (camera angles, blocking, prompts, durations) and executes an **Autonomous Verification Loop** (up to 2 self-correction retries). |
| **Consistent 9:16 Storyboard Keyframes** | `gemini-nano-banana-2.1` | Generates high-consistency vertical (`9:16`) K-drama storyboard frames across all 5 cuts by injecting the locked `cast_profile` and global ARRI Alexa 35mm visual style suffix. (Fallback: `gemini-3.1-flash-lite-image`). |
| **Cut-by-Cut Cinematic Video & Native Audio** | `gemini-omni-1.1-flash` | `background=True` via Interactions API. Animates storyboard keyframes into 3–10s cinematic video clips with synchronized rain and café ambience. |

---

## 5. Autonomous Verification Loop & Multimodal Architecture
Located in the top-right **`[🎬 Studio & Architecture]` Judge Modal**, judges can inspect our live system architecture and verification telemetry in real time:
- **Strict Grounding & Continuity Verification Loop:** Before any image or video model is called, our verifier checks `gemini-4-argon`'s 5-cut plan against four hard constraints:
  1. **Schema & 5-Cut Structure Integrity:** Exact 5-cut arc (`Cut 1: Intro Echo` → `Cut 2: Clue Insert` → `Cut 3: Pivotal Dialogue` → `Cut 4: Climax Action` → `Cut 5: Epilogue & Postcard Reveal`).
  2. **Cast Profile Enforcement:** Verifies that `partner_visual` and `player_visual` descriptors are explicitly embedded in every cut to eliminate character drift.
  3. **Zero Un-Clicked Clue Hallucination:** Verifies that `Cut 2` only features props present in `observed_clues` (never referencing uninspected clues).
  4. **Duration Bounds:** Enforces `3 <= duration_sec <= 10` per cut.
  - *Self-Correction:* Any violation is fed back to `gemini-4-argon` (`thinking_level="high"`) for autonomous repair and logged live in `verification_log`.
- **Two-Stage Fault-Tolerant Video Compilation (`preview.mp4` → `master.mp4`):**
  - **Stage 1 (Instant Gratification):** Compiles the 5 `gemini-nano-banana-2.1` keyframes + styled handwritten postcard card + subtitles via `ffmpeg` into `preview.mp4` in seconds.
  - **Stage 2 (Master Film):** Renders `gemini-omni-1.1-flash` video cuts asynchronously (`background=True`) and stitches `master.mp4`, gracefully substituting any timed-out cut with its animated storyboard clip so live demos never fail.

---

## 6. Quick Start (Local) & Google Cloud Run Deployment

### Local Quick Start
```bash
cd lovestory
cp .env.example .env
# Set GEMINI_API_KEY in .env
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Deploy to Google Cloud Run
Designed as a single stateless/ephemeral container (`FastAPI` + responsive frontend + local `ffmpeg`, storing job state in `/tmp/lovestory_jobs/{job_id}/`):
```bash
gcloud config set project h2gdm-hack26icn-2725
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --quiet
gcloud run deploy lovestory \
  --source . \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --max-instances 1 \
  --no-cpu-throttling \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --set-env-vars GEMINI_API_KEY="YOUR_API_KEY"
```
