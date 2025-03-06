# Instagram Downloader

A Python tool to batch download Instagram posts (images, videos, and albums) from URLs, with automatic organization and support for proxy connections.

## Features

- 📁 **Smart Organization**: Automatically categorizes content into images, videos, and albums
- 🔄 **Duplicate Prevention**: Skips already downloaded posts
- 🔐 **Authentication Support**: Uses cookies to access restricted content
- 🌐 **Proxy Capability**: Optional proxy support to avoid IP restrictions
- 📊 **Detailed Logging**: Tracks operations, errors, and successful downloads
- ⏱️ **Rate Limiting**: Configurable delays between requests to avoid being blocked

## Requirements

- Python 3.6 or higher
- Instaloader library
- Requests library

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/instagram-downloader.git
   cd instagram-downloader
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   ```

   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Setup

1. Add Instagram post URLs to `instagram_urls.txt` (one URL per line):
   ```
   https://www.instagram.com/p/SHORTCODE1/
   https://www.instagram.com/p/SHORTCODE2/
   ```

2. (Optional but recommended) Configure authentication:
   - Export your Instagram cookies to `cookies.json` using a browser extension like Cookie-Editor
   - This allows the tool to download content that requires login

## Usage

### Basic Usage

```
python download.py
```

### Advanced Options

```
python download.py [options]
```

Available options:
- `--proxy PROXY`: Use a proxy server (format: http://user:pwd@host:port)
- `--delay SECONDS`: Set delay between requests in seconds (default: 3)
- `--cookies PATH`: Specify custom path to cookies file
- `--no-verify-ssl`: Disable SSL verification (for self-signed certificates)
- `--skip-proxy-test`: Skip testing the proxy connection

### Examples

Download using a proxy with a 5-second delay:
```
python download.py --proxy http://user:password@proxy.example.com:8080 --delay 5
```

Use custom cookies file:
```
python download.py --cookies my_cookies.json
```

## Output

Downloaded content is organized in the `instagram-downloads` directory:
- `individual_images/`: Single image posts
- `individual_videos/`: Single video posts
- `albums/`: Posts with multiple images/videos (in subfolders by post ID)

Logs are stored in the `logs` directory:
- `instagram_downloader_[timestamp].log`: General operation logs
- `successful_downloads.log`: Record of successfully downloaded posts

## Troubleshooting

- **Authentication Issues**: Make sure your cookies.json is valid and recent
- **Rate Limiting**: Increase the delay between requests using `--delay` 
- **Connection Problems**: Try using a proxy with `--proxy`
- **SSL Errors**: Use `--no-verify-ssl` if using a proxy with self-signed certificates

## License

[MIT License](LICENSE)

## Disclaimer

This tool is for personal use only. Please respect Instagram's Terms of Service and copyright laws.
