BBOX="13.301053047180174,53.028206650012166,13.316202163696289,53.03405226930914"

rm layer-*.png
render --bbox $BBOX --zoom=18 --scale=2 --style=styles/landuse.xml --file=layer-0-landuse
render --bbox $BBOX --zoom=18 --scale=2 --style=styles/ways.xml --file=layer-1-ways
render --bbox $BBOX --zoom=18 --scale=2 --style=styles/buildings.xml --file=layer-2-buildings
render --bbox $BBOX --zoom=18 --scale=2 --style=styles/noc.xml --file=layer-3-noc
render --bbox $BBOX --zoom=18 --scale=2 --style=styles/gpscoords.xml --file=layer-4-gpscoords
render --bbox $BBOX --zoom=17 --style=styles/amenities.xml --file=layer-5-amenities

gm convert -compose Atop layer-*.png -flatten X-composition.png
