#!/bin/bash

assert() {
  expected="$1"
  input="$2"

  ./debug/9cc "$input" > debug/tmp.s
  cat <<-FUNC | cc -c -xc -o debug/tmp2.o -
    int ret1()  { return 1; }
    int ret42() { return 42; }
    int echo_self(int a) { return a; }
    int sum3(int a, int b, int c) { return a + b + c; }
	FUNC

  cc -o debug/tmp debug/tmp.s debug/tmp2.o

  ./debug/tmp
  actual="$?"

  if [ "$actual" = "$expected" ]; then
    echo "$input => $actual"
  else
    echo "$input => $expected expected but got $actual"
    exit 1
  fi
}

assert 5  'main() { int x = 3, y = 2; return x + y; }'
assert 2  'main() { int x = 3, y = x - 2; return x - y; }'

assert 3  'main() { int x = 3; return *&x; }'
assert 2  'main() { int x = 2, y = &x; return *y; }'
assert 7  'main() { int x = 9, y = 7; return *(&x + 8); }'
assert 9  'main() { int x = 9, y = 7; return *(&y - 8); }'
assert 4  'main() { int x = 9, y = &x; *y = 4; return x; }'
assert 7  'main() { int x = 7, y = 5; *(&x + 8) = 3; return x; }'
assert 3  'main() { int x = 7, y = 5; *(&x + 8) = 3; return y; }'
assert 4  'main() { int x = 7, y = 5; *(&y - 8) = 4; return x; }'
assert 5  'main() { int x = 7, y = 5; *(&y - 8) = 4; return y; }'

assert 9  'inc(int x) { return x + 1; } main() { return inc(8); }'
assert 7  'adder(int p, int q, int r, int x, int y, int z) { return p + q + r + x + y + z; } main() { return adder(2, -5, 3, 3, -4, 8); }'
assert 89 '
  fibo(int n) {
    if (n <= 0) {
      return 0;
    }
    if (n == 1) {
      return 1;
    }
    return fibo(n - 1) + fibo(n - 2);
  }
  main() {
    return fibo(11);
  }
'

assert 3  'foo() { return 3; } main() { return foo(); }'
assert 4  'foo() { int hoge = 1; return hoge; } main() { int bar = 3; return foo() + bar; }'
assert 42 'foo() { return 14; } bar() { return 4; } baz() { return 7; } main() { return foo() + bar() * baz(); }'

assert 3  'main() { return echo_self(3); }'
assert 42 'main() { return sum3(7, 12, 23); }'
assert 7  'main() { int foo = 3; int bar = 2; int baz = sum3(foo, -bar, foo * bar); return baz; }'

assert 1  'main() { return ret1(); }'
assert 42 'main() { return ret42(); }'

assert 2  'main() { int foo = 1; foo = foo * 2; return foo; }'
assert 42 'main() { int foo = 42; { int bar = foo * 2; bar = bar + 1;} return foo; }'
assert 0  'main() { if (1 != 1) { int foo = 1; return foo; } else { int foo = 0; return foo; } }'
assert 1  'main() { if (1 == 1) { int foo = 1; return foo; } else { int foo = 0; return foo; } }'


assert 16 'main() { int foo = 1; int i; for (i=0; i<4; i = i + 1) foo = foo * 2; return foo; }'
assert 10 'main() { int i = 0; for (; i<10; i = i + 1) 1 == 1; return i; }'
assert 42 'main() { int i; for (i = 0; i<42;) i = i + 1; return i; }'
assert 42 'main() { int i = 0; for (; i<42;) i = i + 1; return i; }'
assert 1  'main() { for (;;) return 1; return 0; }'

assert 1  'main() { int foo = 1; while (foo == 1) return 1; return 0; }'
assert 0  'main() { int foo = 2; while (foo == 1) return 1; return 0; }'
assert 1  'main() { int foo = 100; while (foo != 1) foo = foo - 1; return foo; }'
assert 42 'main() { int foo = 42; int bar = 0; while ((foo = foo -1) >= 0) bar = bar + 1; return bar; }'

assert 1  'main() { int foo = 1; if (foo == 1) return foo; return 0; }'
assert 0  'main() { int foo = 2; if (foo == 1) return foo; return 0; }'
assert 1  'main() { int foo = 1; if (foo == 1) return foo; else return 0; }'
assert 0  'main() { int foo = 2; if (foo == 1) return foo; else return 0; }'
assert 1  'main() { int foo = 1; int bar = 3; if (foo == 1) return 1; else if (bar == 3) return 3; else 10; }'
assert 3  'main() { int foo = 2; int bar = 3; if (foo == 1) return 1; else if (bar == 3) return 3; return 10; }'
assert 10 'main() { int foo = 2; int bar = 7; if (foo == 1) return 1; else if (bar == 3) return 3; else return 10; }'

assert 1  'main() { int _foo = 1; return _foo; }'
assert 2  'main() { int bar; int foo = bar = 2; return foo; }'
assert 3  'main() { int bar; int foo = bar = 3; return bar; }'
assert 11 'main() { int foo = 3; int bar0 = 2; int bar1 = foo - bar0; return bar1 + 10; }'
assert 6  'main() { int foo = 3; int bar = 2; int _baz = 4; int quix = foo * 4 / (3 * bar - 2 * _baz); return -quix; }'

assert 1  'main() { int a = 1; return a; }'
assert 2  'main() { int z; int a = z = 2; return z; }'
assert 2  'main() { int z; int a = z = 2; return a; }'
assert 1  'main() { int a = 3; int b = 2; int c = a - b; return c; }'
assert 6  'main() { int a = 3; int b = 2; int c = 4; int z = a * 4 / (3 * b - c); return z; }'

assert 1  'main() { return 1; 2; 3; }'
assert 2  'main() { 1; return 2; 3; }'
assert 3  'main() { 1; 2; return 3; }'
assert 1  'main() { return 1; return 2; return 3; }'

assert 0  'main() { return 1 != 2 * 1 - 1; }'
assert 1  'main() { return 7 == -5 * (-2) + 10 / (-2) - (-2); }'

assert 0  'main() { return 0 > 1; }'
assert 0  'main() { return 1 > 1; }'
assert 1  'main() { return 1 > 0; }'
assert 0  'main() { return 0 >= 1; }'
assert 1  'main() { return 1 >= 1; }'
assert 1  'main() { return 1 >= 0; }'

assert 0  'main() { return 1 < 0; }'
assert 0  'main() { return 1 < 1; }'
assert 1  'main() { return 0 < 1; }'
assert 0  'main() { return 1 <= 0; }'
assert 1  'main() { return 1 <= 1; }'
assert 1  'main() { return 0 <= 1; }'

assert 0  'main() { return 0 == 1; }'
assert 1  'main() { return 42 == 42; }'
assert 0  'main() { return 42 != 42; }'
assert 1  'main() { return 0 != 1; }'

assert 0  'main() { return 0; }'
assert 42 'main() { return 42; }'
assert 21 'main() { return 5+20-4; }'
assert 41 'main() { return 12 +  34 - 5 ; }'
assert 7  'main() { return 3 * 12 -  34 + 5 ; }'
assert 4  'main() { return 6 * (3 + 9) -  12 * 10 / 15 - 5 * (2 + 10); }'
assert 7  'main() { return -5 * (-2) + 10 / (-2) - (-2); }'

echo OK
