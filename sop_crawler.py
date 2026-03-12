import requests
from bs4 import BeautifulSoup
import os
import re

def clean_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')

def get_main_content(soup):
    content_selectors = [
        'section',
        'main',
        'div[role="main"]',
        'div[data-automation-id="page-content-wrapper"]',
        '.n3VNCb', 
        '.mY1V9',  
        '#sites-canvas-main-content'
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content and len(content.get_text(strip=True)) > 100:
            return content
            
    for nav in soup.select('nav, header, footer, .navigation, .sidebar, .footer, script, style'):
        nav.decompose()
        
    return soup.find('body')

def crawl_sop_site(base_url):
    print(f"Crawling {base_url}...")
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        kb_dir = "/Users/violinarajbongshi/.gemini/antigravity/brain/442d8d21-a71c-49e5-9205-5fd04db34e9e/KB/SOP"
        if not os.path.exists(kb_dir):
            os.makedirs(kb_dir)
            
        links = soup.find_all('a', href=True)
        sop_links = []
        for link in links:
            href = link.get('href')
            text = link.text.strip()
            if href.startswith('/shiprocket.com/sop-shiprocket/') and text:
                full_url = "https://sites.google.com" + href
                if (text, full_url) not in sop_links:
                    sop_links.append((text, full_url))
                
        print(f"Found {len(sop_links)} SOP links.")
        
        files_saved = 0
        for name, url in sop_links:
            try:
                res = requests.get(url)
                res.raise_for_status()
                sub_soup = BeautifulSoup(res.text, 'html.parser')
                
                main_content = get_main_content(sub_soup)
                
                if main_content:
                    text_content = main_content.get_text(separator=' ', strip=True)
                    # Clean up multiple spaces and newlines
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    file_name = clean_filename(name) + ".md"
                    file_path = os.path.join(kb_dir, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {name}\n\nSource: {url}\n\n{text_content}")
                    files_saved += 1
                else:
                    print(f"Could not find main content for {name}")
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                
        return files_saved
    except Exception as e:
        print(f"Major error during crawl: {e}")
        return 0

if __name__ == "__main__":
    if not os.path.exists("/Users/violinarajbongshi/.gemini/antigravity/brain/442d8d21-a71c-49e5-9205-5fd04db34e9e/KB"):
        os.makedirs("/Users/violinarajbongshi/.gemini/antigravity/brain/442d8d21-a71c-49e5-9205-5fd04db34e9e/KB")
    crawl_sop_site("https://sites.google.com/shiprocket.com/sop-shiprocket/home")
