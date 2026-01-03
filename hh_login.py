import os
import sys
import json
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Path allowed by n8n
N8N_FILES_DIR = os.getenv("N8N_FILES_DIR", r"C:\Users\Joindev\.n8n-files")
SESSION_FILE = os.path.join(N8N_FILES_DIR, "hh_session.json")

def ensure_dir():
    if not os.path.exists(N8N_FILES_DIR):
        print(f"Creating directory: {N8N_FILES_DIR}")
        os.makedirs(N8N_FILES_DIR)

def login():
    ensure_dir()
    with sync_playwright() as p:
        # Launch browser in headed mode so user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        page = context.new_page()
        page.goto("https://hh.ru/login")
        
        print("Please log in to HH.ru in the opened browser window.")
        print("Wait until you see your personal profile or resumes page.")
        print("Once logged in, come back here and press Enter...")
        
        # Verify login by checking for specific element
        try:
            page.wait_for_selector("a[href*='/resume']", timeout=0) # Wait indefinitely until user navigates to a page with resume link (indicating login) or we could just trust the user
        except:
            pass
            
        input("Press Enter after you have successfully logged in...")
        
        # Get and print the User Agent
        ua = page.evaluate("navigator.userAgent")
        print("\n" + "="*50)
        print(f"CRITICAL: Link this User-Agent in n8n headers:\n{ua}")
        print("="*50 + "\n")
        
        # Save storage state (cookies, local storage)
        context.storage_state(path=SESSION_FILE)
        print(f"Session saved to {SESSION_FILE}")
        
        browser.close()

def get_cookies():
    if not os.path.exists(SESSION_FILE):
        print("No session file found. Please run login first.")
        return None
    
    with open(SESSION_FILE, 'r') as f:
        state = json.load(f)
        cookies = state.get('cookies', [])
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        return cookie_str

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--get-cookies":
        print(get_cookies())
    else:
        login()
