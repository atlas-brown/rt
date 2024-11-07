# Split files
split -l 50000 activities.csv parts/

# Rename all files in dir
for i in *; do mv "$i" "$i.csv"; done

# Merge individual activity files into one
find . -name \*.csv\* -print0 | xargs -0 cat > merged.csv

# Create a video out of a sequence of images
ffmpeg -i name_%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p video.mp4 -y

# Create gif from all videos in a folder
for i in 'ls *.mp4'; do ffmpeg -i $i -vf scale=480:-1 -t 15 -r 6 $i.gif; done

# Watermark a gif
convert image.gif -coalesce -gravity SouthWest -geometry +0+0 null: watermark.png -layers composite -layers optimize output.gif

# Resize all images in a folder
mogrify -resize 960x960 "*" *.png

# Watermark all files in a folder
for i in `ls *.png`; do composite -gravity southwest watermark.png $i watermarked/$i; done
