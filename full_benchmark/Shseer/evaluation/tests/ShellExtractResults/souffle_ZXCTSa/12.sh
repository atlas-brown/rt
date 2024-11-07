#!/bin/sh

# Run the build command
case "$DOMAIN_SIZE" in
  	"64bit")
		cmake -S . -B ./build -DSOUFFLE_DOMAIN_64BIT=ON
    ;;

  	"32bit")
		cmake -S . -B ./build
    ;;
esac


# Create the package
cmake --build ./build --parallel "$(nproc)" --target package
