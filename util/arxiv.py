import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import base64
from const import CSV_PATH


# Function to extract information from the ArXiv page
def extract_paper_info(soup):
    extracted_data = []
    papers = soup.find_all('li', class_='arxiv-result')
    for idx, paper in enumerate(papers):
        title = paper.find('p', class_='title').text.strip() if paper.find('p', class_='title') else None
        abstract = paper.find('span', class_='abstract-full').text.strip() if paper.find('span', class_='abstract-full') else None
        doi = None
        pdf_link = None
        links = paper.find_all('a', href=True)
        for link in links:
            if 'doi.org' in link['href']:
                doi = link['href']
            if link.text.strip().lower() == 'pdf':  # Look for the link labeled 'pdf'
                pdf_link = link['href']
        
        extracted_data.append({
            'Title': title,
            'DOI': doi,
            'PDF Link': pdf_link,
            'Abstract': abstract,
            "Hashed": base64.urlsafe_b64encode(title.encode('utf-8')).decode('utf-8')
        })
    return extracted_data


def scraping_arxiv():
    start = 0
    while True:
        url = base_url.format(start)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if "Sorry, your query for" message appears on the page
        if soup.find(string=re.compile("Sorry, your query for")):
            print(f"No more results at start={start}.")
            break
        
        # Extract paper information from the current page
        extracted_data = extract_paper_info(soup)
        
        # Save extracted data immediately to CSV
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            # Append to CSV file (create file if it does not exist)
            df.to_csv(CSV_PATH, mode='a', index=False, header=not pd.io.common.file_exists(CSV_PATH))
            
        # Move to the next page by incrementing 'start'
        start += 200
        
        # Wait to avoid being blocked
        time.sleep(2)

    print(f"Data scraping completed. All papers saved in '{CSV_PATH}'.")

if __name__=="__main__":
    query="recommender system"
    query = query.replace(" ", "+")
    base_url = f"https://arxiv.org/search/?query={query}"+"&searchtype=abstract&abstracts=show&order=-announced_date_first&size=200&start={}"
    scraping_arxiv()