import os
import sys
import asyncio
import fitz  # PyMuPDF
import edge_tts
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip

PDF_PATH = r"D:\My-Learning-Journey\daily_lessons\20260609\huanclass\The_Startup_Profit_Equation.pdf"
OUTPUT_PATH = r"C:\Users\admin\.gemini\antigravity-ide\scratch\output.mp4"
TEMP_AUDIO = "temp_voice.mp3"
TEMP_DIR = "temp_slides"

# Script content for the voiceover (Traditional Chinese summary of the startup profit equation report)
CHINESE_SCRIPT = (
    "歡迎收看新創利潤方程式。本模型分析了五十家新創公司的營運數據，並精準預測其獲利能力。核心發現包括： "
    "第一，研發投入是決定獲利的黃金關鍵。每投入一元研發，可預期帶回零點八一元的新增利潤，回報率高達百分之八十一！ "
    "第二，行銷支出應適量配置，每多投入一元行銷，預期僅能帶回零點零三元的利潤。而行政管理費用每增加一元，利潤反而倒扣零點零七元。 "
    "因此，顧問建議：應將百分之八十以上的預算優先投入產品研發，並嚴格控管行政管理成本。 "
    "第三，落腳地區對獲利影響極低，不到百分之零點二。新創公司選址時，應以租金與稅率等實質營運成本最低的地方為首選。 "
    "最後，異常企業分析顯示，重行銷、輕產品且行政虛胖的組織是行不通的。這就是新創利潤方程式，助您的新創企業從第一天起健康盈利！"
)

def extract_pdf_text_and_images(pdf_path):
    print("Extracting text and pages from PDF...")
    doc = fitz.open(pdf_path)
    
    # 1. Extract text
    text_content = ""
    for page in doc:
        text_content += page.get_text()
    
    # 2. Extract pages as PNG images for the slideshow
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    slide_paths = []
    from PIL import Image
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)  # Render page to high-quality image
        img_path = os.path.join(TEMP_DIR, f"page_{i+1}.png")
        pix.save(img_path)
        
        # Resize to standard even 1920x1080 dimensions for H.264 player compatibility
        with Image.open(img_path) as img:
            resized_img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            resized_img.save(img_path)
            
        slide_paths.append(img_path)
        
    print(f"Extracted and resized {len(slide_paths)} slide pages as 1920x1080 PNGs.")
    return text_content, slide_paths

async def generate_tts(text, voice, output_audio_path):
    print(f"Generating TTS using voice {voice}...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)
    print("TTS generation completed.")

def create_slideshow_video(slide_paths, audio_path, output_video_path):
    print("Creating slideshow video with MoviePy...")
    audio_clip = AudioFileClip(audio_path)
    
    # Calculate duration for each slide
    num_slides = len(slide_paths)
    duration_per_slide = audio_clip.duration / num_slides
    print(f"Total video duration: {audio_clip.duration:.2f}s ({duration_per_slide:.2f}s per slide)")
    
    # Create ImageClips and concatenate them
    clips = [ImageClip(path).with_duration(duration_per_slide) for path in slide_paths]
    video_clip = concatenate_videoclips(clips, method="compose")
    
    # Set audio
    video_clip = video_clip.with_audio(audio_clip)
    
    # Write output file
    video_clip.write_videofile(
        output_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )
    
    # Close clips to release file locks
    video_clip.close()
    audio_clip.close()
    print(f"Video created successfully at: {output_video_path}")

async def main():
    # Step 1: Extract PDF text and render pages
    text, slide_paths = extract_pdf_text_and_images(PDF_PATH)
    
    # If PDF text layer is empty (image-only scanned PDF), use the professional report summary script
    cleaned_text = text.strip()
    if not cleaned_text or len(cleaned_text) < 50:
        print("PDF has no readable text layer (scanned PDF). Falling back to professional voiceover script.")
        tts_text = CHINESE_SCRIPT
    else:
        tts_text = cleaned_text
        
    # Step 2: Generate TTS audio
    await generate_tts(tts_text, "zh-TW-HsiaoChenNeural", TEMP_AUDIO)
    
    # Step 3: Merge audio and slideshow images into final MP4
    create_slideshow_video(slide_paths, TEMP_AUDIO, OUTPUT_PATH)
    
    # Step 4: Clean up temporary files
    print("Cleaning up temporary files...")
    if os.path.exists(TEMP_AUDIO):
        os.remove(TEMP_AUDIO)
    for path in slide_paths:
        if os.path.exists(path):
            os.remove(path)
    if os.path.exists(TEMP_DIR):
        os.rmdir(TEMP_DIR)
        
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
