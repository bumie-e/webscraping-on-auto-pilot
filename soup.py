import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import pandas as pd
from upload_files import AzureBlob
#from argparse import ArgumentParser
import sys


class AutoScrape:

    def __init__(self, home_url) -> None:
        #self.base_url = base_url
        self.home_url = home_url

        if not os.path.exists('data/'):
            os.makedirs('data/')

        #if not os.path.exists('data/categories.csv'):
        # Scrape all categories and store in CSV
        self.scrape_all_categories()

        self.scrape_all_pages()


    # Function to get the total number of pages
    def get_total_pages(self, soup):
        pagination = soup.find('a', {'aria-label': 'Next Page'})
        if pagination:
            # If there's a "Next" button, it means there are multiple pages
            last_page_link = pagination.find_previous('a').get('href')
            last_page_link = last_page_link.split('=')[-1]
            total_pages = last_page_link.split('#')[0]
            return int(total_pages)
        return 1
    
    # Function to get the list of categories dynamically from the page
    def get_categories(self, soup, class_name):
        categories = {}
        
        # Assuming categories are stored in a list or sidebar with links
        category_section = soup.find('div', class_=class_name)  # Adjust class to match actual structure
        if category_section:
            category_links = category_section.find_all('a')
            #print('category_links', category_links)
            for link in category_links:
                category_name = link.text.strip()
                category_url = link.get('href')
                categories[category_name] = category_url
        
        return categories
    
    # Function to get the list of categories dynamically from the page
    def sub_get_categories(self, soup, class_name):
        categories = {}

        # Assuming categories are stored in a div or sidebar with links
        category_section = soup.find('div', class_=class_name)  # Adjust the class name to match the HTML structure

        if category_section:
            # Extract category links and names
            category_links = category_section.find_all('a')  # Links to categories
            category_names = category_section.find_all('p')  # Names of categories
            
            # Debugging: Print the number of links and names to check alignment
            print(f'Found {len(category_links)} links and {len(category_names)} names')

            # Ensure both lists have the same length before zipping
            if len(category_links) == len(category_names):
                for link, name in zip(category_links, category_names):
                    category_name = name.text.strip()  # Get the text from <p> tag (category name)
                    category_url = link.get('href')   # Get the href from <a> tag (category URL)
                    
                    if category_url and category_name:  # Make sure both name and URL exist
                        categories[category_name] = category_url
            else:
                print("Mismatch in the number of category names and links")
        
        return categories



    # Function to scrape a single page
    def scrape_page(self, soup, response, category, csv_writer, category_url):
        
            products = soup.find_all('article', class_='prd _fb col c-prd')
            
            for product in products:
                try:
                    title = product.find('h3', class_='name').text.strip()
                    price = product.find('div', class_='prc').text.strip()
                    
                    rating_tag = product.find('div', class_='stars _s')
                    if rating_tag:
                        # Extract the rating text (e.g., "5 out of 5")
                        rating_text = rating_tag.text.strip()
                        # Extract only the numeric part of the rating
                        rating = rating_text.split(' ')[0]
                    else:
                        rating = "No rating"
                    #rating = rating_tag['data-score'] if rating_tag else "No rating"
                    
                    discount_tag = product.find('div', class_='bdg _dsct _sm')
                    discount = discount_tag.text.strip() if discount_tag else "No discount"

                    # Extract shipping type
                    shipping_tag = product.find('div', class_='tag _dsct _dyn _r')
                    if shipping_tag:
                        shipping_type = shipping_tag.text.strip()
                    else:
                        shipping_type = "No shipping info"

                    print(f"Title: {title}")
                    print(f"Price: {price}")
                    print(f"Rating: {rating}")
                    print(f"Discount: {discount}")
                    print(f"Category: {category}")
                    print(f"Shipping Type: {shipping_type}")
                    print("-" * 40)

                    csv_writer.writerow([title, price, rating, discount, category, shipping_type])
                except Exception as e:
                    print(f"Error processing product: {e}")
            else:
                print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
                print(' Web page url: ', category_url)

    # Main function to scrape all pages
    def scrape_all_pages(self):

        today = datetime.today().strftime('%Y-%m-%d')

        if not os.path.exists(f'data/{today}'):
            os.makedirs(f'data/{today}')

        # Open a CSV file for writing
        csv_file = open(f'data/{today}/newset_arrivals.csv', mode='w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)

        # Write the headers
        csv_writer.writerow(['Title', 'Price', 'Rating', 'Discount', 'Category', 'Shipping Type'])

        df = pd.read_csv('data/categories.csv')
        category_urls = list(df['category_url'])
        categories = list(df['Category'])

        for category_url, category in zip(category_urls, categories):

            newest_arrivals_url = category_url + '?sort=newest#catalog-listing'
            response = requests.get(newest_arrivals_url, timeout=60)
            print(f'Website {newest_arrivals_url} response is {response.status_code }')
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                total_pages = self.get_total_pages(soup)
                print(f"Total Pages: {total_pages}")
                
                # Scrape the first page
                self.scrape_page(soup, response, category, csv_writer, category_url)
                
                # Loop through and scrape the remaining pages
                
                for page in range(2, total_pages + 1):
                    page_url = category_url + f'?sort=newest&page={page}#catalog-listing'
                    print(f"Scraping page {page}...")
                    sub_response = requests.get(page_url, timeout=60)
                    if sub_response.status_code == 200:
                        sub_soup = BeautifulSoup(sub_response.content, "html.parser")
                        self.scrape_page(sub_soup, sub_response, category, csv_writer, page_url)
            else:
                print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

        csv_file.close()

    # Run the scraper
    def scrape_all_categories(self):

        # Open a CSV file for writing
        csv_file = open('data/categories.csv', mode='w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)

        # Write the headers
        csv_writer.writerow(['Category', 'category_url'])


        response = requests.get(self.home_url, timeout=60)

        print(f'Website {self.home_url} response is {response.status_code }')

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Step 1: Get all the categories dynamically from the page
            categories = self.get_categories(soup, 'flyout')
            if categories:
                print("Categories found:")
                for category, category_url in categories.items():
                    print(f"{category}: {category_url}")

                    if category_url != None:
                        # Step 2: Adjust the url of each category
                        if self.home_url not in category_url:
                            category_url = self.home_url+category_url

                        csv_writer.writerow([category, category_url])
                    # TODO list all sub categories of each category   
                    #     # Step 3: Visit the link of each category
                    #     sub_response = requests.get(category_url)

                    #     if sub_response.status_code == 200:
                    #         soup = BeautifulSoup(sub_response.content, "html.parser")

                    #         sub_categories = self.sub_get_categories(soup, 'row _no-g -tac -pvxs -phs _6c-shs')

                    #         for sub_category, sub_category_url in sub_categories:
                    #             # Write product details to CSV 
                    #             csv_writer.writerow([category, sub_category, category_url, sub_category_url])

                    # # Step 2: Scrape products for each category
                    # scrape_category_pages(base_url, category, category_url)
            else:
                print("No categories found.")
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        csv_file.close()
        print("CSV file saved successfully.")


if __name__ == '__main__':

    # # Create the parser
    # parser = ArgumentParser()
    
    # # Add an argument
    # parser.add_argument('FILEPATH', type=str, help="Path to the file you want to upload")
    # parser.add_argument('AZURE_STORAGE_CONNECTION_STRING', type=str, help="Azure storage connection string")
    # parser.add_argument('CONTAINER', type=str, help="Azure storage blob container name")
    
    # # Parse the arguments
    # args = parser.parse_args()

    # Get the arguments passed from Bash
    FILEPATH = sys.argv[1]
    CONTAINER = sys.argv[2]
    AZURE_STORAGE_CONNECTION_STRING = sys.argv[3]

    # Base URL for Jumia search results
    home_url = 'https://www.jumia.com.ng/'

    scrape = AutoScrape(home_url)
    blob = AzureBlob(FILEPATH,  CONTAINER, AZURE_STORAGE_CONNECTION_STRING)
    blob.generate_and_upload_csv()
