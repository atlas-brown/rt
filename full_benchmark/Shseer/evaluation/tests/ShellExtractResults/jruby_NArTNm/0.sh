#!/bin/bash
# Simple Builder v0.0.1
# by wizardbeard <ramonjlongiii@gmail.com>

# Banner:
echo "=====[ Simple Builder ]====="

echo "-----> Running bundler..."
bundle
echo "       'bundle' complete!"

# Perform a git add and commit:
echo "-----> Adding changes to repo..."
git add --all
echo "       'git add -all' complete!"

echo "-----> Commiting changes to repo..."
git commit -m "Commit before build."
echo "       'git commit' complete!"

# Precompile assets:
echo "-----> Precompiling assets..."
rake assets:precompile
echo "       'rake assets:precomile' complete!"

# Run our test suite:
# echo "-----> Running test suite..."
# echo "       Test suite complete!"

# Run warble:
echo "-----> Building WAR with Warble..."
warble executable war
echo "       'warble executable war' complete!"

# Git push (modifiy or comment out as necessary):
echo "-----> Pushing to origin on master branch:"
git push origin master
echo "       'git push origin master' complete!"

# Deploy to Heroku:
# echo "-----> Deploying to Heroku:"
# git push heroku
# echo "       'git push heroku' complete!"
