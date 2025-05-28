#!/usr/bin/env python3
"""
Reddit scraper for r/InternetIsBeautiful subreddit.
Extracts URLs from posts and scrapes them with depth 2.
"""
import json
import re
import time
from urllib.parse import urlparse

import requests
from scraper import scrape_with_discovery


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
    # Handle random sorting by picking a random sort method
    if sort == "random":
        import random

        sort_options = ["hot", "new", "top", "rising"]
        sort = random.choice(sort_options)
        print(f"Random sort selected: {sort}")

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
            continue

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
            domain = urlparse(url).netloc.lower()
            if domain not in skip_domains:
                filtered.add(url)
        except Exception:
            continue

    return filtered


def scrape_reddit_batch(
    subreddit, db_path, limit=25, discover_depth=2, after=None, sort="hot", time_filter=None
):
    """
    Scrape a batch of Reddit posts and extract websites with link discovery.

    Args:
        subreddit: Subreddit name
        db_path: Database path
        limit: Number of Reddit posts to process
        discover_depth: Depth for link discovery on found websites
        after: Pagination token for next page
        sort: Sort method (hot, new, top, rising, random)
        time_filter: Time filter for top posts (hour, day, week, month, year, all)

    Returns:
        tuple: (total_urls_found, new_documents_added, next_after_token)
    """
    print(f"Fetching posts from r/{subreddit} (sort: {sort})...")

    # Get Reddit posts with pagination
    posts, next_after = get_reddit_posts(
        subreddit, limit, sort=sort, after=after, time_filter=time_filter
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

    print(f"\\nStarting link discovery scraping with depth {discover_depth}...")

    # Use existing scraper with discovery
    try:
        new_docs, total_discovered = scrape_with_discovery(
            temp_links_file,
            db_path,
            discover_depth=discover_depth,
            allow_cross_domain=False,  # Stay within same domains for each site
        )

        print("\\nReddit scraping complete!")
        print(f"- Found {len(all_urls)} URLs in Reddit posts")
        print(f"- Processed {len(filtered_urls)} URLs after filtering")
        print(f"- Discovered {total_discovered} total URLs with depth {discover_depth}")
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


def scrape_reddit_continuous(
    subreddit,
    db_path,
    discover_depth=2,
    max_pages=None,
    delay_seconds=5,
    sort="hot",
    time_filter=None,
    random_start=False,
):
    """
    Continuously scrape Reddit subreddit with pagination until exhausted.

    Args:
        subreddit: Subreddit name
        db_path: Database path
        discover_depth: Depth for link discovery on found websites
        max_pages: Maximum pages to process (None = unlimited)
        delay_seconds: Delay between Reddit API calls to be respectful
        sort: Sort method (hot, new, top, rising, random)
        time_filter: Time filter for top posts (hour, day, week, month, year, all)
        random_start: If True, randomize sort method for each page

    Returns:
        dict: Summary statistics
    """
    print(f"Starting continuous scraping of r/{subreddit}")
    print(f"Sort method: {sort}")
    if time_filter:
        print(f"Time filter: {time_filter}")
    if random_start:
        print("Random start points enabled - will vary sort method")
    print(f"Link discovery depth: {discover_depth}")
    print(f"Delay between API calls: {delay_seconds}s")
    print(f"Max pages: {max_pages if max_pages else 'unlimited'}")
    print("-" * 50)

    total_reddit_urls = 0
    total_new_docs = 0
    page_count = 0
    after_token = None

    try:
        while True:
            page_count += 1
            print(f"\n=== PAGE {page_count} ===")

            # Determine sort method for this page
            current_sort = sort
            current_time_filter = time_filter

            if random_start:
                import random

                sort_options = ["hot", "new", "top", "rising"]
                current_sort = random.choice(sort_options)

                # If we picked 'top', also randomize time filter
                if current_sort == "top":
                    time_options = ["day", "week", "month", "year", "all"]
                    current_time_filter = random.choice(time_options)
                    print(f"Random selection: {current_sort} (time: {current_time_filter})")
                else:
                    print(f"Random selection: {current_sort}")
                    current_time_filter = None

                # Reset after_token when changing sort method to start fresh
                after_token = None

            # Scrape batch with pagination
            reddit_urls, new_docs, next_after = scrape_reddit_batch(
                subreddit,
                db_path,
                limit=100,
                discover_depth=discover_depth,
                after=after_token,
                sort=current_sort,
                time_filter=current_time_filter,
            )

            # Update totals
            total_reddit_urls += reddit_urls
            total_new_docs += new_docs

            # Check if we're done
            if not next_after or (max_pages and page_count >= max_pages):
                print("\\nReached end of available posts or max pages limit")
                break

            after_token = next_after

            # Print progress
            print(f"\\nProgress after page {page_count}:")
            print(f"- Total Reddit URLs found: {total_reddit_urls}")
            print(f"- Total new documents added: {total_new_docs}")

            # Respectful delay between API calls
            if delay_seconds > 0:
                print(f"Waiting {delay_seconds}s before next page...")
                time.sleep(delay_seconds)

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
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        final_count = cursor.fetchone()[0]
        conn.close()
        print(f"Final database size: {final_count} documents")
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
        description="Scrape Reddit subreddit and extract linked websites."
    )
    parser.add_argument(
        "--subreddit",
        default="InternetIsBeautiful",
        help="Subreddit to scrape (default: InternetIsBeautiful)",
    )
    parser.add_argument("--db-path", default="search.db", help="Database path (default: search.db)")
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of Reddit posts to process in single batch mode (default: 25)",
    )
    parser.add_argument(
        "--discover-depth",
        type=int,
        default=2,
        help="Link discovery depth for websites (default: 2)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode to scrape all available posts with pagination",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to process in continuous mode (default: unlimited)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Delay in seconds between Reddit API calls (default: 5)",
    )
    parser.add_argument(
        "--sort",
        default="hot",
        choices=["hot", "new", "top", "rising", "random"],
        help="Sort method for Reddit posts (default: hot)",
    )
    parser.add_argument(
        "--time-filter",
        choices=["hour", "day", "week", "month", "year", "all"],
        help="Time filter for top posts (only used with --sort top)",
    )
    parser.add_argument(
        "--random-start",
        action="store_true",
        help="Randomize sort method for each page in continuous mode",
    )

    args = parser.parse_args()

    if args.continuous:
        print("Running in CONTINUOUS mode - will scrape all available posts")
        scrape_reddit_continuous(
            args.subreddit,
            args.db_path,
            args.discover_depth,
            args.max_pages,
            args.delay,
            args.sort,
            args.time_filter,
            args.random_start,
        )
    else:
        print("Running in SINGLE BATCH mode")
        reddit_urls, new_docs, _ = scrape_reddit_batch(
            args.subreddit,
            args.db_path,
            args.limit,
            args.discover_depth,
            sort=args.sort,
            time_filter=args.time_filter,
        )
