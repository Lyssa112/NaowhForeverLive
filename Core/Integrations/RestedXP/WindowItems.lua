-- WindowItems.lua: RestedXP's Active Items window: what a step has is listed at its first show, and its buttons drag onto a bar.
local ns = _G.NaowhForever
local Safe = ns.RXPSafe
local Has, Dig, Run = Safe.Has, Safe.Dig, Safe.Run

local NAME = "WindowItems"
local DRAG_BUTTON = "LeftButton"
local MACRO_NAME, MACRO_BODY_MAX, MACRO_ACCOUNT_MAX, MACRO_CHARACTER_MAX = "RXP Active Item", 255, 120, 18
local MACRO_ICON = 134400
local TEXT_LONG = ns.L("This macro is too long to be dragged onto a bar.")
local TEXT_FULL = ns.L("Your character's macros are full, so this macro cannot be dragged onto a bar. Delete one first.")

local LISTS = { "activeMacros", "activeSpells", "activeItems" }

local wired = setmetatable({}, { __mode = "k" })
local hooked, synced

local function Game(table, name)
    local source = table and _G[table]
    local fn = type(source) == "table" and source[name] or _G[name]
    return type(fn) == "function" and fn or nil
end

local function Pickup(table, name, ...)
    local fn = Game(table, name)
    if fn then Run(NAME, fn, ...) end
end

local function CharacterMacro()
    local account = _G.MAX_ACCOUNT_MACROS or MACRO_ACCOUNT_MAX
    local _, made = _G.GetNumMacros()
    made = made or 0
    for index = account + 1, account + made do
        if _G.GetMacroInfo(index) == MACRO_NAME then return index, made end
    end
    return nil, made
end

local function PickMacro(button)
    local body = Has(button, "GetAttribute") and button:GetAttribute("macrotext")
    if type(body) ~= "string" or body == "" then return end
    if #body > MACRO_BODY_MAX then return ns.Print(TEXT_LONG) end
    local icon = Has(button.icon, "GetTexture") and button.icon:GetTexture() or MACRO_ICON
    local index, made = CharacterMacro()
    if index then
        Run(NAME, _G.EditMacro, index, MACRO_NAME, icon, body)
    else
        if made >= (_G.MAX_CHARACTER_MACROS or MACRO_CHARACTER_MAX) then return ns.Print(TEXT_FULL) end
        index = Run(NAME, _G.CreateMacro, MACRO_NAME, icon, body, true)
    end
    if index then Run(NAME, _G.PickupMacro, index) end
end

local function Pick(button)
    if not ns.RXPWindowActive() or not IsShiftKeyDown() or InCombatLockdown() then return end
    local busy = Game(nil, "GetCursorInfo")
    if busy and busy() then return end
    local id = button.itemId
    if button.macro then
        Run(NAME, PickMacro, button)
    elseif button.spell then
        Pickup("C_Spell", "PickupSpell", id)
    elseif button.toy then
        Pickup("C_ToyBox", "PickupToyBoxItem", id)
    elseif button.bag and button.slot then
        Pickup("C_Container", "PickupContainerItem", button.bag, button.slot)
    elseif button.invSlot then
        Pickup(nil, "PickupInventoryItem", button.invSlot)
    end
end

local function Items()
    local rxp = _G.RXP
    return Dig(rxp, "activeItemWindow") or Dig(rxp, "activeItemFrame")
end

local function Wire(items)
    if not ns.RXPWindowActive() or InCombatLockdown() then return end
    for _, button in ipairs(Dig(items, "buttonList") or {}) do
        if not wired[button] and Has(button, "RegisterForDrag") and Has(button, "HookScript") then
            wired[button] = true
            button:RegisterForDrag(DRAG_BUTTON)
            button:HookScript("OnDragStart", Pick)
        end
    end
end

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
    local rxp = _G.RXP
    if not hooked and Has(rxp, "UpdateItemFrame") then
        hooked = true
        hooksecurefunc(rxp, "UpdateItemFrame", function() Wire(Items()) end)
    end
    local v2 = Dig(rxp, "v2")
    if not synced and Has(v2, "UpdateActiveStepsFrame") then
        synced = true
        hooksecurefunc(v2, "UpdateActiveStepsFrame", Sync)
    end
    Sync()
    Wire(Items())
end
