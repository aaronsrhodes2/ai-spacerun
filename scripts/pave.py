"""
Pave the busy part of the base with refined concrete so walking isn't on dirt.

A chunk (32x32) is paved when it holds at least --min player entities, or when it is a one-chunk gap between paved chunks (left/right or up/down).
Within a paved chunk every walkable land tile is replaced except: tiles already concrete, refined concrete or stone path, water, and tiles
with an ore/resource entity on them (drills keep working, and the patch stays visible). Tiles are placed free, like entities.

Usage: scripts/pave.py [--min 25] [--box X1 Y1 X2 Y2] [--tile refined-concrete] [--apply]
"""
import argparse
import json

import fx

CHUNKS = ("local s=game.surfaces.nauvis local f=game.forces.player local want={} local N=%d for ch in s.get_chunks() do local n=s.count_entities_filtered{area=ch.area,force=f} "
          "if n>=N then want[ch.x..','..ch.y]={ch.x,ch.y} end end local fill={} for k,c in pairs(want) do local x,y=c[1],c[2] "
          "if (want[(x-1)..','..y] and want[(x+1)..','..y]) or (want[x..','..(y-1)] and want[x..','..(y+1)]) then end end "
          "for ch in s.get_chunks() do local x,y=ch.x,ch.y local k=x..','..y if not want[k] then if (want[(x-1)..','..y] and want[(x+1)..','..y]) or (want[x..','..(y-1)] and want[x..','..(y+1)]) then fill[k]={x,y} end end end "
          "for k,c in pairs(fill) do want[k]=c end local out={} for _,c in pairs(want) do out[#out+1]=c end table.sort(out,function(a,b) if a[1]~=b[1] then return a[1]<b[1] end return a[2]<b[2] end) rcon.print(helpers.table_to_json(out))")

PAVE = ("local s=game.surfaces.nauvis local tile='%s' local apply=%s local done,skipped=0,0 for _,c in pairs({%s}) do local x0,y0=c[1]*32,c[2]*32 "
        "local res={} for _,r in pairs(s.find_entities_filtered{area={{x0,y0},{x0+32,y0+32}},type='resource'}) do res[math.floor(r.position.x)..','..math.floor(r.position.y)]=true end "
        "local list={} for tx=x0,x0+31 do for ty=y0,y0+31 do local t=s.get_tile(tx,ty) local n=t.name "
        "if t.collides_with('player') or n:find('water') or n:find('concrete') or n:find('stone%%-path') or res[tx..','..ty] then skipped=skipped+1 else list[#list+1]={name=tile,position={tx,ty}} end end end "
        "if apply and #list>0 then s.set_tiles(list,true) end done=done+#list end rcon.print(done..' '..skipped)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=25)
    ap.add_argument("--tile", default="refined-concrete")
    ap.add_argument("--box", nargs=4, type=int, help="pave exactly the chunks that touch this tile box x1 y1 x2 y2 (instead of the busy-chunk rule)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.box:
        chunks = [[cx, cy] for cx in range(a.box[0] // 32, a.box[2] // 32 + 1) for cy in range(a.box[1] // 32, a.box[3] // 32 + 1)]
    else:
        chunks = fx.jlua(CHUNKS % a.min)
    print(f"{len(chunks)} chunks to pave (about {len(chunks) * 1024} tiles before skips)")
    total = skipped = 0
    for i in range(0, len(chunks), 4):
        part = ",".join("{%d,%d}" % (c[0], c[1]) for c in chunks[i:i + 4])
        done, skip = fx.lua(PAVE % (a.tile, "true" if a.apply else "false", part)).split()
        total += int(done)
        skipped += int(skip)
    print(("PAVED" if a.apply else "DRY RUN (add --apply)"), f"{total} tiles, {skipped} skipped (water, already paved, ore)")


if __name__ == "__main__":
    main()
