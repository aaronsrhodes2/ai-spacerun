"""Keep the current queue, then fill it (cap 7) with techs whose packs the factory really makes; techs needing utility (yellow) go last.
Queueing only; never touches research state. Usage: scripts/topup_research.py"""
from _game import tools

LUA = ("local f=game.forces.player local avail={['automation-science-pack']=1,['logistic-science-pack']=1,['military-science-pack']=1,"
       "['chemical-science-pack']=1,['production-science-pack']=1,['utility-science-pack']=1,['space-science-pack']=1} local ok={} local later={} local keep={} local have={} for _,r in pairs(f.research_queue) do keep[#keep+1]=r.name have[r.name]=true end "
       "for name,t in pairs(f.technologies) do if t.enabled and not t.researched then local ready=true "
       "for _,p in pairs(t.prerequisites) do if not p.researched then ready=false end end local good=true local hasUtil=false "
       "for _,i in pairs(t.research_unit_ingredients) do if not avail[i.name] then good=false end if i.name=='utility-science-pack' then hasUtil=true end end "
       "if ready and good and t.research_unit_count>0 then if have[name] then elseif hasUtil then later[#later+1]=name else ok[#ok+1]=name end end end end "
       "table.sort(ok) local q=keep for _,n in pairs(ok) do q[#q+1]=n end for _,n in pairs(later) do q[#q+1]=n end f.research_queue=q "
       "local o={} for i,r in pairs(f.research_queue) do o[#o+1]=r.name end rcon.print(#q..' in list; queued: '..table.concat(o,', '))")

print(tools["run_lua"](LUA))
