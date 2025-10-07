# bash script to download audio


get_m4a () {
	yt-dlp --no-playlist -f 'bestaudio[ext=m4a]' --embed-thumbnail --embed-metadata "$1"
}
