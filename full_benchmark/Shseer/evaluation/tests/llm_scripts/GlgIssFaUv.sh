
#!/bin/sh

xmlfile=$1
data=$(grep "<specific_data>" $xmlfile)
echo $data

# Modify the XML file
echo "<new_element>new_data</new_element>" >> $xmlfile
