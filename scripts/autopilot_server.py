#!/usr/bin/env python3
"""
Factorio autopilot, runs ON the game VM (so it keeps working when the Captain's PC is off or asleep).
Every CYCLE seconds, over local RCON: top up the research queue (priority: the next-planet techs, then cheapest techs whose packs the factory
really makes), and append a one-line status snapshot to the log (pack rates, labs, research, train fuel).
Queueing only; it never writes research state or places anything. Usage: autopilot_server.py HOST PORT PASSWORD_FILE LOGFILE
"""
import socket
import struct
import sys
import time

import os
CYCLE = int(os.environ.get("AUTOPILOT_CYCLE", "180"))
PRIORITY = ["space-platform-thruster", "planet-discovery-vulcanus", "planet-discovery-fulgora", "planet-discovery-gleba",
            "logistic-system", "landing-pad-unloading-bay"]


class Rcon:
    def __init__(self, host, port, password):
        self.s = socket.create_connection((host, port), timeout=20)
        self.n = 0
        self._send(3, password)
        self._recv()

    def _send(self, kind, body):
        self.n += 1
        data = struct.pack("<ii", self.n, kind) + body.encode() + b"\x00\x00"
        self.s.sendall(struct.pack("<i", len(data)) + data)

    def _recv(self):
        raw = b""
        while len(raw) < 4:
            raw += self.s.recv(4 - len(raw))
        size = struct.unpack("<i", raw)[0]
        data = b""
        while len(data) < size:
            data += self.s.recv(size - len(data))
        return data[8:-2].decode(errors="replace")

    def run(self, lua):
        self._send(2, "/sc " + lua)
        return self._recv()


TOPUP = (
    "local f=game.forces.player local s=game.surfaces.nauvis local seven={['automation-science-pack']=1,['logistic-science-pack']=1,['military-science-pack']=1,"
    "['chemical-science-pack']=1,['production-science-pack']=1,['utility-science-pack']=1,['space-science-pack']=1} "
    "local stock={} for _,l in pairs(s.find_entities_filtered{type='lab'}) do local inv=l.get_inventory(defines.inventory.lab_input) for p,_ in pairs(seven) do stock[p]=(stock[p] or 0)+inv.get_item_count(p) end end "
    "local pri={%s} local rows={} for name,t in pairs(f.technologies) do if t.enabled and not t.researched and t.research_unit_count>0 and t.prototype.max_level<1000000 then "
    "local ready=true for _,p in pairs(t.prerequisites) do if not p.researched then ready=false end end local ok=true local pen=0 "
    "for _,i in pairs(t.research_unit_ingredients) do if not seven[i.name] then ok=false end if (stock[i.name] or 0)<30 then pen=pen+1000000 end end "
    "if ready and ok then local score=t.research_unit_count+pen for k,n in pairs(pri) do if n==name then score=k-1000000 end end rows[#rows+1]={name=name,score=score} end end end "
    "table.sort(rows,function(a,b) return a.score<b.score end) local q={} for _,r in pairs(rows) do q[#q+1]=r.name end "
    "pcall(function() f.research_queue=q end) local o={} for i,r in pairs(f.research_queue) do o[#o+1]=r.name end rcon.print(table.concat(o,','))"
) % ",".join(f"'{p}'" for p in PRIORITY)

SNAP = (
    "local s=game.surfaces.nauvis local f=game.forces.player local ps=f.get_item_production_statistics(s) local function r(n,c) return ps.get_flow_count{name=n,category=c,precision_index=defines.flow_precision_index.one_minute}/60 end "
    "local labs=0 local work=0 for _,l in pairs(s.find_entities_filtered{type='lab'}) do labs=labs+1 if l.status==defines.entity_status.working then work=work+1 end end "
    "local fuel={} for _,t in pairs(game.train_manager.get_trains{surface=s}) do local mn=1e9 for _,l in pairs(t.locomotives.front_movers) do local e=l.burner and l.burner.remaining_burning_fuel or 0 local fi=l.get_fuel_inventory() local c=0 if fi then for _,q in pairs(fi.get_contents()) do c=c+q.count end end mn=math.min(mn,c) end for _,l in pairs(t.locomotives.back_movers) do local fi=l.get_fuel_inventory() local c=0 if fi then for _,q in pairs(fi.get_contents()) do c=c+q.count end end mn=math.min(mn,c) end fuel[#fuel+1]=t.id..':'..mn end "
    "local p=game.surfaces['platform-1'] local hub=p and p.platform and p.platform.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-science-pack') or -1 "
    "rcon.print(string.format('labs %d/%d research %s %.2f | made/s auto %.2f log %.2f mil %.2f chem %.2f prod %.2f util %.2f | used/s chem %.2f space %.2f | cu %.1f/%.1f fe %.1f/%.1f | hub-space %d | train min fuel %s',"
    "work,labs,f.current_research and f.current_research.name or 'none',f.research_progress,r('automation-science-pack','input'),r('logistic-science-pack','input'),r('military-science-pack','input'),r('chemical-science-pack','input'),r('production-science-pack','input'),r('utility-science-pack','input'),"
    "r('chemical-science-pack','output'),r('space-science-pack','output'),r('copper-plate','input'),r('copper-plate','output'),r('iron-plate','input'),r('iron-plate','output'),hub,table.concat(fuel,' ')))"
)


REPAIR = (
    "local p=game.surfaces['platform-1'] if not p then return end local SN=defines.entity_status local short=0 local n=0 "
    "for _,e in pairs(p.find_entities_filtered{force='player',type='assembling-machine'}) do local r=e.get_recipe() if r and r.name=='space-science-pack' then n=n+1 if e.status==SN.item_ingredient_shortage then short=short+1 end end end "
    "if n>0 and short==n then local removed=0 for _,e in pairs(p.find_entities_filtered{type={'transport-belt','underground-belt','splitter'},area={{-12,-5},{-6,-2}}}) do if math.floor(e.position.x)~=-13 then "
    "for i=1,e.get_max_transport_line_index() do local l=e.get_transport_line(i) for _,c in pairs(l.get_contents()) do if c.name:find('asteroid%-chunk') then removed=removed+l.remove_item{name=c.name,count=c.count} end end end end end "
    "rcon.print('platform ice jam: removed '..removed..' chunks') else rcon.print('platform ok') end"
)


SILO_GUARD = (
    "local OUTPOSTS={{{296,71},{341,252}},{{664,300},{731,519}},{{709,-83},{763,122}}} local s=game.surfaces.nauvis local f=game.forces.player local a,c=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator',force=f}) do a=a+e.energy c=c+e.electric_buffer_size end "
    "local frac=c>0 and a/c or 1 local act=nil local n=0 for _,e in pairs(s.find_entities_filtered{name='rocket-silo',force=f}) do if math.abs(e.position.y+195.5)<1 then n=n+1 "
    "if frac<0.3 then e.disabled_by_script=true elseif frac>0.6 then e.disabled_by_script=false end act=not e.disabled_by_script end end "
    "for _,b in pairs(OUTPOSTS) do for _,e in pairs(s.find_entities_filtered{area=b,force=f,type={'furnace','mining-drill'}}) do if frac<0.2 then e.disabled_by_script=true elseif frac>0.5 then e.disabled_by_script=false end end end "
    "rcon.print(string.format('accumulators %.0f%% new silos %d %s',frac*100,n,act==nil and '-' or (act and 'on' or 'PAUSED')))"
)


def log(msg, LOG=None):
    LOG = LOG or sys.argv[4]
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def main():
    HOST, PORT, PWFILE = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    password = open(PWFILE).read().strip()
    log("autopilot started")
    while True:
        try:
            c = Rcon(HOST, PORT, password)
            c.run("rcon.print('x')")
            queue = c.run(TOPUP)
            snap = c.run(SNAP)
            fix = c.run(REPAIR)
            log(snap + " | queue " + queue + " | " + fix + " | " + c.run(SILO_GUARD))
        except Exception as exc:  # noqa: BLE001 - keep going whatever happens
            log("error: " + repr(exc))
        time.sleep(CYCLE)


if __name__ == "__main__":
    main()
