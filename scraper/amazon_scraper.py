import requests
from lxml import html
import re
import json


class Scraper:
    def __init__(self, headers=None, cookies=None) -> None:
        self.headers = headers
        self.cookies = cookies

    def make_get_request(self, url):
        kwargs = {}
        if self.headers:
            kwargs["headers"] = self.headers
        if self.cookies:
            kwargs["cookies"] = self.cookies
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()
        except Exception as err:
            print(f"ERROR: {err}. URL:\t{url}")

        try:
            # TODO
            with open("amazon_product_page.html", "w", encoding="utf-8") as file:
                file.write(response.text)
                print(f"Data saved to amazon_product_page.html")
            return response.text
        except Exception as err:
            print(f"ERROR: {err}. Could not save response to file.")
            return None

    def parse_response(self, selectors):
        # Placeholder for parsing logic
        tree = html.fromstring(self.response)

        product_data = {}

        for field, selector in selectors.items():
            try:
                elements = tree.xpath(selector)
                if elements:
                    # Clean and get the first non-empty result
                    cleaned = [
                        elem.strip().replace("\u200e", "")
                        for elem in elements
                        if elem.strip()
                    ]
                    if cleaned:
                        product_data[field] = cleaned[0]
                        print(f"{field}: {cleaned[0]}")
            except Exception as e:
                print(f"Error extracting {field}: {e}")
        return product_data


class AmazonProductScraper(Scraper):
    def __init__(self, product_sku) -> None:
        super().__init__()
        self.product_sku = product_sku
        self.product_base_url = "https://www.amazon.com/dp/{}".format(self.product_sku)

    def parse_response(self):
        # Placeholder for parsing logic
        try:
            tree = html.fromstring(self.response)
        except Exception as e:
            print(f"Error parsing HTML response: {e}")
            return {}

        # Initialize product data
        product_data = {}
        json_object = None

        # Try to extract JSON data from script tag
        try:
            script_tags = tree.xpath(
                '//script[@type="text/javascript" and contains(text(), "ImageBlockBTF")]/text()'
            )

            if script_tags:
                script_tag_text = script_tags[0]
                match = re.search(r"jQuery\.parseJSON\('({.*})'\);", script_tag_text)
                if match:
                    json_data = match.group(1)
                    json_object = json.loads(json_data)
                    print("Successfully extracted JSON data from script tag")
                else:
                    print("No JSON data pattern found in script tag")
            else:
                print("No ImageBlockBTF script tag found")
        except (IndexError, json.JSONDecodeError, Exception) as e:
            print(f"Error extracting JSON data from script tag: {e}")

        # Extract product data from JSON if available
        if json_object:
            try:
                # Product Title
                if "title" in json_object:
                    product_data["title"] = json_object["title"]

                # Photo URLs - Extract from colorImages
                photo_urls = []
                if "colorImages" in json_object:
                    for color_variant, images in json_object["colorImages"].items():
                        if isinstance(images, list):
                            for image in images:
                                if isinstance(image, dict):
                                    # Add high resolution images
                                    if "hiRes" in image:
                                        photo_urls.append(image["hiRes"])
                                    # Add large images as backup
                                    elif "large" in image:
                                        photo_urls.append(image["large"])

                # Remove duplicates and store
                photo_urls = list(set(photo_urls))
                if photo_urls:
                    product_data["photo_urls"] = photo_urls
            except Exception as e:
                print(
                    f"Error extracting data from JSON object: {e}"
                )  # Extract from HTML tree
        html_selectors = {
            "brand": "//th[contains(text(), ' Brand ')]/following-sibling::td/text()",
            "monthly_sales": "//*[contains(text(), 'in past month')]/../span[@class]/text()",
            "rating": "//span[@class='a-size-small a-color-base'][following-sibling::i]/text()",
            "reviews_count": "//span[@id='acrCustomerReviewText']/@aria-label",
            "price": "//div[@aria-labelledby='Product 1']//*[@class='a-offscreen']/text()",
            "seller_name": "//th[contains(text(), ' Manufacturer ')]/following-sibling::td/text()",
            "seller_id": "//*[@id='bylineInfo']/@href",
        }

        # Process HTML selectors
        for field, selector in html_selectors.items():
            try:
                elements = tree.xpath(selector)
                if elements:
                    # Clean and get the first non-empty result
                    cleaned = [
                        elem.strip().replace("\u200e", "")
                        for elem in elements
                        if elem.strip()
                    ]
                    if cleaned:
                        product_data[field] = cleaned[0]
                        print(f"{field}: {cleaned[0]}")
            except Exception as e:
                print(f"Error extracting {field}: {e}")
        return product_data

    def collect_data(self):
        url = self.product_base_url
        self.response = self.make_get_request(url)
        if self.response:
            print(f"Data collected for product SKU: {self.product_sku}")
            # Process the response as needed
            # TODO
            try:
                with open(f"{self.product_sku}.html", "w", encoding="utf-8") as file:
                    file.write(self.response)
                print(f"HTML saved to {self.product_sku}.html")
            except Exception as e:
                print(f"Error saving HTML file: {e}")

            try:
                self.data = self.parse_response()
                if self.data:  # Only save if we have data
                    with open(
                        f"{self.product_sku}.json", "w", encoding="utf-8"
                    ) as json_file:
                        json.dump(self.data, json_file, ensure_ascii=False, indent=2)
                    print(f"Data saved to {self.product_sku}.json")
                else:
                    print(f"No data extracted for product SKU: {self.product_sku}")
            except Exception as e:
                print(f"Error parsing response or saving JSON: {e}")
        else:
            print(f"Failed to collect data for product SKU: {self.product_sku}")
