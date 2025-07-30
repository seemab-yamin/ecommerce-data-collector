import time

from amazon_scraper import AmazonProductScraper

if __name__ == "__main__":
    # product sku to scraper
    product_skus = ["B0B2JZXW8L", "B01GGKYKQM", "B01GGKZ2SC"]

    for sku in product_skus:
        start_time = time.time()
        amzn_scraper = AmazonProductScraper(sku)
        amzn_scraper.collect_data()
        print(f"Program Completed in {time.time() - start_time} seconds.")
        print("\n\n" + "*" * 20 + "\n\n")
