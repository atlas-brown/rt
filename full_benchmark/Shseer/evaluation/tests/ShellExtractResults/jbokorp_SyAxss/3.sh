for i in $(ls lojban-????{,?}); do
    python -m sb.maillist --fname $i > $i.xml
done
