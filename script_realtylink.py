import asyncio
import datetime
import json
import httpx as httpx
import tenacity


from aiofiles import open as aio_open
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


@dataclass
class Advert:
    """
    Represents an advertisement with various details.

    Attributes:
    - link (str): The URL link to the advertisement.
    - title_advert (str): The title of the advertisement.
    - region (str): The region where the property is located.
    - address (str): The full address of the property.
    - description (str): The description of the advertisement.
    - price (str): The price of the property.
    - bedrooms (int): The number of bedrooms in the property.
    - area (str): The area of the property.
    - photo (list): A list of URLs representing photos associated with the advertisement.
    """
    link: str
    title_advert: str
    region: str
    address: str
    description: str
    price: str
    bedrooms: int
    area: str
    photo: list
    date: str


class AdvertCollect:
    """
    Handles the collection of advertisement data.

    Methods:
    - __init__(self) -> None: Initializes the AdvertCollect object.
    - get_connection(self, url: str, headers: dict) -> httpx: Makes an HTTP GET request to the specified URL with the provided headers.
    - start_collect_links(self) -> None: Initiates the process of collecting advertisement links.
    - get_all_detail_links(self, driver: webdriver) -> set[str]: Extracts all detail links from the current page.
    - collect_info_detail_page(self, detail_links: set) -> list[Advert]: Collects information from each detail page asynchronously.
    - create_advert_object(self, link: list, soup: BeautifulSoup, page: str) -> Advert: Creates an Advert object from the information extracted.
    - get_all_photo(self, page: str) -> list[str]: Retrieves photo URLs associated with an advertisement asynchronously.
    - write_to_json_file(self, adverts): Writes advertisement data to a JSON file asynchronously.
    - __main__: Runs the script by creating an instance of AdvertCollect and starting the collection process.
    """

    def __init__(self) -> None:
        """
        Initializes the AdvertCollect object.

        Attributes:
        - base_url (str): The base URL for the website.
        - url (str): The specific URL path for properties for rent.
        - headers (dict): HTTP headers used for making requests.
        """
        self.base_url = "https://realtylink.org"
        self.url = "/en/properties~for-rent"

        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        }

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(multiplier=1, max=10),
    )
    async def get_connection(self, url: str, headers: dict) -> httpx:
        """
        Makes an HTTP GET request to the specified URL with the provided headers.

        Parameters:
        - url (str): The URL to make the request to.
        - headers (dict): HTTP headers to include in the request.

        Returns:
        - httpx: The HTTPX response object.
        """
        async with httpx.AsyncClient() as session:
            return await session.get(url, headers=headers)

    async def start_collect_links(self) -> None:
        """
        Initiates the process of collecting advertisement links.

        This method starts a Selenium WebDriver, navigates to the specified URL, collects detail links,
        collects information from detail pages, and writes the data to a JSON file.
        """
        url = self.base_url + self.url

        chrome_options = Options()
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        detail_links = self.get_all_detail_links(driver=driver)

        list_adverts = await self.collect_info_detail_page(detail_links)
        await self.write_to_json_file(list_adverts)

    def get_all_detail_links(self, driver: webdriver) -> set[str]:
        """
        Extracts all detail links from the current page.

        Parameters:
        - driver (webdriver): The Selenium WebDriver.

        Returns:
        - set[str]: A set of detail links.
        """
        page = driver.page_source

        detail_links = set()
        while True:
            soup = BeautifulSoup(page, "html.parser")
            detail_page = soup.select(".a-more-detail")

            for link in detail_page:
                detail_links.add(self.base_url + link["href"])
                if len(detail_links) == 60:
                    driver.quit()
                    return detail_links
            next_button = driver.find_element(By.CSS_SELECTOR, 'li.next a')
            next_button.click()
            page = driver.page_source

    async def collect_info_detail_page(self, detail_links: set) -> list[Advert]:
        """
        Collects information from each detail page asynchronously.

        Parameters:
        - detail_links (set): A set of detail links.

        Returns:
        - list[Advert]: A list of Advert objects.
        """
        async def fetch_data(link):
            response = await self.get_connection(link, self.headers)
            page = response.text
            soup = BeautifulSoup(page, "html.parser")
            return await self.create_advert_object(link, soup, page)

        tasks = [fetch_data(link) for link in detail_links]
        return await asyncio.gather(*tasks)

    async def create_advert_object(
            self,
            link: list,
            soup: BeautifulSoup,
            page: str
    ) -> Advert:
        """
        Creates an Advert object from the information extracted.

        Parameters:
        - link (list): The detail link.
        - soup (BeautifulSoup): The BeautifulSoup object for the page.
        - page (str): The HTML content of the page.

        Returns:
        - Advert: An Advert object.
        """

        try:
            title_advert = soup.find('span', {'data-id': 'PageTitle'}).text
        except AttributeError:
            title_advert = None
        address = soup.find('h2', itemprop='address').text.strip()
        region = ",".join(address.split(",")[-2:])[1:]

        try:
            description = soup.find('div', itemprop='description').text.strip()
        except AttributeError:
            description = None

        price = soup.find('div', class_='price').text.strip()[3:].replace(" ", "")

        try:
            bedrooms = int(soup.find('div', class_='col-lg-3 col-sm-6 cac').text.strip()[0])
        except AttributeError:
            bedrooms = 0

        area = soup.find("div", class_="carac-value").text.strip()

        photo = await self.get_all_photo(page)

        return Advert(
            link=link,
            title_advert=title_advert,
            address=address,
            region=region,
            description=description,
            price=price,
            bedrooms=bedrooms,
            area=area,
            photo=photo,
            date=str(datetime.datetime.now())
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(multiplier=1, max=10),
    )
    async def get_all_photo(self, page: str) -> list[str]:
        """
        Retrieves photo URLs associated with an advertisement asynchronously.

        Parameters:
        - page (str): The HTML content of the page.

        Returns:
        - list[str]: A list of photo URLs.
        """

        url = "https://realtylink.org/Property/PhotoViewerDataListing"

        soup = BeautifulSoup(page, 'html.parser')
        id_advert = soup.find('span', id='ListingId').text

        data = {
            "lang": "en",
            "centrisNo": f"{id_advert}",
            "track": "true",
            "authorizationMediaCode": "995"
        }

        async with httpx.AsyncClient() as client:
            data_post = await client.post(url, json=data, headers=self.headers)
            photo_data = json.loads(data_post.text)
            photo_list = photo_data.get("PhotoList", [])

        all_photo = []
        for photo in photo_list:
            photo = photo.get('UrlThumb').split("=")
            width = "640" + photo[-3][-2:]
            height = "480" + photo[-2][-3:]
            photo[-3] = width
            photo[-2] = height

            new_photo_link = "=".join(photo)
            all_photo.append(new_photo_link)
        return all_photo

    async def write_to_json_file(self, adverts: list) -> None:
        """
        Writes advertisement data to a JSON file asynchronously.

        Parameters:
        - adverts: A list of Advert objects.
        """
        async with aio_open('output.json', 'a+') as json_file:
            for adv in adverts:
                await json_file.write(json.dumps(asdict(adv), indent=2))
                await json_file.write(",\n")


if __name__ == "__main__":
    client = AdvertCollect()
    asyncio.run(client.start_collect_links())
