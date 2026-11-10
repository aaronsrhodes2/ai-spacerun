# Skill: name everything you build (SOP)

Full rules: docs/naming-sop.md. A build step is not done until its names are set.
1. Train stops: `<Cargo> <Site> Load|Unload|Yard`. Site is `Depot` for the first patch, then A, B, C. Both ends of a route share the prefix.
2. Trains: `train.group` = the route prefix (`Copper A`). Set the group after the schedule.
3. Chest requests: every manual section goes into a group `<Role>: <What>` (Feed, Belt Feed, Rocket Parts, Rocket Cargo, Train Fuel, Buffer, Relay). Never leave a loose request.
4. Robot network: `custom_name` = `<Planet> <Site>`. Platforms: named for the job or the route, never an icon alone.
5. Map tag at every stop with the stop's name.
Verify: no stop with a generated person name, no train with an empty group, no manual requester section with an empty group.
Renaming a stop by script does not update schedules: rewrite the schedule records in the same call.
