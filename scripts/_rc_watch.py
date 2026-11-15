"""Choice stability probe: N back-to-back reads of each machine's chosen item and recipe; counts changes; then made counts."""
import sys

from _game import tools
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
lua = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local o={} for u=0,2 do local sel=s.find_entities_filtered{name='selector-combinator',position={-354+7*u+6.5,-223},radius=0.4}[1] "
       "local am=s.find_entities_filtered{name='assembling-machine-3',position={-354+7*u+2.5,-221.5},radius=0.6}[1] local n=sel.get_circuit_network(W.combinator_output_green) local c='-' "
       "if n and n.signals and n.signals[1] then c=n.signals[1].signal.name end local r=am.get_recipe() o[#o+1]=c..'/'..(r and r.name or 'none')..'/'..am.products_finished end rcon.print(game.tick..' '..table.concat(o,' '))")
rows = [tools["run_lua"](lua).split() for _ in range(N)]
for u in range(3):
    seq = [r[1 + u].split("/") for r in rows]
    ch = sum(1 for a, b in zip(seq, seq[1:]) if a[0] != b[0])
    print("machine %d: choice changes %d in %d reads over %d ticks; items %s; made %s -> %s" % (
        u + 1, ch, N, int(rows[-1][0]) - int(rows[0][0]), sorted({x[0] for x in seq}), seq[0][2], seq[-1][2]))
