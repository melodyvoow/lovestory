"""
LoveStory; — Data Models, Choices & Cast Profiles (v4.0 Complete Edition)
Google DeepMind AI Hackathon (Track 1: Entertainment)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# 1. Exact Global Style Suffix for Still & Storyboard Image Generation
GLOBAL_STYLE_SUFFIX = (
    "On the delicate boundary between live-action cinema and lyrical Studio Ghibli watercolor animation, "
    "semi-realistic painterly illustration, soft hand-painted gouache and watercolor washes on warm paper grain, "
    "realistic 35mm lens shallow depth of field, warm amber tungsten lighting contrasting with cool rainy night "
    "reflections, emotional Korean romance aesthetic, 16:9 widescreen composition."
)

# 2. Exact 1970s Cinema Verite Video Motion Suffix
CINEMA_VERITE_SUFFIX = (
    "1970s cinema verite documentary style, candid street cinematography, authentic vintage broadcast look."
)


def format_video_prompt(scene_desc: str) -> str:
    """Guarantees the 1970s cinema verite documentary formula is appended to video prompts."""
    clean_desc = (scene_desc or "").strip()
    if CINEMA_VERITE_SUFFIX in clean_desc:
        return clean_desc
    clean_desc = clean_desc.rstrip("., ")
    return f"{clean_desc}, {CINEMA_VERITE_SUFFIX}"


# 3. Dynamic Gender Casting Profiles (Step 1)
CAST_PROFILES: Dict[str, Dict[str, str]] = {
    "female": {
        "mode": "female",
        "player_gender": "female",
        "partner_name": "Ijun",
        "partner_name_kr": "이준",
        "partner_visual": (
            "Ijun, 29-year-old handsome Korean male street photographer, warm deep melancholic eyes, "
            "natural soft comma hair slightly damp from rain, wearing a dark brown trench coat "
            "with a visibly rain-soaked left shoulder over a textured cream knit sweater, "
            "vintage silver 1970s 35mm film camera strap across his chest"
        ),
        "player_visual": (
            "27-year-old Korean female protagonist, soft clear expressive eyes, natural long dark hair, "
            "wearing a cozy warm ivory wool coat"
        ),
        "style_suffix": GLOBAL_STYLE_SUFFIX,
    },
    "male": {
        "mode": "male",
        "player_gender": "male",
        "partner_name": "Iseo",
        "partner_name_kr": "이서",
        "partner_visual": (
            "Iseo, 29-year-old beautiful Korean female street photographer, gentle wistful expressive eyes, "
            "soft wavy dark brown hair with tiny raindrops, wearing a classic beige trench coat "
            "with a visibly rain-soaked left shoulder over a warm oatmeal knit top, "
            "vintage silver 1970s 35mm film camera strap across her shoulder"
        ),
        "player_visual": (
            "28-year-old Korean male protagonist, clean soft dandy hairstyle, gentle warm gaze, "
            "wearing a charcoal wool coat over a black turtleneck"
        ),
        "style_suffix": GLOBAL_STYLE_SUFFIX,
    },
}

# 4. 4-Step Director: Locations (Step 2)
LOCATION_CHOICES: Dict[str, Dict[str, str]] = {
    "rainy_cafe": {
        "id": "rainy_cafe",
        "title_kr": "비 오는 밤, 마감 10분 전의 오래된 창가 카페",
        "title_en": "Rainy Night Vintage Cafe (10 Mins Before Closing)",
        "prompt_env": (
            "Warm tungsten vintage cafe window table, rain streaking down glass, "
            "two warm coffee mugs emitting soft steam on a dark wooden table"
        ),
        "time_str": "🌧️ 마감 10분 전 (22:50)",
        "default_badge": "✈️ DEPARTURE: TOMORROW 09:30 AM",
    },
    "midnight_station": {
        "id": "midnight_station",
        "title_kr": "막차가 끊긴 새벽, 안개 낀 기차역 플랫폼 벤치",
        "title_en": "Misty Midnight Train Station Platform",
        "prompt_env": (
            "Misty vintage train station platform glowing under amber sodium lamps, "
            "damp concrete reflecting faint station lights, quiet wooden platform bench"
        ),
        "time_str": "🌙 막차 직후 새벽 (00:40)",
        "default_badge": "🚉 DEPARTURE: 05:30 AM PLATFORM 3",
    },
    "red_darkroom": {
        "id": "red_darkroom",
        "title_kr": "빗소리가 들리는 지하 아날로그 사진 암실",
        "title_en": "Rainy Underground Analog Darkroom",
        "prompt_env": (
            "Nostalgic underground darkroom glowing with warm amber-red safelights "
            "and hanging black-and-white 35mm prints, muffled sound of rain above"
        ),
        "time_str": "🎞️ 심야 인화 작업실 (01:15)",
        "default_badge": "✈️ DEPARTURE: TOMORROW 09:30 AM (DARKROOM ARCHIVE)",
    },
}

# 5. 4-Step Director: Situations & Motives (Step 3)
SITUATION_CHOICES: Dict[str, Dict[str, Any]] = {
    "parting_before_trip": {
        "id": "parting_before_trip",
        "title_kr": "내일 아침 멀리 떠나는 사람과의 마지막 밤",
        "title_en": "Final Night Before Long Departure",
        "goal": "Confess true feelings and hand over the photo postcard before departure tomorrow morning.",
        "goal_kr": "내일 아침 멀리 떠나기 전 숨겨온 진심을 고백하고 아끼는 사진 엽서를 건넨다.",
        "obstacle": "Fears making the player feel obligated to wait during the long overseas assignment.",
        "obstacle_kr": "상대방이 긴 기다림에 부담을 느끼거나 얽매일까 봐 두려워 엽서를 만지작거리며 망설인다.",
        "opening_lines": {
            "female": "비 많이 오네… 오늘은 조금 일찍 가봐야 할 것 같아.",
            "male": "비가 꽤 거세졌네… 오늘은 조금 일찍 일어나야 할 것 같아.",
        },
        "preset_turn1": [
            "어깨가 많이 젖었네… 우산 나한테만 기울여준 거야?",
            "내일 아침 출발이지? 아까 티켓 끝자락을 봤어.",
            "자꾸 만지작거리는 그 사진 엽서… 암실에서 약속했던 그거야?",
        ],
        "itinerary_badge": "DEPARTURE: TOMORROW 09:30 AM",
    },
    "unspoken_first_love": {
        "id": "unspoken_first_love",
        "title_kr": "7년 지기 친구, 선을 넘기 직전의 고백",
        "title_en": "7-Year Best Friends Crossing the Line",
        "goal": "Break the friend-zone and hand over the secret photo postcard kept since day one.",
        "goal_kr": "7년 동안 친구라는 이름 뒤에 숨겨둔 짝사랑을 고백하고 첫날의 흑백 사진 엽서를 건넨다.",
        "obstacle": "Fears losing the 7-year friendship forever if the confession is rejected.",
        "obstacle_kr": "고백했다가 7년간의 가장 소중한 친구 관계마저 영영 잃을까 봐 손끝을 떨며 주저한다.",
        "opening_lines": {
            "female": "비 많이 오네… 우리 이렇게 우산 하나 나눠 쓴 지 벌써 7년째인 거 알아?",
            "male": "비가 참 많이 온다… 처음 우산 같이 썼던 7년 전 그날도 딱 이런 밤이었는데.",
        },
        "preset_turn1": [
            "7년 전 그날도 네 왼쪽 어깨가 오늘처럼 흠뻑 젖어 있었잖아.",
            "친구라는 말 뒤에 숨지 마. 그 사진 엽서 뒤에 뭐라고 적었어?",
            "오늘 밤이 지나면, 우리 사이는 어떻게 달라질까?",
        ],
        "itinerary_badge": "DEPARTURE: 05:30 AM PLATFORM 3",
    },
    "reunion_after_years": {
        "id": "reunion_after_years",
        "title_kr": "3년 만에 우연히 다시 마주친 옛 연인과의 밤",
        "title_en": "Reunion with Ex-Lover After 3 Years",
        "goal": "Hand over the photo postcard kept in their coat pocket for 3 years.",
        "goal_kr": "3년 동안 차마 부치지 못하고 코트 안주머니에 품고 다니던 흑백 인화 엽서를 마침내 전한다.",
        "obstacle": "Fears it is already too late and that the player's heart has moved on.",
        "obstacle_kr": "이미 너무 늦어버린 것은 아닐지, 상대의 마음이 다 식어버렸을지 두려워 눈빛이 흔들린다.",
        "opening_lines": {
            "female": "비 많이 오네… 3년 만에 마주친 날에도 결국 내 우산은 네 쪽으로 기우네.",
            "male": "정말 3년 만이네… 빗속에 서 있는 널 보자마자 발이 먼저 움직였어.",
        },
        "preset_turn1": [
            "3년이 지났는데도 여전히 내 쪽으로 우산을 기울여 주는구나.",
            "그 낡은 사진 엽서… 혹시 지난 3년 내내 가지고 다닌 거야?",
            "내일 아침 기차로 다시 떠나기 전에, 그 엽서 나한테 주면 안 돼?",
        ],
        "itinerary_badge": "DEPARTURE: TOMORROW 09:30 AM",
    },
}

# 6. Clues Catalog (Step 4 & In-Game Inspection)
CLUES_CATALOG: Dict[str, Dict[str, str]] = {
    "wet_sleeve": {
        "id": "wet_sleeve",
        "title_kr": "젖은 왼쪽 어깨",
        "title_en": "Damp Left Shoulder & Sleeve",
        "observation_kr": (
            "우산을 내 쪽으로 온전히 기울여 주느라 왼쪽 어깨와 트렌치코트 소매가 빗물에 흠뻑 젖어 있다. "
            "정작 본인은 추운 줄도 모른 채 내 쪽만 바라보고 있다."
        ),
    },
    "postcard": {
        "id": "postcard",
        "title_kr": "만지작거리는 흑백 사진 엽서",
        "title_en": "Black-and-White Darkroom Photo Postcard",
        "observation_kr": (
            "테이블 한쪽에 놓인 35mm 암실 인화 흑백 사진 엽서의 앞면 모서리. "
            "상대방이 말을 아끼며 떨리는 손끝으로 자꾸만 그 모서리를 매만지고 있다."
        ),
    },
    "itinerary": {
        "id": "itinerary",
        "title_kr": "시간이 적힌 출발 티켓/일정표",
        "title_en": "Departure Ticket / Schedule",
        "observation_kr": (
            "코트 주머니와 테이블 가장자리 사이에 삐져나온 일정표와 출발 티켓. "
            "선명하게 찍힌 출발 시각이 이 밤의 시간이 얼마 남지 않았음을 알려준다."
        ),
    },
}


# 7. Request & Vault Models
class CharacterAssetRequest(BaseModel):
    player_gender: str = "female"
    partner_ref_image_b64: Optional[str] = None
    player_ref_image_b64: Optional[str] = None
    custom_note: Optional[str] = None


class StartSessionRequest(BaseModel):
    player_gender: str = "female"
    location_id: str = "rainy_cafe"
    situation_id: str = "parting_before_trip"
    anchor_clue_id: str = "wet_sleeve"
    partner_ref_image_b64: Optional[str] = None
    player_ref_image_b64: Optional[str] = None
    custom_note: Optional[str] = None


class ClueRequest(BaseModel):
    session_id: str
    clue_id: str


class ClueSynthesisRequest(BaseModel):
    session_id: str


class TurnRequest(BaseModel):
    session_id: str
    player_input: str



class VaultRecord(BaseModel):
    job_id: str
    created_at: str
    cast_mode: str
    partner_name: str
    partner_name_kr: str
    location_id: str
    location_title_kr: str
    situation_id: str
    situation_title_kr: str
    ending_type: str
    ending_title_kr: str
    ending_title_en: str
    partner_final_dialogue_kr: str
    postcard_back: Dict[str, str]
    observed_clues: List[str]
    preview_mp4_url: Optional[str] = None
    master_mp4_url: Optional[str] = None
    storyboard_urls: Dict[str, str] = Field(default_factory=dict)
    omni_clip_urls: Dict[str, str] = Field(default_factory=dict)
    postcard_image_url: Optional[str] = None
