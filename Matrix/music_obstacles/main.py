import sys
from song_search_engine import searchOnlineFiles
from song_search_engine import play_song



def listen_for_input():
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        query = line.strip()
        result = searchOnlineFiles(query, limit = 1)

        if result:
            print(f"RESULT: {result[0]['url']}")
            sys.stdout.flush()  
            play_song(result[0]['url'])
            
        

if __name__ == "__main__" :
    listen_for_input()





