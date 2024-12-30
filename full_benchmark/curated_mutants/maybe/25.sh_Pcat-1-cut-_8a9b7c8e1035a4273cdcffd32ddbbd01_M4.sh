# @assume "cat $1" --> "FLying so high,\nAMong modern net's\nINspired world-view:\nGOod as it gets!"
# @output "FLAMINGO"
cat ${1} | cut -c 1-2
