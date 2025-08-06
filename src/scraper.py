from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import bot.settings as settings

class GenericScraper:
    def __init__(self, base_url, query_params, sel_ads, sel_title, sel_price, sel_url=None):
        chrome_opts = Options()
        if settings.HEADLESS:
            chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--window-size=1920,1080")

        # Si tu dois forcer le chemin vers Chrome, décommente et adapte :
        # chrome_opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        driver_path = ChromeDriverManager().install()
        self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_opts)

        self.base_url = base_url
        self.query_params = query_params.copy() if query_params is not None else {}
        self.sel_ads = sel_ads
        self.sel_title = sel_title
        self.sel_price = sel_price
        self.sel_url = sel_url

    def build_url(self, page, category, keyword):
        params = {
            "page": page,
            "category": category,
            "text": keyword
        }
        params_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}?{params_str}"

    def is_captcha_present(self):
        try:
            # Détection iframe reCAPTCHA classique
            self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            return True
        except NoSuchElementException:
            return False

    def wait_for_ads_or_captcha(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.sel_ads))
            )
            return "ads_loaded"
        except TimeoutException:
            if self.is_captcha_present():
                return "captcha_detected"
            else:
                return "timeout_no_ads"

    def fetch_ads_multiple_categories(self, categories, keywords, pages):
        results = []
        for category in categories:
            for keyword in keywords:
                print(f"Scraping catégorie {category} avec mot-clé '{keyword}'")
                for page in range(1, pages + 1):
                    url = self.build_url(page, category, keyword)
                    print(f"Scraping catégorie {category} avec mot-clé '{keyword}' page {page}")
                    self.driver.get(url)

                    status = self.wait_for_ads_or_captcha(timeout=40)
                    if status == "ads_loaded":
                        annonces = self.driver.find_elements(By.CSS_SELECTOR, self.sel_ads)
                        if not annonces:
                            print(f"Aucune annonce trouvée sur page {page} cat {category} mot-clé '{keyword}'")
                            continue

                        for annonce in annonces:
                            try:
                                title = annonce.find_element(By.CSS_SELECTOR, self.sel_title).text
                                price = annonce.find_element(By.CSS_SELECTOR, self.sel_price).text
                                if self.sel_url:
                                    url_ad = annonce.find_element(By.CSS_SELECTOR, self.sel_url).get_attribute("href")
                                else:
                                    url_ad = annonce.get_attribute("href")

                                results.append({"title": title, "price": price, "url": url_ad})
                            except Exception as e:
                                print(f"Erreur extraction annonce: {repr(e)}")
                                continue

                    elif status == "captcha_detected":
                        print(f"CAPTCHA détecté sur page {page}, catégorie {category}, mot-clé '{keyword}'.")
                        print("Merci de résoudre manuellement le CAPTCHA dans la fenêtre du navigateur.")
                        input("Après résolution, appuie sur Entrée pour continuer...")

                        # Retenter après résolution manuelle
                        status_after = self.wait_for_ads_or_captcha(timeout=30)
                        if status_after == "ads_loaded":
                            print("CAPTCHA résolu, récupération des annonces en cours...")
                            annonces = self.driver.find_elements(By.CSS_SELECTOR, self.sel_ads)
                            for annonce in annonces:
                                try:
                                    title = annonce.find_element(By.CSS_SELECTOR, self.sel_title).text
                                    price = annonce.find_element(By.CSS_SELECTOR, self.sel_price).text
                                    url_ad = annonce.get_attribute("href") if not self.sel_url else annonce.find_element(By.CSS_SELECTOR, self.sel_url).get_attribute("href")
                                    results.append({"title": title, "price": price, "url": url_ad})
                                except Exception as e:
                                    print(f"Erreur extraction annonce: {repr(e)}")
                                    continue
                        else:
                            print("Impossible de récupérer les annonces après résolution du CAPTCHA, on passe à la suite.")

                    else:
                        print(f"Timeout sans annonces ni CAPTCHA sur page {page} cat {category} mot-clé '{keyword}'.")
                        # Optionnel : print un extrait du HTML pour le debug
                        snippet = self.driver.page_source[:1000]
                        print(f"HTML extrait :\n{snippet}\n---")

        return results

    def close(self):
        self.driver.quit()
