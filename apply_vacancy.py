import json
import os
import sys
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Configuration
N8N_FILES_DIR = os.getenv("N8N_FILES_DIR", r"C:\Users\Joindev\.n8n-files")

SESSION_FILE = os.path.join(N8N_FILES_DIR, "hh_session.json")

def apply_to_vacancy(url, message=""):
    print(f"Applying to: {url}")
    print(f"Cover letter length: {len(message) if message else 0} chars")
    
    if not os.path.exists(SESSION_FILE):
        return {"status": "error", "message": "Session file not found"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        try:
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            
            print(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=90000)
            
            if page.locator("text=Вы откликнулись").count() > 0:
                print("Already applied to this vacancy")
                return {"status": "skipped", "message": "Already applied"}

            cover_letter_link = page.locator("a:has-text('Написать сопроводительное')")
            
            if cover_letter_link.count() > 0 and message:
                print("Found 'Write cover letter' link, clicking...")
                cover_letter_link.first.click()
                
                try:
                    print("Waiting for modal window...")
                    page.wait_for_selector("[data-qa='vacancy-response-popup']", timeout=5000)
                    print("Modal appeared!")
                    
                    page.wait_for_timeout(1000)
                    
                    letter_area = page.locator("textarea[data-qa='vacancy-response-popup-form-letter-input']")
                    if letter_area.count() > 0:
                        print(f"Filling cover letter ({len(message)} chars)...")
                        letter_area.fill(message)
                        print("Cover letter filled successfully")
                    else:
                        print("WARNING: Cover letter field not found in modal")
                    
                    submit_btn = page.locator("button[data-qa='vacancy-response-submit-popup']")
                    if submit_btn.count() > 0:
                        print("Clicking submit button...")
                        submit_btn.click()
                        page.wait_for_timeout(3000)
                        print("Application submitted successfully with cover letter")
                        return {"status": "success", "message": "Applied with cover letter"}
                    else:
                        print("ERROR: Submit button not found")
                        return {"status": "error", "message": "Submit button not found"}
                        
                except Exception as e:
                    print(f"Error with cover letter link: {str(e)}")
                    return {"status": "error", "message": f"Error with cover letter: {str(e)}"}
            
            print("Looking for standard apply button...")
            apply_btn = page.locator("[data-qa='vacancy-response-link-top']")
            if apply_btn.count() == 0:
                apply_btn = page.locator("[data-qa='vacancy-response-link-bottom']")
            
            if apply_btn.count() > 0:
                dropdown_arrow = page.locator("[data-qa='vacancy-response-link-top'] + button, [data-qa='vacancy-response-link-bottom'] + button")
                
                if dropdown_arrow.count() > 0 and message:
                    print("Found dropdown arrow, clicking to see options...")
                    dropdown_arrow.first.click()
                    page.wait_for_timeout(500)
                    
                    with_letter_option = page.locator("text=С сопроводительным письмом")
                    if with_letter_option.count() > 0:
                        print("Found 'With cover letter' option, clicking...")
                        with_letter_option.first.click()
                        
                        try:
                            page.wait_for_selector("[data-qa='vacancy-response-popup']", timeout=5000)
                            page.wait_for_timeout(1000)
                            
                            letter_area = page.locator("textarea[data-qa='vacancy-response-popup-form-letter-input']")
                            if letter_area.count() > 0:
                                print(f"Filling cover letter ({len(message)} chars)...")
                                letter_area.fill(message)
                            
                            submit_btn = page.locator("button[data-qa='vacancy-response-submit-popup']")
                            if submit_btn.count() > 0:
                                submit_btn.click()
                                page.wait_for_timeout(3000)
                                print("Application submitted with cover letter")
                                return {"status": "success", "message": "Applied with cover letter"}
                        except Exception as e:
                            print(f"Error with dropdown option: {str(e)}")
                
                print("Clicking standard apply button...")
                apply_btn.first.click()
                page.wait_for_timeout(2000)

                print("Checking for post-apply cover letter field...")
                if page.locator("text=Резюме доставлено").count() > 0 or page.locator("textarea").count() > 0:
                    print("Found post-apply screen ('Резюме доставлено')")
                    
                    letter_area = page.locator("textarea") # Often it's the only textarea here
                    if letter_area.count() > 0 and message:
                        print(f"Filling post-apply letter field ({len(message)} chars)...")
                        letter_area.first.fill(message)
                        
                        submit_btn = page.locator("button:has-text('Отправить')")
                        if submit_btn.count() > 0:
                            print("Clicking 'Send' on post-apply screen...")
                            submit_btn.first.click()
                            page.wait_for_timeout(2000)
                            print("Application with post-apply letter submitted!")
                            return {"status": "success", "message": "Applied with post-apply cover letter"}

                status_texts = [
                    "Отклик отправлен",
                    "Вы откликнулись",
                    "Резюме доставлено",
                    "Ваш отклик принят",
                    "Спасибо за отклик",
                    "Отклик успешно отправлен"
                ]

                applied = any(page.locator(f"text={txt}").count() > 0 for txt in status_texts)

                if applied:
                    print("Application submitted successfully")
                    return {"status": "success", "message": "Applied successfully"}
                else:
                    print("WARNING: Cannot confirm application status")
                    # опционально сохранить HTML для анализа
                    with open("hh_last_response.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    return {"status": "success", "message": "Applied (status unclear)"}

            else:
                print("ERROR: Apply button not found")
                return {"status": "error", "message": "Apply button not found"}

        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {"status": "error", "message": str(e)}
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(apply_to_vacancy(sys.argv[1]), ensure_ascii=False))
