ghc -prof -fprof-auto -rtsopts fibo.hs
./fibo +RTS -p

ghc -prof -fprof-auto -rtsopts mean.hs
./mean +RTS -p
