import requests
import feedparser
from datetime import datetime
import re
import html
import time
from gtts import gTTS
import os
import tempfile
import xml.etree.ElementTree as ET
import shutil

# -----------------------
# Helper: Clean text
# -----------------------
def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'["“”]', '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r'[–—]', '-', text)
    text = re.sub(r'[…]', '...', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = ' '.join(text.split())
    return text.strip()

# -----------------------
# Fetch feeds
# -----------------------
def fetch_techcrunch_news(limit=10):
    try:
        feed = feedparser.parse('https://techcrunch.com/feed/')
        stories = []
        for entry in feed.entries[:limit]:
            title = clean_text(entry.title)
            summary = getattr(entry, 'summary', '')
            summary = clean_text(summary) if summary else 'TechCrunch breaking news.'
            stories.append({'title': title, 'link': entry.link, 'summary': summary, 'source': 'TechCrunch'})
        return stories
    except Exception as e:
        print(f"Error fetching TechCrunch: {e}")
        return []

def fetch_verge_news(limit=10):
    try:
        feed = feedparser.parse('https://www.theverge.com/rss/index.xml')
        stories = []
        for entry in feed.entries[:limit]:
            title = clean_text(entry.title)
            summary = getattr(entry, 'summary', '')
            summary = clean_text(summary) if summary else 'The Verge tech news.'
            stories.append({'title': title, 'link': entry.link, 'summary': summary, 'source': 'The Verge'})
        return stories
    except Exception as e:
        print(f"Error fetching The Verge: {e}")
        return []

def fetch_hackernews_top(limit=10):
    try:
        top_stories_url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
        response = requests.get(top_stories_url, timeout=10)
        story_ids = response.json()[:limit]
        stories = []
        for story_id in story_ids:
            try:
                story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                story_response = requests.get(story_url, timeout=5)
                story_data = story_response.json()
                if story_data and story_data.get('title'):
                    title = clean_text(story_data['title'])
                    score = story_data.get('score', 0)
                    comments = story_data.get('descendants', 0)
                    by = story_data.get('by', 'Unknown')
                    time_posted = story_data.get('time', 0)
                    post_datetime = datetime.fromtimestamp(time_posted) if time_posted else datetime.now()
                    hours_ago = (datetime.now() - post_datetime).total_seconds() / 3600
                    time_context = f"about {int(hours_ago)} hours ago" if hours_ago < 24 else f"{int(hours_ago/24)} days ago"
                    summary = f"This story has {score} points and {comments} comments on Hacker News, posted {time_context} by {by}."
                    stories.append({'title': title, 'link': story_data.get('url', f'https://news.ycombinator.com/item?id={story_id}'), 'summary': summary, 'source': 'Hacker News'})
            except Exception as e:
                continue
        return stories
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
        return []

# -----------------------
# Create podcast script
# -----------------------
def create_podcast_script(stories_dict):
    current_date = datetime.now().strftime("%B %d, %Y")
    script = f"Welcome to Kai TV Tech News, your Daily Tech News Podcast for {current_date}.\n\n"
    source_intros = {
        'TechCrunch': 'First, the latest from TechCrunch.',
        'The Verge': 'Next, stories from The Verge.',
        'Hacker News': "Finally, what's trending on Hacker News."
    }
    for source_name, stories in stories_dict.items():
        if stories:
            script += f"\n{source_intros.get(source_name, f'Stories from {source_name}.')}\n"
            for i, story in enumerate(stories, 1):
                title = re.sub(r'[^\w\s\-.,!?():]', ' ', story['title'])
                summary = re.sub(r'[^\w\s\-.,!?():]', ' ', story['summary'])
                summary = ' '.join(summary.split()[:50])
                script += f"Story {i}: {title}\n{summary}\n\n"
    script += "That wraps up today's tech news digest from Kai TV Tech News. Stay informed.\n"
    return script

# -----------------------
# Generate MP3
# -----------------------
def generate_podcast_audio(script, filename):
    try:
        tts = gTTS(text=script, lang='en', slow=False, tld='com')
        tts.save(filename)
        return True
    except Exception as e:
        print(f"Audio generation failed: {e}")
        return False

# -----------------------
# Update podcasts.xml
# -----------------------
def update_rss(mp3_filename, rss_file="podcasts.xml"):
    mp3_url_base = "https://DadKai.github.io/Kai-TV-News/"
    if os.path.exists(rss_file):
        tree = ET.parse(rss_file)
        root = tree.getroot()
        channel = root.find("channel")
    else:
        root = ET.Element("rss", version="2.0", attrib={"xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = "Kai TV Tech News"
        ET.SubElement(channel, "link").text = mp3_url_base
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "description").text = "Daily tech news podcast covering startups, AI, and innovation."
        ET.SubElement(channel, "itunes:author").text = "Kai TV"
        ET.SubElement(channel, "itunes:summary").text = "Daily AI-generated tech news podcast."
        ET.SubElement(channel, "itunes:explicit").text = "false"
        ET.SubElement(channel, "itunes:image", href=f"{mp3_url_base}podcast-cover.png")
    now = datetime.now()
    pub_date_str = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    title_str = now.strftime("Daily Tech News - %B %d, %Y")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title_str
    ET.SubElement(item, "description").text = "Latest tech news from TechCrunch, The Verge, and Hacker News."
    ET.SubElement(item, "pubDate").text = pub_date_str
    ET.SubElement(item, "enclosure", url=f"{mp3_url_base}{mp3_filename}", type="audio/mpeg")
    ET.SubElement(item, "guid").text = f"{mp3_url_base}{mp3_filename}"
    ET.indent(tree, space="  ") if hasattr(ET, 'indent') else None
    tree.write(rss_file, encoding="utf-8", xml_declaration=True)

# -----------------------
# Generate HTML news
# -----------------------
def generate_html_news(stories_dict):
    date_str = datetime.now().strftime("%B %d, %Y")
    timestamp_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    html_filename = f"tech_news_{timestamp_str}.html"
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Daily Tech News Digest - {date_str}</title></head>
<body>
<h1>Daily Tech News Digest</h1>
<p>Date: {date_str}</p>
"""
    for source_name, stories in stories_dict.items():
        html_content += f"<h2>{source_name}</h2>\n"
        for story in stories:
            html_content += f"<h3><a href='{story['link']}'>{story['title']}</a></h3>\n<p>{story['summary']}</p>\n"
    html_content += "</body></html>"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_filename

# -----------------------
# Main execution
# -----------------------
if __name__ == "__main__":
    sources = {
        'TechCrunch': fetch_techcrunch_news(),
        'The Verge': fetch_verge_news(),
        'Hacker News': fetch_hackernews_top()
    }

    # Generate HTML
    html_file = generate_html_news(sources)

    # Generate podcast
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    mp3_filename = f"tech_news_podcast_{timestamp}.mp3"
    script = create_podcast_script(sources)
    generate_podcast_audio(script, mp3_filename)

    # Update RSS feed
    update_rss(mp3_filename)

    # Optional: keep latest copy for simple URL
    shutil.copy(mp3_filename, "latest.mp3")

    print(f"HTML file: {html_file}")
    print(f"MP3 file: {mp3_filename}")
    print("podcasts.xml updated")
