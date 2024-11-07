# Save pwd and then change dir to the script location
STARTDIR=`pwd`
cd `dirname $0`/..

# Do the compressed version of SASS compilation
sass --style=compressed assets/sass/input/main.scss assets/sass/compiled.css

# Here's a nice one for dev/readability
sass assets/sass/input/main.scss assets/sass/compiled-dev.css

# Go back to original dir
cd $STARTDIR 

