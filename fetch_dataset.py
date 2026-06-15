import os
import csv
import json
import time
import requests
from tqdm import tqdm

BASE_URL = "https://api.musixmatch.com/ws/1.1"
API_KEY = os.environ.get("MXM_KEY")

if not API_KEY:
    raise ValueError(
        "Errore: la variabile d'ambiente 'MXM_KEY' non è impostata. "
        "Esporta prima la chiave con 'export MXM_KEY=la_tua_chiave'"
    )

CSV_FILE = "/Users/software/MXM-hack/top10ksongs.csv"
OUTPUT_FILE = "/Users/software/MXM-hack/lyrics_dataset.jsonl"

def fetch_song_data(track_name, artist_name):
    # 1. Trova il brano
    search_params = {
        "apikey": API_KEY,
        "q_track": track_name,
        "q_artist": artist_name,
        "page_size": 1
    }
    
    response = requests.get(f"{BASE_URL}/track.search", params=search_params)
    response.raise_for_status()
    
    data = response.json()
    message = data.get("message", {})
    header = message.get("header", {})
    status_code = header.get("status_code")
    
    if status_code != 200:
        return None
        
    body = message.get("body", {})
    if not body or isinstance(body, list):
        return None
        
    track_list = body.get("track_list", [])
    if not track_list:
        return None
        
    track_obj = track_list[0].get("track", {})
    
    # Se has_lyrics è 0, skippa e vai avanti
    if track_obj.get("has_lyrics") == 0:
        return None
        
    track_id = track_obj.get("track_id")
    has_richsync = track_obj.get("has_richsync", 0)
    
    # 2. Recupera le liriche
    lyrics_params = {
        "apikey": API_KEY,
        "track_id": track_id
    }
    response_lyrics = requests.get(f"{BASE_URL}/track.lyrics.get", params=lyrics_params)
    response_lyrics.raise_for_status()
    
    data_lyrics = response_lyrics.json()
    message_lyrics = data_lyrics.get("message", {})
    
    if message_lyrics.get("header", {}).get("status_code") != 200:
        return None
        
    lyrics_body_obj = message_lyrics.get("body", {})
    lyrics_obj = lyrics_body_obj.get("lyrics", {})
    
    if not lyrics_obj:
        return None
        
    # Prepara il dizionario di base da salvare
    result = {
        "track_id": track_id,
        "track_name": track_obj.get("track_name", track_name),
        "artist_name": track_obj.get("artist_name", artist_name),
        "track_data": track_obj,  # metadati primari da track.search
        "lyrics_id": lyrics_obj.get("lyrics_id"),
        "lyrics_data": lyrics_body_obj,  # tutto il data body da track.lyrics.get
        "lyrics_txt": lyrics_obj.get("lyrics_body")
    }
    
    # 3. Se has_richsync=1 salva anche richsync body
    if has_richsync == 1:
        richsync_params = {
            "apikey": API_KEY,
            "track_id": track_id
        }
        response_sync = requests.get(f"{BASE_URL}/track.richsync.get", params=richsync_params)
        if response_sync.status_code == 200:
            data_sync = response_sync.json()
            message_sync = data_sync.get("message", {})
            if message_sync.get("header", {}).get("status_code") == 200:
                sync_body = message_sync.get("body", {})
                richsync_obj = sync_body.get("richsync", {})
                if richsync_obj:
                    result["richsync_body"] = richsync_obj.get("richsync_body")
                    
    return result

def main():
    # Leggi il CSV
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Salta l'header
        rows = list(reader)
        
    print(f"Trovate {len(rows)} canzoni. Inizio il download...")
    
    # Apri in modalità 'append' per salvare riga per riga in tempo reale
    with open(OUTPUT_FILE, mode='a', encoding='utf-8') as out_f:
        for row in tqdm(rows, desc="Elaborazione brani"):
            if len(row) < 3:
                continue
                
            artist_name = row[1].strip()
            song_name = row[2].strip()
            
            try:
                song_data = fetch_song_data(song_name, artist_name)
                
                # Se abbiamo ottenuto dati (cioè has_lyrics != 0 e tutto è andato a buon fine)
                if song_data:
                    # Salva su file convertendo l'oggetto in stringa JSON
                    out_f.write(json.dumps(song_data, ensure_ascii=False) + "\n")
                else:
                    # Stampa che la canzone è stata saltata
                    tqdm.write(f"Nessuna lirica (o brano non trovato) per: '{song_name}' - '{artist_name}'. Skippo.")
                    
            except Exception as e:
                # In caso di errori (es. timeout o disconnessioni) lo segnaliamo ma continuiamo col prossimo brano
                tqdm.write(f"Errore di sistema con '{song_name}' - '{artist_name}': {e}")
                
            # Aggiungiamo un piccolissimo delay per non sovraccaricare le API di Musixmatch
            time.sleep(0.05)

if __name__ == "__main__":
    main()
