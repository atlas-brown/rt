_DIR=$(dirname $(readlink -f $0)) # récupère le dossier du script

pd $_DIR/audio_player.pd &
sleep 2
pd -noaudio $_DIR/video_player.pd &
sleep 2
chromium-browser http://127.0.0.1
