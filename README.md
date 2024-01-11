# Advert Collector

The Advert Collector is a Python script designed to scrape real estate advertisement data from the Realtylink website. It uses asynchronous programming, HTTP requests, and web scraping techniques to gather detailed information about properties available for rent.

## Requirements

* Python 3.10 or higher
* Chrome WebDriver installed
* Python packages listed in requirements.txt

```python
pip install -r requirements.txt
```

## Usage

1. Clone the repository:

```python
git clone https://github.com/your_username/advert-collector.git
cd advert-collector
```

2. Run the script:

```python
python script_realtylink.py
```

## Features

* Asynchronous HTTP requests using httpx
* Web scraping with BeautifulSoup
* Automated browsing using Selenium
* Data storage in JSON format

## Advert Class

The Advert class represents an advertisement with various details. It includes the following attributes:

* link (str): The URL link to the advertisement.
* title_advert (str): The title of the advertisement. 
* region (str): The region where the property is located. 
* address (str): The full address of the property. 
* description (str): The description of the advertisement. 
* price (str): The price of the property. 
* bedrooms (int): The number of bedrooms in the property. 
* area (str): The area of the property. 
* photo (list): A list of URLs representing photos associated with the advertisement. 
* date (str): The date and time when the data was collected.

## AdvertCollect Class

The AdvertCollect class handles the collection of advertisement data. It includes the following methods:

* __init__(self) -> None: Initializes the AdvertCollect object. 
* get_connection(self, url: str, headers: dict) -> httpx: Makes an HTTP GET request to the specified URL with the provided headers. 
* start_collect_links(self) -> None: Initiates the process of collecting advertisement links. 
* get_all_detail_links(self, driver: webdriver) -> set[str]: Extracts all detail links from the current page. 
* collect_info_detail_page(self, detail_links: set) -> list[Advert]: Collects information from each detail page asynchronously. 
* create_advert_object(self, link: list, soup: BeautifulSoup, page: str) -> Advert: Creates an Advert object from the information extracted. 
* get_all_photo(self, page: str) -> list[str]: Retrieves photo URLs associated with an advertisement asynchronously. 
* write_to_json_file(self, adverts: list) -> None: Writes advertisement data to a JSON file asynchronously.