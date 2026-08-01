import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Camila Cabello's Best Songs and Moments",
        "The Voice of Camila Cabello",
        "Camila Cabello — Pop Star and Icon",
        "Best Camila Cabello Performances",
        "From Fifth Harmony to Solo Stardom: Camila Cabello",
        "Camila Cabello's Journey to the Top",
        "Top 5 Camila Cabello Songs You Need to Hear",
        "Camila Cabello Moments That Made Us Fall in Love",
        "The Magic of Camila Cabello's Voice",
        "Camila Cabello Through the Years",
        "Why Camila Cabello Is One of Pop's Brightest Stars",
        "Behind the Scenes With Camila Cabello",
        "Camila Cabello's Most Powerful Performances",
        "Rediscovering Camila Cabello's Music",
        "A Tribute to Camila Cabello",
    ]

    fallback_descriptions = [
        "From her breakout in Fifth Harmony to ruling the charts as a solo artist, Camila Cabello has become one of pop music's brightest stars. Her voice is unmistakable, her songs unforgettable. This tribute celebrates the singer who captured our hearts. Drop a 🎤 if you love Camila Cabello! #camilacabello #music #pop #singer #charts #havana #señorita #fanpage #tribute #camilasquad",
        "Camila Cabello didn't just become a pop star — she became a voice for a generation. From Havana to Señorita, her songs are anthems of love, growth, and self-discovery. Here's a look at the moments that defined her incredible career. Like if you admire her talent! ✨ #camilacabello #havana #señorita #music #pop #singer #charts #tribute #fanpage #camilasquad",
        "There are voices, and then there's Camila Cabello's. With her soulful tone and emotional delivery, she has delivered some of the most beloved pop songs of our time. These are the performances that showcase her incredible range. Comment your favorite Camila Cabello song below! 🎥 #camilacabello #music #songs #bestperformances #pop #singer #tribute #fanpage #camilasquad #charts",
        "Camila Cabello's rise to fame is a story of talent, heart, and hard work. From Miami to the global stage, she has inspired millions with her music and her authenticity. This tribute honors her remarkable journey. Share this with a fellow Camila fan! 🌟 #camilacabello #journey #music #pop #singer #inspiration #tribute #fanpage #camilasquad #charts",
        "Whether she's singing about love in Havana or friendship in Señorita, Camila Cabello brings emotion and authenticity to every song. Her music speaks to the heart. Double tap if Camila Cabello is one of your favorites! 💛 #camilacabello #havana #señorita #music #pop #singer #charts #tribute #fanpage #camilasquad",
        "Camila Cabello's style and stage presence are as captivating as her voice. With grace, energy, and genuine warmth, she lights up every stage she performs on. These moments show the woman behind the hits. Which look is your favorite? Comment below! 👗 #camilacabello #style #fashion #redcarpet #music #pop #singer #elegance #tribute #fanpage",
        "A career full of unforgettable songs. From Crying in the Club to Bam Bam, Camila Cabello has given us anthems for every mood. Her dedication to her craft is unmatched. Save this for your next playlist! 🍿 #camilacabello #songs #music #pop #singer #charts #cryingintheclub #bambam #fanpage #tribute",
        "Behind every powerful performance is a person of incredible warmth. Camila Cabello's humor, honesty, and authenticity shine through in interviews and behind-the-scenes moments. Here's a look at the real woman behind the music. Like if you appreciate her authenticity! 🎥 #camilacabello #behindthescenes #authentic #interview #music #pop #singer #tribute #fanpage #bts",
        "Camila Cabello's words inspire as much as her music. Her thoughts on self-love, growth, and staying true to yourself resonate with fans worldwide. These are the moments where she shared her heart. Share this with someone who needs the reminder! 💬 #camilacabello #quotes #inspiration #selflove #authenticity #music #pop #singer #tribute #fanpage",
        "From chart-topping singles to acclaimed albums, Camila Cabello has proven her incredible versatility as an artist. Her ability to blend pop, Latin, and soul sets her apart. Here's to her most powerful performances. Comment your favorite song! 🏆 #camilacabello #music #pop #singer #charts #greatest #albums #tribute #fanpage #camilasquad",
        "What makes Camila Cabello extraordinary? Her voice, her heart, and her ability to connect with listeners. Whether upbeat or emotional, her music speaks to people of all ages. This fan tribute celebrates her artistry. Drop a ❤️ if you're a Camila fan! #camilacabello #music #artistry #pop #singer #charts #tribute #fanpage #camilasquad #voice",
        "Some artists leave a mark on music forever. Camila Cabello is one of them. Her songs are part of the soundtrack of our lives, and her legacy continues to grow. Here's a celebration of her greatest moments. Like if you agree! 🌟 #camilacabello #legacy #music #pop #singer #charts #inspiration #tribute #fanpage #camilasquad",
        "There's an undeniable magic in Camila Cabello's music. From intimate ballads to dance-floor anthems, she captivates listeners every single time. This is a celebration of her incredible body of work and the joy she brings to fans. Double tap for Camila! ✨ #camilacabello #music #pop #singer #charts #camilasquad #tribute #fanpage #voice",
        "One artist. Countless unforgettable songs. Camila Cabello has given the world music that speaks to love, growth, and dreaming big. Her voice carries stories that touch hearts around the globe. Share this with a fellow Camila fan! 🦸‍♀️ #camilacabello #music #pop #singer #charts #iconic #tribute #fanpage #camilasquad",
        "Camila Cabello proves that true talent and heart never fade. Her enduring career is a testament to her dedication, her authenticity, and her love for music. This fan tribute is our little way of celebrating her impact. Like if Camila Cabello inspires you! 💖 #camilacabello #music #pop #singer #charts #legacy #inspiration #tribute #fanpage #camilasquad",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "admiring and celebratory — speak as a devoted fan paying tribute",
        "energetic and fun — make viewers feel the joy of her music",
        "warm and appreciative — celebrate her talent, heart and authenticity",
        "inspiring and heartfelt — highlight her journey and growth",
        "nostalgic and fond — celebrate the songs and moments fans love",
        "respectful and admiring — appreciate the craft behind the music",
        "bright and uplifting — match the positivity of her personality",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'CamTok Lens'. "
        f"It is a fan page dedicated to the Cuban-American pop singer Camila Cabello, "
        f"best known for Havana, Señorita, Bam Bam, and her time in Fifth Harmony. "
        f"It shares appreciation content, iconic performances, and tributes to her music career. "
        f"It is an unofficial fan page that does not impersonate anyone - just celebrates her work. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if you love Camila Cabello! Comment your favorite Camila Cabello song below! Share this with a fellow Camila fan! Follow CamTok Lens for daily Camila Cabello appreciation! "
        f"Include relevant hashtags in ALL LOWERCASE such as #camilacabello #havana #señorita #music #pop #singer #charts #fifthharmony #bambam #camilasquad #fanpage #appreciation #performance #tribute. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["camilacabello", "havana", "señorita", "music", "pop", "singer", "charts", "fifthharmony", "bambam", "camilasquad", "fanpage", "appreciation", "performance", "tribute"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
