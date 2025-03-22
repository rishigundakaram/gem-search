#!/usr/bin/env python
import concurrent.futures
import json
import os
import logging
import requests
import pandas as pd
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Global requests session for efficiency
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def fetch_and_parse(url, timeout=10):
    """
    Fetch a URL using a HEAD request to check availability,
    then download and parse the article using newspaper.
    Returns (title, full_text) if successful; otherwise (None, None).
    """
    try:
        head_resp = session.head(url, timeout=timeout)
        if head_resp.status_code != 200:
            logger.warning(f"HEAD request failed for {url} with status {head_resp.status_code}")
            return None, None

        article = Article(url, language='en')
        article.download()
        article.parse()

        if article.title and article.text:
            return article.title, article.text
        else:
            logger.warning(f"Article at {url} lacks title or text.")
            return None, None
    except Exception as e:
        logger.error(f"Failed to process {url}. Error: {e}")
        return None, None

def process_links(links, max_workers=5):
    """
    Process a list of links concurrently.
    Returns a tuple: (list of article data, list of failed links).
    """
    new_data = []
    failed_links = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_and_parse, url): url for url in links}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                title, full_text = future.result()
                if title and full_text:
                    new_data.append({'url': url, 'title': title, 'extracted text': full_text})
                else:
                    failed_links.append(url)
            except Exception as exc:
                logger.error(f"Unexpected error processing {url}: {exc}")
                failed_links.append(url)
    return new_data, failed_links

def load_links(file_path):
    """
    Load links from a JSON file and return them as a set.
    """
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                links = json.load(f)
                return set(links)
            except json.JSONDecodeError:
                logger.error("JSON decode error in links file. Starting with an empty set.")
                return set()
    else:
        return set()

def update_links_file(file_path, links_set):
    """
    Write the updated set of links back to the JSON file.
    """
    with open(file_path, "w") as f:
        json.dump(list(links_set), f, indent=2)
    logger.info(f"Updated {file_path} with {len(links_set)} total links.")

def is_blog_link(url, blog_keywords=None):
    """
    A basic heuristic to check if a URL likely points to a blog/news/review post.
    """
    if blog_keywords is None:
        blog_keywords = ["blog", "post", "article", "news", "review"]
    return any(keyword.lower() in url.lower() for keyword in blog_keywords)

def crawl_page(url, max_depth=1, visited=None, blog_keywords=None):
    """
    Crawl the given URL recursively up to max_depth.
    Only consider links on the same domain that pass the blog link filter.
    Returns a set of discovered blog links.
    """
    if visited is None:
        visited = set()
    discovered_links = set()

    def _crawl(current_url, depth):
        if depth < 0:
            return
        if current_url in visited:
            return
        visited.add(current_url)
        try:
            response = session.get(current_url, timeout=10)
            if response.status_code != 200:
                return
            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current_url, href)
                # Only consider links on the same domain as the original URL.
                if urlparse(url).netloc not in urlparse(full_url).netloc:
                    continue
                if is_blog_link(full_url, blog_keywords):
                    discovered_links.add(full_url)
                _crawl(full_url, depth - 1)
        except Exception as e:
            logger.error(f"Error crawling {current_url}: {e}")

    _crawl(url, max_depth)
    return discovered_links

def main(links_file, output_file, max_workers=5):
    # Load base links from JSON file.
    base_links = load_links(links_file)
    logger.info(f"Loaded {len(base_links)} base links from {links_file}.")

    # For each base link, perform a shallow crawl (depth = 1) to discover more blog links.
    crawled_links = set()
    for url in base_links:
        discovered = crawl_page(url, max_depth=1)
        logger.info(f"Crawled {url}: found {len(discovered)} additional links.")
        crawled_links.update(discovered)

    # Merge the base and crawled links.
    all_links = base_links.union(crawled_links)
    logger.info(f"Total unique links to process: {len(all_links)}")

    # Load existing CSV data (if any) and filter out links already processed.
    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
    else:
        df = pd.DataFrame(columns=['url', 'title', 'extracted text'])
    existing_urls = set(df['url'])
    new_links = [link for link in all_links if link not in existing_urls]
    logger.info(f"Found {len(new_links)} new links to process.")

    # Process new links concurrently.
    new_data, _ = process_links(new_links, max_workers=max_workers)

    if new_data:
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote data to {output_file}")
    else:
        logger.warning("No new data to write.")

    # Update the links file with the union of base and discovered links.
    update_links_file(links_file, all_links)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process links from a base JSON file and output to CSV.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the base links.')
    parser.add_argument('output_file', type=str, help='The CSV file to write the output.')
    parser.add_argument('--max_workers', type=int, default=5, help='Number of concurrent workers.')
    args = parser.parse_args()

    main(
        links_file=args.links_file,
        output_file=args.output_file,
        max_workers=args.max_workers
    )
