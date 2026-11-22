-- WindowMenu.lua: the menu of the Naowh guide window: RestedXP's menu with the switches of its V2 settings menu in it.
local ns = _G.NaowhForever
local Safe = ns.RXPSafe
local Has, Dig, Run = Safe.Has, Safe.Dig, Safe.Run

local NAME = "WindowSettingsMenu"
local TEXT_STEPS, TEXT_COMPLETED, TEXT_UNUSED = "Show step list", "Hide completed steps", "Show unused guides"

local function Said(rxp, text)
    local get = Dig(rxp, "locale", "Get")
    return type(get) == "function" and get(text) or text
end

local function Closed(this)
    if Has(this, "Hide") then this:Hide() end
end

local function Switches(rxp, settings, stepsShown, toggleSteps)
    return {
        {
            text = Said(rxp, TEXT_STEPS),
            checked = stepsShown,
            func = function(this)
                toggleSteps()
                Closed(this)
            end,
        },
        {
            text = Said(rxp, TEXT_COMPLETED),
            checked = function() return settings.profile.hideCompletedSteps and true or false end,
            func = function(this)
                Run(NAME, settings.SetHideCompletedSteps, settings, not settings.profile.hideCompletedSteps)
                Closed(this)
            end,
        },
        {
            text = Said(rxp, TEXT_UNUSED),
            checked = function() return settings.profile.showUnusedGuides and true or false end,
            func = function(this)
                settings.profile.showUnusedGuides = not settings.profile.showUnusedGuides
                Closed(this)
            end,
        },
        { text = "", notCheckable = 1, isTitle = 1 },
    }
end

-- the switches go after the list of guides, which RestedXP's menu ends with a rule: the place of that rule, or none
local function Rule(list)
    for i, item in ipairs(list) do
        if item.isTitle and item.text == "" then return i end
    end
    return 0
end

-- true once the menu is up; false when RestedXP has not the pieces of it, and its older menu is the caller's
function ns.RXPWindowMenu(stepsShown, toggleSteps)
    local rxp = _G.RXP
    local settings, frame = Dig(rxp, "settings"), Dig(rxp, "RXPFrame")
    if not (Has(rxp, "ShowMenu") and Has(frame, "GenerateMenuTable") and Has(settings, "SetHideCompletedSteps")
            and type(settings.profile) == "table") then
        return false
    end
    local list = Run(NAME, frame.GenerateMenuTable, frame, {})
    if type(list) ~= "table" then return false end
    local menu, rule = {}, Rule(list)
    for i = 1, rule do menu[#menu + 1] = list[i] end
    for _, item in ipairs(Switches(rxp, settings, stepsShown, toggleSteps)) do menu[#menu + 1] = item end
    for i = rule + 1, #list do menu[#menu + 1] = list[i] end
    Run(NAME, rxp.ShowMenu, rxp, menu)
    return true
end
