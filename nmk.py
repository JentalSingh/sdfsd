"""
Northeastern - Public Art Submission (Only Upload + URL Capture)
"""

import json
import os
import time
import re
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
TARGET_URL = "https://publicart.northeastern.edu/submit/"
PDF_NAME = "6dedec5c37a30557a5dd432818c6a5bc.pdf"
PDF_PATH = BASE_DIR / PDF_NAME

# ✅ PROXY DETAILS
IP = "38.154.191.183"
PORT = 8760
USER = "xgxowcgc"
PASS = "h6r17blc86s8"

# ============================================================
# CREATE PROXY EXTENSION
# ============================================================
def create_proxy_extension():
    ext_dir = BASE_DIR / "proxy_ext"
    os.makedirs(ext_dir, exist_ok=True)
    
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy", "tabs", "unlimitedStorage", "storage",
            "<all_urls>", "webRequest", "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]}
    }
    
    background = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{IP}",
                port: parseInt({PORT})
            }}
        }}
    }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{authCredentials: {{username: "{USER}", password: "{PASS}"}}}};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """
    
    with open(ext_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)
    with open(ext_dir / "background.js", "w") as f:
        f.write(background)
    
    return str(ext_dir.absolute())

# ============================================================
# XHR INTERCEPT SCRIPT
# ============================================================
XHR_INTERCEPT_JS = """
(function () {
    window.__ajax_log = [];
    var _open = XMLHttpRequest.prototype.open;
    var _send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (body) {
        var xhr = this;
        xhr.addEventListener('load', function () {
            if (xhr.responseURL && xhr.responseURL.indexOf('admin-ajax.php') !== -1) {
                window.__ajax_log.push({
                    url: xhr.responseURL,
                    body: xhr.responseText,
                    status: xhr.status
                });
            }
        });
        return _send.apply(this, arguments);
    };
})();
"""

# ============================================================
# CREATE SAMPLE PDF
# ============================================================
def create_sample_pdf():
    if PDF_PATH.exists():
        return PDF_PATH
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        c = canvas.Canvas(str(PDF_PATH), pagesize=letter)
        c.drawString(100, 750, "Northeastern - Public Art Proposal")
        c.drawString(100, 730, f"File: {PDF_NAME}")
        c.drawString(100, 710, "Test proposal for public art submission.")
        c.save()
        print(f"✅ Created PDF: {PDF_PATH}")
    except:
        with open(PDF_PATH, "w") as f:
            f.write(f"Northeastern - Public Art Proposal\nFile: {PDF_NAME}\n")
        print(f"✅ Created PDF (text): {PDF_PATH}")
    return PDF_PATH

# ============================================================
# MAIN FUNCTION
# ============================================================
def main():
    print("\n" + "="*70)
    print("📄 NORTHEASTERN - PDF UPLOAD + URL CAPTURE")
    print("="*70)
    print(f"📁 Target: {TARGET_URL}")
    print(f"📄 PDF: {PDF_NAME}")
    print(f"🌐 Proxy: {IP}:{PORT}")
    print("="*70)
    
    # Create PDF
    pdf_path = create_sample_pdf()
    if not pdf_path.exists():
        print("❌ PDF not available!")
        return
    
    # Create proxy extension
    print("\n🔧 Creating proxy extension...")
    ext_path = create_proxy_extension()
    print(f"✅ Extension: {ext_path}")
    
    # Setup driver
    print("\n🌐 Launching Chrome with proxy...")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--load-extension={ext_path}")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options)
    
    try:
        # Inject XHR interceptor
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": XHR_INTERCEPT_JS
        })
        
        # Navigate
        print(f"\n🌐 Opening: {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(5)
        
        # ✅ ONLY UPLOAD PDF - NO FORM FIELDS
        print("\n📤 Uploading PDF...")
        
        file_input = None
        selectors = [
            "input[type='file']",
            "input[name*='file']",
            "input[name*='upload']",
        ]
        
        for selector in selectors:
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, selector)
                if file_input:
                    break
            except:
                continue
        
        if not file_input:
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
        
        driver.execute_script("""
            arguments[0].style.display = 'block';
            arguments[0].style.visibility = 'visible';
            arguments[0].style.opacity = '1';
            arguments[0].style.height = 'auto';
            arguments[0].style.width = 'auto';
            arguments[0].style.position = 'relative';
        """, file_input)
        file_input.send_keys(str(pdf_path))
        print("✅ PDF uploaded!")
        time.sleep(3)
        
        # ✅ SUBMIT FORM
        print("\n📨 Submitting form...")
        try:
            submit = driver.find_element(By.XPATH, "//*[contains(text(), 'Submit')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", submit)
            print("✅ Form submitted!")
        except:
            try:
                submit = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                driver.execute_script("arguments[0].click();", submit)
                print("✅ Form submitted!")
            except:
                print("ℹ️ No submit button found")
        
        # ✅ CAPTURE URL
        print("\n📡 Capturing upload URL...")
        time.sleep(5)
        logs = driver.execute_script("return window.__ajax_log || [];")
        
        pdf_url = None
        for entry in logs:
            body = entry.get("body", "")
            try:
                data = json.loads(body)
                if data.get("success") == True and "data" in data:
                    if data["data"].get("url"):
                        pdf_url = data["data"]["url"].replace("\\/", "/")
                        break
            except:
                pass
            
            matches = re.findall(r'https?://[^\s"\'<>]*wpforms[^\s"\'<>]+\.pdf', body)
            if matches:
                pdf_url = matches[0]
                break
        
        # ✅ SAVE SCREENSHOT
        driver.save_screenshot(str(BASE_DIR / "northeastern_result.png"))
        print("📸 Screenshot saved")
        
        print("\n" + "="*70)
        if pdf_url:
            print("✅ SUCCESS!")
            print(f"🔗 PDF URL: {pdf_url}")
            with open(BASE_DIR / "northeastern_url.txt", "w") as f:
                f.write(pdf_url)
            print(f"📁 URL saved to: northeastern_url.txt")
        else:
            print("⚠️ Upload completed but URL not captured")
            print("💡 Check screenshot")
        print("="*70)
        
        
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()