#!/bin/bash
# https://stackoverflow.com/questions/50061202/how-to-grep-a-matching-pattern-in-all-the-lines-in-a-file-except-the-first-two-l

# ---
# tags: unclear
# ---

# no bug present (except: two functions are called that are not present in this file)
# unclear how to annotate this

echo -n "Enter the value to search: ";
read search1;
echo -e "\n"

if [ $(tail -n +3 /root/scripts/contacts.txt | grep -i $search1 | wc -l) -eq 0 ]; then
    echo -e "No matching rows found!!!! \n"
    echo -n "To re-enter press r. To go back to main menu press any key: ";
    read reenter;
    echo -e "\n";
    if [ "$reenter" == "R" ] || [ "$reenter" == "r" ]; then
        remove_entry # calling a function
    else
        inputscan # calling a function
    fi
else
    echo -n "Number of Matching rows found:";
    tail -n +3 /root/scripts/contacts.txt | grep -i $search1 | wc -l;
    echo -e "\n";
    tail -n +3 /root/scripts/contacts.txt | grep -i "$search1" | column -t -s";";
fi
