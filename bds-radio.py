import ffmpeg
import json
import os
import threading
from mpd import MPDClient
from select import select
from transliterate import translit

def _load_config():
	with open('config.json', 'r') as f:
		return json.load(f)

config = _load_config()

youtube_url='{}/{}'.format(config['youtube_url'], config['youtube_key'])
audio = ffmpeg.input(config['audio_url'])
background = ffmpeg.input(**config['background_params'])

client = MPDClient()
client.connect(config['mpd_hostname'], config['mpd_port'])
if config['mpd_password']:
	client.password(config['mpd_password'])

def _parse_song_name():
	song_data = client.currentsong()

	if 'title' not in song_data or 'artist' not in song_data:
		return os.path.splitext(os.path.basename(song_data['file']))[0]

	title = song_data['title']
	artist = song_data['artist']

	if config['transliterate']:
		title = translit(title, 'ru', reversed=True)
		artist = translit(artist, 'ru', reversed=True)
	
	return '{}\n{}'.format(title, artist)

def _write_song_data():
	with open('song.txt.tmp', 'w') as f:
		f.write(_parse_song_name())

	os.replace('song.txt.tmp', 'song.txt')

def _run_ffmpeg():
	return (
		ffmpeg.concat(background.video, audio, v=1, a=1)
		.drawtext(textfile='song.txt', reload=True, **config['text_params'])
		.output(youtube_url, **config['output_params'])
		.run_async()
	)

def _check_mpd():
	while True:
		_write_song_data()
		client.idle()

def _check_ffmpeg():
	while True:
		process = _run_ffmpeg()
		process.wait()

threading.Thread(target=_check_mpd).start()
threading.Thread(target=_check_ffmpeg).start()