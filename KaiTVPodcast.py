import requests
import feedparser
from datetime import datetime
import re
import html
import time
import pyttsx3
import os
from gtts import gTTS
import tempfile
 
 
def clean_text(text):
    """Clean text by removing special characters and HTML tags"""
    if not text:
        return ""
   
    # Decode HTML entities
    text = html.unescape(text)
   
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
   
    # Remove common problematic characters and replace with clean alternatives
    text = re.sub(r'["""]', '"', text)  # Smart quotes to regular quotes
    text = re.sub(r"['']", "'", text)   # Smart apostrophes to regular apostrophes
    text = re.sub(r'[–—]', '-', text)   # Em/en dashes to regular dashes
    text = re.sub(r'[…]', '...', text)  # Ellipsis
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
   
    # Clean up whitespace
    text = ' '.join(text.split())
   
    return text.strip()
 
 
def fetch_techcrunch_news(limit=10):
    """Fetch latest TechCrunch headlines and summaries"""
    try:
        feed = feedparser.parse('https://techcrunch.com/feed/')
        stories = []
        for entry in feed.entries[:limit]:
            title = clean_text(entry.title)
           
            # Use the best available content field (prioritized, not combined)
            summary = ""
            if hasattr(entry, 'summary') and entry.summary:
                summary = clean_text(entry.summary)
            elif hasattr(entry, 'content') and entry.content:
                # Use the first content item
                if entry.content[0].value:
                    summary = clean_text(entry.content[0].value)
            elif hasattr(entry, 'description') and entry.description:
                summary = clean_text(entry.description)
           
            # Keep reasonable length for reading
            if summary and len(summary) > 1500:
                sentences = summary.split('. ')
                truncated_summary = ''
                for sentence in sentences:
                    if len(truncated_summary + sentence + '. ') < 1500:
                        truncated_summary += sentence + '. '
                    else:
                        break
                summary = truncated_summary.strip() if truncated_summary else summary[:1500] + '...'
           
            if not summary:
                summary = 'This is a breaking news story from TechCrunch covering the latest developments in technology and startups.'
           
            stories.append({
                'title': title,
                'link': entry.link,
                'summary': summary.strip(),
                'source': 'TechCrunch'
            })
        return stories
    except Exception as e:
        print(f"Error fetching TechCrunch: {e}")
        return []
 
def fetch_verge_news(limit=10):
    """Fetch latest The Verge headlines and summaries"""
    try:
        feed = feedparser.parse('https://www.theverge.com/rss/index.xml')
        stories = []
        for entry in feed.entries[:limit]:
            title = clean_text(entry.title)
           
            # Use the best available content field (prioritized, not combined)
            summary = ""
            if hasattr(entry, 'summary') and entry.summary:
                summary = clean_text(entry.summary)
            elif hasattr(entry, 'content') and entry.content:
                # Use the first content item
                if entry.content[0].value:
                    summary = clean_text(entry.content[0].value)
            elif hasattr(entry, 'description') and entry.description:
                summary = clean_text(entry.description)
           
            # Keep reasonable length for reading
            if summary and len(summary) > 1500:
                sentences = summary.split('. ')
                truncated_summary = ''
                for sentence in sentences:
                    if len(truncated_summary + sentence + '. ') < 1500:
                        truncated_summary += sentence + '. '
                    else:
                        break
                summary = truncated_summary.strip() if truncated_summary else summary[:1500] + '...'
           
            if not summary:
                summary = 'This is a story from The Verge covering technology, science, art, and culture, exploring how technology is changing our world.'
           
            stories.append({
                'title': title,
                'link': entry.link,
                'summary': summary.strip(),
                'source': 'The Verge'
            })
        return stories
    except Exception as e:
        print(f"Error fetching The Verge: {e}")
        return []
 
def fetch_hackernews_top(limit=10):
    """Fetch top Hacker News stories with comprehensive details"""
    try:
        top_stories_url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
        response = requests.get(top_stories_url, timeout=10, verify=False)
        story_ids = response.json()[:limit]
        stories = []
        for story_id in story_ids:
            try:
                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=5, verify=False)
                story_data = story_response.json()
                if story_data and story_data.get('title'):
                    title = clean_text(story_data['title'])
                   
                    # Create concise, informative summary for Hacker News stories
                    score = story_data.get('score', 0)
                    comments = story_data.get('descendants', 0)
                    by = story_data.get('by', 'Unknown')
                    time_posted = story_data.get('time', 0)
                   
                    # Convert timestamp to readable format
                    if time_posted:
                        post_datetime = datetime.fromtimestamp(time_posted)
                        readable_time = post_datetime.strftime('%B %d, %Y')
                        hours_ago = (datetime.now() - post_datetime).total_seconds() / 3600
                        if hours_ago < 24:
                            time_context = f"about {int(hours_ago)} hours ago"
                        else:
                            days_ago = int(hours_ago / 24)
                            time_context = f"{days_ago} day{'s' if days_ago > 1 else ''} ago"
                    else:
                        readable_time = 'recently'
                        time_context = 'recently'
                   
                    # Create a focused summary without repetition
                    summary = f"This story has {score} points and {comments} comments on Hacker News, posted {time_context} by {by}. "
                   
                    if score > 300:
                        summary += "This is a highly popular story that has captured significant community attention, indicating important tech industry developments or thought-provoking content."
                    elif score > 100:
                        summary += "This story has generated solid engagement from the tech community, suggesting valuable insights or noteworthy developments."
                    else:
                        summary += "This is an emerging story gaining traction among developers and tech professionals."
                   
                    stories.append({
                        'title': title,
                        'link': story_data.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                        'summary': summary,
                        'source': 'Hacker News'
                    })
            except Exception as e:
                print(f"Error fetching Hacker News story {story_id}: {e}")
                continue
        return stories
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
        return []
 
 
def create_podcast_script(stories_dict):
    """Create a natural-sounding podcast script from news stories"""
    current_date = datetime.now().strftime("%B %d, %Y")
   
    # Podcast introduction
    script = f"""
    Welcome to Kai TV Tech News, brought to you by The Dad-Son Tech Lab.
    This is your Daily Tech News Podcast for {current_date}.
    I'm your AI host Kai bringing you the latest developments in technology, startups, and digital innovation.
   
    Today we're covering stories from TechCrunch, The Verge, and the top discussions from Hacker News.
    Let's dive into today's tech headlines.
   
    """
   
    # Add each source section
    source_intros = {
        'TechCrunch': 'First, let\'s start with the latest from TechCrunch, covering startup news and venture capital.',
        'The Verge': 'Next, we have stories from The Verge, focusing on technology, science, and digital culture.',
        'Hacker News': 'Finally, let\'s look at what\'s trending on Hacker News, the front page of the internet for developers and tech enthusiasts.'
    }
   
    for source_name, stories in stories_dict.items():
        if stories:
            script += f"\n\n{source_intros.get(source_name, f'Now, stories from {source_name}.')}\n\n"
           
            for i, story in enumerate(stories, 1):
                # Clean the title for speech
                title = story['title'].replace('&', 'and')
                title = re.sub(r'[^\w\s\-.,!?():]', ' ', title)
                title = ' '.join(title.split()).strip()
               
                # Create a concise summary for audio (limit to 50 words max)
                summary = story['summary'].replace('&', 'and')
                summary = re.sub(r'[^\w\s\-.,!?():]', ' ', summary)
                summary_words = summary.split()[:50]  # Limit to 50 words
                summary = ' '.join(summary_words).strip()
               
                # Add the story (no duplication)
                script += f"Story {i}: {title}\n\n{summary}\n\n"
               
                # Add a natural pause between stories (but not after the last one)
                if i < len(stories):
                    script += "Moving on to our next story.\n\n"
   
    # Podcast conclusion
    script += """
   
    That wraps up today's tech news digest from Kai TV Tech News.
    Stay curious, stay informed, and keep innovating.
    This has been your Daily Tech News Podcast from The Dad-Son Tech Lab.
    We'll be back tomorrow with more of the latest in technology.
    Thanks for listening!
    """
   
    return script.strip()
 
 
def generate_podcast_audio(script, filename):
    """Generate MP3 audio file from text script using Google TTS"""
    try:
        print("🎙️ Generating podcast audio with Google TTS...")
       
        # Use Google TTS for natural-sounding voice
        tts = gTTS(text=script, lang='en', slow=False, tld='com')
        tts.save(filename)
        print(f"✅ High-quality podcast MP3 created: {filename}")
        return True
       
    except Exception as e:
        print(f"⚠️ Could not generate audio: {e}")
        print("💡 Audio generation requires internet connection for Google TTS")
        print("📝 Continuing with HTML-only version...")
        return False
 
 
def generate_html_news():
    """Generate beautiful HTML news digest and save to file"""
    current_date = datetime.now()
    date_str = current_date.strftime("%B %d, %Y")
    timestamp_str = current_date.strftime('%Y-%m-%d_%H%M%S')
    html_filename = f"tech_news_{timestamp_str}.html"
    audio_filename = f"tech_news_podcast_{timestamp_str}.mp3"
   
    sources = [
        (fetch_techcrunch_news, 'TechCrunch', '#e74c3c', '#2c3e50'),
        (fetch_verge_news, 'The Verge', '#673ab7', '#2c3e50'),
        (fetch_hackernews_top, 'Hacker News', '#f39c12', '#2c3e50')
    ]
   
    # Collect stories for both HTML and podcast
    all_stories = {}
 
    # CSS styles for beautiful formatting
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Tech News Digest - {date_str}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin: 20px 0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 3px solid #667eea;
            }}
            .header h1 {{
                color: #2c3e50;
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: bold;
            }}
            .header .date {{
                color: #7f8c8d;
                font-size: 1.2em;
                font-style: italic;
            }}
            .source-section {{
                margin: 40px 0;
                background: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
                border-left: 5px solid #667eea;
            }}
            .source-title {{
                font-size: 1.8em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 25px;
                padding-bottom: 10px;
                border-bottom: 2px solid #ecf0f1;
            }}
            .article {{
                background: white;
                border-radius: 10px;
                padding: 35px;
                margin: 30px 0;
                box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                border-left: 5px solid #667eea;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .article:hover {{
                transform: translateY(-3px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.18);
            }}
            .article-title {{
                font-size: 1.4em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
                line-height: 1.4;
            }}
            .article-title a {{
                color: #2c3e50;
                text-decoration: none;
                transition: color 0.3s ease;
            }}
            .article-title a:hover {{
                color: #667eea;
            }}
            .article-summary {{
                color: #444;
                font-size: 1.05em;
                line-height: 1.8;
                margin-bottom: 25px;
                text-align: justify;
                padding: 0 8px;
                max-width: none;
            }}
            .article-link {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                text-decoration: none;
                font-size: 0.9em;
                transition: background 0.3s ease;
            }}
            .article-link:hover {{
                background: #5a67d8;
            }}
            .no-stories {{
                color: #e74c3c;
                font-style: italic;
                text-align: center;
                padding: 30px;
                background: #fdf2f2;
                border-radius: 5px;
                border: 1px solid #fed7d7;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                color: #95a5a6;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📰 Daily Tech News Digest</h1>
                <div class="date">{date_str}</div>
            </div>
    """
 
    for fetch_func, source_name, primary_color, text_color in sources:
        html_content += f"""
            <div class="source-section">
                <div class="source-title">{source_name}</div>
        """
       
        try:
            stories = fetch_func()
            all_stories[source_name] = stories  # Store for podcast
           
            if stories:
                for story in stories:
                    html_content += f"""
                    <div class="article">
                        <div class="article-title">
                            <a href="{story['link']}" target="_blank">{story['title']}</a>
                        </div>
                        <div class="article-summary">{story['summary']}</div>
                        <a href="{story['link']}" target="_blank" class="article-link">Read Full Article</a>
                    </div>
                    """
            else:
                html_content += f'<div class="no-stories">No stories available from {source_name} at this time.</div>'
        except Exception as e:
            html_content += f'<div class="no-stories">Error loading {source_name}: {str(e)}</div>'
            all_stories[source_name] = []  # Empty list for podcast
       
        html_content += "</div>"
 
    html_content += f"""
            <div class="footer">
                <p>Generated by Daily Tech News Script | Created on {current_date.strftime("%B %d, %Y at %I:%M %p")}</p>
                <p>Stay informed, stay ahead!  🚀</p>
                <p>📻 Audio podcast version: {audio_filename}</p>
            </div>
        </div>
    </body>
    </html>
    """
 
    # Save HTML file
    try:
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Beautiful HTML news digest created: {html_filename}")
       
        # Generate podcast
        print("🎙️ Creating podcast version...")
        script = create_podcast_script(all_stories)
        podcast_success = generate_podcast_audio(script, audio_filename)
       
        if podcast_success:
            print(f"📻 Podcast audio file created: {audio_filename}")
       
        print(f"📂 Files location: {html_filename}")
        return html_filename
       
    except Exception as e:
        print(f"❌ Error creating files: {e}")
        return None
 
if __name__ == "__main__":
    generate_html_news()
