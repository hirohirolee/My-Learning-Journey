import os
import sys
import math
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageSequenceClip, AudioFileClip

OUTPUT_PATH = r"C:\Users\admin\Desktop\output.mp4"
TEMP_AUDIO = "temp_voice.mp3"
FRAMES_DIR = "animated_frames"
FPS = 24
TOTAL_SCENES = 8
FRAMES_PER_SCENE = 220  # ~9.16 seconds per scene at 24fps
TOTAL_FRAMES = TOTAL_SCENES * FRAMES_PER_SCENE

# Voiceover Script
CHINESE_SCRIPT = (
    "歡迎收看新創利潤方程式。本模型分析了五十家新創公司的營運數據，並精準預測其獲利能力。核心發現包括： "
    "第一，研發投入是決定獲利的黃金關鍵。每投入一元研發，可預期帶回零點八一元的新增利潤，回報率高達百分之八十一！ "
    "第二，行銷支出應適量配置，每多投入一元行銷，預期僅能帶回零點零三元的利潤。而行政管理費用每增加一元，利潤反而倒扣零點零七元。 "
    "因此，顧問建議：應將百分之八十以上的預算優先投入產品研發，並嚴格控管行政管理成本。 "
    "第三，落腳地區對獲利影響極低，不到百分之零點二。新創公司選址時，應以租金與稅率等實質營運成本最低的地方為首選。 "
    "最後，異常企業分析顯示，重行銷、輕產品且行政虛胖的組織是行不通的。這就是新創利潤方程式，助您的新創企業從第一天起健康盈利！"
)

def get_font(font_name, size):
    paths = [
        os.path.join("C:\\Windows\\Fonts", font_name),
        os.path.join("C:\\Windows\\Fonts", "segoeui.ttf"),
        os.path.join("C:\\Windows\\Fonts", "msyh.ttc"),
        os.path.join("C:\\Windows\\Fonts", "arial.ttf")
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_background(draw):
    # Draw dark premium slate-blue gradient
    for y in range(1080):
        # Interpolate between Slate 900 (#0f172a) and Slate 800 (#1e293b)
        r = int(15 + (30 - 15) * (y / 1080))
        g = int(23 + (41 - 23) * (y / 1080))
        b = int(42 + (59 - 42) * (y / 1080))
        draw.line([(0, y), (1920, y)], fill=(r, g, b, 255))

def draw_glass_card(draw, x, y, w, h, radius=20, border_color=(255, 255, 255, 30), bg_color=(15, 23, 42, 180)):
    # Draw translucent glassmorphism card
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, fill=bg_color, outline=border_color, width=2)

def draw_rocket(draw, cx, cy, scale=1.0):
    # Draw flat vector rocket centered at (cx, cy)
    # Body
    body_w = 40 * scale
    body_h = 120 * scale
    draw.rounded_rectangle([(cx - body_w/2, cy - body_h/2), (cx + body_w/2, cy + body_h/2)], radius=15, fill=(240, 240, 240, 255))
    # Nose Cone (Triangle)
    draw.polygon([
        (cx - body_w/2, cy - body_h/2),
        (cx + body_w/2, cy - body_h/2),
        (cx, cy - body_h/2 - 40 * scale)
    ], fill=(239, 68, 68, 255))  # Red
    # Fins (Left & Right)
    draw.polygon([
        (cx - body_w/2, cy + body_h/4),
        (cx - body_w/2 - 25 * scale, cy + body_h/2 + 10 * scale),
        (cx - body_w/2, cy + body_h/2)
    ], fill=(239, 68, 68, 255))
    draw.polygon([
        (cx + body_w/2, cy + body_h/4),
        (cx + body_w/2 + 25 * scale, cy + body_h/2 + 10 * scale),
        (cx + body_w/2, cy + body_h/2)
    ], fill=(239, 68, 68, 255))
    # Window (Circle)
    draw.ellipse([(cx - 10 * scale, cy - 20 * scale), (cx + 10 * scale, cy)], fill=(59, 130, 246, 255), outline=(200, 200, 200, 255), width=2)

def draw_flame(draw, cx, cy, scale=1.0, pulse=1.0):
    # Pulsing fire flame
    flame_w = 20 * scale * pulse
    flame_h = 40 * scale * pulse
    draw.polygon([
        (cx - flame_w/2, cy),
        (cx + flame_w/2, cy),
        (cx, cy + flame_h)
    ], fill=(249, 115, 22, 255))  # Orange
    draw.polygon([
        (cx - flame_w/4, cy),
        (cx + flame_w/4, cy),
        (cx, cy + flame_h/2)
    ], fill=(234, 179, 8, 255))  # Yellow

# Scene renderers
def render_scene_1(draw, f, t):
    # Scene 1: Title and Rocket Launch
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 72)
    font_sub = get_font("segoeui.ttf", 36)
    
    # Title fade-in and hover
    alpha = min(255, int(t * 150))
    title_text = "THE STARTUP PROFIT EQUATION"
    title_w = draw.textlength(title_text, font=font_title)
    draw.text((960 - title_w/2, 250), title_text, font=font_title, fill=(255, 215, 0, alpha))
    
    sub_text = "50 Startups Performance & Budget Strategy"
    sub_w = draw.textlength(sub_text, font=font_sub)
    draw.text((960 - sub_w/2, 350), sub_text, font=font_sub, fill=(226, 232, 240, min(255, max(0, int((t - 1) * 150)))))
    
    # Rocket launch animation
    rocket_y = 1200 - (t * 120) if t < 6 else 480 + 15 * math.sin(t * 4)
    pulse = 1.0 + 0.15 * math.sin(f * 0.8)
    draw_flame(draw, 960, rocket_y + 60, scale=1.5, pulse=pulse)
    draw_rocket(draw, 960, rocket_y, scale=1.5)

def render_scene_2(draw, f, t):
    # Scene 2: Budget Buckets
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 30)
    font_label = get_font("segoeuib.ttf", 28)
    
    draw.text((100, 100), "Golden Rule: Sales - Profit = Expenses", font=font_title, fill=(255, 215, 0, 255))
    
    # Draw three buckets
    buckets = [
        {"label": "R&D Spend (81%)", "color": (59, 130, 246, 255), "target_h": 240, "x": 350},
        {"label": "Marketing (3%)", "color": (34, 197, 94, 255), "target_h": 15, "x": 960},
        {"label": "Admin (-7%)", "color": (239, 68, 68, 255), "target_h": 0, "x": 1570}
    ]
    
    bucket_w = 260
    base_y = 800
    max_h = 300
    
    for b in buckets:
        bx = b["x"]
        # Draw bucket glass outline
        draw_glass_card(draw, bx - bucket_w/2, base_y - max_h, bucket_w, max_h, radius=10, border_color=(255, 255, 255, 50))
        
        # Fill animation
        progress = min(1.0, t / 2.0)
        current_h = b["target_h"] * progress
        
        if current_h > 5:
            draw.rounded_rectangle([
                (bx - bucket_w/2 + 5, base_y - current_h),
                (bx + bucket_w/2 - 5, base_y - 5)
            ], radius=5, fill=b["color"])
            
        # Labels and values
        draw.text((bx - draw.textlength(b["label"], font=font_label)/2, base_y + 40), b["label"], font=font_label, fill=(255, 255, 255, 255))
        
        # Draw target text
        val_text = f"+${int(b['target_h']*3.38):,}" if b["target_h"] > 0 else "$0 (Inefficient)"
        if b["label"].startswith("Admin"):
            val_text = "-$0.07 Drag"
        draw.text((bx - draw.textlength(val_text, font=font_body)/2, base_y - max_h - 50), val_text, font=font_body, fill=b["color"])

def render_scene_3(draw, f, t):
    # Scene 3: Autopsy Report - Index 49
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 32)
    
    draw.text((100, 100), "Autopsy Report: Index 49 Failure", font=font_title, fill=(239, 68, 68, 255))
    
    # Pulse warning sign
    warn_cx, warn_cy = 450, 550
    scale = 1.0 + 0.08 * math.sin(t * 5)
    
    # Draw yellow/orange warning triangle
    tw = 200 * scale
    th = 180 * scale
    draw.polygon([
        (warn_cx, warn_cy - th/2),
        (warn_cx - tw/2, warn_cy + th/2),
        (warn_cx + tw/2, warn_cy + th/2)
    ], fill=(249, 115, 22, 255))
    # Exclamation mark
    draw.text((warn_cx - 15, warn_cy - 40), "!", font=get_font("segoeuib.ttf", 90), fill=(15, 23, 42, 255))
    
    # Render details card
    draw_glass_card(draw, 750, 280, 1000, 520, radius=20)
    
    details = [
        "• Model Anomaly: Heavy Administration, Zero Product R&D",
        "• Administration Expenses: $116,983 (Fat structure)",
        "• R&D Investment: $0.00 (No core technology)",
        "• Marketing Expenses: $45,173 (Inefficient acquisition)",
        "• Realized Net Profit: $14,681 (Extremely low margins)"
    ]
    
    for i, line in enumerate(details):
        alpha = min(255, int((t - i*0.8) * 200))
        if alpha > 0:
            fill_color = (239, 68, 68, alpha) if "R&D" in line or "Profit" in line else (240, 240, 240, alpha)
            draw.text((800, 340 + i * 80), line, font=font_body, fill=fill_color)

def render_scene_4(draw, f, t):
    # Scene 4: IQR Outlier Filter & Dummy Trap
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 28)
    
    draw.text((100, 100), "Data Preprocessing: Outliers & Dummy Trap", font=font_title, fill=(255, 215, 0, 255))
    
    # Draw clean IQR box plot visual
    bx, by, bw, bh = 200, 500, 700, 120
    draw.line([(bx, by + bh/2), (bx + bw, by + bh/2)], fill=(240, 240, 240, 150), width=3) # Whiskers line
    # Min/max ticks
    draw.line([(bx, by + bh/4), (bx, by + 3*bh/4)], fill=(240, 240, 240, 200), width=4)
    draw.line([(bx + bw, by + bh/4), (bx + bw, by + 3*bh/4)], fill=(240, 240, 240, 200), width=4)
    
    # Box
    box_x = bx + 180
    box_w = 350
    draw_glass_card(draw, box_x, by, box_w, bh, radius=5, border_color=(255, 255, 255, 100), bg_color=(59, 130, 246, 150))
    # Median line
    draw.line([(box_x + 160, by), (box_x + 160, by + bh)], fill=(255, 215, 0, 255), width=4)
    
    # Blinking Outlier dot (Index 49)
    outlier_x = bx - 80
    outlier_y = by + bh/2
    if int(t * 3.5) % 2 == 0:
        draw.ellipse([(outlier_x - 12, outlier_y - 12), (outlier_x + 12, outlier_y + 12)], fill=(239, 68, 68, 255))
        draw.text((outlier_x - 60, outlier_y + 25), "Index 49 (Outlier)", font=font_body, fill=(239, 68, 68, 255))
        
    # Dummy Trap text block
    draw_glass_card(draw, 1050, 260, 750, 550, radius=20)
    trap_text = [
        "IQR Outlier Filter:",
        "  • Threshold: $15,698 to $214,206",
        "  • Cleaned dataset size: 49 samples",
        "",
        "Dummy Variable Trap:",
        "  • One-hot encoded state variable",
        "  • Baseline: Drop California",
        "  • Avoids perfect multicollinearity"
    ]
    for i, line in enumerate(trap_text):
        color = (255, 215, 0, 255) if ":" in line else (240, 240, 240, 255)
        draw.text((1100, 300 + i * 50), line, font=font_body, fill=color)

def render_scene_5(draw, f, t):
    # Scene 5: Model Comparison
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 32)
    font_bold = get_font("segoeuib.ttf", 36)
    
    draw.text((100, 100), "Model Evaluation: Linear vs Random Forest", font=font_title, fill=(255, 215, 0, 255))
    
    # Two comparing slides sliding in
    ols_x = min(200, -600 + int(t * 400))
    rf_x = max(1050, 2500 - int(t * 400))
    
    # OLS Card
    draw_glass_card(draw, ols_x, 280, 680, 500, radius=20)
    draw.text((ols_x + 50, 330), "Multiple Linear Regression", font=font_bold, fill=(59, 130, 246, 255))
    draw.text((ols_x + 50, 420), "• Baseline OLS regression", font=font_body, fill=(240, 240, 240, 255))
    draw.text((ols_x + 50, 500), "• Test R-squared: 0.919", font=font_body, fill=(240, 240, 240, 255))
    draw.text((ols_x + 50, 580), "• MAE Score: $6,550.86", font=font_bold, fill=(34, 197, 94, 255))
    
    # RF Card
    draw_glass_card(draw, rf_x, 280, 680, 500, radius=20)
    draw.text((rf_x + 50, 330), "Random Forest Regressor", font=font_bold, fill=(255, 215, 0, 255))
    draw.text((rf_x + 50, 420), "• Non-parametric ensemble", font=font_body, fill=(240, 240, 240, 255))
    draw.text((rf_x + 50, 500), "• Test R-squared: 0.926", font=font_body, fill=(240, 240, 240, 255))
    draw.text((rf_x + 50, 580), "• MAE Score: $6,892.37", font=font_bold, fill=(240, 240, 240, 255))

def render_scene_6(draw, f, t):
    # Scene 6: Feature Importance
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 28)
    font_label = get_font("segoeuib.ttf", 28)
    
    draw.text((100, 100), "Random Forest Feature Importance", font=font_title, fill=(255, 215, 0, 255))
    
    # Feature horizontal bar charts
    features = [
        {"name": "R&D Spend", "val": 0.917, "color": (59, 130, 246, 255)},
        {"name": "Marketing Spend", "val": 0.073, "color": (34, 197, 94, 255)},
        {"name": "Administration", "val": 0.008, "color": (239, 68, 68, 255)},
        {"name": "落腳州別 (State)", "val": 0.002, "color": (156, 163, 175, 255)}
    ]
    
    start_y = 280
    bar_max_w = 1100
    
    for i, feat in enumerate(features):
        cy = start_y + i * 140
        # Draw Label
        draw.text((150, cy), feat["name"], font=font_label, fill=(240, 240, 240, 255))
        
        # Base bar container
        draw_glass_card(draw, 450, cy - 5, bar_max_w, 45, radius=5, border_color=(255, 255, 255, 20))
        
        # Growing bar animation
        progress = min(1.0, t / 2.0)
        current_w = max(5, int(bar_max_w * feat["val"] * progress))
        
        draw.rounded_rectangle([
            (450, cy - 5),
            (450 + current_w, cy + 40)
        ], radius=5, fill=feat["color"])
        
        # Value text
        val_text = f"{feat['val']*100:.1f}%"
        draw.text((460 + current_w, cy), val_text, font=font_body, fill=feat["color"])

def render_scene_7(draw, f, t):
    # Scene 7: Simulator Dashboard
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 28)
    font_bold = get_font("segoeuib.ttf", 36)
    
    draw.text((100, 100), "Dynamic Budget Optimizer & Calculator", font=font_title, fill=(255, 215, 0, 255))
    
    # Draw simulated slider dashboard card
    draw_glass_card(draw, 150, 250, 900, 600, radius=20)
    draw.text((200, 300), "Streamlit Interactive Panel", font=font_bold, fill=(59, 130, 246, 255))
    
    # Slider 1: R&D Spend
    draw.text((200, 390), "R&D Spend Simulator", font=font_body, fill=(240, 240, 240, 255))
    draw_glass_card(draw, 200, 440, 700, 15, radius=5, border_color=(255, 255, 255, 30))
    # Animate slider thumb back and forth
    slider_1_prog = 0.5 + 0.3 * math.sin(t * 1.5)
    draw.ellipse([
        (200 + 700 * slider_1_prog - 15, 440 - 7),
        (200 + 700 * slider_1_prog + 15, 440 + 22)
    ], fill=(59, 130, 246, 255))
    draw.text((750, 390), f"${int(slider_1_prog*150000):,}", font=font_body, fill=(59, 130, 246, 255))
    
    # Slider 2: Marketing Spend
    draw.text((200, 520), "Marketing Spend Simulator", font=font_body, fill=(240, 240, 240, 255))
    draw_glass_card(draw, 200, 570, 700, 15, radius=5, border_color=(255, 255, 255, 30))
    slider_2_prog = 0.4 + 0.25 * math.cos(t * 1.5)
    draw.ellipse([
        (200 + 700 * slider_2_prog - 15, 570 - 7),
        (200 + 700 * slider_2_prog + 15, 570 + 22)
    ], fill=(34, 197, 94, 255))
    draw.text((750, 520), f"${int(slider_2_prog*150000):,}", font=font_body, fill=(34, 197, 94, 255))
    
    # Right-side dynamic calculation result card
    res_x = 1150
    draw_glass_card(draw, res_x, 250, 600, 600, radius=20, bg_color=(15, 23, 42, 220))
    draw.text((res_x + 50, 300), "Vectorized Prediction", font=font_bold, fill=(255, 215, 0, 255))
    
    # Predict profit based on slider positions
    simulated_profit = 50000 + 0.8 * (slider_1_prog*150000) + 0.03 * (slider_2_prog*150000)
    draw.text((res_x + 50, 420), "Estimated Profit:", font=font_body, fill=(240, 240, 240, 255))
    draw.text((res_x + 50, 480), f"${int(simulated_profit):,}", font=get_font("segoeuib.ttf", 64), fill=(34, 197, 94, 255))
    draw.text((res_x + 50, 600), "Optimization: Batch 0.005s", font=font_body, fill=(156, 163, 175, 255))

def render_scene_8(draw, f, t):
    # Scene 8: Cloud Deployment
    draw_background(draw)
    font_title = get_font("segoeuib.ttf", 54)
    font_body = get_font("segoeui.ttf", 32)
    font_bold = get_font("segoeuib.ttf", 36)
    
    draw.text((100, 100), "Streamlit Community Cloud Deployment", font=font_title, fill=(255, 215, 0, 255))
    
    # Cloud illustration in the center
    cloud_cx, cloud_cy = 960, 450
    scale = 1.0 + 0.04 * math.sin(t * 3.5)
    
    # Draw cloud shape with overlapping circles
    c_color = (59, 130, 246, 200)
    draw.ellipse([(cloud_cx - 150*scale, cloud_cy - 80*scale), (cloud_cx + 50*scale, cloud_cy + 80*scale)], fill=c_color)
    draw.ellipse([(cloud_cx - 50*scale, cloud_cy - 120*scale), (cloud_cx + 150*scale, cloud_cy + 80*scale)], fill=c_color)
    draw.ellipse([(cloud_cx - 200*scale, cloud_cy - 40*scale), (cloud_cx, cloud_cy + 80*scale)], fill=c_color)
    draw.rounded_rectangle([(cloud_cx - 180*scale, cloud_cy + 10*scale), (cloud_cx + 140*scale, cloud_cy + 80*scale)], radius=20, fill=c_color)
    
    # Draw cloud text
    draw.text((cloud_cx - 100, cloud_cy + 10), "DEPLOYED", font=font_bold, fill=(255, 255, 255, 255))
    
    # Details at the bottom
    draw_glass_card(draw, 360, 700, 1200, 240, radius=20)
    
    dep_text = [
        "1. Push code to GitHub Repository",
        "2. Configure Branch (main) & Main file path (app.py)",
        "3. Live prediction calculator running at Streamlit Cloud"
    ]
    for i, line in enumerate(dep_text):
        draw.text((400, 730 + i * 60), line, font=font_body, fill=(240, 240, 240, 255))

# Main loop to render all frames
def generate_all_frames():
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)
        
    print(f"Pre-rendering {TOTAL_FRAMES} frames as PNGs (1920x1080)...")
    
    for f in range(TOTAL_FRAMES):
        scene = f // FRAMES_PER_SCENE
        scene_frame = f % FRAMES_PER_SCENE
        t = scene_frame / FPS
        
        # Create image canvas
        img = Image.new("RGBA", (1920, 1080), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img, "RGBA")
        
        if scene == 0:
            render_scene_1(draw, f, t)
        elif scene == 1:
            render_scene_2(draw, f, t)
        elif scene == 2:
            render_scene_3(draw, f, t)
        elif scene == 3:
            render_scene_4(draw, f, t)
        elif scene == 4:
            render_scene_5(draw, f, t)
        elif scene == 5:
            render_scene_6(draw, f, t)
        elif scene == 6:
            render_scene_7(draw, f, t)
        elif scene == 7:
            render_scene_8(draw, f, t)
            
        # Save frame
        frame_path = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        img.save(frame_path)
        
        if f % 100 == 0:
            print(f"Rendered {f}/{TOTAL_FRAMES} frames...")
            
    print("Pre-rendering finished!")

async def main():
    # Step 1: Generate TTS voice
    print("Generating TTS voiceover...")
    communicate = edge_tts.Communicate(CHINESE_SCRIPT, "zh-TW-HsiaoChenNeural")
    await communicate.save(TEMP_AUDIO)
    print("TTS voiceover generated.")
    
    # Step 2: Render all animation frames
    generate_all_frames()
    
    # Step 3: Combine PNG sequence and audio using MoviePy
    print("Combining frame sequence and audio using MoviePy...")
    audio_clip = AudioFileClip(TEMP_AUDIO)
    
    # Get frame filenames
    frame_files = [os.path.join(FRAMES_DIR, f"frame_{i:04d}.png") for i in range(TOTAL_FRAMES)]
    
    # Load frame sequence (we truncate or set clip duration to match audio)
    video_clip = ImageSequenceClip(frame_files, fps=FPS)
    
    # Cut or loop video to match audio length
    video_clip = video_clip.with_duration(audio_clip.duration)
    video_clip = video_clip.with_audio(audio_clip)
    
    print(f"Saving final video to: {OUTPUT_PATH}")
    video_clip.write_videofile(
        OUTPUT_PATH,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )
    
    # Close clips
    video_clip.close()
    audio_clip.close()
    
    # Step 4: Cleanup temp files
    print("Cleaning up temp files...")
    if os.path.exists(TEMP_AUDIO):
        try:
            os.remove(TEMP_AUDIO)
        except Exception as e:
            print(f"Warning: could not remove temp audio: {e}")
    for f in frame_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
    if os.path.exists(FRAMES_DIR):
        try:
            os.rmdir(FRAMES_DIR)
        except Exception:
            pass
        
    print("All tasks finished successfully!")

if __name__ == "__main__":
    asyncio.run(main())
