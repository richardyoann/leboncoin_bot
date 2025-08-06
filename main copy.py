from bot.config_loader import ConfigLoader
from bot.scraper import LeboncoinScraper
from bot.message_template import MessageTemplate
from bot.sender import MessageSender
import logging
import os

def main():
    # Création dossier logs si nécessaire
    os.makedirs("logs", exist_ok=True)

    # Configuration du logger
    logging.basicConfig(
        filename="logs/envoi_log.csv",
        level=logging.INFO,
        format="%(asctime)s,%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Chargement config
    config = ConfigLoader("config.yaml").load()

    # Scraping
    scraper = LeboncoinScraper(config)
    annonces = scraper.scrape()

    if not annonces:
        print("Aucune annonce trouvée selon les critères.")
        return

    # Préparation template et envoi
    template = MessageTemplate("message_template.txt")
    sender = MessageSender()

    for annonce in annonces:
        message = template.render(annonce)
        sender.send(annonce, message)
        logging.info(f"{annonce['title']},{annonce['url']}")

if __name__ == "__main__":
    main()
