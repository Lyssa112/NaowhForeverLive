-- WindowItems.lua: RestedXP's Active Items window: what a step has is listed the first time it is shown.
local ns = _G.NaowhForever
local Safe = ns.RXPSafe
local Has, Dig, Run = Safe.Has, Safe.Dig, Safe.Run

local NAME = "WindowItems"
local LISTS = { "activeMacros", "activeSpells", "activeItems" }

local synced

local function Sync()
    if not ns.RXPWindowActive() or InCombatLockdown() then return end
    local rxp = _G.RXP
    local steps = Dig(rxp, "RXPFrame", "activeSteps")
    if type(steps) ~= "table" then return end
    local added
    for _, step in ipairs(steps) do
        if step.active then
            for _, name in ipairs(LISTS) do
                local have, list = step[name], rxp[name]
                if type(have) == "table" and type(list) == "table" then
                    for key, value in pairs(have) do
                        if list[key] == nil then
                            list[key] = value
                            added = true
                        end
                    end
                end
            end
        end
    end
    if added and Has(rxp, "UpdateItemFrame") then Run(NAME, rxp.UpdateItemFrame) end
end

function ns.RXPItemsStart()
    local v2 = Dig(_G.RXP, "v2")
    if not synced and Has(v2, "UpdateActiveStepsFrame") then
        synced = true
        hooksecurefunc(v2, "UpdateActiveStepsFrame", Sync)
    end
    Sync()
end
