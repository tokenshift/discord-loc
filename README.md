# LocBot

A Discord bot for tracking combatant locations in theatre-of-the-mind style RPGs.

Loc tracks "entities" (players, NPCs, monsters and the like) and "locations"
(places where entities might end up in a fight) to help keep track of where
everyone is in a fight without using an actual VTT.

Location tracking is channel-specific, so that you can have different encounters
going on in different channels at the same time.

Use `loc help` to display all commands.

Visit [authorization URL](https://discord.com/api/oauth2/authorize?client_id=803709516121505823&permissions=75776&scope=bot) to invite LocBot to
your server.

## Examples

Input: `loc move "Player 1" "Left Tunnel"`

> **Left Tunnel (1)**  
> Player 1 (1)

Input: `loc move "Player 2" "Around the corner"`

> **Left Tunnel (1)**  
> Player 1 (1)
>
> **Around the corner (2)**  
> Player 2 (2)

Input: `loc create "Pit trap"`

> **Left Tunnel (1)**  
> Player 1 (1)
>
> **Around the corner (2)**  
> Player 2 (2)
>
> **Pit trap (3)**  
> *Empty*

*You can refer to entities and locations by either name or ID.*

Input: `loc move "Player 1" 3`

> **Left Tunnel (1)**  
> *Empty*
>
> **Around the corner (2)**  
> Player 2 (2)
>
> **Pit trap (3)**  
> Player 1 (1)

Input: `loc reset`

> Nothing tracked!

## Commands

`loc help`  
Display all available commands.

`loc show`  
Display all entities and locations.

`loc move {entity} {location}`  
Sets an entity's location. `{entity}` and `{location}` can be either names or
numbers assigned by loc.

`loc kill {entity}`  
Removes an entity from location tracking.

`loc rename {entity} {new name}`  
Renames an entity.

`loc create {location}`  
Creates a new location without assigning anyone to it yet.

`loc delete {location}`  
Deletes a location from tracking.

`loc update {location} {new name}`  
Renames a location.

`loc reset`  
Clear out all locations and entities.