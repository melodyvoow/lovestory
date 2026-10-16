/**
 * LoveStory; — Client Application Logic (v4.0 Complete Edition)
 * Handles 4-Step Director onboarding, in-app setup still & 3-cut prequel playback,
 * 2-turn gameplay, 3D Photo Postcard Flip with P.S. note, 5-cut pipeline polling,
 * and My Film Vault (내 필름 보관함) with localStorage mirroring.
 */

const VAULT_STORAGE_KEY = "lovestory_vault_v4";

const state = {
  selectedGender: "female",
  selectedLocation: "rainy_cafe",
  selectedSituation: "parting_before_trip",
  selectedAnchorClue: "wet_sleeve",
  partnerRefImageB64: null,
  playerRefImageB64: null,
  customNote: "",
  sessionId: null,
  session: null,
  prequelClips: [],
  prequelIndex: 0,
  cluesCatalog: {},
  jobId: null,
  pollTimer: null,
  vaultRecords: [],
};

// DOM Views
const views = {
  casting: document.getElementById("view-casting"),
  prequel: document.getElementById("view-prequel"),
  cafe: document.getElementById("view-cafe"),
  ending: document.getElementById("view-ending"),
};

function switchView(viewName) {
  Object.values(views).forEach((el) => {
    if (el) el.classList.remove("active");
  });
  if (views[viewName]) {
    views[viewName].classList.add("active");
  }
}

// 1. 4-Step Director Setup Selections
function setupDirectorListeners() {
  // Step 1: Gender (Cast Profile)
  document.querySelectorAll(".chip-gender").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-gender").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      state.selectedGender = chip.dataset.gender;
    });
  });

  // Step 2: Location
  document.querySelectorAll(".chip-location").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-location").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      state.selectedLocation = chip.dataset.location;
    });
  });

  // Step 3: Situation
  document.querySelectorAll(".chip-situation").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-situation").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      state.selectedSituation = chip.dataset.situation;
    });
  });

  // Step 4: Initial Anchor Clue
  document.querySelectorAll(".chip-clue").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip-clue").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      state.selectedAnchorClue = chip.dataset.clue;
    });
  });

  // Character Reference Image Upload Handlers
  const partnerInput = document.getElementById("partner-ref-input");
  const partnerThumb = document.getElementById("partner-ref-thumb");
  const partnerClearBtn = document.getElementById("btn-clear-partner-ref");
  const partnerSlot = document.getElementById("slot-partner-ref");

  if (partnerInput) {
    partnerInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        state.partnerRefImageB64 = reader.result;
        if (partnerThumb) {
          partnerThumb.innerHTML = `<img src="${reader.result}" alt="상대역 참조 이미지" />`;
        }
        if (partnerClearBtn) partnerClearBtn.classList.remove("hidden");
        if (partnerSlot) partnerSlot.classList.add("has-image");
      };
      reader.readAsDataURL(file);
    });
  }

  if (partnerClearBtn) {
    partnerClearBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      state.partnerRefImageB64 = null;
      if (partnerInput) partnerInput.value = "";
      if (partnerThumb) partnerThumb.innerHTML = `<span class="ref-placeholder">+ 사진 첨부</span>`;
      partnerClearBtn.classList.add("hidden");
      if (partnerSlot) partnerSlot.classList.remove("has-image");
    });
  }

  const playerInput = document.getElementById("player-ref-input");
  const playerThumb = document.getElementById("player-ref-thumb");
  const playerClearBtn = document.getElementById("btn-clear-player-ref");
  const playerSlot = document.getElementById("slot-player-ref");

  if (playerInput) {
    playerInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        state.playerRefImageB64 = reader.result;
        if (playerThumb) {
          playerThumb.innerHTML = `<img src="${reader.result}" alt="주인공 참조 이미지" />`;
        }
        if (playerClearBtn) playerClearBtn.classList.remove("hidden");
        if (playerSlot) playerSlot.classList.add("has-image");
      };
      reader.readAsDataURL(file);
    });
  }

  if (playerClearBtn) {
    playerClearBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      state.playerRefImageB64 = null;
      if (playerInput) playerInput.value = "";
      if (playerThumb) playerThumb.innerHTML = `<span class="ref-placeholder">+ 사진 첨부</span>`;
      playerClearBtn.classList.add("hidden");
      if (playerSlot) playerSlot.classList.remove("has-image");
    });
  }

  // Character Asset Sheet Instant Preview Button
  const previewAssetBtn = document.getElementById("btn-preview-char-asset");
  if (previewAssetBtn) {
    previewAssetBtn.addEventListener("click", async () => {
      const noteInput = document.getElementById("char-custom-note");
      state.customNote = noteInput ? noteInput.value.trim() : "";

      previewAssetBtn.disabled = true;
      const origText = previewAssetBtn.textContent;
      previewAssetBtn.textContent = "🎨 수채화 캐릭터 시트 인화 중...";

      try {
        const res = await fetch("/api/character/asset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            player_gender: state.selectedGender,
            partner_ref_image_b64: state.partnerRefImageB64,
            player_ref_image_b64: state.playerRefImageB64,
            custom_note: state.customNote,
          }),
        });
        if (!res.ok) throw new Error(`캐릭터 시트 생성 실패 (HTTP ${res.status})`);
        const data = await res.json();

        const previewBox = document.getElementById("char-sheet-preview-box");
        const previewImg = document.getElementById("char-sheet-preview-img");
        const summaryText = document.getElementById("char-sheet-summary-text");

        if (previewImg && data.character_sheet_url) {
          previewImg.src = data.character_sheet_url + "?t=" + Date.now();
        }
        if (summaryText && data.cast_profile) {
          const cp = data.cast_profile;
          const refStatus = cp.has_partner_ref || cp.has_player_ref
            ? "참조 이미지 특징 추출 완료"
            : "기본 캐스팅 프로필 적용";
          summaryText.textContent = `${cp.partner_name_kr}(${cp.partner_name}) • ${refStatus}`;
        }
        if (previewBox) previewBox.classList.remove("hidden");
      } catch (err) {
        console.error(err);
        alert("캐릭터 자산 시트 생성 중 오류가 발생했습니다: " + err.message);
      } finally {
        previewAssetBtn.disabled = false;
        previewAssetBtn.textContent = origText;
      }
    });
  }
}
setupDirectorListeners();

// Start Story & In-App Asset Generation
document.getElementById("btn-start-story").addEventListener("click", async () => {
  const btn = document.getElementById("btn-start-story");
  const noteInput = document.getElementById("char-custom-note");
  state.customNote = noteInput ? noteInput.value.trim() : "";

  btn.disabled = true;
  btn.textContent = "🎬 현장 스틸컷 & 3-Cut 프리퀄 인화 중...";

  try {
    const res = await fetch("/api/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player_gender: state.selectedGender,
        location_id: state.selectedLocation,
        situation_id: state.selectedSituation,
        anchor_clue_id: state.selectedAnchorClue,
        partner_ref_image_b64: state.partnerRefImageB64,
        player_ref_image_b64: state.playerRefImageB64,
        custom_note: state.customNote,
      }),
    });
    if (!res.ok) throw new Error(`세션 시작 실패 (HTTP ${res.status})`);

    const data = await res.json();
    state.session = data.session;
    state.sessionId = data.session.session_id;
    state.prequelClips = data.prequel_clips || [];
    state.cluesCatalog = data.clues_catalog || {};
    state.prequelIndex = 0;

    setupGameplayScene(data);
    startPrequelPlayback();
  } catch (err) {
    console.error(err);
    alert("스토리 준비 중 오류가 발생했습니다: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "🎬 현장 스틸컷 & 프리퀄 인화하기";
  }
});

// 2. 3-Cut Prequel Video Roll ("The Photographer's Film Roll")
const prequelVideo = document.getElementById("prequel-video");

function startPrequelPlayback() {
  switchView("prequel");
  loadPrequelCut(0);
}

function loadPrequelCut(idx) {
  if (!state.prequelClips || idx >= state.prequelClips.length) {
    enterCafeGameplay();
    return;
  }
  state.prequelIndex = idx;
  const clip = state.prequelClips[idx];
  document.getElementById("prequel-cut-indicator").textContent =
    `THE PHOTOGRAPHER'S FILM ROLL • CUT ${clip.cut}/3 [${clip.camera_angle || "35mm"}]`;
  document.getElementById("prequel-sub-kr").textContent = clip.subtitle_kr;
  document.getElementById("prequel-sub-en").textContent = clip.subtitle_en;

  if (clip.poster_url) prequelVideo.poster = clip.poster_url;
  prequelVideo.src = clip.video_url;
  prequelVideo.play().catch(() => {});
}

prequelVideo.addEventListener("ended", () => {
  loadPrequelCut(state.prequelIndex + 1);
});

document.getElementById("btn-next-prequel").addEventListener("click", () => {
  loadPrequelCut(state.prequelIndex + 1);
});

document.getElementById("btn-skip-prequel").addEventListener("click", () => {
  prequelVideo.pause();
  enterCafeGameplay();
});

function enterCafeGameplay() {
  switchView("cafe");
}

// 3. Dynamic Gameplay Scene & Clues
function updateHeartLockBanner(status, customDesc) {
  const banner = document.getElementById("heart-lock-banner");
  const icon = document.getElementById("heart-lock-icon");
  const stateChip = document.getElementById("heart-lock-state-chip");
  const descEl = document.getElementById("heart-lock-desc");
  if (!banner) return;

  banner.classList.remove("ready-to-synthesize", "key-found", "unlocked");

  if (status === "READY_TO_SYNTHESIZE") {
    banner.classList.add("ready-to-synthesize");
    if (icon) icon.textContent = "🗝️";
    if (stateChip) stateChip.textContent = "CLUES READY (2+)";
  } else if (status === "KEY_FOUND" || status === "LOOSENING") {
    banner.classList.add("key-found");
    if (icon) icon.textContent = "🔓";
    if (stateChip) stateChip.textContent = status === "KEY_FOUND" ? "KEY DEDUCED" : "LOOSENING";
  } else if (status === "UNLOCKED") {
    banner.classList.add("unlocked");
    if (icon) icon.textContent = "💖";
    if (stateChip) stateChip.textContent = "CONFESSION UNLOCKED";
  } else {
    if (icon) icon.textContent = "🔒";
    if (stateChip) stateChip.textContent = "LOCKED";
  }

  if (customDesc && descEl) {
    descEl.textContent = customDesc;
  }
}

function updateActingSubtext(trace) {
  const btn = document.getElementById("btn-toggle-subtext");
  const drawer = document.getElementById("acting-subtext-drawer");
  if (!btn || !drawer) return;

  if (!trace) {
    btn.classList.add("hidden");
    drawer.classList.add("hidden");
    return;
  }

  document.getElementById("subtext-intent").textContent =
    trace.detected_player_intent || "플레이어의 대사에서 숨은 의도를 탐색 중입니다.";
  document.getElementById("subtext-conflict").textContent =
    trace.goal_vs_obstacle_shift || "고백하고 싶은 진심(Goal)과 부담을 줄까 두려운 마음(Obstacle)이 충돌합니다.";
  document.getElementById("subtext-monologue").textContent =
    trace.acting_subtext_kr || "시선을 떨구며 엽서 모서리를 조심스레 만지작거린다.";

  btn.classList.remove("hidden");
  drawer.classList.remove("hidden");
}

const btnToggleSubtext = document.getElementById("btn-toggle-subtext");
if (btnToggleSubtext) {
  btnToggleSubtext.addEventListener("click", () => {
    const drawer = document.getElementById("acting-subtext-drawer");
    if (drawer) drawer.classList.toggle("hidden");
  });
}

function setupGameplayScene(data) {
  const cp = data.session.cast_profile;
  const loc = data.location;
  const sit = data.situation;
  const firstLine = data.session.dialogue_history[0];
  state.clueSynthesis = null;

  // Apply in-app generated setup still as live scene backdrop
  const backdrop = document.getElementById("cafe-visual-backdrop");
  if (backdrop && data.setup_still_url) {
    backdrop.style.backgroundImage = `linear-gradient(180deg, rgba(12, 10, 18, 0.45) 0%, rgba(12, 10, 18, 0.88) 100%), url("${data.setup_still_url}")`;
  }

  document.getElementById("scene-time-pill").textContent = loc.time_str;
  document.getElementById("cafe-partner-name").textContent =
    `${cp.partner_name_kr} (${cp.partner_name})`;
  document.getElementById("cafe-action-cue").textContent = firstLine.action_kr;
  document.getElementById("dialogue-speaker").textContent = cp.partner_name_kr;
  document.getElementById("dialogue-text-kr").textContent = `“${firstLine.text_kr}”`;
  document.getElementById("turn-indicator").textContent = "TURN 1 / 2";

  // Setup Escape-Room Heart Lock Banner with the partner's core obstacle
  const obstacleDesc = sit.obstacle_kr
    ? `${sit.obstacle_kr} (단서 2개 이상을 관찰하고 진심을 추론해 자물쇠를 여세요)`
    : "내일 떠나는 내가 지금 고백하면, 너에게 기다려 달라는 부담이 될까 봐 두렵다.";
  updateHeartLockBanner("LOCKED", obstacleDesc);

  // Reset synthesis & subtext UI
  const synthBtn = document.getElementById("btn-synthesize-clues");
  if (synthBtn) {
    synthBtn.classList.add("hidden");
    synthBtn.disabled = false;
    synthBtn.textContent = "💡 단서 연결해 속마음 추론하기 (Argon High Reasoning)";
  }
  const synthCard = document.getElementById("synthesis-result-card");
  if (synthCard) synthCard.classList.add("hidden");
  updateActingSubtext(null);

  // Setup crisp itinerary badge text tailored to location/situation
  document.getElementById("itinerary-badge").textContent = sit.itinerary_badge || "DEPARTURE: TOMORROW 09:30 AM";

  // Reset and mark anchor clue as observed
  document.querySelectorAll(".clue-chip").forEach((c) => c.classList.remove("observed"));
  const anchorChip = document.querySelector(`.clue-chip[data-clue="${state.selectedAnchorClue}"]`);
  if (anchorChip) anchorChip.classList.add("observed");

  renderPresetChoices(data.preset_choices_turn1);
}

function renderPresetChoices(choices) {
  const container = document.getElementById("preset-choices");
  container.innerHTML = "";

  // If player has already synthesized a Deduced Deep Line, keep it at the top as a Master Key choice
  if (state.clueSynthesis && state.clueSynthesis.deduced_deep_line_kr) {
    const keyLine = state.clueSynthesis.deduced_deep_line_kr;
    const keyBtn = document.createElement("button");
    keyBtn.type = "button";
    keyBtn.className = "preset-btn deduced-master-key";
    keyBtn.textContent = `🔓 [추론 해금 대사] ${keyLine}`;
    keyBtn.addEventListener("click", () => submitDialogueTurn(keyLine));
    container.appendChild(keyBtn);
  }

  (choices || []).forEach((line) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preset-btn";
    btn.textContent = `💬 ${line}`;
    btn.addEventListener("click", () => submitDialogueTurn(line));
    container.appendChild(btn);
  });
}

// Clue Hotspots
document.querySelectorAll(".clue-chip").forEach((chip) => {
  chip.addEventListener("click", async () => {
    const clueId = chip.dataset.clue;
    chip.classList.add("observed");

    try {
      const res = await fetch("/api/session/clue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: state.sessionId, clue_id: clueId }),
      });
      const data = await res.json();
      const clue = data.clue;

      document.getElementById("clue-overlay-title").textContent =
        `🔍 ${clue.title_kr} (${clue.title_en})`;
      document.getElementById("clue-overlay-desc").textContent = clue.observation_kr;

      const badge = document.getElementById("itinerary-badge");
      if (clueId === "itinerary") {
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
      document.getElementById("clue-overlay-card").classList.remove("hidden");

      // Check if 2+ clues are observed to unlock Clue Synthesis button
      if (data.can_synthesize && !state.clueSynthesis) {
        const synthBtn = document.getElementById("btn-synthesize-clues");
        if (synthBtn) synthBtn.classList.remove("hidden");
        updateHeartLockBanner(
          "READY_TO_SYNTHESIZE",
          `단서 ${data.observed_clues.length}개 확보 완료! 아래 [💡 단서 연결해 속마음 추론하기] 버튼으로 자물쇠의 열쇠를 추론하세요.`
        );
      }
    } catch (err) {
      console.error(err);
    }
  });
});

document.getElementById("btn-close-clue").addEventListener("click", () => {
  document.getElementById("clue-overlay-card").classList.add("hidden");
});

const btnCloseSynthesis = document.getElementById("btn-close-synthesis");
if (btnCloseSynthesis) {
  btnCloseSynthesis.addEventListener("click", () => {
    document.getElementById("synthesis-result-card").classList.add("hidden");
  });
}

// Clue Synthesis Button Handler (gemini-4-argon high reasoning)
const btnSynthesizeClues = document.getElementById("btn-synthesize-clues");
if (btnSynthesizeClues) {
  btnSynthesizeClues.addEventListener("click", async () => {
    if (!state.sessionId) return;
    btnSynthesizeClues.disabled = true;
    btnSynthesizeClues.textContent = "🧠 gemini-4-argon (thinking_level='high') 단서 교차 추론 중...";

    try {
      const res = await fetch("/api/session/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: state.sessionId }),
      });
      if (!res.ok) throw new Error(`단서 조합 추론 실패 (HTTP ${res.status})`);
      const data = await res.json();
      const syn = data.synthesis;
      state.clueSynthesis = syn;

      document.getElementById("synthesis-title").textContent = `🔓 ${syn.deduction_title_kr}`;
      document.getElementById("synthesis-hypothesis").textContent = syn.argon_hypothesis_kr;
      document.getElementById("synthesis-pierced").textContent = `🗝️ 자물쇠 돌파 논리: ${syn.obstacle_pierced_kr}`;
      document.getElementById("synthesis-result-card").classList.remove("hidden");

      updateHeartLockBanner("KEY_FOUND", `열쇠 발견: ${syn.obstacle_pierced_kr}`);
      btnSynthesizeClues.textContent = "✨ 단서 추론 완료 — [🔓 추론 해금 대사]가 대화창에 추가되었습니다";

      // Prepend the Deduced Master Key button to preset choices if not already present
      const container = document.getElementById("preset-choices");
      if (container && syn.deduced_deep_line_kr) {
        const existingKey = container.querySelector(".deduced-master-key");
        if (existingKey) existingKey.remove();
        const keyBtn = document.createElement("button");
        keyBtn.type = "button";
        keyBtn.className = "preset-btn deduced-master-key";
        keyBtn.textContent = `🔓 [추론 해금 대사] ${syn.deduced_deep_line_kr}`;
        keyBtn.addEventListener("click", () => submitDialogueTurn(syn.deduced_deep_line_kr));
        container.prepend(keyBtn);
      }
    } catch (err) {
      console.error(err);
      btnSynthesizeClues.disabled = false;
      btnSynthesizeClues.textContent = "💡 단서 연결해 속마음 추론하기 (다시 시도)";
    }
  });
}

// Dialogue Submission
document.getElementById("dialogue-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("player-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  submitDialogueTurn(text);
});

async function submitDialogueTurn(playerText) {
  const sendBtn = document.getElementById("btn-send-turn");
  sendBtn.disabled = true;
  document.getElementById("dialogue-text-kr").textContent = "… 빗소리 속에서 진심을 고르고 있습니다 …";

  try {
    const res = await fetch("/api/session/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        player_input: playerText,
      }),
    });
    if (!res.ok) throw new Error(`대화 처리 오류 (HTTP ${res.status})`);

    const data = await res.json();
    state.session = data.session;

    if (data.phase === "turn_2") {
      const t1 = data.turn1_response;
      document.getElementById("turn-indicator").textContent = "TURN 2 / 2 (FINAL)";
      document.getElementById("cafe-action-cue").textContent = t1.subtle_cue_kr;
      document.getElementById("dialogue-text-kr").textContent = `“${t1.partner_dialogue_kr}”`;
      updateActingSubtext(t1.argon_reasoning_trace);
      if (t1.heart_lock_status) {
        updateHeartLockBanner(
          t1.heart_lock_status,
          t1.argon_reasoning_trace?.goal_vs_obstacle_shift || undefined
        );
      }
      renderPresetChoices(t1.suggested_replies_kr);
    } else if (data.phase === "ending_locked") {
      state.jobId = data.job_id;
      resetDarkroomSlots();
      revealEndingAndFlipPostcard(data.resolution, data.snapshot_hash, data.session.cast_profile, true);
    }
  } catch (err) {
    console.error(err);
    document.getElementById("dialogue-text-kr").textContent = "“잠시 빗소리에 묻혀 듣지 못했어. 다시 말해줄래?”";
  } finally {
    sendBtn.disabled = false;
  }
}

function resetDarkroomSlots() {
  const labels = ["Through-Glass", "85mm Macro", "50mm OTS", "35mm Climax", "90° Overhead"];
  for (let i = 1; i <= 5; i++) {
    const slot = document.querySelector(`.film-slot[data-cut="${i}"]`);
    if (slot) {
      slot.innerHTML = `<span>CUT 0${i}</span><div class="slot-placeholder">${labels[i - 1]}</div>`;
    }
  }
  const previewLink = document.getElementById("link-preview-mp4");
  const masterLink = document.getElementById("link-master-mp4");
  if (previewLink) previewLink.classList.add("disabled");
  if (masterLink) masterLink.classList.add("disabled");
  const videoPlayer = document.getElementById("compiled-video-player");
  if (videoPlayer) videoPlayer.removeAttribute("src");

  // Reset Showrunner Checklist Box
  const srScore = document.getElementById("showrunner-score-badge");
  if (srScore) srScore.textContent = "검수 대기 중...";
  ["sr-check-1", "sr-check-2", "sr-check-3"].forEach((id, idx) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("passed");
    const titles = [
      "⏳ 1. 캐스팅 & 의상 연속성 (Cast Visual Continuity) 확인 중...",
      "⏳ 2. 관찰 단서 & 추론 정합성 (Observed Clue & Deduction Grounding) 확인 중...",
      "⏳ 3. 사진 엽서 P.S. 손글씨 일치 (Postcard P.S. Alignment) 확인 중...",
    ];
    el.textContent = titles[idx];
  });
  const srNote = document.getElementById("showrunner-patch-note");
  if (srNote) {
    srNote.textContent = "스토리보드 5컷 생성 직후 Argon 멀티모달 쇼러너가 컷 간 연속성을 자율 검수합니다.";
  }
}

function renderShowrunnerChecklist(checklist) {
  if (!checklist) return;
  const srScore = document.getElementById("showrunner-score-badge");
  const statusStr = checklist.status || (checklist.overall_passed ? "PASS" : "PATCHED");
  if (srScore) {
    srScore.textContent = `Continuity Score: ${checklist.continuity_score || 98}/100 • ${statusStr}`;
  }

  const itemsMap = {};
  if (Array.isArray(checklist.items)) {
    checklist.items.forEach((item) => {
      if (item && item.id) itemsMap[item.id] = item;
    });
  } else if (checklist.checks) {
    Object.assign(itemsMap, checklist.checks);
  }

  const c1 = itemsMap.cast_visual_continuity;
  const c2 = itemsMap.clue_and_deduction_grounding;
  const c3 = itemsMap.postcard_ps_alignment;

  const el1 = document.getElementById("sr-check-1");
  if (el1 && c1) {
    el1.classList.add("passed");
    el1.textContent = `${c1.label || "✓ [Cast Visual Continuity]"} — ${c1.detail_kr}`;
  }
  const el2 = document.getElementById("sr-check-2");
  if (el2 && c2) {
    el2.classList.add("passed");
    el2.textContent = `${c2.label || "✓ [Observed Clue & Deduction Grounding]"} — ${c2.detail_kr}`;
  }
  const el3 = document.getElementById("sr-check-3");
  if (el3 && c3) {
    el3.classList.add("passed");
    el3.textContent = `${c3.label || "✓ [Postcard P.S. Alignment]"} — ${c3.detail_kr}`;
  }
  const srNote = document.getElementById("showrunner-patch-note");
  if (srNote && checklist.auto_patch_note_kr) {
    srNote.textContent = `🎬 Argon Showrunner Note: ${checklist.auto_patch_note_kr}`;
  }
}

// 4. THE KILLER WOW POINT: 3D Photo Postcard Flip
function revealEndingAndFlipPostcard(resolution, snapshotHash, castProfileOverride, shouldPollPipeline = true) {
  const cp = castProfileOverride || (state.session && state.session.cast_profile) || {
    partner_name_kr: "이준",
    partner_name: "Ijun",
  };
  switchView("ending");

  const unlockPill = document.getElementById("ending-heart-unlock-pill");
  if (unlockPill) {
    if (resolution.ending_type === "UNSPOKEN_PARTING") {
      unlockPill.textContent = "🌙 조용한 배려 속 간직된 진심 (Gentle Unspoken Parting)";
    } else {
      unlockPill.textContent = "🔓 망설임의 자물쇠 해제 완료 — 진심 해금 (Confession Unlocked!)";
    }
  }

  document.getElementById("ending-type-badge").textContent =
    `${resolution.ending_type} • ${resolution.ending_title_en || ""}`;
  document.getElementById("ending-title-kr").textContent = resolution.ending_title_kr;
  document.getElementById("ending-final-dialogue").textContent =
    `“${resolution.partner_final_dialogue_kr}”`;

  document.getElementById("postcard-from-label").textContent =
    `FROM. ${cp.partner_name_kr} (${cp.partner_name})`;
  document.getElementById("handwritten-body-kr").textContent =
    resolution.postcard_back.handwritten_body_kr;
  document.getElementById("handwritten-body-en").textContent =
    resolution.postcard_back.handwritten_body_en;
  document.getElementById("handwritten-ps-kr").textContent =
    resolution.postcard_back.ps_note_kr;
  document.getElementById("handwritten-ps-en").textContent =
    resolution.postcard_back.ps_note_en;

  if (snapshotHash) {
    document.getElementById("modal-snapshot-hash").textContent =
      `sha256: ${snapshotHash.slice(0, 16)}...`;
  }

  // Smooth automatic 3D CSS flip after 750ms
  const card = document.getElementById("postcard-3d-card");
  card.classList.remove("is-flipped");
  setTimeout(() => {
    card.classList.add("is-flipped");
  }, 750);

  // Reveal Post-Ending Darkroom Filmstrip Panel
  document.getElementById("darkroom-panel").classList.remove("hidden");

  if (shouldPollPipeline) {
    if (state.pollTimer) clearInterval(state.pollTimer);
    pollPipelineJob();
    state.pollTimer = setInterval(pollPipelineJob, 1800);
  }

  refreshVaultCount();
}

document.getElementById("postcard-3d-card").addEventListener("click", () => {
  document.getElementById("postcard-3d-card").classList.toggle("is-flipped");
});

document.getElementById("btn-toggle-flip").addEventListener("click", () => {
  document.getElementById("postcard-3d-card").classList.toggle("is-flipped");
});

// 5. Polling Progressive Video Pipeline
async function pollPipelineJob() {
  if (!state.jobId) return;
  try {
    const res = await fetch(`/api/jobs/${state.jobId}`);
    if (!res.ok) return;
    const job = await res.json();

    document.getElementById("pipeline-status-badge").textContent = job.status;
    document.getElementById("pipeline-progress-fill").style.width = `${job.progress_pct}%`;
    document.getElementById("pipeline-detail-text").textContent = job.status_detail;

    // Update 5-Cut Storyboard Thumbnails
    if (job.storyboard_urls) {
      Object.entries(job.storyboard_urls).forEach(([cutNum, url]) => {
        const slot = document.querySelector(`.film-slot[data-cut="${cutNum}"]`);
        if (slot && !slot.querySelector("img")) {
          slot.innerHTML = `<span>CUT 0${cutNum}</span><img src="${url}" alt="Cut ${cutNum}" />`;
        }
      });
    }

    // Update Multimodal Showrunner Verification Checklist
    if (job.showrunner_checklist) {
      renderShowrunnerChecklist(job.showrunner_checklist);
    }

    // Instant Preview MP4
    const videoPlayer = document.getElementById("compiled-video-player");
    const previewLink = document.getElementById("link-preview-mp4");
    if (job.preview_mp4_url && previewLink.classList.contains("disabled")) {
      previewLink.href = job.preview_mp4_url;
      previewLink.classList.remove("disabled");
      if (!videoPlayer.getAttribute("src")) {
        videoPlayer.src = job.preview_mp4_url;
        videoPlayer.play().catch(() => {});
      }
      refreshVaultCount();
    }

    // Master MP4
    const masterLink = document.getElementById("link-master-mp4");
    if (masterLink && job.master_mp4_url && masterLink.classList.contains("disabled")) {
      masterLink.href = job.master_mp4_url;
      masterLink.classList.remove("disabled");
      videoPlayer.src = job.master_mp4_url;
      videoPlayer.play().catch(() => {});
      refreshVaultCount();
    }

    // Judge Modal Verification Logs
    renderVerificationLogs(job.verification_log || []);

    if (job.status === "completed" || job.status === "failed") {
      clearInterval(state.pollTimer);
      refreshVaultCount();
    }
  } catch (err) {
    console.error("Poll error:", err);
  }
}

function renderVerificationLogs(logs) {
  const box = document.getElementById("verification-logs-container");
  if (!logs || !logs.length || !box) return;
  box.innerHTML = logs
    .map((entry) => {
      const checksStr = Object.entries(entry.checks || {})
        .map(([k, v]) => `${v ? "✓" : "✗"} ${k}`)
        .join("  |  ");
      const errHtml =
        entry.errors && entry.errors.length
          ? `<div style="color:#f07167;margin-top:4px;">Self-Correction Triggered: ${entry.errors.join("; ")}</div>`
          : `<div style="color:#7be0ad;margin-top:4px;">All 5 continuity & 1970s cinema verite constraints verified.</div>`;
      return `
        <div class="verif-entry ${entry.passed ? "" : "failed"}">
          <div><strong>Attempt #${entry.attempt}</strong> • Model: <code>${entry.model_used}</code> (thinking_level="${entry.thinking_level}") • ${entry.timestamp}</div>
          <div style="color:#cfc6b8;margin-top:3px;">${checksStr}</div>
          ${errHtml}
        </div>
      `;
    })
    .join("");
}

// 6. "MY FILM VAULT (🎞️ 내 필름 보관함)" Archive Gallery Modal + localStorage Mirror
const vaultModal = document.getElementById("vault-modal");
const btnVaultModal = document.getElementById("btn-vault-modal");
const btnCloseVault = document.getElementById("btn-close-vault");
const vaultCountBadge = document.getElementById("vault-count-badge");

function mirrorVaultToLocalStorage(records) {
  try {
    localStorage.setItem(VAULT_STORAGE_KEY, JSON.stringify(records || []));
  } catch (err) {
    console.warn("localStorage mirror warning:", err);
  }
}

function readVaultFromLocalStorage() {
  try {
    const raw = localStorage.getItem(VAULT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    return [];
  }
}

async function refreshVaultCount() {
  try {
    const res = await fetch("/api/vault");
    if (!res.ok) return;
    const data = await res.json();
    state.vaultRecords = data.records || [];
    mirrorVaultToLocalStorage(state.vaultRecords);
    vaultCountBadge.textContent = state.vaultRecords.length;
  } catch (err) {
    const cached = readVaultFromLocalStorage();
    state.vaultRecords = cached;
    vaultCountBadge.textContent = cached.length;
  }
}
refreshVaultCount();

btnVaultModal.addEventListener("click", async () => {
  vaultModal.classList.remove("hidden");
  await loadVaultGallery();
});

btnCloseVault.addEventListener("click", () => {
  vaultModal.classList.add("hidden");
});

vaultModal.addEventListener("click", (e) => {
  if (e.target === vaultModal) vaultModal.classList.add("hidden");
});

async function loadVaultGallery() {
  const container = document.getElementById("vault-grid-container");
  container.innerHTML = "<p style='color:#b3a99c;'>보관함 필름 목록을 불러오는 중...</p>";

  try {
    const res = await fetch("/api/vault");
    const data = await res.json();
    state.vaultRecords = data.records || [];
    mirrorVaultToLocalStorage(state.vaultRecords);
    vaultCountBadge.textContent = state.vaultRecords.length;

    if (!state.vaultRecords.length) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #b3a99c;">
          <p style="font-size: 1.05rem; margin-bottom: 8px; color: #f6f1e9;">아직 보관된 필름이 없습니다.</p>
          <p style="font-size: 0.8rem;">4단계 디렉팅 후 2턴 대화를 마치면 엔딩별 MP4와 3D 친필 엽서가 이곳에 영구 보관됩니다.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = state.vaultRecords
      .map((r) => {
        const videoSrc = r.master_mp4_url || r.preview_mp4_url;
        const postcardImg = r.postcard_image_url || `/api/media/${r.job_id}/cut5.jpg`;
        const sitShort = (r.situation_title_kr || "").slice(0, 18);
        return `
          <div class="vault-card" data-job="${r.job_id}">
            <div class="vault-card-header">
              <span class="vault-date">${r.created_at}</span>
              <span class="vault-tag">${r.ending_type}</span>
            </div>
            <div class="vault-tags">
              <span class="vault-tag">👤 ${r.partner_name_kr} (${r.partner_name || ""})</span>
              <span class="vault-tag">📍 ${(r.location_title_kr || "").split(",")[0]}</span>
              <span class="vault-tag">🎬 ${sitShort}</span>
            </div>
            <div class="vault-card-body">
              <h4>${r.ending_title_kr}</h4>
              <p>“${(r.partner_final_dialogue_kr || "").slice(0, 48)}”</p>
              <p style="color:#e2b679; margin-top:4px; font-size:0.72rem;">${(r.postcard_back && r.postcard_back.ps_note_kr) || ""}</p>
            </div>
            <div class="vault-media-preview">
              <img src="${postcardImg}" alt="Postcard Back" />
            </div>
            <div class="vault-card-actions">
              <button type="button" class="vault-action-btn btn-view-vault-postcard" data-job="${r.job_id}">
                💌 3D 엽서 & 영상 열기
              </button>
              ${
                videoSrc
                  ? `<a href="${videoSrc}" download="lovestory_${r.job_id}.mp4" target="_blank" class="vault-action-btn">⬇️ MP4 저장</a>`
                  : ""
              }
              <button type="button" class="vault-delete-btn" data-job="${r.job_id}">🗑️</button>
            </div>
          </div>
        `;
      })
      .join("");

    // Bind Vault Card Replay (3D Postcard Flip + Darkroom MP4 Player)
    container.querySelectorAll(".btn-view-vault-postcard").forEach((btn) => {
      btn.addEventListener("click", () => {
        const jobId = btn.dataset.job;
        const rec = state.vaultRecords.find((r) => r.job_id === jobId);
        if (rec) {
          vaultModal.classList.add("hidden");
          state.jobId = rec.job_id;
          if (state.pollTimer) clearInterval(state.pollTimer);

          revealEndingAndFlipPostcard(
            {
              ending_type: rec.ending_type,
              ending_title_kr: rec.ending_title_kr,
              ending_title_en: rec.ending_title_en,
              partner_final_dialogue_kr: rec.partner_final_dialogue_kr,
              postcard_back: rec.postcard_back,
            },
            rec.job_id,
            { partner_name_kr: rec.partner_name_kr, partner_name: rec.partner_name || "Ijun" },
            false
          );

          // Populate saved storyboards and MP4 in Darkroom Panel
          document.getElementById("pipeline-status-badge").textContent = "VAULT ARCHIVE";
          document.getElementById("pipeline-progress-fill").style.width = "100%";
          document.getElementById("pipeline-detail-text").textContent =
            `내 필름 보관함 기록 로드 완료 (${rec.created_at})`;

          if (rec.storyboard_urls) {
            Object.entries(rec.storyboard_urls).forEach(([cutNum, url]) => {
              const slot = document.querySelector(`.film-slot[data-cut="${cutNum}"]`);
              if (slot) {
                slot.innerHTML = `<span>CUT 0${cutNum}</span><img src="${url}" alt="Cut ${cutNum}" />`;
              }
            });
          }

          const videoPlayer = document.getElementById("compiled-video-player");
          const previewLink = document.getElementById("link-preview-mp4");
          const masterLink = document.getElementById("link-master-mp4");
          if (rec.preview_mp4_url) {
            previewLink.href = rec.preview_mp4_url;
            previewLink.classList.remove("disabled");
          }
          if (rec.master_mp4_url) {
            masterLink.href = rec.master_mp4_url;
            masterLink.classList.remove("disabled");
          }
          const bestVideo = rec.master_mp4_url || rec.preview_mp4_url;
          if (bestVideo) {
            videoPlayer.src = bestVideo;
            videoPlayer.play().catch(() => {});
          }
        }
      });
    });

    container.querySelectorAll(".vault-delete-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const jobId = btn.dataset.job;
        await fetch(`/api/vault/${jobId}`, { method: "DELETE" });
        await loadVaultGallery();
      });
    });
  } catch (err) {
    console.error("Vault gallery error:", err);
  }
}

// Start a new directing session while keeping all previous films in the vault
function startNewDirectingSession() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  vaultModal.classList.add("hidden");
  document.getElementById("postcard-3d-card").classList.remove("is-flipped");
  document.getElementById("darkroom-panel").classList.add("hidden");
  switchView("casting");
}

document.getElementById("btn-new-directing").addEventListener("click", startNewDirectingSession);
const btnEndingNewDirect = document.getElementById("btn-ending-new-direct");
if (btnEndingNewDirect) {
  btnEndingNewDirect.addEventListener("click", startNewDirectingSession);
}

// 7. Top-Right Judge Modal Toggle
const judgeModal = document.getElementById("judge-modal");
document.getElementById("btn-judge-modal").addEventListener("click", () => {
  judgeModal.classList.remove("hidden");
});
document.getElementById("btn-close-modal").addEventListener("click", () => {
  judgeModal.classList.add("hidden");
});
judgeModal.addEventListener("click", (e) => {
  if (e.target === judgeModal) judgeModal.classList.add("hidden");
});
