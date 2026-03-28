# search engine using yt-dlp
import os
import sys
import subprocess
from difflib import SequenceMatcher

try:
    # try normal import
    from youtubesearchpython import VideosSearch
    import httpx
    
    # verify httpx compatibility
    if httpx.__version__ >= "0.28.0":
        raise ImportError("httpx version is incompatible (the version should be older).")
        
    HAS_ONLINE_LIB = True

except ImportError:
    print("incompatible imports. trying brute force installation")
    try:
        # install youtube-search-python and httpx version 0.27.2 
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "youtube-search-python", 
            "httpx==0.27.2"
        ])
        
        # trying import again after installation
        from youtubesearchpython import VideosSearch
        HAS_ONLINE_LIB = True
        print("fixed. modules are installed")
    except Exception as e:
        HAS_ONLINE_LIB = False
        print(f"could not fix. error: {e}")

# searched extensions
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.m4a')

def getSimilarity(a, b):
    return SequenceMatcher(None, a,b).ratio()

def searchOnlineFiles(query, limit=10):
    results = []
    
    if not HAS_ONLINE_LIB:
        return []
    
    if not query or query.strip() == "":
        return []
    
    print(f"Searching on YouTube: '{query}'...")
    
    try:
        # efective search
        videosSearch = VideosSearch(query, limit=limit)
        results_raw = videosSearch.result()
    
        # check for result
        if 'result' in results_raw:
            for item in results_raw['result']:
                results.append({
                    'title': item.get('title'),
                    # chanel name
                    'artist': item.get('channel', {}).get('name'),
                    'url': item.get('link'),
                    # duration
                    'duration': item.get('duration'),
                    # cover image
                    'thumbnail': item.get('thumbnails', [{}])[0].get('url')
                })
                
    except Exception as e:
        print(f"Search error: {e}")
        results.append({'title': f"EROARE CRITICA: {str(e)}", 'artist': 'System', 'url': '', 'duration': '0:00'})
        
    return results
