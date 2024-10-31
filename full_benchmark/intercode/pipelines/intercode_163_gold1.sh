# Query: Save first IP address of domain 'google.com' in 'address' variable and display it

address=$(dig +short google.com | grep -E '^[0-9.]+$' | head -n 1) && echo $address