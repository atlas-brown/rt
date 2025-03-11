#!/bin/sh
# https://stackoverflow.com/questions/48089352/merge-two-files-using-awk-in-linux

# ---
# tags: buggy, awk, unclear
# bug:  output file is empty
# ---

# 1.txt contents:
# betomak@msn.com||o||0174686211||o||7880291304ca0404f4dac3dc205f1adf||o||Mario||o||Mario||o||Kawati
# zizipi@libero.it||o||174732943.0174732943||o||e10adc3949ba59abbe56e057f20f883e||o||Tiziano||o||Tiziano||o||D'Intino
# frankmel@hotmail.de||o||0174844404||o||8d496ce08a7ecef4721973cb9f777307||o||Melanie||o||Melanie||o||Kiesel
# apoka-paris@hotmail.fr||o||0174847613||o||536c1287d2dc086030497d1b8ea7a175||o||Sihem||o||Sihem||o||Sousou
# sofianomovic@msn.fr||o||174902297.0174902297||o||9893ac33a018e8d37e68c66cae23040e||o||Nabile||o||Nabile||o||Nassime
# donaldduck@yahoo.com||o||174912161.0174912161||o||0c770713436695c18a7939ad82bc8351||o||Donald||o||Donald||o||Duck
# cernakova@centrum.cz||o||0174991962||o||d161dc716be5daf1649472ddf9e343e6||o||Dagmar||o||Dagmar||o||Cernakova
# trgsrl@tiscali.it||o||0175099675||o||d26005df3e5b416d6a39cc5bcfdef42b||o||Esmeralda||o||Esmeralda||o||Trogu
# catherinesou@yahoo.fr||o||0175128896||o||2e9ce84389c3e2c003fd42bae3c49d12||o||Cat||o||Cat||o||Sou
# ermimurati24@hotmail.com||o||0175228687||o||a7766a502e4f598c9ddb3a821bc02159||o||Anna||o||Anna||o||Beratsja
# cece_89@live.fr||o||0175306898||o||297642a68e4e0b79fca312ac072a9d41||o||Celine||o||Celine||o||Jacinto
# kendinegel39@hotmail.com||o||0175410459||o||a6565ca2bc8887cde5e0a9819d9a8ee9||o||Adem||o||Adem||o||Bulut

# 2.txt contents:
# 9893ac33a018e8d37e68c66cae23040e:134:@a1
# 536c1287d2dc086030497d1b8ea7a175:~~@!:/92\
# 8d496ce08a7ecef4721973cb9f777307:demodemo

# expected output example:
# sofianomovic@msn.fr||o||174902297.0174902297||o||134:@a1||o||Nabile||o||Nabile||o||Nassime

awk -F "||o||" '
    NR==FNR {
        s = $0;
        sub(/:[^:]*$/, "", s);
        a[s] = $NF;
        next
    }
    {
        s = $5;
        for (i=6; i<=NF; ++i) s = s "," $i;
        if (s in a) {
            NF = 5;
            $5=a[s];
            print
        }
    }
' FS=: <(tr -d '\r' < 2.txt) \
    FS="||o||" OFS="||o||" <(tr -d '\r' < 1.txt) > result.txt

# 1.txt regex:
# [^|]+@[^ \t\n]+\|\|o\|\|[0-9]+\.?[0-9]+\|\|o\|\|[a-f0-9]{32}\|\|o\|\|[^|]+\|\|o\|\|[^|]+\|\|o\|\|[^|]+

# 2.txt regex:
# [a-f0-9]{32}:.+
