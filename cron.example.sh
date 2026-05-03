#!/bin/sh
set -eux

base_url="https://github.com/newcoderlife/chnroutes/releases/latest/download"
tmp="$(mktemp -d)"

trap 'rm -rf "$tmp"' EXIT

curl -fsSL "$base_url/noncn4.routes" -o "$tmp/noncn4.routes"
curl -fsSL "$base_url/noncn6.routes" -o "$tmp/noncn6.routes"
curl -fsSL "$base_url/noncn.sha256" -o "$tmp/noncn.sha256"

(cd "$tmp" && sha256sum -c noncn.sha256)

install -m 0644 -o bird -g bird "$tmp/noncn4.routes" /etc/bird/noncn4.routes
install -m 0644 -o bird -g bird "$tmp/noncn6.routes" /etc/bird/noncn6.routes

bird -p -c /etc/bird/bird.conf
birdc configure
