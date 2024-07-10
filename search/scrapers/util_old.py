import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os

def extract_title(soup):
    # Try to get the title from the <title> tag
    try:
        title = soup.find('title').get_text().strip()
    except:
        title = None

    # Fallback to first h1, h2, etc. if title is not found
    if not title:
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            first_heading = soup.find(tag)
            if first_heading:
                title = first_heading.get_text().strip()
                break
        else:
            title = 'No title found'

    return title

def fetch_and_parse(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the title using the new function
        title = extract_title(soup)

        # Container for all text
        all_text = []

        # Check for body or main tag
        main_content = soup.find('body') or soup.find('main')
        if main_content is not None:
            # Iterate through the main content's children to maintain order
            for element in main_content.descendants:
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote']:
                    text = element.get_text().strip()
                    if text:
                        all_text.append(text)
        
        # Combine all extracted text into a single string
        full_text = '\n'.join(all_text)

        return title, full_text
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None, None


def main(links_file, output_file):
    # Headers to simulate a browser visit
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    # Read links from links.json
    with open(links_file, 'r') as file:
        links = json.load(file)

    # Read existing data from output.csv if it exists
    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
    else:
        df = pd.DataFrame(columns=['url', 'title', 'extracted text'])

    # Identify new links
    existing_urls = set(df['url'])
    new_links = [link for link in links if link not in existing_urls]

    # Process new links
    new_data = []
    for url in new_links:
        title, full_text = fetch_and_parse(url, headers)
        if title and full_text:
            new_data.append({'url': url, 'title': title, 'extracted text': full_text})

    # Append new data to the dataframe and save to CSV
    if new_data:
        print(new_data)
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(output_file, index=False)
        print(f"Data successfully written to {output_file}")
    else:
        print("No new data to write.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process links and output to CSV.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the links.')
    parser.add_argument('output_file', type=str, help='The CSV file to write the output.')
    args = parser.parse_args()
    main(args.links_file, args.output_file)
