import requests
import pandas as pd
import json
import os
from newspaper import Article

def fetch_and_parse(url):
    try:
        # Use newspaper3k to extract the article
        article = Article(url)
        article.download()
        article.parse()

        # Extract title and text
        title = article.title
        full_text = article.text

        return title, full_text
    except Exception as e:
        print(f"Failed to process {url}. Error: {e}")
        return None, None

def main(links_file, output_file):
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
        title, full_text = fetch_and_parse(url)
        if title and full_text:
            new_data.append({'url': url, 'title': title, 'extracted text': full_text})

    # Append new data to the dataframe and save to CSV
    if new_data:
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
