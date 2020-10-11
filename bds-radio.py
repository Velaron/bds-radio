import os
import ffmpeg
import json
from mpd import MPDClient
from transliterate import translit

config = {}

with open('config.json', 'r') as f:
	config = json.load(f)

client = MPDClient()
client.connect(config['mpd_hostname'], int(config['mpd_port']))

def _write_song_data():
	song_data = client.currentsong()
	title = song_data.get('title', 'UNKNOWN')
	artist = song_data.get('artist', 'UNKNOWN')

	if config['transliterate']:
		title = translit(title, 'ru', reversed=True)
		artist = translit(artist, 'ru', reversed=True)

	with open('song.txt.tmp', 'w') as f:
		f.write('{}\n{}'.format(title, artist))

	os.replace('song.txt.tmp', 'song.txt')

youtube_url='{}/{}'.format(config['youtube_url'], config['youtube_key'])

audio = ffmpeg.input(config['audio_url'])
background = ffmpeg.input(config['background'], loop=True, framerate=int(config['framerate']))

text_params = {
	'fontsize': config['font_size'],
	'x': 16,
	'y': 16,
	'reload': True,
	'textfile': 'song.txt',
	'fontcolor': config['font_color']
}

if len(config['font_file']) > 0:
	text_params.update({'fontfile': config['font_file']})

_write_song_data()
process = (
	ffmpeg.concat(background, audio, v=1, a=1)
	.drawtext(**text_params)
	.output(youtube_url, audio_bitrate='320k', video_bitrate='2500k', acodec='aac', format='flv', framerate=int(config['framerate']))
	.run_async()
)

while True:
	client.idle()
	_write_song_data()