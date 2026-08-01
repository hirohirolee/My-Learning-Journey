import streamlit as st

import os
import re
import ssl
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser

class MovieParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.movies = []
        self.current_movie = {}
        self.in_h2 = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # Match the cover image
        if tag == "img" and attrs_dict.get("class") == "cover":
            src = attrs_dict.get("src")
            if src:
                self.current_movie["cover"] = src
        # Match the title container
        elif tag == "h2" and attrs_dict.get("class") == "m-b-sm":
            self.in_h2 = True
            
    def handle_data(self, data):
        if self.in_h2:
            self.current_movie["title"] = data.strip()
            
    def handle_endtag(self, tag):
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
            # If we have both cover and title, store it
            if "cover" in self.current_movie and "title" in self.current_movie:
                self.movies.append(self.current_movie)
                self.current_movie = {}

def sanitize_filename(name):
    # Remove characters that are illegal in Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_posters():
    html_path = "page1.html"
    if not os.path.exists(html_path):
        st.write(f"Error: '{html_path}' does not exist. Please run crawler.py first.")
        return
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Parse HTML content
    parser = MovieParser()
    parser.feed(html_content)
    movies = parser.movies

    if not movies:
        st.write("No movies found in the HTML file!")
        return

    output_dir = "posters"
    os.makedirs(output_dir, exist_ok=True)
    st.write(f"Found {len(movies)} movies. Downloading to folder '{output_dir}'...\n")

    # Bypassing SSL verification if needed for external image hosting servers
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for idx, movie in enumerate(movies, 1):
        img_url = movie["cover"]
        raw_title = movie["title"]
        
        # Clean title to use as filename
        title = raw_title.split("-")[0].strip()
        safe_title = sanitize_filename(title)
        
        # Extract extension or default to .jpg
        ext = ".jpg"
        if ".png" in img_url.lower():
            ext = ".png"
            
        filename = f"{idx}_{safe_title}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        st.write(f"Downloading [{idx}/{len(movies)}]: {title}")
        st.write(f"  URL: {img_url}")
        
        try:
            req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                img_data = response.read()
            with open(filepath, "wb") as f:
                f.write(img_data)
            st.write(f"  -> Saved to: {filepath}\n")
        except Exception as e:
            st.write(f"  -> Failed to download: {e}\n", file=sys.stderr)

    st.write("Finished downloading all available posters.")

if __name__ == "__main__":
    # Configure console output streams to use UTF-8 encoding to avoid Windows console Unicode errors
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    download_posters()
