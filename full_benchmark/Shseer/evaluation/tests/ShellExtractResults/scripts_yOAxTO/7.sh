#!/bin/bash

generate_cmake_helper() {

if [ $1 ] ; then
    echo $1
    mkdir -p $1
    cd $1
fi

local RESULT_FILE=CMakeLists.txt

cat > $RESULT_FILE <<- "EOM"
cmake_minimum_required(VERSION 3.10.2)

project(a.out)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Remove for compiler-specific features
set(CMAKE_CXX_EXTENSIONS OFF)

string(APPEND CMAKE_CXX_FLAGS " -Wall")
string(APPEND CMAKE_CXX_FLAGS " -Wbuiltin-macro-redefined")
string(APPEND CMAKE_CXX_FLAGS " -pedantic")
string(APPEND CMAKE_CXX_FLAGS " -Werror")

# clangd completion
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories(${CMAKE_SOURCE_DIR})
file(GLOB SOURCES "${CMAKE_SOURCE_DIR}/*.cpp")

add_executable(${PROJECT_NAME} ${SOURCES})

# Uncomment the following if needed
#find_package(Boost 1.69 EXACT REQUIRED COMPONENTS system)
#find_package(OpenSSL REQUIRED)
#find_package(Threads REQUIRED)
#target_link_libraries(${PROJECT_NAME} PUBLIC Boost::system OpenSSL::SSL Threads::Threads)
EOM

RESULT_FILE=main.cpp

cat > $RESULT_FILE <<- "EOM"

int main() {
    return 0;
}
EOM

cp ${HOME}/scripts/utils/.clang-format .
cp ${HOME}/scripts/dotfiles/git/general_gitignore .gitignore

mkdir build && cd build && cmake ..
cd ..

# Symlink to compilation database
ln -s ./build/compile_commands.json compile_commands.json

vim main.cpp
}

alias gencppenv=generate_cmake_helper
