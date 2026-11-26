#!/usr/bin/env bash
# Fetch rendered 3D chunks from out-<tag>-<i> branches, add bloom, join with the desktop sequence.
# usage: assemble.sh <tag> <desk.mp4> <out.mp4>
set -euo pipefail
TAG=$1; DESK=$2; OUT=$3
REPO=/home/claude/workspace; W=$(mktemp -d)
cd "$REPO"
for i in $(seq 0 19); do
  git fetch -q --depth 1 origin "+refs/heads/out-$TAG-$i:refs/remotes/origin/out-$TAG-$i"
  git show "origin/out-$TAG-$i:out/chunk.mp4" > "$W/c$(printf %02d $i).mp4"
done
: > "$W/a.txt"; : > "$W/b.txt"
for i in $(seq 0 6);  do echo "file 'c$(printf %02d $i).mp4'" >> "$W/a.txt"; done
for i in $(seq 7 19); do echo "file 'c$(printf %02d $i).mp4'" >> "$W/b.txt"; done
cd "$W"
ffmpeg -loglevel error -y -f concat -safe 0 -i a.txt -c copy A.mp4
ffmpeg -loglevel error -y -f concat -safe 0 -i b.txt -c copy B.mp4
glow(){ echo "[$1:v]format=gbrp,split[$2b][$2h];[$2h]curves=all='0/0 0.5/0 1/1',gblur=sigma=22[$2g];[$2b][$2g]blend=all_mode=screen:all_opacity=0.32,format=yuv420p[$2]"; }
ffmpeg -loglevel error -y -i A.mp4 -i "$DESK" -i B.mp4 -filter_complex \
 "$(glow 0 a);$(glow 2 b);[1:v]format=yuv420p[d];[a][d][b]concat=n=3:v=1:a=0[v]" \
 -map "[v]" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -r 30 -movflags +faststart "${OUT%.mp4}.tmp.mp4"
mv "${OUT%.mp4}.tmp.mp4" "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
