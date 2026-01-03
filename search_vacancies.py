import json
import os
import sys
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Configuration
N8N_FILES_DIR = os.getenv("N8N_FILES_DIR", r"C:\Users\Joindev\.n8n-files")
SESSION_FILE = os.path.join(N8N_FILES_DIR, "hh_session.json")
SEARCH_TEXT = os.getenv("DEFAULT_SEARCH_TEXT", "Frontend") # Default, can be overridden by args
AREA_CODE = os.getenv("AREA_CODE", "113") # Russia

def get_vacancy_description(page, vacancy_url):
    """
    Переходит на страницу вакансии и извлекает полное описание
    """
    try:
        page.goto(vacancy_url, wait_until="domcontentloaded", timeout=15000)
        
        # Ждем загрузки описания вакансии
        page.wait_for_selector("[data-qa='vacancy-description']", timeout=10000)
        
        # Получаем полное описание
        description_el = page.locator("[data-qa='vacancy-description']")
        full_description = description_el.inner_text() if description_el.count() > 0 else ""
        
        return full_description.strip()
    except Exception as e:
        print(f"Warning: Failed to get description for {vacancy_url}: {str(e)}", file=sys.stderr)
        return ""

def search_vacancies(query=SEARCH_TEXT, page_num=0):
    if not os.path.exists(SESSION_FILE):
        print(json.dumps({"error": "Session file not found. Run hh_login.py first."}))
        return

    with sync_playwright() as p:
        # Launch browser (headless for automation)
        browser = p.chromium.launch(headless=True)
        # Create context with saved storage state (cookies/local storage)
        try:
            context = browser.new_context(storage_state=SESSION_FILE)
        except Exception as e:
            print(json.dumps({"error": f"Failed to load session: {str(e)}"}))
            browser.close()
            return

        page = context.new_page()
        
        # Build Search URL with pagination
        url = f"https://hh.ru/search/vacancy?text={query}&area={AREA_CODE}&items_on_page=20&page={page_num}"
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            
            # Check if we triggered bot protection
            if "captcha" in page.title().lower() or "robot" in page.content().lower():
               print(json.dumps({"error": "Bot protection triggered"}))
               return

            # Wait for results to appear
            page.wait_for_selector("[data-qa='vacancy-serp__vacancy']", timeout=10000)
            
            # Сначала собираем все базовые данные со страницы поиска
            vacancy_data = []
            cards = page.locator("[data-qa='vacancy-serp__vacancy']").all()
            
            for i, card in enumerate(cards):
                try:
                    title_el = card.locator("[data-qa='serp-item__title']")
                    
                    # Ждем появления элемента перед получением атрибутов
                    title_el.wait_for(state="visible", timeout=5000)
                    
                    href = title_el.get_attribute("href")
                    title = title_el.inner_text()
                    
                    # Employer
                    employer_el = card.locator("[data-qa='vacancy-serp__vacancy-employer']").first
                    employer = employer_el.inner_text() if employer_el.count() > 0 else "Unknown"
                    
                    vacancy_data.append({
                        "title": title,
                        "url": href,
                        "employer": employer
                    })
                except Exception as e:
                    print(f"Warning: Failed to parse vacancy card {i}: {str(e)}", file=sys.stderr)
                    continue
            
            # Теперь получаем полные описания для каждой вакансии
            vacancies = []
            for data in vacancy_data:
                full_description = get_vacancy_description(page, data["url"])
                
                vacancies.append({
                    "title": data["title"],
                    "url": data["url"],
                    "employer": data["employer"],
                    "description": full_description
                })
                
            # Output JSON for n8n
            if __name__ == "__main__":
                print(json.dumps(vacancies, ensure_ascii=False, indent=2))
            
            return vacancies
            
        except Exception as e:
            err = {"error": str(e)}
            if __name__ == "__main__":
                print(json.dumps(err))
            return err
        finally:
            browser.close()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else SEARCH_TEXT
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    search_vacancies(query, page_num)
