#!/usr/bin/env python3
"""Gleba cell restart by moving what is already there (2026-11-16; nothing is created, items only change hands):
  1 spoilage   egg chambers stop with 24 to 60 spoilage in their output (the output inserter has no room for it): it is taken out and put into the
               nutrients-from-spoilage assemblers, which were short of spoilage. What does not fit goes into a passive provider chest on the same surface.
  2 eggs       the egg loop needs one egg in every chamber as the catalyst (30 nutrients + 1 egg + 60 water -> 2 eggs). Eggs sitting in pack chambers that
               cannot run (no fuel) go to the egg chambers that hold 30 or more nutrients and no egg.
  4 seeds      a fruit processor halts when its seed output chests are full (1,200 seeds each on 2026-11-16: no mash, no bioflux, the whole cell starved).
               Provider chests holding 1,000+ seeds are cut back to 600 while the network holds over 1,200 of that seed (surplus voided; the vault and the
               Captain's 210 floor are untouched: steel chests are not looked at).
  3 fuel       biochambers with an empty fuel slot and status no_fuel get 10 nutrients each from provider chests that hold them (nutrients rot in 5 minutes
               anyway). Only no_fuel chambers are touched.
Usage: gleba_restart.py [--apply]     (default: report what it would move)"""
import re
import sys

from _game import tools

APPLY = "true" if "--apply" in sys.argv else "false"

CODE = """
local s=game.surfaces.gleba local f=game.forces.player local apply=APPLY local o={}
local E=defines.entity_status
local function invs(m,k) return m.get_inventory(k) end
-- 1 spoilage out of egg chambers into the spoilage converters
local conv={} for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r and r.name=='nutrients-from-spoilage' then conv[#conv+1]=m end end
local moved,left=0,0
for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r and r.name=='pentapod-egg' then local out=m.get_inventory(defines.inventory.crafter_output) local n=out.get_item_count('spoilage') if n>0 then
  local rest=n for _,c in pairs(conv) do if rest>0 then local inp=c.get_inventory(defines.inventory.crafter_input) local room=math.max(0,400-inp.get_item_count('spoilage')) local put=math.min(rest,room) if put>0 then if apply then put=inp.insert{name='spoilage',count=put} end rest=rest-put end end end
  local took=n-rest if apply and took>0 then out.remove{name='spoilage',count=took} end moved=moved+took left=left+rest end end end
o[#o+1]='spoilage moved to converters '..moved..' (left in egg outputs '..left..')'
-- 2 eggs from stuck pack chambers to egg chambers with nutrients and no egg
local donors={} for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r and r.name=='agricultural-science-pack' and m.status==E.no_fuel then local inp=m.get_inventory(defines.inventory.crafter_input) local e=inp.get_item_count('pentapod-egg') if e>0 then donors[#donors+1]={m,e} end end end
local pool=0 for _,d in pairs(donors) do pool=pool+d[2] end local given=0
for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r and r.name=='pentapod-egg' then local inp=m.get_inventory(defines.inventory.crafter_input) if inp.get_item_count('pentapod-egg')==0 and inp.get_item_count('nutrients')>=30 and given<pool then
  if apply then for _,d in pairs(donors) do if d[2]>0 then d[1].get_inventory(defines.inventory.crafter_input).remove{name='pentapod-egg',count=1} d[2]=d[2]-1 inp.insert{name='pentapod-egg',count=1} break end end end given=given+1 end end end
o[#o+1]='eggs available in stuck pack chambers '..pool..', given to egg chambers '..given
-- 3 fuel
local srcs={} for _,e in pairs(s.find_entities_filtered{type='logistic-container',name='passive-provider-chest',force=f}) do local inv=e.get_inventory(defines.inventory.chest) if inv.get_item_count('nutrients')>=10 then srcs[#srcs+1]=inv end end
local fueled,short=0,0
for _,m in pairs(s.find_entities_filtered{name='biochamber',force=f}) do if m.status==E.no_fuel then local fi=m.get_fuel_inventory() if fi and fi.get_item_count()==0 then local ok=false for _,inv in pairs(srcs) do if inv.get_item_count('nutrients')>=10 then if apply then inv.remove{name='nutrients',count=10} fi.insert{name='nutrients',count=10} end ok=true break end end if ok then fueled=fueled+1 else short=short+1 end end end end
o[#o+1]='biochambers fuelled '..fueled..' (no nutrients left for '..short..')'
-- 4 seed overflow: a fruit processor stops with seeds in its output when its seed chests are full (found 2026-11-16: 1,200 seeds in each chest, processors full_output, no mash, no bioflux, whole cell starved)
local trimmed=0 local net=s.find_logistic_network_by_position({90,26},f)
for _,sd in pairs{'yumako-seed','jellynut-seed'} do if net and net.get_item_count(sd)>1200 then for _,e in pairs(s.find_entities_filtered{name='passive-provider-chest',force=f}) do local inv=e.get_inventory(defines.inventory.chest) local n=inv.get_item_count(sd) if n>=1000 then local cut=n-600 if apply then cut=inv.remove{name=sd,count=cut} end trimmed=trimmed+cut end end end end
o[#o+1]='seeds trimmed from full output chests '..trimmed
rcon.print((apply and 'APPLIED: ' or 'DRY: ')..table.concat(o,' | '))
"""


def run(apply):
    code = CODE.replace("APPLY", "true" if apply else "false")
    return tools["run_lua"](" ".join(l for l in code.split("\n") if not l.lstrip().startswith("--"))).strip()


def cycle():
    """For the autopilot: apply, and report only when something moved (spoilage, eggs or fuel)."""
    r = run(True)
    return r if re.search(r"converters [1-9]|chambers [1-9]|fuelled [1-9]|trimmed from full output chests [1-9]", r) else ""


def main():
    print(run(APPLY == "true"))


if __name__ == "__main__":
    main()
