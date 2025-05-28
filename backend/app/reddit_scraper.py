#!/usr/bin/env python3
"""
Simplified Reddit scraper for discovering hidden gems.
Extracts URLs from posts and scrapes them with concurrent processing.
"""
import json
import random
import re

# Import from the same directory
import time
from urllib.parse import urlparse

import requests

from .scraper import scrape_with_discovery_concurrent

# Configuration constants
MAX_CONCURRENT = 30  # Max concurrent requests for optimal speed
DISCOVER_DEPTH = 2  # Link discovery depth (2 is sweet spot)
DEFAULT_DELAY = 2  # Delay between Reddit API calls (seconds)
DEFAULT_PAGES = 20  # Default pages to scrape in continuous mode


def get_random_time_filter():
    """
    Get a random time filter for discovering content from different periods.

    Returns:
        str: Random time filter (day, week, month, year, all)
    """
    time_options = ["day", "week", "month", "year", "all"]
    weights = [1, 2, 3, 2, 1]  # Prefer week/month for best content
    return random.choices(time_options, weights=weights)[0]


def get_random_sort_and_time():
    """
    Get a random sort method and time filter for content discovery.

    Returns:
        tuple: (sort_method, time_filter)
    """
    sort_options = ["hot", "new", "top", "rising"]
    sort = random.choice(sort_options)

    time_filter = None
    if sort == "top":
        time_filter = get_random_time_filter()

    return sort, time_filter


def get_reddit_posts(
    subreddit="InternetIsBeautiful", limit=25, sort="hot", after=None, time_filter=None
):
    """
    Get posts from a Reddit subreddit using the JSON API with pagination.

    Args:
        subreddit: Subreddit name (default: InternetIsBeautiful)
        limit: Number of posts to fetch (max 100)
        sort: Sort method (hot, new, top, rising, random)
        after: Pagination token for next page
        time_filter: Time filter for top posts (hour, day, week, month, year, all)

    Returns:
        tuple: (posts_list, next_after_token)
    """
    # Note: Random sorting is now handled by get_random_sort_and_time()

    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"

    headers = {"User-Agent": "gem-search-bot/1.0 (content discovery tool)"}

    params = {"limit": min(limit, 100)}  # Reddit API limit

    # Add time filter for top posts
    if sort == "top" and time_filter:
        params["t"] = time_filter

    if after:
        params["after"] = after

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        posts = []

        for item in data["data"]["children"]:
            post = item["data"]
            posts.append(
                {
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "selftext": post.get("selftext", ""),
                    "score": post.get("score", 0),
                    "created_utc": post.get("created_utc", 0),
                    "permalink": f"https://www.reddit.com{post.get('permalink', '')}",
                }
            )

        # Get next page token
        next_after = data["data"].get("after")

        return posts, next_after

    except Exception as e:
        print(f"Failed to fetch Reddit posts: {e}")
        return [], None


def extract_urls_from_text(text):
    """
    Extract URLs from text using regex.

    Args:
        text: Text to search for URLs

    Returns:
        set: Set of found URLs
    """
    # Regex pattern for URLs
    url_pattern = r'https?://[^\s<>"{\}|\\^`\[\]]+[^\s<>"{\}|\\^`\[\].,;!?\'")\]]*'

    urls = set()
    matches = re.findall(url_pattern, text)

    for match in matches:
        # Clean up common trailing characters
        url = match.rstrip(".,;!?'\")]*")

        # Validate URL
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                urls.add(url)
        except Exception:
            pass

    return urls


def filter_reddit_urls(urls):
    """
    Filter out Reddit URLs and other unwanted domains.

    Args:
        urls: Set of URLs to filter

    Returns:
        set: Filtered URLs
    """
    filtered = set()

    # Domains to skip
    skip_domains = {
        "reddit.com",
        "www.reddit.com",
        "old.reddit.com",
        "m.reddit.com",
        "redd.it",
        "imgur.com",
        "i.imgur.com",
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "x.com",
        "facebook.com",
        "instagram.com",
    }

    for url in urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Skip if no domain (invalid URL) or domain is in skip list
            if domain and domain not in skip_domains:
                filtered.add(url)
        except Exception:
            pass

    return filtered


def scrape_reddit_batch(subreddit, db_path, after=None, sort="hot", time_filter=None):
    """
    Scrape a batch of Reddit posts and extract websites with link discovery.
    Uses concurrent processing with optimized settings.

    Args:
        subreddit: Subreddit name
        db_path: Database path
        after: Pagination token for next page (optional)
        sort: Sort method (hot, new, top, rising)
        time_filter: Time filter for top posts (hour, day, week, month, year, all)

    Returns:
        tuple: (total_urls_found, new_documents_added, next_after_token)
    """
    print(f"Fetching posts from r/{subreddit} (sort: {sort})...")

    # Get Reddit posts with pagination (100 is Reddit API max)
    posts, next_after = get_reddit_posts(
        subreddit, 100, sort=sort, after=after, time_filter=time_filter
    )
    if not posts:
        print("No posts found")
        return 0, 0, None

    print(f"Found {len(posts)} posts")

    # Extract URLs from all posts
    all_urls = set()

    for post in posts:
        # Check post URL (main link)
        if post["url"] and not post["url"].startswith("https://www.reddit.com"):
            all_urls.add(post["url"])

        # Check self text for URLs
        if post["selftext"]:
            text_urls = extract_urls_from_text(post["selftext"])
            all_urls.update(text_urls)

    print(f"Extracted {len(all_urls)} URLs from posts")

    # Filter out Reddit and social media URLs
    filtered_urls = filter_reddit_urls(all_urls)
    print(f"After filtering: {len(filtered_urls)} URLs to process")

    if not filtered_urls:
        print("No URLs to process after filtering")
        return len(all_urls), 0, next_after

    # Show first few URLs
    print("\\nFirst 10 URLs to scrape:")
    for i, url in enumerate(list(filtered_urls)[:10]):
        print(f"{i+1}. {url}")

    # Create temporary links file
    temp_links_file = "/tmp/reddit_links.json"
    with open(temp_links_file, "w") as f:
        json.dump(list(filtered_urls), f, indent=2)

    print(
        f"\\nStarting concurrent link discovery scraping (depth {DISCOVER_DEPTH}, {MAX_CONCURRENT} max requests)..."
    )

    # Use concurrent scraper with optimized settings
    try:
        import asyncio

        new_docs, total_discovered = asyncio.run(
            scrape_with_discovery_concurrent(
                temp_links_file,
                db_path,
                discover_depth=DISCOVER_DEPTH,
                allow_cross_domain=False,  # Stay within same domains for each site
                max_concurrent=MAX_CONCURRENT,
            )
        )

        print("\\nReddit scraping complete!")
        print(f"- Found {len(all_urls)} URLs in Reddit posts")
        print(f"- Processed {len(filtered_urls)} URLs after filtering")
        print(f"- Discovered {total_discovered} total URLs with depth {DISCOVER_DEPTH}")
        print(f"- Added {new_docs} new documents to database")

        return len(all_urls), new_docs, next_after

    except Exception as e:
        print(f"Error during scraping: {e}")
        return len(all_urls), 0, next_after
    finally:
        # Clean up temp file
        try:
            import os

            os.remove(temp_links_file)
        except Exception:
            pass


def scrape_reddit_continuous(subreddit, db_path, max_pages=DEFAULT_PAGES, random_dates=True):
    """
    Continuously scrape Reddit subreddit with random date exploration.
    Always uses concurrent processing for optimal speed.

    Args:
        subreddit: Subreddit name (default: InternetIsBeautiful)
        db_path: Database path
        max_pages: Maximum pages to process (default: 20)
        random_dates: Use random sort methods and time filters for diversity

    Returns:
        dict: Summary statistics
    """
    print(f"🚀 Starting high-speed scraping of r/{subreddit}")
    print(f"Random date exploration: {'enabled' if random_dates else 'disabled'}")
    print(f"Link discovery depth: {DISCOVER_DEPTH}")
    print(f"Concurrent requests: {MAX_CONCURRENT}")
    print(f"API call delay: {DEFAULT_DELAY}s")
    print(f"Max pages: {max_pages}")
    print("-" * 60)

    total_reddit_urls = 0
    total_new_docs = 0
    page_count = 0
    after_token = None

    try:
        while True:
            page_count += 1
            print(f"\n=== PAGE {page_count} ===")

            # Determine sort method and time filter
            if random_dates:
                current_sort, current_time_filter = get_random_sort_and_time()
                if current_time_filter:
                    print(f"🎲 Random selection: {current_sort} (time: {current_time_filter})")
                else:
                    print(f"🎲 Random selection: {current_sort}")
                # Reset after_token when changing sort method to start fresh
                after_token = None
            else:
                current_sort = "hot"
                current_time_filter = None

            # Scrape batch with pagination
            reddit_urls, new_docs, next_after = scrape_reddit_batch(
                subreddit,
                db_path,
                after=after_token,
                sort=current_sort,
                time_filter=current_time_filter,
            )

            # Update totals
            total_reddit_urls += reddit_urls
            total_new_docs += new_docs

            # Check if we're done
            if not next_after or page_count >= max_pages:
                print("\\nReached end of available posts or max pages limit")
                break

            after_token = next_after

            # Print progress
            print(f"\\nProgress after page {page_count}:")
            print(f"- Total Reddit URLs found: {total_reddit_urls}")
            print(f"- Total new documents added: {total_new_docs}")

            # Respectful delay between API calls
            print(f"Waiting {DEFAULT_DELAY}s before next page...")
            time.sleep(DEFAULT_DELAY)

    except KeyboardInterrupt:
        print("\\n\\nScraping interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\\n\\nError during continuous scraping: {e}")

    # Final summary
    print("\\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    print(f"Pages processed: {page_count}")
    print(f"Total Reddit URLs found: {total_reddit_urls}")
    print(f"Total new documents added: {total_new_docs}")

    # Get final database count
    try:
        import os
        import sqlite3

        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist")
        else:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Check if documents table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM documents")
                final_count = cursor.fetchone()[0]
                print(f"Final database size: {final_count} documents")
            else:
                print("Documents table not found - need to initialize database")
                print("Run: python init_db.py")
            conn.close()
    except Exception as e:
        print(f"Could not get final database count: {e}")

    return {
        "pages_processed": page_count,
        "reddit_urls_found": total_reddit_urls,
        "new_documents_added": total_new_docs,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="🚀 High-speed Reddit scraper for discovering hidden gems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python reddit_scraper.py                           # Quick single batch
  python reddit_scraper.py --continuous              # Continuous with random dates
  python reddit_scraper.py --subreddit programming   # Different subreddit

Configuration:
  Max concurrent requests: {MAX_CONCURRENT}
  Link discovery depth: {DISCOVER_DEPTH}
  API delay: {DEFAULT_DELAY}s
        """,
    )

    parser.add_argument(
        "--subreddit",
        "-s",
        default="InternetIsBeautiful",
        help="Subreddit to scrape (default: %(default)s)",
    )
    parser.add_argument(
        "--db-path", default="search.db", help="Database path (default: %(default)s)"
    )
    parser.add_argument(
        "--continuous",
        "-c",
        action="store_true",
        help="Run continuously with random date exploration",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_PAGES,
        help="Max pages in continuous mode (default: %(default)s)",
    )
    parser.add_argument(
        "--no-random-dates",
        action="store_true",
        help="Disable random date exploration (use hot posts only)",
    )

    args = parser.parse_args()

    if args.continuous:
        print("🔄 Running in CONTINUOUS mode")
        scrape_reddit_continuous(
            args.subreddit, args.db_path, args.max_pages, random_dates=not args.no_random_dates
        )
    else:
        print("⚡ Running SINGLE BATCH mode")
        reddit_urls, new_docs, _ = scrape_reddit_batch(args.subreddit, args.db_path)
        print(f"\nQuick batch complete: {new_docs} documents added")
