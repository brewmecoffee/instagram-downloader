#!/usr/bin/env python3
import os
import re
import instaloader
import shutil
import argparse
import logging
import time
import requests
import json
from datetime import datetime

def test_proxy(proxy_url, logger, verify_ssl=True):
    """
    Test if the proxy is working by making a request to Instagram.
    
    Args:
        proxy_url: The proxy URL in format http://user:pwd@host:port
        logger: Logger object for logging the results
        verify_ssl: Whether to verify SSL certificates (set to False for self-signed certs)
        
    Returns:
        bool: True if proxy is working, False otherwise
    """
    logger.info(f"Testing proxy connection: {proxy_url}")
    
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Try to connect to Instagram with a timeout of 10 seconds
        response = requests.get('https://www.instagram.com/', 
                              proxies=proxies, 
                              timeout=10,
                              verify=verify_ssl)  # Set verify to False to ignore SSL errors
        
        if response.status_code == 200:
            logger.info("Proxy test successful!")
            return True
        else:
            logger.error(f"Proxy test failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ProxyError:
        logger.error("Proxy connection error. Please check your proxy settings.")
        return False
    except requests.exceptions.ConnectTimeout:
        logger.error("Proxy connection timed out.")
        return False
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL verification error: {e}")
        logger.warning("Consider using --no-verify-ssl option if using a proxy with self-signed certificates")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy test failed with error: {e}")
        return False

def extract_shortcode_from_url(url: str) -> str:
    """
    Extract the shortcode from a typical Instagram post URL.
    For example: https://www.instagram.com/p/ShortCode/
    """
    # This regex should match the substring between "/p/" and the next slash (or end).
    match = re.search(r"instagram\.com/p/([^/]+)/?", url)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Could not extract shortcode from URL: {url}")

def is_already_downloaded(shortcode, base_dir, post_type=None):
    """
    Check if a post has already been downloaded based on its shortcode.
    
    Args:
        shortcode: The Instagram post shortcode
        base_dir: The base directory for downloads
        post_type: If known, the type of post ('album', 'image', 'video')
    
    Returns:
        bool: True if already downloaded, False otherwise
    """
    # If we know it's an album, check in albums directory
    if post_type == 'album':
        return os.path.exists(os.path.join(base_dir, "albums", shortcode))
    
    # If we know it's an image, check in individual_images directory
    if post_type == 'image':
        # Check if any file with the shortcode exists in individual_images
        img_dir = os.path.join(base_dir, "individual_images")
        if os.path.exists(img_dir):
            for filename in os.listdir(img_dir):
                if shortcode in filename:
                    return True
        return False
    
    # If we know it's a video, check in individual_videos directory
    if post_type == 'video':
        # Check if any file with the shortcode exists in individual_videos
        vid_dir = os.path.join(base_dir, "individual_videos")
        if os.path.exists(vid_dir):
            for filename in os.listdir(vid_dir):
                if shortcode in filename:
                    return True
        return False
    
    # If post_type is not specified, check all possible locations
    # Check albums directory
    if os.path.exists(os.path.join(base_dir, "albums", shortcode)):
        return True
    
    # Check individual_images directory
    img_dir = os.path.join(base_dir, "individual_images")
    if os.path.exists(img_dir):
        for filename in os.listdir(img_dir):
            if shortcode in filename:
                return True
    
    # Check individual_videos directory
    vid_dir = os.path.join(base_dir, "individual_videos")
    if os.path.exists(vid_dir):
        for filename in os.listdir(vid_dir):
            if shortcode in filename:
                return True
    
    return False

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a timestamp for the log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/instagram_downloader_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Also create a success log for completed downloads
    success_log_file = 'logs/successful_downloads.log'
    
    # Create the success logger
    success_logger = logging.getLogger('success')
    success_logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if the function is called multiple times
    if not success_logger.handlers:
        success_handler = logging.FileHandler(success_log_file)
        success_formatter = logging.Formatter('%(asctime)s - %(message)s')
        success_handler.setFormatter(success_formatter)
        success_logger.addHandler(success_handler)
    
    return logging.getLogger(), success_logger

def main():
    # Add command line arguments
    parser = argparse.ArgumentParser(description='Download Instagram posts with optional proxy support.')
    parser.add_argument('--proxy', type=str, help='Proxy in format: http://user:pwd@host:port')
    parser.add_argument('--delay', type=int, default=3, help='Delay in seconds between requests (default: 3)')
    parser.add_argument('--skip-proxy-test', action='store_true', help='Skip proxy testing')
    parser.add_argument('--no-verify-ssl', action='store_true', help='Disable SSL certificate verification (use with caution)')
    parser.add_argument('--cookies', type=str, help='Path to Instagram cookies.json file')
    args = parser.parse_args()
    
    # Set up logging
    logger, success_logger = setup_logging()
    logger.info("Starting Instagram downloader script")
    
    # Disable SSL verification if requested
    if args.no_verify_ssl:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        logger.warning("SSL certificate verification is disabled. This is less secure.")
    
    # Test proxy if provided
    if args.proxy and not args.skip_proxy_test:
        if not test_proxy(args.proxy, logger, verify_ssl=not args.no_verify_ssl):
            logger.error("Proxy test failed. Exiting script.")
            return
    
    # Create Instaloader instance with custom settings to skip .txt and .json files
    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,  # This will skip the .json files
        compress_json=False,
        post_metadata_txt_pattern=None,  # This will skip the .txt files
    )
    
    # Set proxy if provided
    if args.proxy:
        logger.info(f"Using proxy: {args.proxy}")
        L.context._session.proxies = {
            'http': args.proxy,
            'https': args.proxy
        }
    
    # Load cookies if provided
    if args.cookies:
        try:
            logger.info(f"Loading cookies from {args.cookies}")
            with open(args.cookies, 'r') as f:
                cookies = json.load(f)
            
            # Apply cookies to the session - using _session instead of session
            for cookie in cookies:
                L.context._session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie.get('domain', '.instagram.com')
                )
            
            logger.info("Cookies loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return
    
    # If you need authentication (for private posts, rate-limit avoidance, etc.), 
    # uncomment and fill in your credentials:
    # L.login("your_username", "your_password")
    
    # Create the main directory structure
    base_dir = "instagram-downloads"
    individual_images_dir = os.path.join(base_dir, "individual_images")
    individual_videos_dir = os.path.join(base_dir, "individual_videos")
    albums_dir = os.path.join(base_dir, "albums")
    
    os.makedirs(individual_images_dir, exist_ok=True)
    os.makedirs(individual_videos_dir, exist_ok=True)
    os.makedirs(albums_dir, exist_ok=True)
    
    # Path to the text file containing Instagram post URLs
    input_file = "instagram_urls.txt"
    
    if not os.path.isfile(input_file):
        logger.error(f"Error: {input_file} not found in current directory.")
        return
    
    # Count total URLs
    with open(input_file, "r") as f:
        total_urls = sum(1 for line in f if line.strip())
    
    logger.info(f"Found {total_urls} URLs to process")
    
    processed = 0
    skipped = 0
    failed = 0
    
    with open(input_file, "r") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue  # skip empty lines
            
            try:
                shortcode = extract_shortcode_from_url(url)
                processed += 1
                
                # Check if already downloaded
                if is_already_downloaded(shortcode, base_dir):
                    logger.info(f"Skipping already downloaded post: {url}")
                    skipped += 1
                    continue
                
                # Add delay to avoid rate limiting
                if processed > 1:  # Don't delay on the first request
                    time.sleep(args.delay)
                
                # Instantiate a Post object using the shortcode
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                
                # Create a temporary directory for download
                temp_dir = f"temp_{shortcode}"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Download the post to the temporary directory
                logger.info(f"Downloading post [{processed}/{total_urls}]: {url}")
                L.download_post(post, target=temp_dir)
                
                # Determine if it's an album, single image, or video
                is_album = post.typename == "GraphSidecar"
                is_video = post.is_video
                
                # Move files to appropriate directories
                if is_album:
                    # For albums, create a subdirectory inside albums_dir
                    album_subdir = os.path.join(albums_dir, shortcode)
                    os.makedirs(album_subdir, exist_ok=True)
                    
                    # Move all media files from temp_dir to the album subdirectory
                    for filename in os.listdir(temp_dir):
                        if filename.endswith(('.jpg', '.jpeg', '.png', '.mp4')):
                            src_path = os.path.join(temp_dir, filename)
                            dst_path = os.path.join(album_subdir, filename)
                            shutil.move(src_path, dst_path)
                else:
                    # For single media posts
                    for filename in os.listdir(temp_dir):
                        if filename.endswith(('.jpg', '.jpeg', '.png')) and not is_video:
                            # Move image to individual_images directory
                            src_path = os.path.join(temp_dir, filename)
                            dst_path = os.path.join(individual_images_dir, filename)
                            shutil.move(src_path, dst_path)
                        elif filename.endswith('.mp4'):
                            # Move video to individual_videos directory
                            src_path = os.path.join(temp_dir, filename)
                            dst_path = os.path.join(individual_videos_dir, filename)
                            shutil.move(src_path, dst_path)
                
                # Clean up temporary directory
                shutil.rmtree(temp_dir)
                
                # Log successful download
                success_logger.info(f"Successfully downloaded: {url}")
                logger.info(f"Download finished for shortcode: {shortcode}")
                
            except Exception as e:
                failed += 1
                logger.error(f"Error processing URL '{url}': {e}")
    
    # Log summary
    logger.info("\n" + "="*50)
    logger.info(f"Download Summary:")
    logger.info(f"Total URLs: {total_urls}")
    logger.info(f"Successfully downloaded: {processed - skipped - failed}")
    logger.info(f"Skipped (already downloaded): {skipped}")
    logger.info(f"Failed: {failed}")
    logger.info("="*50)

if __name__ == "__main__":
    main()