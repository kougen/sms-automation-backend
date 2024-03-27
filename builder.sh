#!/bin/bash

target=$1
push_target=$2

if [ -z "$target" ]; then
  echo "Usage: $0 <target>"
  exit 1
fi

if [ ! -d scripts/$target ]; then
  echo "The target directory does not exist"
  exit 1
fi

if [ -d build ]; then
  rm -rf build
fi

mkdir build

cd build

pc_dir=../scripts
cp -r $pc_dir/$target/*.py ./
cp -r $pc_dir/$target/Dockerfile ./
cp -r $pc_dir/requirements.txt ./
cp -r $pc_dir/dblib/dblib.py ./

command="--load"

if [ -n "$push_target" ]; then
  command="--push"
fi

docker buildx build --platform linux/amd64,linux/arm64 -t $push_target $command .

