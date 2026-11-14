#!/bin/bash
# Does the compositor blend transparent windows? Draws a half-transparent terminal over a red background.
OUT=${OUT:-/tmp/out}; mkdir -p "$OUT"
sleep 1
foot -o colors.alpha=0.5 -o colors.background=0000ff -e sh -c 'sleep 60' & sleep 3
grim "$OUT/alpha-$R.png"
# pixel inside the terminal: red background (ff0000) mixed 50/50 with blue (0000ff) should be purple (~7f007f); black/blue means no blending
px=$(convert "$OUT/alpha-$R.png" -format '%[pixel:p{300,300}]' info:)
echo "$R pixel inside the half-transparent window: $px" >>"$OUT/alpha.txt"
xlinctl exit
