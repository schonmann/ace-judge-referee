#!/bin/bash
dir="$(dirname $(dirname $(realpath $0)) )/scripts"
# $1 is the command to be executed in the sandbox environment
# bwrap \
#       --unshare-net \
#       --unshare-user \
#       --ro-bind /lib /lib \
#       --ro-bind /lib64 /lib64 \
#       --ro-bind /usr /usr \
#       --ro-bind $(dirname $1) $(dirname $1) \
$($dir/sleep <<< 1000); "$1"