for i in $@
do
	if ! grep -q Copyright $i
	then
		cat ../../copy_short.txt $i > $i.new && mv $i.new $i
	fi
done
