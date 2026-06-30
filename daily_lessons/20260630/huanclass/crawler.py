import ssl
import sys
import urllib.request
import urllib.error

def fetch_page(url, output_path):
    """
    Fetches the HTML content of the given URL and saves it to the output path.
    Bypasses SSL certificate verification due to expired certificate on the host.
    """
    print(f"Fetching URL: {url}")
    
    # Configure custom SSL context to bypass expired/invalid SSL certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Set up headers to mimic a real browser request
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            html_content = response.read()
            
        with open(output_path, "wb") as f:
            f.write(html_content)
            
        print(f"Success! Saved content to: {output_path}")
        return True
    except urllib.error.URLError as e:
        print(f"URL Error occurred: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    TARGET_URL = "https://ssr1.scrape.center/page/1"
    OUTPUT_FILE = "page1.html"
    fetch_page(TARGET_URL, OUTPUT_FILE)
