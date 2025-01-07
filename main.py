import moviepy.editor as mpe
import edge_tts
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
from stories import RedditScraper

class ShortsGenerator:
    def __init__(self, script_text, background_video, output_filename):
        self.script_text = script_text
        self.background = background_video
        self.output_filename = output_filename
        self.word_timings = []

    def create_word_clip(self, text, size=(1080, 1920)):
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("Komika", 90)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 90)
            except:
                font = ImageFont.load_default()
        
        bbox = font.getbbox(text)
        w = draw.textlength(text, font=font)
        h = bbox[3] - bbox[1]
        x = (size[0] - w) / 2
        y = (size[1] - h) / 2
        
        # Smooth outline effect
        outline_thickness = 8
        steps = 32  # More steps = smoother outline
        for angle in range(0, 360, int(360/steps)):
            for r in range(1, outline_thickness + 1):
                dx = int(r * np.cos(np.radians(angle)))
                dy = int(r * np.sin(np.radians(angle)))
                draw.text((x + dx, y + dy), text, font=font, fill='black')
        
        # Main text in bright white
        draw.text((x, y), text, font=font, fill='white')
        
        return mpe.ImageClip(np.array(img)).set_opacity(1.0)

    def group_words(self, word_timings, max_words=2):
        groups = []
        current_group = []
        current_words = []
        
        for timing in word_timings:
            current_words.append(timing["word"])
            current_group.append(timing)
            
            if len(current_words) == max_words:
                groups.append({
                    "text": " ".join(current_words),
                    "start": current_group[0]["start"],
                    "end": current_group[-1]["end"]
                })
                current_words = []
                current_group = []
        
        if current_words:
            groups.append({
                "text": " ".join(current_words),
                "start": current_group[0]["start"],
                "end": current_group[-1]["end"]
            })
            
        return groups

    async def create_video(self):
        try:
            communicate = edge_tts.Communicate(self.script_text, 'en-US-GuyNeural', rate='+20%', pitch="-30Hz")

            async for event in communicate.stream():
                if event["type"] == "WordBoundary":
                    offset = event.get("offset", 0)
                    duration = event.get("duration", 0)
                    word = event["text"]
                    
                    if self.word_timings:
                        last_timing = self.word_timings[-1]
                        if offset / 10000000 <= last_timing["end"]:
                            offset = int((last_timing["end"] + 0.05) * 10000000)
                    
                    self.word_timings.append({
                        "text": word,
                        "start": offset / 10000000,
                        "end": (offset + duration) / 10000000
                    })

            save_communicate = edge_tts.Communicate(self.script_text, 'en-US-GuyNeural', rate='+20%', pitch="-30Hz")
            await save_communicate.save('temp_audio.mp3')
            
            with mpe.AudioFileClip('temp_audio.mp3') as audio:
                video = mpe.VideoFileClip(self.background)
                
                if video.size[0] > video.size[1]:
                    video = video.resize(height=1920)
                    x1 = (video.size[0] - 1080) / 2
                    video = video.crop(x1=x1, y1=0, x2=x1+1080, y2=1920)
                
                max_start = max(0, video.duration - audio.duration)
                if max_start > 0:
                    start_time = random.uniform(0, max_start)
                    video = video.subclip(start_time, start_time + audio.duration)
                else:
                    video = video.loop(duration=audio.duration)

                word_clips = []
                for timing in self.word_timings:
                    word_clip = self.create_word_clip(timing["text"])
                    word_clip = word_clip.set_position('center')
                    word_clip = word_clip.set_start(timing["start"])
                    word_clip = word_clip.set_duration(timing["end"] - timing["start"])
                    word_clips.append(word_clip)

                final = mpe.CompositeVideoClip([video, *word_clips])
                final = final.set_audio(audio)
                
                final.write_videofile(
                    self.output_filename,
                    fps=60,
                    codec='libx264',
                    audio_codec='aac'
                )
                
                final.close()
                video.close()
                
        finally:
            if os.path.exists("temp_audio.mp3"):
                os.remove("temp_audio.mp3")

scraper = RedditScraper(
    client_id="t1Gf6DTH55XRtJa9vejW6Q",
    client_secret="JF6VXLrOvsGK0WGsb_ggzRF1oms3QQ", 
    user_agent="moneyprinter",
    subreddit_name="AmItheAsshole"
)

posts = scraper.fetch_posts(limit=20) 

script = None

if posts:
    selected_post = random.choice(posts)
    script = f"{selected_post['title']}\n\n{selected_post['text']}"
    print(f"Selected Post: {selected_post['title']}")
else:
    raise Exception("Post is None, Check subreddit name")


generator = ShortsGenerator(
    script_text=script,
    background_video="minecraft_parkour.mp4",
    output_filename="output_short.mp4"
)
asyncio.run(generator.create_video())