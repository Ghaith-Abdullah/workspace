#!/usr/bin/env bash
# Join: 3D opening (A) + desktop recording + 3D end plate (B) held under the title layer.
# usage: assemble.sh <tag> <desk.mp4> <titles_dir> <out.mp4>
set -euo pipefail
TAG=$1; DESK=$2; TITLES=$3; OUT=$4
REPO=/home/claude/workspace; W=$(mktemp -d)
cd "$REPO"
for i in $(seq 0 19); do
  git fetch -q --depth 1 origin "+refs/heads/out-$TAG-$i:refs/remotes/origin/out-$TAG-$i"
  git show "origin/out-$TAG-$i:out/chunk.mp4" > "$W/c$(printf %02d $i).mp4"
done
: > "$W/a.txt"; : > "$W/b.txt"
for i in $(seq 0 12);  do echo "file 'c$(printf %02d $i).mp4'" >> "$W/a.txt"; done
for i in $(seq 13 19); do echo "file 'c$(printf %02d $i).mp4'" >> "$W/b.txt"; done
cd "$W"
ffmpeg -loglevel error -y -f concat -safe 0 -i a.txt -c copy A.mp4
ffmpeg -loglevel error -y -f concat -safe 0 -i b.txt -c copy B.mp4
glow(){ echo "format=gbrp,split[$1b][$1h];[$1h]curves=all='0/0 0.5/0 1/1',gblur=sigma=22[$1g];[$1b][$1g]blend=all_mode=screen:all_opacity=0.32"; }
ffmpeg -loglevel error -y -i A.mp4 -i "$DESK" -i B.mp4 -framerate 30 -i "$TITLES/t_%04d.png" -filter_complex \
 "[0:v]$(glow a),format=yuv420p[a];[2:v]$(glow p),tpad=stop_mode=clone:stop_duration=10,trim=end_frame=405,setpts=PTS-STARTPTS,format=rgba[pl];[3:v]format=rgba[tt];[pl][tt]overlay=0:0:format=auto,noise=alls=5:allf=t,format=yuv420p[b];[1:v]format=yuv420p[d];[a][d][b]concat=n=3:v=1:a=0[v]" \
 -map "[v]" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -r 30 -movflags +faststart "${OUT%.mp4}.tmp.mp4"
mv "${OUT%.mp4}.tmp.mp4" "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
