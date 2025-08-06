from bot.scraper import GenericScraper
import bot.settings as settings

if __name__ == "__main__":
    scraper = GenericScraper(
        base_url=settings.BASE_URL,
        query_params=None,  # non utilisé avec fetch_ads_multiple_categories
        sel_ads=settings.SEL_ADS,
        sel_title=settings.SEL_TITLE,
        sel_price=settings.SEL_PRICE,
        sel_url=settings.SEL_URL
    )
    try:
        ads = scraper.fetch_ads_multiple_categories(settings.CATEGORIES, settings.KEYWORDS, settings.PAGES)
        print(f"\nTotal annonces récupérées : {len(ads)}")
        for ad in ads:
            print(f"{ad['title']} - {ad['price']} - {ad['url']}")
    finally:
        scraper.close()