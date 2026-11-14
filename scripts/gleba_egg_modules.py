#!/usr/bin/env python3
"""Gleba: egg chambers hold productivity modules, never speed (2026-11-14).
Why: `module_mall.py install` gives a machine that is working at that moment speed modules. Keeper pair A (117.5/121.5, y 14.5) always
works, so it got four speed module 2 each (crafting speed 12.5 instead of 2.3). At that speed the pair can swallow 50 nutrients a second,
more than the one nutrient lane carries (30 a second), and it stands first on the tail: nothing reached the four production chambers, the
egg gate (nutrients on tail tiles x 100..105 > 10) never opened, and every egg was made at the worse rate (productivity 0.5 instead of
0.96: 15 nutrients an egg instead of 10). Chamber 101.5 had speed modules too.
What it does: in every pentapod-egg biochamber on Gleba, each speed module goes back to the Nauvis network and one productivity module 2
is taken from the Nauvis network in its place, at the quality of the module it replaces. Nothing is created. Safe to run again.
Usage: gleba_egg_modules.py [--apply]"""
import sys

from _game import tools

LUA = ("local s=game.surfaces.gleba local net=game.surfaces.nauvis.find_logistic_network_by_position({-27.5,-393.5},'player') "
       "local want,put,back,o=0,0,0,{} for _,e in pairs(s.find_entities_filtered{name='biochamber',area={{60,12},{125,17}}}) do local r=e.get_recipe() "
       "if r and r.name=='pentapod-egg' then local mi=e.get_module_inventory() for i=1,#mi do local st=mi[i] if st.valid_for_read and st.name:find('^speed') then want=want+1 "
       "if APPLY and net.get_item_count('productivity-module-2')>0 and net.remove_item{name='productivity-module-2',count=1}==1 then local q=st.quality.name "
       "back=back+net.insert{name=st.name,count=1,quality='normal'} st.set_stack{name='productivity-module-2',count=1,quality=q} put=put+1 end end end "
       "o[#o+1]=e.position.x..': speed '..string.format('%.2f',e.crafting_speed)..' productivity '..string.format('%.2f',e.productivity_bonus) end end "
       "rcon.print('speed modules in egg chambers '..want..', replaced '..put..', handed back to Nauvis '..back..', productivity module 2 left on Nauvis '..net.get_item_count('productivity-module-2')..' | '..table.concat(o,' ; '))")
print(tools["run_lua"](LUA.replace("APPLY", "true" if "--apply" in sys.argv else "false")))
