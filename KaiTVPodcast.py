import os
from datetime import datetime
import xml.etree.ElementTree as ET

# -----------------------
# CONFIG
# -----------------------
rss_file = "feed.xml"  # Path to your RSS file
mp3_filename = "tech_news_podcast_2026-03-29_190239.mp3"  # Today's generated MP3
mp3_url_base = "https://DadKai.github.io/Kai-TV-News/"  # Base URL for GitHub Pages

# -----------------------
# STEP 1: Load or create RSS
# -----------------------
if os.path.exists(rss_file):
    tree = ET.parse(rss_file)
    root = tree.getroot()
    channel = root.find("channel")
else:
    # Create fresh RSS
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

# -----------------------
# STEP 2: Add today's episode
# -----------------------
now = datetime.now()
pub_date_str = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
title_str = now.strftime("Daily Tech News - %B %d, %Y")

item = ET.SubElement(channel, "item")
ET.SubElement(item, "title").text = title_str
ET.SubElement(item, "description").text = "Latest tech news from TechCrunch, The Verge, and Hacker News."
ET.SubElement(item, "pubDate").text = pub_date_str
ET.SubElement(item, "enclosure", url=f"{mp3_url_base}{mp3_filename}", type="audio/mpeg")
ET.SubElement(item, "guid").text = f"{mp3_url_base}{mp3_filename}"

# -----------------------
# STEP 3: Save back to file
# -----------------------
ET.indent(tree, space="  ") if hasattr(ET, 'indent') else None  # Pretty print Python 3.9+
tree.write(rss_file, encoding="utf-8", xml_declaration=True)

print(f"RSS updated with {mp3_filename}")
