"""
Pre-generate static prequel clips & posters for LoveStory;
Lyrical Studio Ghibli Watercolor Animation x 35mm Alexa Cinema Aesthetic
Diverse Camera Angles:
- Cut 1: Exterior Through-Glass / Low-Angle Two-Shot
- Cut 2: Extreme Macro Rack-Focus / Dutch-Tilt Over-the-Shoulder
- Cut 3: High-Angle Overhead / Low-Angle Tabletop Entrance
"""

import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "prequel"

PREQUEL_DATA = {
    "female": [
        {
            "cut": 1,
            "title": "First Rain",
            "camera_angle": "Exterior Through-Glass / Low-Angle",
            "kr": "처음 우산을 나눠 썼던 날부터, 내 렌즈가 멈추는 곳은 늘 너였다.",
            "en": "From the rainy day we first shared an umbrella, my lens always paused on you.",
            "partner": "Ijun (이준)",
            "color_top": "#191629",
            "color_bot": "#0c0a14",
            "accent": "#e2b679",
            "icon": "☂️",
            "cinematography": "Low-angle looking up through transparent vinyl umbrella with trickling raindrops"
        },
        {
            "cut": 2,
            "title": "The Darkroom Promise",
            "camera_angle": "Extreme Macro Rack-Focus / Dutch-Tilt",
            "kr": "언젠가 멀리 떠나게 되는 날, 제일 아끼는 사진 뒤에 진짜 마음을 적어 주겠다고 했었지.",
            "en": "I promised that before leaving far away, I would write my feelings on the back of my favorite photo.",
            "partner": "Ijun (이준)",
            "color_top": "#2a1518",
            "color_bot": "#0f0910",
            "accent": "#e8987b",
            "icon": "🎞️",
            "cinematography": "Dutch-tilt rack-focus from glowing amber safelight to fountain pen over photo postcard"
        },
        {
            "cut": 3,
            "title": "Tonight, 10 Minutes Before Closing",
            "camera_angle": "High-Angle Overhead Entrance",
            "kr": "그리고 내일, 나는 긴 촬영을 떠난다. 오늘 밤 우리는 어떤 마지막 장면을 남기게 될까?",
            "en": "And tomorrow, I leave for a long shoot. What final scene will we leave behind tonight?",
            "partner": "Ijun (이준)",
            "color_top": "#1a1f2b",
            "color_bot": "#0b0e14",
            "accent": "#7be0ad",
            "icon": "🌧️",
            "cinematography": "High-angle overhead tracking dolly into warm tungsten cafe from rainy exterior"
        }
    ],
    "male": [
        {
            "cut": 1,
            "title": "First Rain",
            "camera_angle": "Exterior Through-Glass / Low-Angle",
            "kr": "처음 우산을 나눠 썼던 날부터, 내 렌즈가 멈추는 곳은 늘 너였다.",
            "en": "From the rainy day we first shared an umbrella, my lens always paused on you.",
            "partner": "Iseo (이서)",
            "color_top": "#1a1626",
            "color_bot": "#0d0a13",
            "accent": "#e2b679",
            "icon": "☂️",
            "cinematography": "Low-angle looking up through transparent vinyl umbrella with trickling raindrops"
        },
        {
            "cut": 2,
            "title": "The Darkroom Promise",
            "camera_angle": "Extreme Macro Rack-Focus / Dutch-Tilt",
            "kr": "언젠가 멀리 떠나게 되는 날, 제일 아끼는 사진 뒤에 진짜 마음을 적어 주겠다고 했었지.",
            "en": "I promised that before leaving far away, I would write my feelings on the back of my favorite photo.",
            "partner": "Iseo (이서)",
            "color_top": "#291620",
            "color_bot": "#0e0912",
            "accent": "#e8987b",
            "icon": "🎞️",
            "cinematography": "Dutch-tilt rack-focus from glowing amber safelight to fountain pen over photo postcard"
        },
        {
            "cut": 3,
            "title": "Tonight, 10 Minutes Before Closing",
            "camera_angle": "High-Angle Overhead Entrance",
            "kr": "그리고 내일, 나는 긴 촬영을 떠난다. 오늘 밤 우리는 어떤 마지막 장면을 남기게 될까?",
            "en": "And tomorrow, I leave for a long shoot. What final scene will we leave behind tonight?",
            "partner": "Iseo (이서)",
            "color_top": "#171c26",
            "color_bot": "#0a0c12",
            "accent": "#7be0ad",
            "icon": "🌧️",
            "cinematography": "High-angle overhead tracking dolly into warm tungsten cafe from rainy exterior"
        }
    ]
}


def create_poster(out_path: Path, data: dict):
    w, h = 720, 1280
    img = Image.new("RGB", (w, h), color="#120e17")
    draw = ImageDraw.Draw(img)

    for y in range(h):
        alpha = y / float(h)
        t_r = int(int(data["color_top"][1:3], 16) * (1 - alpha) + int(data["color_bot"][1:3], 16) * alpha)
        t_g = int(int(data["color_top"][3:5], 16) * (1 - alpha) + int(data["color_bot"][3:5], 16) * alpha)
        t_b = int(int(data["color_top"][5:7], 16) * (1 - alpha) + int(data["color_bot"][5:7], 16) * alpha)
        draw.line([(0, y), (w, y)], fill=(t_r, t_g, t_b))

    draw.rectangle([(24, 24), (w - 24, h - 24)], outline=data["accent"], width=2)
    draw.rectangle([(32, 32), (w - 32, h - 32)], outline=(90, 80, 100), width=1)

    draw.text((w // 2, 80), "THE PHOTOGRAPHER'S FILM ROLL", fill=data["accent"], anchor="mm")
    draw.text((w // 2, 115), f"CUT {data['cut']} / 3 — {data['title'].upper()}", fill="#d0c6b8", anchor="mm")
    draw.text((w // 2, 145), f"ANGLE: {data['camera_angle'].upper()}", fill="#7be0ad", anchor="mm")
    draw.text((w // 2, 172), f"WITH {data['partner'].upper()}", fill="#a69d90", anchor="mm")

    draw.rectangle([(80, 260), (w - 80, 780)], fill="#1f1b26", outline=data["accent"], width=2)
    draw.text((w // 2, 480), data["icon"], fill="#ffffff", anchor="mm")
    draw.text((w // 2, 580), "STUDIO GHIBLI WATERCOLOR x 35MM", fill="#9c9182", anchor="mm")
    draw.text((w // 2, 620), data["cinematography"][:38], fill="#d0c6b8", anchor="mm")

    draw.text((w // 2, 880), data["kr"][:28], fill="#f6f1e9", anchor="mm")
    if len(data["kr"]) > 28:
        draw.text((w // 2, 920), data["kr"][28:], fill="#f6f1e9", anchor="mm")
    draw.text((w // 2, 980), data["en"][:40], fill="#b3a99c", anchor="mm")
    if len(data["en"]) > 40:
        draw.text((w // 2, 1015), data["en"][40:], fill="#b3a99c", anchor="mm")

    img.save(out_path, "JPEG", quality=92)


def generate_video_from_poster(poster_path: Path, video_path: Path, duration_sec: int = 3):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(poster_path),
        "-f", "lavfi",
        "-i", "anoisesrc=d=3:c=pink:r=44100:a=0.035,lowpass=f=1200",
        "-c:v", "libx264",
        "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale=720:1280,zoompan=z='min(zoom+0.0012,1.06)':d={duration_sec*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def main():
    for mode, cuts in PREQUEL_DATA.items():
        mode_dir = STATIC_DIR / mode
        mode_dir.mkdir(parents=True, exist_ok=True)
        for cut in cuts:
            cut_num = cut["cut"]
            poster_file = mode_dir / f"cut{cut_num}.jpg"
            video_file = mode_dir / f"cut{cut_num}.mp4"

            print(f"Generating [{mode}] cut{cut_num} ({cut['camera_angle']}) poster & video...")
            create_poster(poster_file, cut)
            generate_video_from_poster(poster_file, video_file, duration_sec=3)
            print(f"  ✓ Created: {video_file} ({video_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
