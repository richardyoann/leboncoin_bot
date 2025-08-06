from selenium.webdriver.common.by import By

def parse_ads(annonces):
    ads_data = []
    for annonce in annonces:
        try:
            title = annonce.find_element(By.TAG_NAME, "p").text
            price = annonce.find_element(By.CSS_SELECTOR, "span[data-qa-id='aditem_price']").text
            url_annonce = annonce.get_attribute("href")
            ads_data.append({
                "title": title,
                "price": price,
                "url": url_annonce
            })
        except Exception as e:
            print(f"Erreur extraction annonce : {e}")
            continue
    return ads_data