from stream.regular_type import RegularType
from stream.transducer import create_fst, product_fst_automaton

def full_stream_grep():
    pattern_char = "d"
    # pattern_char = "a"
    # grep d
    input = "total [0-9]+\n([drwx-]+( )+[0-9]+( )+[^\n]*\n)+"
    specs = [
        (0, pattern_char, pattern_char, 1),
        (0, "\n", "", 0),
        (0, "$other", "", 2),
        (0, "$other", "$self", 3),
        (1, "\n", "\n", 0),
        (1, "$other", "$self", 1),
        (2, pattern_char, '', 100),
        (2, '\n', '', 0),
        (2, '$other', '', 2),
        (3, pattern_char, pattern_char, 1),
        (3, "\n", "", 100),
        (3, "$other", "$self", 3),
    ]
    fst = create_fst(specs, start_state=0, final_states={0})
    product = product_fst_automaton(fst, RegularType(input).nfa)
    print(product)
    print(product.run("total 4\ndrwxr-xr-x  2 root root 4096 Mar  5  2013 bin\n"))
    print(product.run("total 4\ndrwxr-xr-x  a root root 4096 Mar  5  2013 bin\n"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin\ntotal 4\n"))
    print(product.run("drwxr-xr-x  a root root 4096 Mar  5  2013 bin\n"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin\n"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin\ndrwxr-xr-x  2 root root 4096 Mar  5  2013 bin\n"))

def full_stream_to_line_based():
    specs = [
        (0, "\n", "", 100),
        (0, "$other", "$self", 1),
        (0, "$other", "", 2),
        (1, "\n", "", 100),
        (1, "$other", "$self", 1),
        (2, "\n", "", 0),
        (2, "$other", "", 2),
        (100, "$other", "", 100),
    ]
    input = "total [0-9]+\n([drwx-]+( )+[0-9]+( )+[^\n]*\n)+[0-9\n]+"
    fst = create_fst(specs, start_state=0, final_states={100})
    print(fst)
    print(fst.transform_all("total 4\ntdrwxr-xr-x  2 a a 4096 Mar 10  2013 bin\n"))
    product = product_fst_automaton(fst, RegularType(input).nfa)
    print(product)
    print(product.run("total 4"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin"))
    print(product.run("31248127493874"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin\n"))
    print(product.run("drwxr-xr-x  2 root root 4096 Mar  5  2013 bin\ndrwxr-xr-x  2 root root 4096 Mar  5  2013 bin\n"))

if __name__ == "__main__":
    # full_stream_grep()
    full_stream_to_line_based()
