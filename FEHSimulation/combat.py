import math
from hero import *


# CONSTANTS
HP = 0
ATK = 1
SPD = 2
DEF = 3
RES = 4

# A set of modifiers that change how combat and attacks work
# One is held by each unit in combat and keeps track of their effects
class HeroModifiers:
    def __init__(self):
        # Exact HP and Special counts at start of combat, before burn damage/healing
        self.start_of_combat_HP: int = -1
        self.start_of_combat_special: int = -1

        # Attack stat preserved before being modified by the weapon triangle
        # Used for calculating special damage
        self.preTriangleAtk: int = 0

        # Attack twice per hit
        self.brave: bool = False

        # Enables defender to attack first
        self.vantage: bool = False
        self.self_desperation: bool = False
        self.other_desperation: bool = False

        # Disable's this unit's skills that change attack ordering (vantage & desperation)
        self.hardy_bearing: bool = False

        # Perform potent follow up
        self.potent_FU = False
        self.potent_new_percentage = -1 # Special-enabled potent percentage increase (Lodestar Rush)

        # Follow-ups
        self.follow_ups_skill = 0 # granted by skills
        self.follow_ups_spd = 0 # granted by speed
        self.follow_up_denials = 0 # granted by skills

        # Null Follow-Up (NFU)
        self.prevent_foe_FU = False # Disables skills that guarantee foe's skill-based follow-ups
        self.prevent_self_FU_denial = False # Disable skills that deny self's skill-based follow-ups

        # If special disabled during combat
        self.special_disabled = False

        # Increased/decreased special charge gain per hit
        self.spGainOnAtk = 0 # when self attacks
        self.spLossOnAtk = 0
        self.spGainWhenAtkd = 0 # when self is attacked
        self.spLossWhenAtkd = 0

        # Pre-hit special jumps
        self.sp_charge_first = 0      # before this unit's first attack
        self.sp_charge_FU = 0         # before this unit's first follow-up

        self.sp_charge_foe_first = 0  # before foe's first attack
        self.sp_charge_foe_first_brave = 0 # before foe's first brave attack
        self.sp_charge_foe_first_FU = 0 # before foe's first follow-up attack

        # Disable increased/decreased special charge gain (Tempo)
        self.disable_foe_fastcharge = False # foe +1 charge per attack
        self.disable_foe_guard = False      # self -1 charge per attack

        # Charge give charge immediately after first defensive special activation (Negating Fang II)
        self.double_def_sp_charge = False

        # Charge give charge immediately after first offensive special activation (Supreme Astra)
        self.triggered_sp_charge = 0

        # If special has been triggered any time before or during this combat
        self.special_triggered = False

        # Non-special percentage-based damage reduction
        self.DR_all_hits_NSP = []              # present on all hits
        self.DR_first_hit_NSP = []             # present on first hit
        self.DR_first_strikes_NSP = []         # present on first hit (first two if foe has Brave enabled)
        self.DR_second_strikes_NSP = []        # present on follow-up and potent hits
        self.DR_consec_strikes_NSP = []        # present on second hit onwards iff consecutive
        self.DR_sp_trigger_next_only_NSP = []  # present only after first special activation

        # Special percentage-based damage reduction
        self.DR_all_hits_SP = []                   # present on all hits
        self.DR_sp_trigger_next_only_SP = []       # present on next hit once per combat
        self.DR_sp_trigger_next_all_SP = []        # present on next hit, can trigger multiple times
        self.DR_sp_trigger_next_all_SP_CACHE = []

        # Armored Beacon/Floe/Blaze, Supreme Heaven, Emblem Ike Ring, etc.
        self.DR_sp_trigger_by_any_special_SP = []  # present after unit or foe's special is ready or triggered

        # DR specific to Great Aether
        self.DR_great_aether_SP = False  # based on special count and if hits are consecutive

        # Damage reduction reduction (partial)
        # Multiplies all damage reduction foe has by this number.
        self.damage_reduction_reduction = 1

        # Damage reduction piercing (full)
        self.sp_pierce_DR = False            # DR pierce on offensive special
        self.pierce_DR_FU = False            # DR pierce on follow-up
        self.always_pierce_DR = False        # DR pierce on any hit
        self.sp_pierce_after_def_sp = False  # DR pierce on next hit after defensive special trigger (laguz friend)
        self.sp_pierce_after_def_sp_CACHE = False

        # True damage
        self.true_all_hits = 0         # damage added to all hits
        self.true_first_hit = 0        # damage added on only first hit
        self.true_finish = 0           # added after special is currently ready or has triggered
        self.true_after_foe_first = 0  # added after foe's first attack
        self.true_sp = 0               # added only on offensive special trigger

        self.true_sp_next = 0          # damage added after each special trigger (divine pulse/negating fang)
        self.true_sp_next_CACHE = 0    #

        # An array to easily store true damage given by a particular stat (ex. (20, RES) means "deals damage = 20% of unit's Res")
        self.true_stat_damages = []

        # Enables extra true damage and DR piercing based on current HP
        self.resonance = False

        # True damage reduction
        self.TDR_all_hits = 0
        self.TDR_first_strikes = 0
        self.TDR_second_strikes = 0
        self.TDR_on_def_sp = 0

        # Niðhöggr
        self.TDR_dmg_taken_cap = 0
        self.TDR_dmg_taken_extra_stacks = 0

        self.reduce_self_sp_damage = 0  # emblem marth

        self.retaliatory_reduced = False  # enables divine recreation
        self.nonstacking_retaliatory_damage = 0  # divine recreation
        self.stacking_retaliatory_damage = 0  # ice mirror
        self.retaliatory_full_damages = []  # full retaliatory damage values for brash assault/counter roar
        self.retaliatory_full_damages_CACHE = []  # temporarily holds full retaliatory
        self.most_recent_atk = 0  # used in calculating this vvvvv
        self.retaliatory_next = 0  # brash assault/counter roar uses most recent hit's damage

        # no chat, I'm not calling it "precombat damage"
        self.self_burn_damage = 0
        self.foe_burn_damage = 0
        self.capped_foe_burn_damage = 0

        # healing
        self.all_hits_heal = 0
        self.follow_up_heal = 0
        self.finish_mid_combat_heal = 0 # heal applied to all hits granted that special is ready or triggered

        # reduces the effect of deep wounds
        self.deep_wounds_allowance = 0
        self.disable_foe_healing = False

        self.surge_heal = 0 # healing when triggering a special

        self.initial_heal = 0 #BoL 4

        # miracle
        self.pseudo_miracle = False
        self.circlet_miracle = False
        self.disable_foe_miracle = False

        # staff
        self.wrathful_staff = False
        self.disable_foe_wrathful = False

        # hexblade
        self.disable_foe_hexblade = False


def move_letters(s, letter):
    if letter not in ['A', 'D']:
        return "Invalid letter"

    first_occurrence = s.find(letter)
    if first_occurrence == -1:
        return s

    remaining_part = s[first_occurrence + 1:]
    moved_letters = s[first_occurrence] * remaining_part.count(letter)
    new_string = s[:first_occurrence + 1] + moved_letters + remaining_part.replace(letter, '')

    return new_string


# Perform a combat between two heroes
def simulate_combat(attacker, defender, is_in_sim, turn, spaces_moved_by_atkr, combat_effects, aoe_triggered, atkHPCur=None, defHPCur=None):
    # Invalid Combat if one unit is dead
    # or if attacker does not have weapon
    if attacker.HPcur <= 0 or defender.HPcur <= 0 or attacker.weapon is None:
        raise Exception("Invalid Combat: One hero is either already dead, or the attacker has no weapon.")

    # who possesses the weapon triangle advantage
    # 0 - attacker
    # 1 - defender
    # -1 - neither
    wpnAdvHero: int = -1

    # lists of attacker/defender's skills & stats
    atkSkills = attacker.getSkills()
    atkStats = attacker.getStats()
    atkPhantomStats = [0] * 5

    defSkills = defender.getSkills()
    defStats = defender.getStats()
    defPhantomStats = [0] * 5

    # stores important modifiers going into combat
    atkr = HeroModifiers()
    defr = HeroModifiers()

    if atkHPCur is None: atkHPCur = attacker.HPcur
    if defHPCur is None: defHPCur = defender.HPcur

    atkr.start_of_combat_HP = atkHPCur
    defr.start_of_combat_HP = defHPCur

    atkSpCountCur = attacker.specialCount
    defSpCountCur = defender.specialCount

    atkr.start_of_combat_special = atkSpCountCur
    defr.start_of_combat_special = defSpCountCur

    atkr.special_triggered = aoe_triggered

    if "phantomSpd" in atkSkills: atkPhantomStats[SPD] += atkSkills["phantomSpd"]
    if "phantomRes" in atkSkills: atkPhantomStats[RES] += atkSkills["phantomRes"]
    if "phantomSpd" in defSkills: defPhantomStats[SPD] += defSkills["phantomSpd"]
    if "phantomRes" in defSkills: defPhantomStats[RES] += defSkills["phantomRes"]

    # stored combat buffs (essentially everything)
    atkCombatBuffs = [0] * 5
    defCombatBuffs = [0] * 5

    # add effects of CombatFields
    if is_in_sim:

        atkr_x = attacker.attacking_tile.x_coord
        atkr_y = attacker.attacking_tile.y_coord
        atkr_coords = (atkr_x, atkr_y)

        defr_x = defender.tile.x_coord
        defr_y = defender.tile.y_coord
        defr_coords = (defr_x, defr_y)

        for e in combat_effects:
            owner_x = e.owner.tile.x_coord
            owner_y = e.owner.tile.y_coord

            if e.owner == attacker:
                owner_x = atkr_x
                owner_y = atkr_y

            owner_coords = (owner_x, owner_y)

            targeted_side = int(e.owner.side == e.affectedSide)


            if targeted_side == attacker.side:
                coords = atkr_coords
                updated_skills = atkSkills
                afflicted = attacker
            if targeted_side == defender.side:
                coords = defr_coords
                updated_skills = defSkills
                afflicted = defender

            condition = e.condition(afflicted)

            in_range = e.range(coords)(owner_coords)

            if in_range and ((e.owner == afflicted) == e.affectSelf) and condition:
                updated_skills = {x: updated_skills.get(x, 0) + e.effect.get(x, 0) for x in set(updated_skills).union(e.effect)}

            if targeted_side == attacker.side:
                atkSkills = updated_skills
            if targeted_side == defender.side:
                defSkills = updated_skills

    def allies_within_n(unit, tile, n):
        unit_list = tile.unitsWithinNSpaces(n)
        returned_list = []

        for x in unit_list:
            if (x != attacker and x != defender) and unit.side == x.side:
                returned_list.append(x)

        return returned_list

    def foes_within_n(unit, tile, n):
        unit_list = tile.unitsWithinNSpaces(n)
        returned_list = []

        for x in unit_list:
            if unit.side != x.side:
                returned_list.append(x)

        return returned_list

    # common position-based conditions
    atkAdjacentToAlly = 0
    atkAllyWithin2Spaces = 0
    atkAllyWithin3Spaces = 0
    atkAllyWithin4Spaces = 0

    defAdjacentToAlly = 0
    defAllyWithin2Spaces = 0
    defAllyWithin3Spaces = 0
    defAllyWithin4Spaces = 0

    atkAllyWithin3RowsCols = []
    defAllyWithin3RowsCols = []

    atkAllAllies = []
    defAllAllies = []

    atkWithin1SpaceOfSupportPartner = False
    atkWithin2SpaceOfSupportPartner = False

    defWithin1SpaceOfSupportPartner = False
    defWithin2SpaceOfSupportPartner = False

    if is_in_sim:
        atkAdjacentToAlly = allies_within_n(attacker, attacker.attacking_tile, 1)
        atkAllyWithin2Spaces = allies_within_n(attacker, attacker.attacking_tile, 2)
        atkAllyWithin3Spaces = allies_within_n(attacker, attacker.attacking_tile, 3)
        atkAllyWithin4Spaces = allies_within_n(attacker, attacker.attacking_tile, 4)

        atkAllAllies = allies_within_n(attacker, attacker.attacking_tile, 25)

        defAdjacentToAlly = allies_within_n(defender, defender.tile, 1)
        defAllyWithin2Spaces = allies_within_n(defender, defender.tile, 2)
        defAllyWithin3Spaces = allies_within_n(defender, defender.tile, 3)
        defAllyWithin4Spaces = allies_within_n(defender, defender.tile, 4)

        defAllAllies = allies_within_n(defender, defender.tile, 25)

        tiles_within_3_col = attacker.attacking_tile.tilesWithinNCols(3)
        tiles_within_3_row = attacker.attacking_tile.tilesWithinNRows(3)
        tiles_within_3_row_or_column = list(set(tiles_within_3_col) | set(tiles_within_3_row))

        for tile in tiles_within_3_row_or_column:
            if tile.hero_on is not None and tile.hero_on.isAllyOf(attacker):
                atkAllyWithin3RowsCols.append(tile.hero_on)

        tiles_within_3_col = defender.tile.tilesWithinNCols(3)
        tiles_within_3_row = defender.tile.tilesWithinNRows(3)
        tiles_within_3_row_or_column = list(set(tiles_within_3_col) | set(tiles_within_3_row))

        for tile in tiles_within_3_row_or_column:
            if tile.hero_on is not None and tile.hero_on.isAllyOf(defender):
                defAllyWithin3RowsCols.append(tile.hero_on)


        # Support partner
        for ally in atkAdjacentToAlly:
            if ally.intName == attacker.allySupport:
                atkWithin1SpaceOfSupportPartner = True

        for ally in atkAllyWithin2Spaces:
            if ally.intName == attacker.allySupport:
                atkWithin2SpaceOfSupportPartner = True

        for ally in defAdjacentToAlly:
            if ally.intName == defender.allySupport:
                defWithin1SpaceOfSupportPartner = True

        for ally in defAllyWithin2Spaces:
            if ally.intName == defender.allySupport:
                defWithin2SpaceOfSupportPartner = True


    atkFoeWithin2Spaces = 0  # Includes opposing unit in combat!
    defFoeWithin2Spaces = 0  # Includes opposing unit in combat!

    if is_in_sim:
        atkFoeWithin2Spaces = foes_within_n(attacker, attacker.attacking_tile, 2)
        defFoeWithin2Spaces = foes_within_n(defender, defender.tile, 2)

    atk_allies_arr = []
    def_allies_arr = []

    atkInfAlliesWithin2Spaces = 0
    atkCavAlliesWithin2Spaces = 0
    atkFlyAlliesWithin2Spaces = 0
    atkArmAlliesWithin2Spaces = 0
    defInfAlliesWithin2Spaces = 0
    defCavAlliesWithin2Spaces = 0
    defFlyAlliesWithin2Spaces = 0
    defArmAlliesWithin2Spaces = 0

    if is_in_sim:
        temp_atk_allies_arr = attacker.attacking_tile.unitsWithinNSpaces(2)

        for x in temp_atk_allies_arr:
            if x is not attacker and x.side == attacker.side:
                atk_allies_arr.append(x)

        temp_def_allies_arr = defender.tile.unitsWithinNSpaces(2)
        for x in temp_def_allies_arr:
            if x is not defender and x.side == defender.side:
                def_allies_arr.append(x)

    for x in atk_allies_arr:
        if x.move == 0: atkInfAlliesWithin2Spaces += 1
        if x.move == 1: atkCavAlliesWithin2Spaces += 1
        if x.move == 2: atkFlyAlliesWithin2Spaces += 1
        if x.move == 3: atkArmAlliesWithin2Spaces += 1

    for x in def_allies_arr:
        if x.move == 0: defInfAlliesWithin2Spaces += 1
        if x.move == 1: defCavAlliesWithin2Spaces += 1
        if x.move == 2: defFlyAlliesWithin2Spaces += 1
        if x.move == 3: defArmAlliesWithin2Spaces += 1

    # common HP-based conditions
    atkHPGreaterEqual25Percent = atkHPCur / atkStats[0] >= 0.25
    atkHPGreaterEqual50Percent = atkHPCur / atkStats[0] >= 0.50
    atkHPGreaterEqual75Percent = atkHPCur / atkStats[0] >= 0.75
    atkHPEqual100Percent = atkHPCur == atkStats[0]

    defHPGreaterEqual25Percent = defHPCur / defStats[0] >= 0.25
    defHPGreaterEqual50Percent = defHPCur / defStats[0] >= 0.50
    defHPGreaterEqual75Percent = defHPCur / defStats[0] >= 0.75
    defHPEqual100Percent = defHPCur == defStats[0]

    # Special Conditions

    # Unit's special is triggered by unit's attack (Offense, AOE)
    atkSpTriggeredByAttack = False
    defSpTriggeredByAttack = False

    # Genesis Falchion
    atkTop3AllyBuffTotal = 0
    defTop3AllyBuffTotal = 0

    # Dark Creator Sword
    atkNumAlliesHPGE90Percent = 0
    defNumAlliesHPGE90Percent = 0

    if is_in_sim:
        atkDefensiveTerrain = attacker.attacking_tile.is_def_terrain
        defDefensiveTerrain = defender.tile.is_def_terrain
    else:
        atkDefensiveTerrain = False
        defDefensiveTerrain = False

    # Panic Status Effect
    AtkPanicFactor = 1
    DefPanicFactor = 1

    # buffs + debuffs calculation
    # throughout combat, PanicFactor * buff produces the current buff value
    if Status.Panic in attacker.statusNeg: AtkPanicFactor *= -1
    if Status.Panic in defender.statusNeg: DefPanicFactor *= -1

    if Status.NullPanic in attacker.statusPos: AtkPanicFactor = 1
    if Status.NullPanic in defender.statusPos: DefPanicFactor = 1

    # apply buffs/debuffs

    atkStats[ATK] += attacker.buffs[ATK] * AtkPanicFactor + attacker.debuffs[ATK]
    atkStats[SPD] += attacker.buffs[SPD] * AtkPanicFactor + attacker.debuffs[SPD]
    atkStats[DEF] += attacker.buffs[DEF] * AtkPanicFactor + attacker.debuffs[DEF]
    atkStats[RES] += attacker.buffs[RES] * AtkPanicFactor + attacker.debuffs[RES]

    defStats[ATK] += defender.buffs[ATK] * DefPanicFactor + defender.debuffs[ATK]
    defStats[SPD] += defender.buffs[SPD] * DefPanicFactor + defender.debuffs[SPD]
    defStats[DEF] += defender.buffs[DEF] * DefPanicFactor + defender.debuffs[DEF]
    defStats[RES] += defender.buffs[RES] * DefPanicFactor + defender.debuffs[RES]

    # [Bonus] and [Penalty] conditions
    atkHasBonus = attacker.hasBonus()
    defHasBonus = defender.hasBonus()
    atkHasPenalty = attacker.hasPenalty()
    defHasPenalty = defender.hasPenalty()

    # triangle adept during combat, default of -1
    triAdept = -1

    # ignore range (distant/close counter)
    ignoreRng = False

    # prevent counterattacks from defender (sweep, flash)
    cannotCounter = False
    disableCannotCounter = False

    # cancel affinity, differs between ally and foe for
    # levels 2/3 because my life can't be easy
    atkCA = 0
    defCA = 0

    # OKAY CHAT TODAY WE ARE GONNA REDO THE SYSTEM THAT CONSIDERS THIS STUFF

    # damage done to self after combat
    atkSelfDmg = 0
    defSelfDmg = 0

    # damage done to other after combat iff self attacks other (should be added to atk/defSelfDmg)
    atkOtherDmg = 0
    defOtherDmg = 0

    # damage done to self iff self attacks other (should be added to atk/defSelfDmg)
    atkRecoilDmg = 0
    defRecoilDmg = 0

    # i dunno how to explain but i need them and to remove them i need to use a bit of brainpower
    NEWatkOtherDmg = 0
    NEWdefOtherDmg = 0

    # healing after combat, negated by deep wounds, cannot be reduced by special fighter 4
    atkPostCombatHealing = 0
    defPostCombatHealing = 0

    # special charge granted after combat (special spiral, dark mystletainn, etc.)
    atkPostCombatSpCharge = 0
    defPostCombatSpCharge = 0

    # status effects given after combat
    # 0 - given regardless
    # 1 - given if attacked by foe
    # 2 - given if attacked foe
    # ex: attacker has panic, defender is hit
    # elements of 2 with be appended to 0
    # at end of combat, all of 0 will be given to defender
    atkPostCombatStatusesApplied = [[], [], []]
    defPostCombatStatusesApplied = [[], [], []]

    # ALL OF THESE!!!!!!!!!!!!!!!!!!

    # NEW SYSTEM VVVVVVV
    # index 0 - given regardless
    # index 1 - given if attacked by foe
    # index 2 - given if attacked foe
    # index 3 - given only if user survives
    # ex: attacker has panic, defender is hit
    # elements of 2 with be appended to 0
    # at end of combat, all effects at index 0 will be given to defender

    # each array within the array holds a set with 3 strings:
    # index 0 - what effect is given out? (buffs/debuffs, damage/healing, end turn, extra action)
    # index 1 - what is the level of this effect? (+7 buff, 10 damage, etc.)
    # index 2 - who is it being given to? (self, allies, foes)
    # index 3 - across what area? (2 spaces of self, 2 spaces of foe, 3 rows or 3 columns, all, etc.)
    atkPostCombatEffs = [[], [], []]
    defPostCombatEffs = [[], [], []]

    atkBonusesNeutralized = [False] * 5
    defBonusesNeutralized = [False] * 5
    atkPenaltiesNeutralized = [False] * 5
    defPenaltiesNeutralized = [False] * 5

    # SOME STATUSES
    if Status.Discord in attacker.statusNeg:
        atkCombatBuffs[1] -= min(2 + atkAllyWithin2Spaces, 5)
        atkCombatBuffs[2] -= min(2 + atkAllyWithin2Spaces, 5)
        atkCombatBuffs[3] -= min(2 + atkAllyWithin2Spaces, 5)
        atkCombatBuffs[4] -= min(2 + atkAllyWithin2Spaces, 5)

    if Status.Discord in defender.statusNeg:
        defCombatBuffs[1] -= min(2 + defAllyWithin2Spaces, 5)
        defCombatBuffs[2] -= min(2 + defAllyWithin2Spaces, 5)
        defCombatBuffs[3] -= min(2 + defAllyWithin2Spaces, 5)
        defCombatBuffs[4] -= min(2 + defAllyWithin2Spaces, 5)

    # ATTACKER SKILLS -----------------------------------------------------------------------------------------------------------------------

    if atkWithin1SpaceOfSupportPartner and not atkWithin2SpaceOfSupportPartner:
        atkCombatBuffs = [x + 2 for x in atkCombatBuffs]

    if atkWithin2SpaceOfSupportPartner:
        atkCombatBuffs = [x + 1 for x in atkCombatBuffs]

    if defWithin1SpaceOfSupportPartner and not defWithin2SpaceOfSupportPartner:
        defCombatBuffs = [x + 2 for x in defCombatBuffs]

    if defWithin2SpaceOfSupportPartner:
        defCombatBuffs = [x + 1 for x in defCombatBuffs]


    if "atkBlow" in atkSkills: atkCombatBuffs[1] += atkSkills["atkBlow"] * 2
    if "spdBlow" in atkSkills: atkCombatBuffs[2] += atkSkills["spdBlow"] * 2
    if "defBlow" in atkSkills: atkCombatBuffs[3] += atkSkills["defBlow"] * 2
    if "resBlow" in atkSkills: atkCombatBuffs[4] += atkSkills["resBlow"] * 2

    # SPUR / DRIVE / GOAD / WARD SKILLS

    if "spurAtk_f" in atkSkills: atkCombatBuffs[ATK] += atkSkills["spurAtk_f"]
    if "spurSpd_f" in atkSkills: atkCombatBuffs[SPD] += atkSkills["spurSpd_f"]
    if "spurDef_f" in atkSkills: atkCombatBuffs[DEF] += atkSkills["spurDef_f"]
    if "spurRes_f" in atkSkills: atkCombatBuffs[RES] += atkSkills["spurRes_f"]

    if "spurAtk_f" in defSkills: defCombatBuffs[ATK] += defSkills["spurAtk_f"]
    if "spurSpd_f" in defSkills: defCombatBuffs[SPD] += defSkills["spurSpd_f"]
    if "spurDef_f" in defSkills: defCombatBuffs[DEF] += defSkills["spurDef_f"]
    if "spurRes_f" in defSkills: defCombatBuffs[RES] += defSkills["spurRes_f"]

    if "driveAtk_f" in atkSkills: atkCombatBuffs[ATK] += atkSkills["driveAtk_f"]
    if "driveSpd_f" in atkSkills: atkCombatBuffs[SPD] += atkSkills["driveSpd_f"]
    if "driveDef_f" in atkSkills: atkCombatBuffs[DEF] += atkSkills["driveDef_f"]
    if "driveRes_f" in atkSkills: atkCombatBuffs[RES] += atkSkills["driveRes_f"]

    if "driveAtk_f" in defSkills: defCombatBuffs[ATK] += defSkills["driveAtk_f"]
    if "driveSpd_f" in defSkills: defCombatBuffs[SPD] += defSkills["driveSpd_f"]
    if "driveDef_f" in defSkills: defCombatBuffs[DEF] += defSkills["driveDef_f"]
    if "driveRes_f" in defSkills: defCombatBuffs[RES] += defSkills["driveRes_f"]

    if "goadCav_f" in atkSkills and attacker.move == 1:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "goadCav_f" in defSkills and defender.move == 1:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "wardCav_f" in atkSkills and attacker.move == 1:
        atkCombatBuffs[DEF] += 4
        atkCombatBuffs[RES] += 4

    if "wardCav_f" in defSkills and attacker.move == 1:
        defCombatBuffs[DEF] += 4
        defCombatBuffs[RES] += 4

    if "goadFly_f" in atkSkills and attacker.move == 2:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "goadFly_f" in defSkills and defender.move == 2:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "wardFly_f" in atkSkills and attacker.move == 2:
        atkCombatBuffs[DEF] += 4
        atkCombatBuffs[RES] += 4

    if "wardFly_f" in defSkills and attacker.move == 2:
        defCombatBuffs[DEF] += 4
        defCombatBuffs[RES] += 4

    if "goadArmor_f" in atkSkills and attacker.move == 3:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "goadArmor_f" in defSkills and defender.move == 3:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "wardArmor_f" in atkSkills and attacker.move == 3:
        atkCombatBuffs[DEF] += 4
        atkCombatBuffs[RES] += 4

    if "wardArmor_f" in defSkills and defender.move == 3:
        defCombatBuffs[DEF] += 4
        defCombatBuffs[RES] += 4

    # LULL SKILLS

    if "lullAtk" in atkSkills:
        defCombatBuffs[ATK] -= atkSkills["lullAtk"]
        defBonusesNeutralized[ATK] = True

    if "lullSpd" in atkSkills:
        defCombatBuffs[SPD] -= atkSkills["lullSpd"]
        defBonusesNeutralized[SPD] = True

    if "lullDef" in atkSkills:
        defCombatBuffs[DEF] -= atkSkills["lullDef"]
        defBonusesNeutralized[DEF] = True

    if "lullRes" in atkSkills:
        defCombatBuffs[RES] -= atkSkills["lullRes"]
        defBonusesNeutralized[RES] = True

    if "lullAtk" in defSkills:
        atkCombatBuffs[ATK] -= defSkills["lullAtk"]
        atkBonusesNeutralized[ATK] = True

    if "lullSpd" in defSkills:
        atkCombatBuffs[SPD] -= defSkills["lullSpd"]
        atkBonusesNeutralized[SPD] = True

    if "lullDef" in defSkills:
        atkCombatBuffs[DEF] -= defSkills["lullDef"]
        atkBonusesNeutralized[DEF] = True

    if "lullRes" in defSkills:
        atkCombatBuffs[RES] -= defSkills["lullRes"]
        atkBonusesNeutralized[RES] = True

    # BOOST SKILLS

    if "fireBoost" in atkSkills and atkHPCur >= defHPCur + 3: atkCombatBuffs[ATK] += atkSkills["fireBoost"] * 2
    if "windBoost" in atkSkills and atkHPCur >= defHPCur + 3: atkCombatBuffs[SPD] += atkSkills["windBoost"] * 2
    if "earthBoost" in atkSkills and atkHPCur >= defHPCur + 3: atkCombatBuffs[DEF] += atkSkills["earthBoost"] * 2
    if "waterBoost" in atkSkills and atkHPCur >= defHPCur + 3: atkCombatBuffs[RES] += atkSkills["waterBoost"] * 2

    if "fireBoost" in defSkills and defHPCur >= atkHPCur + 3: defCombatBuffs[ATK] += defSkills["fireBoost"] * 2
    if "windBoost" in defSkills and defHPCur >= atkHPCur + 3: defCombatBuffs[SPD] += defSkills["windBoost"] * 2
    if "earthBoost" in defSkills and defHPCur >= atkHPCur + 3: defCombatBuffs[DEF] += defSkills["earthBoost"] * 2
    if "waterBoost" in defSkills and defHPCur >= atkHPCur + 3: defCombatBuffs[RES] += defSkills["waterBoost"] * 2

    # BRAZEN SKILLS

    if "brazenAtk" in atkSkills and atkHPCur / atkStats[HP] <= 0.8: atkCombatBuffs[1] += atkSkills["brazenAtk"]
    if "brazenSpd" in atkSkills and atkHPCur / atkStats[HP] <= 0.8: atkCombatBuffs[2] += atkSkills["brazenSpd"]
    if "brazenDef" in atkSkills and atkHPCur / atkStats[HP] <= 0.8: atkCombatBuffs[3] += atkSkills["brazenDef"]
    if "brazenRes" in atkSkills and atkHPCur / atkStats[HP] <= 0.8: atkCombatBuffs[4] += atkSkills["brazenRes"]

    if "brazenAtk" in defSkills and defHPCur / defStats[HP] <= 0.8: defCombatBuffs[1] += defSkills["brazenAtk"]
    if "brazenSpd" in defSkills and defHPCur / defStats[HP] <= 0.8: defCombatBuffs[2] += defSkills["brazenSpd"]
    if "brazenDef" in defSkills and defHPCur / defStats[HP] <= 0.8: defCombatBuffs[3] += defSkills["brazenDef"]
    if "brazenRes" in defSkills and defHPCur / defStats[HP] <= 0.8: defCombatBuffs[4] += defSkills["brazenRes"]

    # BOND SKILLS

    if "atkBond" in atkSkills and atkAdjacentToAlly: atkCombatBuffs[1] += atkSkills["atkBond"]
    if "spdBond" in atkSkills and atkAdjacentToAlly: atkCombatBuffs[2] += atkSkills["spdBond"]
    if "defBond" in atkSkills and atkAdjacentToAlly: atkCombatBuffs[3] += atkSkills["defBond"]
    if "resBond" in atkSkills and atkAdjacentToAlly: atkCombatBuffs[4] += atkSkills["resBond"]

    # REIN SKILLS

    if "atkRein" in atkSkills: defCombatBuffs[ATK] -= atkSkills["atkRein"]
    if "spdRein" in atkSkills: defCombatBuffs[SPD] -= atkSkills["atkRein"]
    if "defRein" in atkSkills: defCombatBuffs[DEF] -= atkSkills["atkRein"]
    if "resRein" in atkSkills: defCombatBuffs[RES] -= atkSkills["atkRein"]

    # CRUX SKILLS

    if "spdRC_f" in atkSkills: atkCombatBuffs[SPD] -= 4
    if "defRC_f" in atkSkills: atkCombatBuffs[DEF] -= 4

    if "spdRC_f" in defSkills: defCombatBuffs[SPD] -= 4
    if "defRC_f" in defSkills: defCombatBuffs[DEF] -= 4

    if "cruxField_f" in atkSkills:
        defr.follow_ups_skill += 1

    if "cruxField_f" in defSkills:
        atkr.follow_ups_skill += 1

    # CLASH SKILLS

    if "atkClash" in atkSkills and spaces_moved_by_atkr > 0: atkCombatBuffs[ATK] += min(atkSkills["atkClash"], spaces_moved_by_atkr) + min(2 * atkSkills["atkClash"] - 1, 6)
    if "spdClash" in atkSkills and spaces_moved_by_atkr > 0: atkCombatBuffs[SPD] += min(atkSkills["spdClash"], spaces_moved_by_atkr) + min(2 * atkSkills["spdClash"] - 1, 6)
    if "defClash" in atkSkills and spaces_moved_by_atkr > 0: atkCombatBuffs[DEF] += min(atkSkills["defClash"], spaces_moved_by_atkr) + min(2 * atkSkills["defClash"] - 1, 6)

    if "atkClash" in defSkills and spaces_moved_by_atkr > 0: defCombatBuffs[ATK] += min(defSkills["atkClash"], spaces_moved_by_atkr) + min(2 * defSkills["atkClash"] - 1, 6)
    if "spdClash" in defSkills and spaces_moved_by_atkr > 0: defCombatBuffs[SPD] += min(defSkills["spdClash"], spaces_moved_by_atkr) + min(2 * defSkills["spdClash"] - 1, 6)
    if "defClash" in defSkills and spaces_moved_by_atkr > 0: defCombatBuffs[DEF] += min(defSkills["defClash"], spaces_moved_by_atkr) + min(2 * defSkills["defClash"] - 1, 6)

    # EXCEL
    if "atk_spd_dashing_defense" in atkSkills:
        if spaces_moved_by_atkr > 0:
            atkr.TDR_all_hits += 3 * min(spaces_moved_by_atkr, 4)
        if defender.getSpecialType() == "Offense":
            atkr.TDR_all_hits += 3 * min(spaces_moved_by_atkr, 4)

    if "atk_spd_dashing_defense" in defSkills:
        if defender.getSpecialType() == "Offense":
            atkr.TDR_all_hits += 3 * min(spaces_moved_by_atkr, 4)

    # FINISH

    if "atkFinish" in atkSkills and atkAllyWithin3Spaces: atkCombatBuffs[ATK] += min(atkSkills["atkFinish"] * 2, 7)
    if "spdFinish" in atkSkills and atkAllyWithin3Spaces: atkCombatBuffs[SPD] += min(atkSkills["spdFinish"] * 2, 7)
    if "defFinish" in atkSkills and atkAllyWithin3Spaces: atkCombatBuffs[DEF] += min(atkSkills["defFinish"] * 2, 7)
    if "resFinish" in atkSkills and atkAllyWithin3Spaces: atkCombatBuffs[RES] += min(atkSkills["resFinish"] * 2, 7)

    if "finishDmg" in atkSkills and atkAllyWithin3Spaces: atkr.true_finish += atkSkills["finishDmg"]
    if "finishHeal" in atkSkills and atkAllyWithin3Spaces: atkr.finish_mid_combat_heal += 7

    if "atkFinish" in defSkills and defAllyWithin3Spaces: defCombatBuffs[ATK] += min(defSkills["atkFinish"] * 2, 7)
    if "spdFinish" in defSkills and defAllyWithin3Spaces: defCombatBuffs[SPD] += min(defSkills["spdFinish"] * 2, 7)
    if "defFinish" in defSkills and defAllyWithin3Spaces: defCombatBuffs[DEF] += min(defSkills["defFinish"] * 2, 7)
    if "resFinish" in defSkills and defAllyWithin3Spaces: defCombatBuffs[RES] += min(defSkills["resFinish"] * 2, 7)

    if "finishDmg" in defSkills and defAllyWithin3Spaces: defr.true_finish += defSkills["finishDmg"]
    if "finishHeal" in defSkills and defAllyWithin3Spaces: defr.finish_mid_combat_heal += 7

    # (PREMIUM) WAVE SKILLS
    if "premiumEvenRes" in atkSkills and turn % 2 == 0: atkCombatBuffs[RES] += 6
    if "premiumEvenRes" in defSkills and turn % 2 == 0: defCombatBuffs[RES] += 6

    # START OF UNIT-EXCLUSIVE WEAPONS

    # Falchion (Refine Eff) - Marth
    if "driveSpectrum_f" in atkSkills:
        atkCombatBuffs = [x + 2 for x in atkCombatBuffs]

    if "driveSpectrum_f" in defSkills:
        defCombatBuffs = [x + 2 for x in defCombatBuffs]

    if "ILOVEBONUSES" in atkSkills and atkHPGreaterEqual50Percent or atkHasBonus:
        map(lambda x: x + 4, atkCombatBuffs)

    if "SEGAAAA" in atkSkills or "nintenesis" in atkSkills:
        map(lambda x: x + 5, atkCombatBuffs)
        if atkTop3AllyBuffTotal >= 10:
            atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True
            if "nintenesis" in atkSkills:
                atkr.disable_foe_guard = True
        if atkTop3AllyBuffTotal >= 25:
            atkCombatBuffs[1] += 5
            atkr.all_hits_heal += 5 + 2 * ("nintenesis" in atkSkills)

    if ("SEGAAAA" in defSkills or "nintenesis" in defSkills) and defAllyWithin2Spaces:
        map(lambda x: x + 5, defCombatBuffs)
        if defTop3AllyBuffTotal >= 10:
            defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
            if "nintenesis" in defSkills:
                defr.disable_foe_guard = True
        if defTop3AllyBuffTotal >= 25:
            defCombatBuffs[1] += 5
            defr.all_hits_heal += 5 + 2 * ("nintenesis" in defSkills)
        if defTop3AllyBuffTotal >= 60:
            defr.vantage = True

    if "denesis" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.DR_first_strikes_NSP.append(40)
        atkCombatBuffs[1] += 5  # + highest atk bonus on self/allies within 2 spaces
        # and the rest of them

    if "denesis" in defSkills and defHPGreaterEqual25Percent:
        defr.DR_first_strikes_NSP.append(40)
        defCombatBuffs[1] += 5  # + highest atk bonus on self/allies within 2 spaces
        # and the rest of them

    if "potentExtras" in atkSkills:
        if atkSkills["potentExtras"] == 4:
            defCombatBuffs[SPD] -= 4
            defCombatBuffs[DEF] -= 4

        if atkSkills["potentExtras"] > 1:
            atkr.DR_all_hits_NSP.append((atkSkills["potentExtras"] - 1) * 10)

    if "caedaVantage" in defSkills and (
            attacker.wpnType in ["Sword", "Lance", "Axe", "CBow"] or attacker.move == 3 or defHPCur / defStats[0] <= 0.75):
        defr.vantage = True

    if "pureWing" in atkSkills and atkAllyWithin3Spaces:
        Y = min(atkAllyWithin3Spaces * 3 + 5, 14)
        atkCombatBuffs = [x + Y for x in atkCombatBuffs]
        atkr.damage_reduction_reduction *= (1-0.5)
        atkr.DR_all_hits_NSP.append(30)
        atkr.all_hits_heal += 7
        if defender.move == 3 or attacker.move == 1:
            atkr.all_hits_heal += 7

    if "tikiBoost" in atkSkills:
        ally_cond = False
        for ally in atkAllyWithin2Spaces:
            if ally.wpnType == "Sword" or ally.wpnType in DRAGON_WEAPONS:
                ally_cond = True

        if ally_cond:
            atkCombatBuffs[ATK] += 5
            atkCombatBuffs[DEF] += 5

    if "tikiBoost" in defSkills:
        ally_cond = False
        for ally in defAllyWithin2Spaces:
            if ally.wpnType == "Sword" or ally.wpnType in DRAGON_WEAPONS:
                ally_cond = True

        if ally_cond:
            defCombatBuffs[ATK] += 5
            defCombatBuffs[DEF] += 5

    # Veteran Lance (Jagen)
    if "old" in atkSkills and defHPCur/defStats[HP] >= 0.70:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[RES] += 5

    if "old" in defSkills:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[RES] += 5

    # Stalwart Sword (Draug)
    if "draugBlade" in defSkills: atkCombatBuffs[ATK] -= 6

    if "guardraug" in atkSkills and atkAllyWithin2Spaces:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5
        atkPenaltiesNeutralized[ATK] = True
        atkPenaltiesNeutralized[DEF] = True

    if "guardraug" in defSkills and defAllyWithin2Spaces:
        defCombatBuffs[1] += 5
        defCombatBuffs[3] += 5
        defPenaltiesNeutralized[ATK] = True
        defPenaltiesNeutralized[DEF] = True

    # Renowned Bow (Gordin)
    if "gordin_field_f" in atkSkills:
        atkCombatBuffs[ATK] -= 4
        atkCombatBuffs[DEF] -= 4

    if "gordin_field_f" in defSkills:
        defCombatBuffs[ATK] -= 4
        defCombatBuffs[DEF] -= 4

    # Devil Axe (Barst)
    if "devilAxe" in atkSkills:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
    if "devilAxe" in defSkills:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Parthia (Jeorge)
    if "parthiaRedu" in atkSkills and defender.wpnType in TOME_WEAPONS:
        atkr.DR_first_hit_NSP.append(30)

    if "parthia2RangeBoost" in atkSkills and defender.wpnType in RANGED_WEAPONS:
        atkCombatBuffs[ATK] += 6

    if "parthiaRedu" in defSkills and attacker.wpnType in TOME_WEAPONS:
        defr.DR_first_hit_NSP.append(30)

    if "parthia2RangeBoost" in defSkills and attacker.wpnType in RANGED_WEAPONS:
        defCombatBuffs[ATK] += 6

    # Aura (Linde) / Excalibur (Merric)
    if "lindeBoost" in atkSkills:
        magic_cond = False

        for ally in atkAllyWithin2Spaces:
            if ally.wpnType in TOME_WEAPONS or ally.wpnType == "Staff":
                magic_cond = True

        if magic_cond:
            atkCombatBuffs[ATK] += 5
            atkCombatBuffs[SPD] += 5

    if "lindeBoost" in defSkills:
        magic_cond = False

        for ally in defAllyWithin2Spaces:
            if ally.wpnType in TOME_WEAPONS or ally.wpnType == "Staff":
                magic_cond = True

        if magic_cond:
            defCombatBuffs[ATK] += 5
            defCombatBuffs[SPD] += 5

    # Dark Aura (Linde/Delthea)
    if "darkAuraBoost" in atkSkills:
        melee_cond = False

        for ally in atkAllyWithin2Spaces:
            if ally.wpnType in MELEE_WEAPONS:
                melee_cond = True

        if melee_cond:
            atkCombatBuffs[ATK] += 5
            atkCombatBuffs[SPD] += 5

    if "darkAuraBoost" in defSkills:
        melee_cond = False

        for ally in defAllyWithin2Spaces:
            if ally.wpnType in MELEE_WEAPONS:
                melee_cond = True

        if melee_cond:
            defCombatBuffs[ATK] += 5
            defCombatBuffs[SPD] += 5

    # Pegasus Sisters (Palla, Catria, Est)

    if "triangleAtk" in atkSkills and atkFlyAlliesWithin2Spaces >= 2:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]
        atkr.brave = True

    if "triangleAtk" in defSkills and defFlyAlliesWithin2Spaces >= 2:
        map(lambda x: x + 3, defCombatBuffs)

    # Gladiator's Blade - Ogma
    if "ogmaBoost" in atkSkills and (atkInfAlliesWithin2Spaces or atkFlyAlliesWithin2Spaces):
        atkCombatBuffs[1] += 4
        atkCombatBuffs[2] += 4

    if "ogmaBoost" in defSkills and (defInfAlliesWithin2Spaces or defFlyAlliesWithin2Spaces):
        defCombatBuffs[1] += 4
        defCombatBuffs[2] += 4

    # Cain, Abel
    if "bibleBros" in atkSkills:
        atkCombatBuffs[1] += min(len(atkAllyWithin2Spaces) * 2, 6)
        atkCombatBuffs[3] += min(len(atkAllyWithin2Spaces) * 2, 6)

    # Cain, Abel, Stahl, Sully
    if "bibleBrosBrave" in atkSkills:
        for ally in atkAllyWithin2Spaces:
            if ally.move == 1 and (ally.wpnType == "Sword" or ally.wpnType == "Lance" or ally.wpnType == "Axe"):
                atkr.brave = True

    if "bibleBros" in defSkills:
        defCombatBuffs[1] += min(len(defAllyWithin2Spaces) * 2, 6)
        defCombatBuffs[3] += max(len(defAllyWithin2Spaces) * 2, 6)

    if "sheenaBoost" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5
        defr.spLossOnAtk -= 1
        defr.spLossWhenAtkd -= 1

    if "sheenaBoost" in defSkills and atkHPEqual100Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[DEF] += 5
        atkr.spLossOnAtk -= 1
        atkr.spLossWhenAtkd -= 1

    # Gradivus (Refine Eff) - Camus/FA!Hardin
    if "gradivu" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkr.all_hits_heal += 7

    if "gradivu" in defSkills:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkr.all_hits_heal += 7

    if "mercuriusMegabuff" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)

    if "mercuriusMegabuff" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)

    if "yahoo" in atkSkills and atkAllyWithin3Spaces:
        atkCombatBuffs[1] += 4  # plus highest atk buff among self & allies within 3 spaces
        atkCombatBuffs[2] += 4  # and so on
        atkCombatBuffs[3] += 4  # and so forth
        atkCombatBuffs[4] += 4  # for all 4 stats

    if "yahoo" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs[1] += 4  # if you have panic
        defCombatBuffs[2] += 4  # and not null panic
        defCombatBuffs[3] += 4  # your buff don't count
        defCombatBuffs[4] += 4  # bottom text

    # Astra Blade - P!Catria
    if "extraAstra" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)

    if "extraAstra" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4, defCombatBuffs)

    if "superExtraAstra" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkCombatBuffs[1] += min(spaces_moved_by_atkr * 2, 8)
        defCombatBuffs[3] -= min(spaces_moved_by_atkr * 2, 8)

    if "superExtraAstra" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)
        defCombatBuffs[1] += min(spaces_moved_by_atkr * 2, 8)
        atkCombatBuffs[3] -= min(spaces_moved_by_atkr * 2, 8)

    if "shadowBlade" in atkSkills and defHPEqual100Percent:
        defCombatBuffs[1] -= 4
        defCombatBuffs[2] -= 4
        defCombatBuffs[3] -= 4
        atkPenaltiesNeutralized = [True] * 5

    if "shadowBlade" in defSkills and atkHPEqual100Percent:
        atkCombatBuffs[1] -= 4
        atkCombatBuffs[2] -= 4
        atkCombatBuffs[3] -= 4
        defPenaltiesNeutralized = [True] * 5

    if "Hello, I like money" in atkSkills:
        map(lambda x: x + 4 + (2 * attacker.flowers > 0), atkCombatBuffs)
        if attacker.flowers > 1:
            atkr.disable_foe_fastcharge = True
            atkr.disable_foe_guard = True

    if "Hello, I like money" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4 + (2 * defender.flowers > 0), defCombatBuffs)
        if defender.flowers > 1:
            defr.disable_foe_fastcharge = True
            defr.disable_foe_guard = True

    # Sneering Axe (Refine Eff) - Legion
    if "legionBoost" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkr.spGainOnAtk += 1

    if "legionBoost" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defr.spGainOnAtk += 1

    # Clarisse's Bow+ (Refine)
    if "clarisseDebuffB" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_atk", 5, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_spd", 5, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "clarisseDebuffB" in defSkills:
        defPostCombatEffs[2].append(("debuff_atk", 5, "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_spd", 5, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Sniper's Bow (Base) - Clarisse
    if "clarisseDebuffC" in atkSkills:
        atkPostCombatEffs[2].append(("damage", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "clarisseDebuffC" in defSkills:
        defPostCombatEffs[2].append(("damage", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Sniper's Bow (Refine Eff) - Clarisse
    if "clarisseBoost" in atkSkills:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

        if any(attacker.isSupportOf(ally) for ally in atkAllyWithin2Spaces):
            cannotCounter = True

    if "clarisseBoost" in defSkills:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4


    # Falchion (Refine Eff) - Alm
    if "doubleLion" in atkSkills and atkHPEqual100Percent:
        atkr.brave = True
        atkPostCombatEffs[0].append(("damage", 5, "self", "one"))

    if "dracofalchion" in atkSkills and atkFoeWithin2Spaces >= atkAllyWithin2Spaces: map(lambda x: x + 5,
                                                                                         atkCombatBuffs)
    if "dracofalchion" in defSkills and defFoeWithin2Spaces >= defAllyWithin2Spaces: map(lambda x: x + 5,
                                                                                         defCombatBuffs)
    if "dracofalchionDos" in atkSkills: map(lambda x: x + 5, atkCombatBuffs)
    if "dracofalchionDos" in defSkills and defAllyWithin2Spaces: map(lambda x: x + 5, defCombatBuffs)

    if "sweeeeeeep" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        if defender.getTargetedDef() == -1 and atkPhantomStats[2] > defPhantomStats[2]:
            atkDoSkillFU = True
            cannotCounter = True

    if "sweeeeeeep" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 5, defCombatBuffs)
        if attacker.getTargetedDef() == -1 and defPhantomStats[2] > atkPhantomStats[2]:
            defDoSkillFU = True

    # Bow of Devotion (Refine) - Faye
    if "fayeBoost" in defSkills and defender.wpnType in RANGED_WEAPONS:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Laid-Back Blade (Base) - Gray
    if "grayBoost" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "grayBoost" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]

    # Laid-Back Blade (Refine Eff) - Gray
    if "challenger" in atkSkills and len(atkAllyWithin2Spaces) <= len(atkFoeWithin2Spaces) - 1:
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

    if "challenger" in defSkills and len(defAllyWithin2Spaces) <= len(defFoeWithin2Spaces) - 1:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]

    # Jubilent Blade (Refine Eff) - Tobin / Dignified Bow (Refine Eff) - Virion
    if "HPWarrior" in atkSkills and atkStats[0] >= defHPCur + 1: atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
    if "HPWarrior" in defSkills and defStats[0] >= atkHPCur + 1: defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Knightly Lance (Refine Eff) - Mathilda / Lordly Lance (Refine Eff) - Clive
    if "jointSupportPartner" in atkSkills:
        if any(attacker.isSupportOf(ally) for ally in atkAllyWithin2Spaces):
            atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "jointSupportPartner" in defSkills:
        if any(defender.isSupportOf(ally) for ally in defAllyWithin2Spaces):
            defCombatBuffs = [x + 3 for x in defCombatBuffs]

    if "jointSupportPartner_f" in atkSkills:
        atkCombatBuffs = [x + atkSkills["jointSupportPartner_f"] for x in atkCombatBuffs]

    if "jointSupportPartner_f" in defSkills:
        defCombatBuffs = [x + defSkills["jointSupportPartner_f"] for x in defCombatBuffs]

    # Ragnarok (Base) - Celica
    if "celicaBoost100" in atkSkills and atkHPEqual100Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkPostCombatEffs[2].append(("damage", 5, "self", "one"))

    if "celicaBoost100" in defSkills and defHPEqual100Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defPostCombatEffs[2].append(("damage", 5, "self", "one"))

    # Ragnarok (Refine) - Celica
    if "celicaBoost5" in atkSkills:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkPostCombatEffs[2].append(("damage", 5, "self", "one"))

    if "celicaBoost5" in defSkills:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defPostCombatEffs[2].append(("damage", 5, "self", "one"))

    if ("belovedZofia" in atkSkills and atkHPEqual100Percent) or "belovedZofia2" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)
        atkRecoilDmg += 4

    if "A man has fallen into the river in LEGO City!" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkPostCombatHealing += 7

    if "ALMMM" in atkSkills and (not atkHPEqual100Percent or not defHPEqual100Percent):
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.all_hits_heal += 7

    if "eCelicaBoost" in atkSkills:
        atkCombatBuffs[ATK] += 6 + trunc(atkStats[SPD] * 0.2)
        atkCombatBuffs[SPD] += 6 + trunc(atkStats[SPD] * 0.2)

        atkr.true_stat_damages.append((SPD, 20))

        defBonusesNeutralized[SPD] = True
        defBonusesNeutralized[RES] = True

        atkr.sp_charge_FU += 1

        atkr.self_desperation = True

    if "eCelicaBoost" in defSkills:
        defCombatBuffs[ATK] += 6 + trunc(defStats[SPD] * 0.2)
        defCombatBuffs[SPD] += 6 + trunc(defStats[SPD] * 0.2)

        defr.true_stat_damages.append((SPD, 20))

        atkBonusesNeutralized[SPD] = True
        atkBonusesNeutralized[RES] = True

        defr.sp_charge_FU += 1

    # Springtime Staff (Refine Eff) - Genny
    if "gennyBoost" in atkSkills:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[RES] += 5

        atkPostCombatEffs[0].append(("heal", 7, "self_and_allies", "within_2_spaces_self"))

    if "gennyBoost" in defSkills:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[RES] += 5

        defPostCombatEffs[0].append(("heal", 7, "self_and_allies", "within_2_spaces_self"))

    # Golden Dagger (Refine Eff) - Saber
    if "SUPER MARIO!!!" in atkSkills and atkSpCountCur == 0:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "SUPER MARIO!!!" in defSkills and defSpCountCur == 0:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]
        ignoreRng = True

    # Bow of Beauty (Refine Eff) - Leon
    if "leonBoost" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4
        atkCombatBuffs[DEF] += 4
        defr.follow_up_denials -= 1

    if "leonBoost" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4
        defCombatBuffs[DEF] += 4
        atkr.follow_up_denials -= 1

    # Dark Royal Spear (Base) - Berkut
    if "berkutBoost" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5
        atkCombatBuffs[RES] += 5

    if "berkutBoost" in defSkills:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[DEF] += 5
        defCombatBuffs[RES] += 5

    # Tyrfing (Base) - Seliph

    if "baseTyrfing" in atkSkills and atkHPCur / atkStats[0] <= 0.5:
        atkCombatBuffs[3] += 4

    if "baseTyrfing" in defSkills and defHPCur / defStats[0] <= 0.5:
        defCombatBuffs[3] += 4

    # Tyrfing (Refine) - Seliph
    if "pseudoMiracle" in atkSkills and atkHPGreaterEqual50Percent:
        atkr.pseudo_miracle = True

    if "pseudoMiracle" in defSkills and defHPGreaterEqual50Percent:
        defr.pseudo_miracle = True

    # Divine Tyrfing (Refine) - Seliph/Sigurd
    if "refDivTyrfing" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5

    if "refDivTyrfing" in defSkills and atkHPGreaterEqual50Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[DEF] += 5

    # Divine Tyrfing (Refine +Eff) - Seliph/Sigurd
    if "WE MOVE" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5
        atkr.follow_ups_skill += 1

    if "WE MOVE" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[DEF] += 5
        defr.follow_ups_skill += 1

    # Divine Tyrfing (Base & Refine) - Seliph/Sigurd
    if ("divTyrfing" in atkSkills or "refDivTyrfing" in atkSkills) and defender.wpnType in ["RTome", "BTome", "GTome", "CTome"]:
        atkr.DR_first_hit_NSP.append(50)
    if ("divTyrfing" in defSkills or "refDivTyrfing" in defSkills) and attacker.wpnType in ["RTome", "BTome", "GTome", "CTome"]:
        defr.DR_first_hit_NSP.append(50)

    # Crusader's Ward - Sigurd/L!Sigurd
    if "deflectRanged" in atkSkills and defender.wpnType in RANGED_WEAPONS:
        atkr.DR_consec_strikes_NSP.append(80)

    if "deflectRanged" in defSkills and attacker.wpnType in RANGED_WEAPONS:
        defr.DR_consec_strikes_NSP.append(80)

    if "vTyrfing" in atkSkills and not atkHPEqual100Percent:
        defCombatBuffs[1] -= 6
        defCombatBuffs[3] -= 6
        atkr.all_hits_heal += 7

    if "vTyrfing" in defSkills:
        atkCombatBuffs[1] -= 6
        atkCombatBuffs[3] -= 6
        defr.all_hits_heal += 7

    if "newVTyrfing" in atkSkills and (not atkHPEqual100Percent or defHPGreaterEqual75Percent):
        defCombatBuffs[1] -= 6
        defCombatBuffs[3] -= 6
        atkr.all_hits_heal += 8
        atkr.prevent_foe_FU = True

    if "newVTyrfing" in defSkills:
        atkCombatBuffs[1] -= 6
        atkCombatBuffs[3] -= 6
        defr.all_hits_heal += 8
        defr.prevent_foe_FU = True

    # L!Seliph - Virtuous Tyrfing - Refined Eff
    if "NO MORE LOSSES" in atkSkills:
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5
        if defender.wpnType in ["RTome", "BTome", "GTome", "CTome", "Staff"]:
            atkr.DR_all_hits_NSP.append(80)
        else:
            atkr.DR_all_hits_NSP.append(40)

    if "NO MORE LOSSES" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5
        if attacker.wpnType in ["RTome", "BTome", "GTome", "CTome", "Staff"]:
            defr.DR_all_hits_NSP.append(80)
        else:
            defr.DR_all_hits_NSP.append(40)

    if "I HATE FIRE JOKES >:(" in atkSkills and spaces_moved_by_atkr:
        map(lambda x: x + 5, atkCombatBuffs)
        if atkHPGreaterEqual25Percent:
            atkr.pseudo_miracle = True

    if "I HATE FIRE JOKES >:(" in defSkills and spaces_moved_by_atkr:
        map(lambda x: x + 5, defCombatBuffs)
        if defHPGreaterEqual25Percent:
            defr.pseudo_miracle = True

    # L!Sigurd - Hallowed Tyrfing - Base

    if "WaitIsHeAGhost" in atkSkills and defHPGreaterEqual75Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        atkr.follow_ups_skill += 1
        atkr.DR_first_hit_NSP.append(40)

    if "WaitIsHeAGhost" in defSkills and atkHPGreaterEqual75Percent:
        map(lambda x: x + 5, defCombatBuffs)
        defr.follow_ups_skill += 1
        if attacker.getRange() == 2:
            defr.DR_first_hit_NSP.append(40)

    # Naga (Refine +Eff) - Julia
    if "nagaAntiDragon" in atkSkills and defender.wpnType in DRAGON_WEAPONS:
        atkr.disable_foe_hexblade = True

    if "nagaAntiDragon" in defSkills and attacker.wpnType in DRAGON_WEAPONS:
        defr.disable_foe_hexblade = True
        ignoreRng = True

    # Divine Naga (Base) - Julia/Deirdre
    if "nullFoeBonuses" in atkSkills:
        defBonusesNeutralized = [True] * 5

    if "nullFoeBonuses" in defSkills:
        atkBonusesNeutralized = [True] * 5

    if "disableFoeHexblade" in atkSkills:
        atkr.disable_foe_hexblade = True

    if "disableFoeHexblade" in defSkills:
        defr.disable_foe_hexblade = True

    if "divineNagaBoost" in atkSkills and atkStats[RES] + atkPhantomStats[RES] >= defStats[RES] + defPhantomStats[RES] + 3:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "divineNagaBoost" in defSkills and defStats[RES] + defPhantomStats[RES] >= atkStats[RES] + atkPhantomStats[RES] + 3:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]

    # Arden's Blade (Refine Eff) - Arden
    if "I'M STRONG AND YOU'RE TOAST" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[DEF] += 6
        defr.spLossWhenAtkd -= 1
        defr.spLossOnAtk -= 1

    if "I'M STRONG AND YOU'RE TOAST" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[DEF] += 6
        atkr.spLossWhenAtkd -= 1
        atkr.spLossOnAtk -= 1

    # Follow-Up Ring
    if "ardenFollowUp" in atkSkills and atkHPGreaterEqual50Percent: atkr.follow_ups_skill += 1
    if "ardenFollowUp" in defSkills and defHPGreaterEqual50Percent: defr.follow_ups_skill += 1

    # Ayra's Blade (Refine Eff) - Ayra
    if "Ayragate" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkr.DR_first_hit_NSP.append(20)

    if "Ayragate" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]
        defr.DR_first_hit_NSP.append(20)

    if "balmungBoost" in atkSkills and defHPEqual100Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkPenaltiesNeutralized = [True] * 5

    if "larceiEdge" in atkSkills and (
            atkStats[SPD] + atkPhantomStats[2] > defStats[SPD] + defPhantomStats[2] or defHPEqual100Percent):
        map(lambda x: x + 4, atkCombatBuffs)
        defBonusesNeutralized = [True] * 5

    if "larceiEdge" in defSkills and (
            atkStats[2] + atkPhantomStats[2] < defStats[2] + defPhantomStats[2] or atkHPEqual100Percent):
        map(lambda x: x + 4, defCombatBuffs)
        atkBonusesNeutralized = [True] * 5

    if "larceiEdge2" in atkSkills and (atkStats[2] + atkPhantomStats[2] > defStats[2] + defPhantomStats[
        2] or defHPGreaterEqual75Percent):
        map(lambda x: x + 4, atkCombatBuffs)
        defBonusesNeutralized = [True] * 5
        atkr.disable_foe_guard = True

    if "larceiEdge2" in defSkills and (defStats[2] + defPhantomStats[2] > atkStats[2] + atkPhantomStats[
        2] or atkHPGreaterEqual75Percent):
        map(lambda x: x + 4, defCombatBuffs)
        atkBonusesNeutralized = [True] * 5
        defr.disable_foe_guard = True

    if "infiniteSpecial" in atkSkills and atkHPGreaterEqual25Percent: map(lambda x: x + 4, atkCombatBuffs)
    if "infiniteSpecial" in defSkills and defHPGreaterEqual25Percent: map(lambda x: x + 4, defCombatBuffs)

    # Dark Mystletainn (+Eff) - Eldigan/Ares
    if "DRINK" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[3] += 5
        atkr.true_sp += 7

    if "DRINK" in defSkills:
        defCombatBuffs[1] += 5
        defCombatBuffs[3] += 5
        defr.true_sp += 7

    # Venin Edge - (Kempf)

    if "AMERICA" in atkSkills:
        NEWatkOtherDmg += 10
        defPostCombatStatusesApplied[2].append(Status.Flash)

    if "AMERICA" in defSkills:
        NEWdefOtherDmg += 10
        atkPostCombatStatusesApplied[2].append(Status.Flash)

    if "FREEDOM" in atkSkills and atkHPGreaterEqual25Percent: map(lambda x: x + 4, atkCombatBuffs)
    if "FREEDOM" in defSkills and defHPGreaterEqual25Percent: map(lambda x: x + 4, defCombatBuffs)

    if "MY TRAP! 🇺🇸" in atkSkills and atkAdjacentToAlly <= 1:
        map(lambda x: x + 4, atkCombatBuffs)
        defPostCombatStatusesApplied[2].append(Status.Discord)
        atkr.DR_first_hit_NSP.append(30)

    if "MY TRAP! 🇺🇸" in defSkills and defAdjacentToAlly <= 1:
        map(lambda x: x + 4, defCombatBuffs)
        defPostCombatStatusesApplied[2].append(Status.Discord)
        defr.DR_first_hit_NSP.append(30)

    if "leafSword" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs[2] += 4
        atkCombatBuffs[3] += 4

    if "theLand" in atkSkills and atkHPGreaterEqual25Percent:
        atkCombatBuffs[1] += 6
        atkCombatBuffs[2] += 6
        atkr.always_pierce_DR = True
        atkPostCombatHealing += 7
        if defender.getSpecialType() == "Defense":
            defr.special_disabled = True

    if "theLand" in defSkills and defHPGreaterEqual25Percent:
        defCombatBuffs[1] += 6
        defCombatBuffs[2] += 6
        defr.always_pierce_DR = True
        defPostCombatHealing += 7
        if attacker.getSpecialType() == "Defense":
            atkr.special_disabled = True

    if "bigHands" in atkSkills and defHPGreaterEqual50Percent:
        atkCombatBuffs[1] += 5
        defCombatBuffs[1] -= 5
        atkr.follow_up_denials -= 1

    if "swagDesp" in atkSkills and atkHPGreaterEqual50Percent:
        atkr.self_desperation = True

    if "swagDespPlus" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.self_desperation = True
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        if defStats[SPD] + defPhantomStats[SPD] > defStats[DEF] + defPhantomStats[DEF]:
            defCombatBuffs[2] -= 8
        else:
            defCombatBuffs[3] -= 8

    if "swagDespPlus" in defSkills and defHPGreaterEqual25Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5
        if atkStats[SPD] + defPhantomStats[SPD] > atkStats[DEF] + defPhantomStats[DEF]:
            atkCombatBuffs[2] -= 8
        else:
            atkCombatBuffs[3] -= 8

    if "swagDespPlusPlus" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        atkr.disable_foe_guard = True



    if "swagDespPlusPlus" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5
        defr.disable_foe_guard = True

    if "spectrumSolo" in atkSkills and not atkAdjacentToAlly:
        map(lambda x: x + 4, atkCombatBuffs)

    if "spectrumSolo" in defSkills and not defAdjacentToAlly:
        map(lambda x: x + 4, defCombatBuffs)

    if "NFUSolo" in atkSkills and not atkAdjacentToAlly:
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    if "NFUSolo" in defSkills and not defAdjacentToAlly:
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True

    if "mareeeeta" in atkSkills and atkAdjacentToAlly <= 1:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True
        defBonusesNeutralized[SPD], defBonusesNeutralized[DEF] = True

    if "mareeeeta" in defSkills and defAdjacentToAlly <= 1:
        map(lambda x: x + 4, defCombatBuffs)
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
        atkBonusesNeutralized[SPD], atkBonusesNeutralized[DEF] = True

    if "moreeeeta" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.sp_pierce_DR = True
        atkr.disable_foe_guard = True

    if "moreeeeta" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)
        defr.sp_pierce_DR = True
        defr.disable_foe_guard = True

    if "ascendingBlade" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True
        atkPostCombatSpCharge += 1

    if "ascendingBlade" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 5, defCombatBuffs)
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
        defPostCombatSpCharge += 1

    # Blazing Durandal (Refine) - B!Roy/Eliwood
    if "ourBoyBlade" in atkSkills:
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1
        defr.spLossWhenAtkd -= 1
        defr.spLossOnAtk -= 1

    # Blazing Durandal (Refine Eff) - B!Roy/Eliwood
    if "roys" in atkSkills:
        atkCombatBuffs[SPD] += 7
        atkCombatBuffs[DEF] += 10
        defr.follow_up_denials -= 1

    if "ROY'S OUR BOY" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1
        atkr.disable_foe_guard = True

    if "ROY'S OUR BOY" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)
        defr.spGainOnAtk += 1
        defr.spGainWhenAtkd += 1
        defr.disable_foe_guard = True

    # Weighted Lance (Gwendolyn)
    if "gwendyBoost" in atkSkills and atkHPGreaterEqual50Percent:
        atkr.spGainWhenAtkd += 1

        atkCombatBuffs[DEF] += 4
        atkCombatBuffs[RES] += 4

    if "gwendyBoost" in defSkills and defHPGreaterEqual50Percent:
        defr.spGainWhenAtkd += 1

        defCombatBuffs[DEF] += 4
        defCombatBuffs[RES] += 4

    if "light_buff" in atkSkills:
        atkPostCombatEffs[0].append(("buff_def", 4, "allies", "within_1_spaces_self"))
        atkPostCombatEffs[0].append(("buff_res", 4, "allies", "within_1_spaces_self"))

    if "super_light_buff" in atkSkills:
        atkPostCombatEffs[2].append(("buff_atk", 4, "self_and_allies", "within_2_spaces_self"))
        atkPostCombatEffs[2].append(("buff_spd", 4, "self_and_allies", "within_2_spaces_self"))
        atkPostCombatEffs[2].append(("buff_def", 4, "self_and_allies", "within_2_spaces_self"))
        atkPostCombatEffs[2].append(("buff_res", 4, "self_and_allies", "within_2_spaces_self"))

    if "super_light_buff" in defSkills:
        defPostCombatEffs[2].append(("buff_atk", 4, "self_and_allies", "within_2_spaces_self"))
        defPostCombatEffs[2].append(("buff_spd", 4, "self_and_allies", "within_2_spaces_self"))
        defPostCombatEffs[2].append(("buff_def", 4, "self_and_allies", "within_2_spaces_self"))
        defPostCombatEffs[2].append(("buff_res", 4, "self_and_allies", "within_2_spaces_self"))

    if "faeBonus" in atkSkills and attacker.hasBonus():
        defCombatBuffs[ATK] -= 4
        defCombatBuffs[RES] -= 4
        atkr.spGainWhenAtkd += 1

    if "faeBonus" in defSkills and defender.hasBonus():
        atkCombatBuffs[ATK] -= 4
        atkCombatBuffs[RES] -= 4
        defr.spGainWhenAtkd += 1

    if "wanderer" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5

    if "like the university" in atkSkills and atkHPGreaterEqual25Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5

    if "wanderer" in defSkills and atkHPGreaterEqual75Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5

    if "like the university" in defSkills and defHPGreaterEqual25Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5

    # Runeaxe (Base) - Narcian
    if "runeaxeHeal" in atkSkills: atkr.all_hits_heal += 7
    if "runeaxeHeal" in defSkills: defr.all_hits_heal += 7

    # Runeaxe (Refine +Eff) - Narcian
    if "runeaxeBoost" in atkSkills and defHasPenalty: atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
    if "runeaxeBoost" in defSkills and atkHasPenalty: defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # L!Eliwood

    if "elistats" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)

    if "elistats" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)

    if "closeSpectrum" in defSkills and attacker.wpnType in MELEE_WEAPONS:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    if "hamburger" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)
        defBonusesNeutralized = [True] * 5

    if "hamburger" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4, defCombatBuffs)
        atkBonusesNeutralized = [True] * 5

    # Mulagir (Refine Eff) - B!Lyn
    if "blynBoost" in atkSkills and atkStats[SPD] + atkPhantomStats[SPD] > defStats[SPD] + defPhantomStats[SPD]:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "blynBoost" in defSkills and defStats[SPD] + defPhantomStats[SPD] > atkStats[SPD] + atkPhantomStats[SPD]:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Sacae's Blessing - B!Lyn
    if "sacaeSweep" in atkSkills and defender.wpnType in ["Sword", "Lance", "Axe"]:
        cannotCounter = True

    # Berserk Armads

    if "oho ono" in atkSkills and defHPEqual100Percent:
        defCombatBuffs[ATK] -= 5
        defCombatBuffs[DEF] -= 5
        atkr.surge_heal += trunc(atkStats[HP] * 0.30)

    if "oho ono" in defSkills:
        atkCombatBuffs[ATK] -= 5
        atkCombatBuffs[DEF] -= 5
        defr.surge_heal += trunc(defStats[HP] * 0.30)


    # H!Hector

    if ("curiosBoost" in atkSkills or "reduFU" in atkSkills) and turn % 2 == 1 or not defHPEqual100Percent:
        map(lambda x: x + 4, atkCombatBuffs)

    if ("curiosBoost" in defSkills or "reduFU" in defSkills) and turn % 2 == 1 or not atkHPEqual100Percent:
        map(lambda x: x + 4, defCombatBuffs)

    if "oho dad" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)

        defCombatBuffs[1] -= math.trunc(atkStats[ATK] * 0.1)
        defCombatBuffs[3] -= math.trunc(atkStats[ATK] * 0.1)

        atkPostCombatHealing += 7

    if "oho dad" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)

        atkCombatBuffs[1] -= math.trunc(defStats[ATK] * 0.1)
        atkCombatBuffs[3] -= math.trunc(defStats[ATK] * 0.1)

        atkPostCombatHealing += 7

    # Rebecca's Bow (Refine +Eff) - Rebecca
    if "rebeccaBoost" in atkSkills and sum(attacker.buffs) > 0 and AtkPanicFactor == 1: atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
    if "rebeccaBoost" in defSkills and sum(defender.buffs) > 0 and DefPanicFactor == 1: defCombatBuffs = [x + 4 for x in defCombatBuffs]

    if "mutton idk" in atkSkills:
        defCombatBuffs[ATK] -= 5
        defCombatBuffs[DEF] -= 5
        defBonusesNeutralized = [True] * 5

    if "mutton idk" in defSkills and defAllyWithin2Spaces:
        atkCombatBuffs[ATK] -= 5
        atkCombatBuffs[DEF] -= 5
        atkBonusesNeutralized = [True] * 5

    # Deathly Dagger (Refine) - Jaffar
    if "jaffarDmg" in atkSkills: atkPostCombatEffs[2].append(("damage", 10, "foe_and_foes_allies", "within_2_spaces_foe"))
    if "jaffarDmg" in defSkills: defPostCombatEffs[2].append(("damage", 10, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Deathly Dagger (Refine +Eff) - Jaffar
    if "magicDenial" in atkSkills and defender.wpnType in TOME_WEAPONS:
        cannotCounter = True

    # Regal Blade (Base/Refine) - LLoyd
    if "garbageSword" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs[ATK] += atkSkills["garbageSword"]
        atkCombatBuffs[SPD] += atkSkills["garbageSword"]

    if "garbageSword" in defSkills and atkHPEqual100Percent:
        defCombatBuffs[ATK] += defSkills["garbageSword"]
        defCombatBuffs[SPD] += defSkills["garbageSword"]

    # Regal Blade (Refine Eff) - Lloyd
    if "Hi Nino" in atkSkills:
        magic_cond = False
        for ally in atkAllyWithin2Spaces:
            if ally.wpnType in TOME_WEAPONS and ally.move == 0:
                magic_cond = True

        if magic_cond:
            atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "Hi Nino" in defSkills:
        magic_cond = False
        for ally in defAllyWithin2Spaces:
            if ally.wpnType in TOME_WEAPONS and ally.move == 0:
                magic_cond = True

        if magic_cond:
            defCombatBuffs = [x + 3 for x in defCombatBuffs]

    if "vassalBlade" in atkSkills:
        atkCombatBuffs[SPD] += 5

    if "Barry B. Benson" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    # Sieglinde (+Eff)
    if "bonusInheritor" in atkSkills:  # eirika, should be highest bonus for each given stat on allies within 2 spaces
        highest_stats = [0, 0, 0, 0, 0]
        for ally in atkAllyWithin2Spaces:
            ally_panic = Status.Panic in ally.statusNeg and Status.NullPanic not in ally.statusPos
            if ally_panic: continue

            i = 1
            while i < 5:
                cur_buff = ally.buffs[i]
                highest_stats[i] = max(highest_stats[i], cur_buff)

                i += 1

        i = 1
        while i < 5:
            atkCombatBuffs[i] += highest_stats[i]
            i += 1

    if "bonusInheritor" in defSkills:
        highest_stats = [0, 0, 0, 0, 0]
        for ally in defAllyWithin2Spaces:
            ally_panic = Status.Panic in ally.statusNeg and Status.NullPanic not in ally.statusPos
            if ally_panic: continue

            i = 1
            while i < 5:
                cur_buff = ally.buffs[i]
                highest_stats[i] = max(highest_stats[i], cur_buff)

                i += 1

        i = 1
        while i < 5:
            defCombatBuffs[i] += highest_stats[i]
            i += 1


    if "stormSieglinde" in atkSkills and atkFoeWithin2Spaces >= atkAllyWithin2Spaces:
        atkCombatBuffs[3] += 3
        atkCombatBuffs[4] += 3
        atkr.spGainOnAtk += 1

    if "stormSieglinde2" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

    if "stormSieglinde2" in defSkills and not defAdjacentToAlly:
        map(lambda x: x + 4, defCombatBuffs)
        defr.spGainOnAtk += 1
        defr.spGainWhenAtkd += 1

    if "Just Lean" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)

    if "Just Lean" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)

    if "renaisTwins" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)

    if "renaisTwins" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4, defCombatBuffs)

    # Sisterly Axe (X!Eirika)
    if "sisterlyBoost" in atkSkills and atkAllyWithin3Spaces:

        num_ally_3_row_3_col = 0

        tiles_within_3_col = attacker.attacking_tile.tilesWithinNCols(3)
        tiles_within_3_row = attacker.attacking_tile.tilesWithinNRows(3)
        tiles_within_3_row_or_column = list(set(tiles_within_3_col) | set(tiles_within_3_row))

        for tile in tiles_within_3_row_or_column:
            if tile.hero_on != None and tile.hero_on.isAllyOf(attacker):
                num_ally_3_row_3_col += 1

        boost = min(5 + num_ally_3_row_3_col * 3, 14)

        atkCombatBuffs = [x + boost for x in atkCombatBuffs]

        atkr.damage_reduction_reduction *= 0.5

    # Nidhogg (Refine Eff) - Innes
    if "innesDenial" in atkSkills and defender.wpnType in MAGICAL_WEAPONS + DRAGON_WEAPONS:
        cannotCounter = True

    # Vidofnir (Base) - Tana
    if "meleeStance" in defSkills and defender.wpnType in ["Sword", "Lance", "Axe"]:
        defCombatBuffs[DEF] += 7

    # Vidofnir (Refine Eff) - Tana
    if "tanaBoost" in atkSkills and (atkInfAlliesWithin2Spaces or atkArmAlliesWithin2Spaces):
        atkCombatBuffs[ATK] += 7
        atkCombatBuffs[SPD] += 7

    if "tanaBoost" in defSkills and (defInfAlliesWithin2Spaces or defArmAlliesWithin2Spaces):
        defCombatBuffs[ATK] += 7
        defCombatBuffs[SPD] += 7

    # Cursed Lance (Refine Eff) - Valter
    if "valterBoost" in atkSkills and defHasPenalty:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkCombatBuffs[DEF] += 5
        defr.spLossOnAtk -= 1
        defr.spLossWhenAtkd -= 1

    if "valterBoost" in defSkills and atkHasPenalty:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defCombatBuffs[DEF] += 5
        atkr.spLossOnAtk -= 1
        atkr.spLossWhenAtkd -= 1

    # Weirding Tome (Refine Eff) - Lute
    if "luteBoost" in atkSkills and defHasPenalty:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "luteBoost" in defSkills and atkHasPenalty:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    if "audBoost" in atkSkills and defHPEqual100Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        defr.spLossWhenAtkd -= 1
        defr.spLossOnAtk -= 1

    if "audBoost" in defSkills:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]
        atkr.spLossWhenAtkd -= 1
        atkr.spLossOnAtk -= 1

    if "hey all scott here" in atkSkills:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5

    if "hey all scott here" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5

    # Ragnell/Alondite (Refine Eff) - Ike, L!Ike/Black Knight, Zelgius
    if ("I fight for my friends" in atkSkills or "WILLYOUSURVIVE?" in atkSkills) and atkHPGreaterEqual25Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if ("I fight for my friends" in defSkills or "WILLYOUSURVIVE?" in defSkills) and defHPGreaterEqual25Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    # Urvan (Base) - B!Ike
    if "bikeDR" in atkSkills:
        atkr.DR_consec_strikes_NSP.append(80)

    if "bikeDR" in defSkills:
        defr.DR_consec_strikes_NSP.append(80)

    # Urvan (Refine Eff) - B!Ike
    if "bikeDesp" in atkSkills:
        atkr.DR_first_hit_NSP.append(40)

    if "bikeDesp" in defSkills:
        defr.DR_first_hit_NSP.append(40)
        defr.other_desperation = True

    # CH!Ike - Sturdy War Sword - Base

    if "sturdyWarrr" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        if attacker.getSpecialType() == "Offense":
            if atkAllyWithin4Spaces >= 1:
                atkr.sp_charge_first += math.trunc(attacker.getMaxSpecialCooldown() / 2)
            if atkAllyWithin4Spaces >= 2:
                atkr.DR_first_hit_NSP.append(10 * defender.getMaxSpecialCooldown())
            if atkAllyWithin4Spaces >= 3:
                atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    if "sturdyWarrr" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 5, defCombatBuffs)
        if defender.getSpecialType() == "Offense":
            if defAllyWithin4Spaces >= 1:
                defr.sp_charge_first += math.trunc(defender.getMaxSpecialCooldown() / 2)
            if defAllyWithin4Spaces >= 2:
                defr.DR_first_hit_NSP.append(10 * defender.getMaxSpecialCooldown())
            if defAllyWithin4Spaces >= 3:
                defr.prevent_foe_FU, defr.prevent_self_FU_denial = True

    if "BIGIKEFAN" in atkSkills and atkHPGreaterEqual25Percent:
        X = min(max(trunc(defStats[ATK] * 0.2) - 2, 6), 16)
        atkCombatBuffs[ATK] += X
        defCombatBuffs[ATK] -= X
        atkPenaltiesNeutralized = [True] * 5
        disableCannotCounter = True
        atkr.disable_foe_guard = True

    if "BIGIKEFAN" in defSkills and defHPGreaterEqual25Percent:
        X = min(max(trunc(atkStats[ATK] * 0.2) - 2, 6), 16)
        defCombatBuffs[ATK] += X
        atkCombatBuffs[ATK] -= X
        defPenaltiesNeutralized = [True] * 5
        defr.disable_foe_guard = True

    if "AETHER_GREAT" in atkSkills:
        atkr.vantage = True
        atkr.other_desperation = True
        atkr.DR_great_aether_SP = True

    if "AETHER_GREAT" in defSkills:
        defr.other_desperation = True
        defr.DR_great_aether_SP = True

    # Elena's Staff (Base) - Mist
    if "mistDebuff" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "mistDebuff" in defSkills:
        defPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Elena's Staff (Refine Eff) - Mist
    if "mistPanic" in atkSkills:
        atkPostCombatEffs[2].append(("status", Status.Panic, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "mistPanic" in defSkills:
        defPostCombatEffs[2].append(("status", Status.Panic, "foe_and_foes_allies", "within_2_spaces_foe"))


    if "pointySword" in atkSkills: map(lambda x: x + 5, atkCombatBuffs)
    if "pointySword" in defSkills and defAllyWithin2Spaces: map(lambda x: x + 5, atkCombatBuffs)

    # Loyal Greatlance (Refine Eff) - Oscar
    if "oscarDrive" in atkSkills and atkInfAlliesWithin2Spaces or atkCavAlliesWithin2Spaces:
        atkCombatBuffs[ATK] += 3
        atkCombatBuffs[SPD] += 3

    if "oscarDrive" in defSkills and defInfAlliesWithin2Spaces or defCavAlliesWithin2Spaces:
        defCombatBuffs[ATK] += 3
        defCombatBuffs[SPD] += 3

    if "oscarDrive_f" in atkSkills:
        atkCombatBuffs[ATK] += 3
        atkCombatBuffs[SPD] += 3

    if "oscarDrive_f" in defSkills:
        defCombatBuffs[ATK] += 3
        defCombatBuffs[SPD] += 3

    if "sanakiBoost" in atkSkills and atkFlyAlliesWithin2Spaces:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[RES] += 5

    if "sanakiBoost" in defSkills and defFlyAlliesWithin2Spaces:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[RES] += 5

    # Ragnell·Alondite (Refine + Eff) - Altina/WI!Altina
    if "TWO?" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[4] += 5
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

        defBonusesNeutralized[ATK] = True
        defBonusesNeutralized[DEF] = True

    if "TWO?" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[4] += 5
        defr.spGainWhenAtkd += 1
        defr.spGainOnAtk += 1
        atkBonusesNeutralized[ATK] = True
        atkBonusesNeutralized[DEF] = True

    # yeah we'll be here for a while
    if "You get NOTHING" in atkSkills:
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
        atkr.special_disabled = True
        defr.special_disabled = True
        atkDefensiveTerrain = False
        defDefensiveTerrain = False
        atkr.hardy_bearing = True
        defr.hardy_bearing = True
        if atkHPGreaterEqual25Percent: map(lambda x: x + 5, atkCombatBuffs)

    if "You get NOTHING" in defSkills:
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
        atkr.special_disabled = True
        defr.special_disabled = True
        atkDefensiveTerrain = False
        defDefensiveTerrain = False
        atkr.hardy_bearing = True
        defr.hardy_bearing = True
        if defHPGreaterEqual25Percent: map(lambda x: x + 5, defCombatBuffs)

    # Awakening Falchion (Refine)
    if "spectrumBond" in atkSkills and atkAdjacentToAlly:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "spectrumBond" in defSkills and defAdjacentToAlly:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Sealed Falchion (Base) - Awakening Falchion users + P!Chrom
    if "sealedFalchion" in atkSkills and not atkHPEqual100Percent:
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

    if "sealedFalchion" in defSkills and not atkHPEqual100Percent:
        defCombatBuffs = [x + 5 for x in defCombatBuffs]

    # Sealed Falchion (Refine) - Awakening Falchion users + P!Chrom
    if "newSealedFalchion" in atkSkills and (not atkHPEqual100Percent or atkHasBonus):
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

    if "newSealedFalchion" in defSkills and (not defHPEqual100Percent or defHasBonus):
        defCombatBuffs = [x + 5 for x in defCombatBuffs]

    # Sealed Falchion (Refine Eff) - Awakening Falchion users + P!Chrom
    if "I CANT STOP THIS THING" in atkSkills and defHPGreaterEqual75Percent:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkCombatBuffs[DEF] += 5
        defr.follow_up_denials -= 1

    if "I CANT STOP THIS THING" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defCombatBuffs[DEF] += 5
        atkr.follow_up_denials -= 1

    # Carrot Lance/Axe+ and Blue/Green Egg+ (Refine)
    if "easterHealB" in atkSkills:
        atkPostCombatEffs[2].append(("heal", 4, "self", "one"))
    if "easterHealB" in defSkills:
        defPostCombatEffs[2].append(("heal", 4, "self", "one"))

    if "summerPush" in atkSkills and atkHPEqual100Percent:
        atkCombatBuffs = [x + 2 for x in atkCombatBuffs]
        atkPostCombatEffs[2].append(("damage", 2, "self", "one"))

    if "summerPush" in defSkills and defHPEqual100Percent:
        defCombatBuffs = [x + 2 for x in defCombatBuffs]
        defPostCombatEffs[2].append(("damage", 2, "self", "one"))

    # Geirskögul (Base) - B!Lucina
    if "lucinaDrive_f" in atkSkills:
        atkCombatBuffs[ATK] += 3
        atkCombatBuffs[SPD] += 3

    if "lucinaDrive_f" in defSkills:
        defCombatBuffs[ATK] += 3
        defCombatBuffs[SPD] += 3

    # Geirskögul (Refine Eff) - B!Lucina
    if "refinedLucinaDrive_f" in atkSkills:
        atkCombatBuffs[DEF] += 3
        atkCombatBuffs[RES] += 3
        atkr.spGainWhenAtkd += 1
        atkr.spGainOnAtk += 1

    if "refinedLucinaDrive_f" in defSkills:
        defCombatBuffs[DEF] += 3
        defCombatBuffs[RES] += 3
        defr.spGainWhenAtkd += 1
        defr.spGainOnAtk += 1

    # Missiletainn (Owain)
    if "average" in atkSkills and defHPGreaterEqual50Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5

    if "average" in defSkills and atkHPGreaterEqual50Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5

    # Cordelia's Lance
    if "cordeliaLance" in atkSkills and atkHPCur/atkStats[HP] >= 0.70:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    # Blessed Bouquet/First Bite/Cupid Arrow (Refine)
    if "bridalBuffsB" in atkSkills:
        atkPostCombatEffs[2].append(("buff_def", 5, "self_and_allies", "within_2_spaces_self"))
        atkPostCombatEffs[2].append(("buff_res", 5, "self_and_allies", "within_2_spaces_self"))

    if "bridalBuffsB" in defSkills:
        defPostCombatEffs[2].append(("buff_def", 5, "self_and_allies", "within_2_spaces_self"))
        defPostCombatEffs[2].append(("buff_res", 5, "self_and_allies", "within_2_spaces_self"))

    # Hewn Lance - Donnel
    if "donnelBoost" in atkSkills:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[DEF] += 4
        defr.follow_up_denials -= 1

    # Candied Dagger - Gaius
    if "gaius_candy" in atkSkills:
        atkCombatBuffs[SPD] += 4
        atkr.true_stat_damages.append((SPD, 10))

    if "gaius_damage_ref" in atkSkills and defHPEqual100Percent:
        atkr.true_all_hits += 7

    # Corvus Tome (Refine Eff) - Henry
    if "henryLowAtkBoost" in atkSkills and defStats[ATK] + defPhantomStats[ATK] >= atkStats[ATK] + atkPhantomStats[ATK] + 3:
        defCombatBuffs[ATK] -= 6
        defCombatBuffs[RES] -= 6
        defr.spLossOnAtk -= 1
        defr.spLossWhenAtkd -= 1

    if "henryLowAtkBoost" in defSkills and atkStats[ATK] + atkPhantomStats[ATK] >= defStats[ATK] + defPhantomStats[ATK] + 3:
        atkCombatBuffs[ATK] -= 6
        atkCombatBuffs[RES] -= 6
        atkr.spLossOnAtk -= 1
        atkr.spLossWhenAtkd -= 1

    # Spectral Tome+/Monstrous Bow+
    if "halloweenPanic" in atkSkills: atkPostCombatEffs[2].append(("status", Status.Panic, "foes_allies", "within_2_spaces_foe"))
    if "halloweenPanic" in defSkills: defPostCombatEffs[2].append(("status", Status.Panic, "foes_allies", "within_2_spaces_foe"))

    # Tharja's Hex - Tharja
    if "tharja_field_f" in atkSkills:
        atkCombatBuffs[ATK] -= 4
        atkCombatBuffs[SPD] -= 4

    if "tharja_field_f" in defSkills:
        defCombatBuffs[ATK] -= 4
        defCombatBuffs[SPD] -= 4


    # Purifying Breath - Nowi

    if "nowiBoost" in atkSkills and atkHPGreaterEqual50Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkPenaltiesNeutralized = [True] * 5

    if "nowiBoost" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]
        defPenaltiesNeutralized = [True] * 5

    # Grimoire (Refine) - Nowi
    if "nowiSchmovement" in atkSkills and atkAllyWithin2Spaces:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "nowiSchmovement" in defSkills and defAllyWithin2Spaces:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "nowiField_f" in atkSkills:
        atkCombatBuffs[ATK] -= 4
        atkCombatBuffs[SPD] -= 4
        atkCombatBuffs[RES] -= 4

    if "nowiField_f" in defSkills:
        defCombatBuffs[ATK] -= 4
        defCombatBuffs[SPD] -= 4
        atkCombatBuffs[RES] -= 4

    # Owain
    if "Sacred Stones Strike!" in atkSkills and atkAllyWithin3Spaces:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5

    if "ancientRagnell" in atkSkills and (atkHPGreaterEqual50Percent or atkHasBonus):
        defCombatBuffs[1] -= 6
        defCombatBuffs[3] -= 6

    if "ancientRagnell" in defSkills and (defHPGreaterEqual50Percent or defHasBonus):
        atkCombatBuffs[1] -= 6
        atkCombatBuffs[3] -= 6

    if "lioness" in atkSkills and atkHPGreaterEqual25Percent:
        atkCombatBuffs[1] += 6
        atkCombatBuffs[2] += 6
        atkr.sp_pierce_DR = True
        if defHPGreaterEqual75Percent:
            atkr.spGainWhenAtkd += 1
            atkr.spGainOnAtk += 1

    if "lioness" in defSkills and defHPGreaterEqual25Percent:
        defCombatBuffs[1] += 6
        defCombatBuffs[2] += 6
        defr.sp_pierce_DR = True
        if atkHPGreaterEqual75Percent:
            defr.spGainWhenAtkd += 1
            defr.spGainOnAtk += 1

    # Yato - Ref (M!Corrin)

    if "corrinField_f" in atkSkills: atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
    if "corrinField_f" in defSkills: defCombatBuffs = [x + 4 for x in defCombatBuffs]

    if "oldDarkBreath" in atkSkills:
        atkPostCombatEffs[0].append(("debuff_atk", 5, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[0].append(("debuff_spd", 5, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "refDarkBreath" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    if "refDarkBreath" in defSkills:
        defPostCombatEffs[2].append(("debuff_atk", 7, "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_spd", 7, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Felicia's Plate (Felicia)

    if "feliciaMagicGuard" in atkSkills and defender.wpnType in ["RTome", "BTome", "GTome", "CTome"]:
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

    if "feliciaMagicGuard" in defSkills and attacker.wpnType in ["RTome", "BTome", "GTome", "CTome"]:
        defr.spGainOnAtk += 1
        defr.spGainWhenAtkd += 1

    # Jakob's Tray (Jakob)

    if "jakobDebuff" in atkSkills:
        defCombatBuffs = [x - 4 for x in defCombatBuffs]

    if "jakobAllyBoost" in atkSkills:
        ally_condition = False
        for ally in atkAllyWithin2Spaces:
            if ally.HPcur < ally.visible_stats[HP]:
                ally_condition = True

        if ally_condition:
            atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "jakobAllyBoost" in defSkills:
        ally_condition = False
        for ally in defAllyWithin2Spaces:
            if ally.HPcur < ally.visible_stats[HP]:
                ally_condition = True

        if ally_condition:
            defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Inveterate Axe (Gunter)
    if "gunterJointDrive" in atkSkills and atkAllyWithin2Spaces:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[DEF] += 4

    if "gunterJointDrive" in defSkills and defAllyWithin2Spaces:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[DEF] += 4

    if "gunterJointDrive_f" in atkSkills and (attacker.move == 0 or attacker.move == 1):
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[DEF] += 4

    if "gunterJointDrive_f" in defSkills and (defender.move == 0 or defender.move == 1):
        defCombatBuffs[ATK] += 4
        defCombatBuffs[DEF] += 4

    # Raijinto (Ryoma)
    if "waitTurns" in atkSkills:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkr.prevent_foe_FU = True
        atkr.prevent_self_FU_denial = True

    if "waitTurns" in defSkills and defAllyWithin2Spaces:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]
        defr.prevent_foe_FU = True
        defr.prevent_self_FU_denial = True

    if "kageroBoost" in atkSkills and atkStats[ATK] + atkPhantomStats[ATK] > defStats[ATK] + defPhantomStats[ATK]:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "kageroBoost" in defSkills and defStats[ATK] + defPhantomStats[ATK] > atkStats[ATK] + atkPhantomStats[ATK]:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "kageroRedu" in atkSkills:
        atkr.DR_first_hit_NSP.append(50)

    # Hinoka's Spear
    if "hinokaBoost" in atkSkills and (atkFlyAlliesWithin2Spaces or atkInfAlliesWithin2Spaces):
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "hinokaBoost" in defSkills and (defFlyAlliesWithin2Spaces or defInfAlliesWithin2Spaces):
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "setsunaRangedBoost" in atkSkills and defender.wpnType in RANGED_WEAPONS:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "setsunaRangedBoost" in defSkills and attacker.wpnType in RANGED_WEAPONS:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    if "setsunaBonusBoost" in atkSkills and atkHasBonus:
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[SPD] += 5
        atkPenaltiesNeutralized[ATK] = True
        atkPenaltiesNeutralized[SPD] = True

    if "setsunaBonusBoost" in atkSkills and defHasBonus:
        defCombatBuffs[ATK] += 5
        defCombatBuffs[SPD] += 5
        defPenaltiesNeutralized[ATK] = True
        defPenaltiesNeutralized[SPD] = True

    # Subaki
    if "subakiDamage" in atkSkills and atkHPCur/atkStats[HP] >= 0.70:
        atkr.true_all_hits += 7

    if "subakiDamage" in defSkills and defHPCur/defStats[HP] >= 0.70:
        defr.true_all_hits += 7

    # Siegfried (Refine Eff) - Xander
    if "xanderific" in atkSkills and defHPGreaterEqual75Percent:
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5
        defr.follow_up_denials -= 1

    if "xanderific" in defSkills and atkHPGreaterEqual75Percent:
        atkCombatBuffs[ATK] -= 5
        atkCombatBuffs[DEF] -= 5
        atkr.follow_up_denials -= 1

    # Siegbert
    if "Toaster" in atkSkills and not atkAdjacentToAlly:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        atkPenaltiesNeutralized = [True] * 5

    # Peri's Spear (Peri)
    if "periBoost" in atkSkills and not atkHPEqual100Percent:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]

    if "periBoost" in defSkills and not defHPEqual100Percent:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]

    # Laslow's Blade (Laslow)
    if "laslowBrave" in atkSkills:
        bonus_total_reached = 0

        for ally in atkAllyWithin3Spaces:
            panic_factor = 1
            if Status.Panic in ally.statusNeg: panic_factor = -1
            if Status.NullPanic in ally.statusPos: panic_factor = 1
            if sum(ally.buffs) * panic_factor >= 10:
                bonus_total_reached += 1

        if bonus_total_reached >= 2:
            atkCombatBuffs[1] += 3
            atkCombatBuffs[3] += 3
            atkr.brave = True

    if "laslowBrave" in defSkills:
        bonus_total_reached = 0

        for ally in defAllyWithin3Spaces:
            panic_factor = 1
            if Status.Panic in ally.statusNeg: panic_factor = -1
            if Status.NullPanic in ally.statusPos: panic_factor = 1
            if sum(ally.buffs) * panic_factor >= 10:
                bonus_total_reached += 1

        if bonus_total_reached >= 2:
            defCombatBuffs[1] += 3
            defCombatBuffs[3] += 3
            defr.brave = True

    # Brynhildr (Leo)

    if "leoGravity" in atkSkills:
        atkPostCombatEffs[0].append(("status", Status.Gravity, "foe", "one"))

    if "leoWhateverTheHellThisIs" in atkSkills and defender.wpnType in TOME_WEAPONS:
        atkr.DR_first_hit_NSP.append(30)

    if "leoWhateverTheHellThisIs" in defSkills and attacker.wpnType in TOME_WEAPONS:
        defr.DR_first_hit_NSP.append(30)


    # Camilla
    if "camillaBoost" in atkSkills and (atkCavAlliesWithin2Spaces or atkFlyAlliesWithin2Spaces):
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4

    if "camillaBoost" in defSkills and (defCavAlliesWithin2Spaces or defFlyAlliesWithin2Spaces):
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4

    if "camillaField_f" in atkSkills and (attacker.move == 1 or attacker.move == 2):
        atkCombatBuffs[ATK] += 3
        atkCombatBuffs[SPD] += 3

    if "camillaField_f" in defSkills and (defender.move == 1 or defender.move == 2):
        defCombatBuffs[ATK] += 3
        defCombatBuffs[SPD] += 3

    # Beruka
    if "berukaAxe" in atkSkills and atkHPGreaterEqual50Percent:
        defCombatBuffs[ATK] -= 4
        defr.spLossOnAtk -= 1
        defr.spLossWhenAtkd -= 1

    if "berukaAxe" in defSkills and defHPGreaterEqual50Percent:
        defCombatBuffs[ATK] -= 4
        atkr.spLossOnAtk -= 1
        atkr.spLossWhenAtkd -= 1

    # Selena
    if "lowAtkBoost" in atkSkills and defStats[ATK] + defPhantomStats[ATK] >= atkStats[ATK] + atkPhantomStats[ATK] + 3:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "lowAtkBoost" in defSkills and atkStats[ATK] + atkPhantomStats[ATK] >= defStats[ATK] + defPhantomStats[ATK] + 3:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]

    if "eliseField_f" in defSkills:
        defCombatBuffs = [x - 4 for x in defCombatBuffs]

    # Arthur's Axe

    if "arthurBonus" in atkSkills and sum(attacker.buffs) > 0 and AtkPanicFactor != -1:
        atkCombatBuffs = [x + 3 for x in atkCombatBuffs]

    if "arthurBonus" in defSkills and sum(defender.buffs) > 0 and DefPanicFactor != -1:
        defCombatBuffs = [x + 3 for x in defCombatBuffs]

    if "arthurDebuffer" in atkSkills and (attacker.hasPenalty() or not atkHPEqual100Percent):
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

    if "arthurDebuffer" in defSkills and (defender.hasPenalty() or not defHPEqual100Percent):
        defCombatBuffs = [x + 5 for x in defCombatBuffs]

    # Effie's Lance
    if "effieAtk" in atkSkills and atkHPGreaterEqual50Percent: atkCombatBuffs[ATK] += 6
    if "effieAtk" in defSkills and defHPGreaterEqual50Percent: defCombatBuffs[ATK] += 6

    if "effieFirstCombat" in atkSkills and attacker.unitCombatInitiates == 0:
        defCombatBuffs[ATK] -= 5
        defCombatBuffs[DEF] -= 5
        defBonusesNeutralized[ATK] = True
        defBonusesNeutralized[DEF] = True

    if "effieFirstCombat" in defSkills and defender.unitCombatInitiates == 0:
        atkCombatBuffs[ATK] -= 5
        atkCombatBuffs[DEF] -= 5
        atkBonusesNeutralized[ATK] = True
        atkBonusesNeutralized[DEF] = True

    # Soleil
    if "ladies, whats good" in atkSkills:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        atkr.spGainOnAtk += 1

    # Byleth

    if "up b bair" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)
    if "up b bair" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4, defCombatBuffs)

    if "up b side b" in atkSkills or "up b bair" in defSkills:
        atkr.disable_foe_fastcharge = True
        atkr.disable_foe_guard = True

        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    if "up b side b" in defSkills or "up b bair" in defSkills:
        defr.disable_foe_fastcharge = True
        defr.disable_foe_guard = True

        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True

    # Byleth - Creator Sword - Refined Eff

    if "HERE'S SOMETHING TO BELIEVE IN" in atkSkills:
        atkr.sp_pierce_DR = True
        if atkHPGreaterEqual25Percent:
            map(lambda x: x + 4, atkCombatBuffs)
            atkr.DR_first_hit_NSP.append(30)

    if "HERE'S SOMETHING TO BELIEVE IN" in defSkills:
        defr.sp_pierce_DR = True
        if defHPGreaterEqual25Percent:
            map(lambda x: x + 4, defCombatBuffs)
            defr.DR_first_hit_NSP.append(30)

    if "he lives" in atkSkills and atkHPGreaterEqual25Percent:
        defCombatBuffs[ATK] -= 6
        defCombatBuffs[DEF] -= 6
        defr.follow_up_denials -= 1

    if "he lives" in defSkills and defHPGreaterEqual25Percent:
        atkCombatBuffs[ATK] -= 6
        atkCombatBuffs[DEF] -= 6
        atkr.follow_up_denials -= 1

    # SU!Edelgard - Regal Sunshade - Base

    if "regalSunshade" in atkSkills and atkHPGreaterEqual25Percent:
        numFoesLeft = 0
        numFoesWithin3Columns3Rows = 0

        atkCombatBuffs[1] += 6
        atkCombatBuffs[3] += 6
        atkr.DR_first_hit_NSP.append(40)

        X = 1 if numFoesLeft <= 2 else (2 if 3 <= numFoesLeft <= 5 else 3)
        if X <= numFoesWithin3Columns3Rows:
            atkr.brave = True

    if "regalSunshade" in defSkills and defHPGreaterEqual25Percent:
        numFoesLeft = 0
        numFoesWithin3Columns3Rows = 0

        defCombatBuffs[1] += 6
        defCombatBuffs[3] += 6
        defr.DR_first_hit_NSP.append(40)

        X = 1 if numFoesLeft <= 2 else (2 if 3 <= numFoesLeft <= 5 else 3)
        if X <= numFoesWithin3Columns3Rows:
            defr.brave = True

    # Breaker Bow (SU!Petra)
    if "summerPetraBoost" in atkSkills and atkHPGreaterEqual25Percent:
        defPenaltiesNeutralized[SPD] = True
        defPenaltiesNeutralized[DEF] = True

        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

        num_ally_high_atk = 0
        num_ally_high_spd = 0

        tiles_within_3_col = attacker.attacking_tile.tilesWithinNCols(3)
        tiles_within_3_row = attacker.attacking_tile.tilesWithinNRows(3)
        tiles_within_3_row_or_column = list(set(tiles_within_3_col) | set(tiles_within_3_row))

        for tile in tiles_within_3_row_or_column:
            if tile.hero_on != None and tile.hero_on.isAllyOf(attacker):
                ally_atk = tile.hero_on.get_visible_stat(ATK)

                if ally_atk >= 55: num_ally_high_atk += 1

                ally_spd = tile.hero_on.get_visible_stat(SPD)

                if ally_spd >= 40: num_ally_high_spd += 1

        # X is capped for stats, but not cooldown gain. Currently bugged?
        # https://twitter.com/i/status/1809296394047701142
        X = num_ally_high_atk + num_ally_high_spd

        atkCombatBuffs[ATK] += 6 * min(X, 3)
        atkCombatBuffs[SPD] += 6 * min(X, 3)

        if attacker.getSpecialType() == "Offense":
            A = X + 1
            B = max(X + 1 - atkr.start_of_combat_special, 0)

            atkr.sp_charge_first += A
            atkr.sp_charge_FU += B

    if "summerPetraBoost" in defSkills and defHPGreaterEqual25Percent:
        atkPenaltiesNeutralized[SPD] = True
        atkPenaltiesNeutralized[DEF] = True

        defCombatBuffs = [x + 5 for x in defCombatBuffs]

        num_ally_high_atk = 0
        num_ally_high_spd = 0

        tiles_within_3_col = defender.tile.tilesWithinNCols(3)
        tiles_within_3_row = defender.tile.tilesWithinNRows(3)
        tiles_within_3_row_or_column = list(set(tiles_within_3_col) | set(tiles_within_3_row))

        for tile in tiles_within_3_row_or_column:
            if tile.hero_on is not None and tile.hero_on.isAllyOf(defender):
                ally_atk = tile.hero_on.get_visible_stat(ATK)

                if ally_atk >= 55: num_ally_high_atk += 1

                ally_spd = tile.hero_on.get_visible_stat(SPD)

                if ally_spd >= 40: num_ally_high_spd += 1

        X = min(num_ally_high_atk + num_ally_high_spd, 3)

        defCombatBuffs[ATK] += 6 * X
        defCombatBuffs[SPD] += 6 * X

        if defender.getSpecialType() == "Offense":
            A = X + 1
            B = max(X + 1 - defr.start_of_combat_special, 0)

            defr.sp_charge_first += A
            defr.sp_charge_FU += B

    # Flingster Spear (SP!Sylvain)
    if "sling a thing" in atkSkills and atkHPGreaterEqual25Percent:
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]
        atkr.prevent_self_FU_denial = True
        atkr.DR_first_strikes_NSP.append(40)
        if Status.SpecialCharge in attacker.statusPos:
            atkr.disable_foe_guard = True

    # Reginn - Lyngheiðr - Base
    if "reginn :)" in atkSkills:
        atkCombatBuffs[ATK] += 6
        atkCombatBuffs[SPD] += 6
        atkr.DR_first_hit_NSP.append(30)

    # Dvergr Wayfinder (Base) - AI!Reginn
    # ok yeah 3 rows or cols is becoming a more common condition
    if "reginnAccel" in atkSkills and atkHPGreaterEqual25Percent:
        boost = min(len(atkAllyWithin3RowsCols) * 3 + 5, 14)
        atkCombatBuffs = [x + boost for x in atkCombatBuffs]

        atkr.true_stat_damages.append((SPD, 20))
        atkr.DR_first_strikes_NSP.append(40)
        atkr.sp_pierce_DR = True

    if "reginnAccel" in defSkills and defHPGreaterEqual25Percent:
        boost = min(len(defAllyWithin3RowsCols) * 3 + 5, 14)
        defCombatBuffs = [x + boost for x in defCombatBuffs]

        defr.true_stat_damages.append((SPD, 20))
        defr.DR_first_strikes_NSP.append(40)
        defr.sp_pierce_DR = True

    if "reginnField_f" in atkSkills and turn <= 4:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[SPD] += 4
        if attacker.special is not None and attacker.special.type == "Offense":
            atkr.sp_charge_first += 1

    if "reginnField_f" in defSkills and turn <= 4:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[SPD] += 4
        if defender.special is not None and defender.special.type == "Offense":
            defr.sp_charge_first += 1

    # Catherine: Thunderbrand

    if "thundabrand" in atkSkills and defHPGreaterEqual50Percent:
        atkCombatBuffs[1] += 5
        atkCombatBuffs[2] += 5
        atkr.self_desperation = True
        atkDoSkillFU = True

    if "thundabrand" in defSkills and atkHPGreaterEqual50Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[1] += 5
        defDoSkillFU = True

    # Nemesis: Dark Creator S
    if "DCSIYKYK" in atkSkills:
        atkCombatBuffs[1] += 2 * atkNumAlliesHPGE90Percent
        atkCombatBuffs[3] += 2 * defNumAlliesHPGE90Percent

    if "TMSFalchion" in atkSkills:
        atkCombatBuffs[1] += min(3 + 2 * 00000, 7)  # 00000 - number of allies who have acted
        atkCombatBuffs[3] += min(3 + 2 * 00000, 7)

    if "TMSFalchion" in defSkills:
        atkCombatBuffs[1] += max(3, 7 - 000000 * 2)  # 000000 - number of foes who have acted
        atkCombatBuffs[3] += max(3, 7 - 000000 * 2)

    # 00000 and 000000 should be equal

    if "Garfield You Fat Cat" in atkSkills:
        atkCombatBuffs[1] += min(4 + 3 * 00000, 10)  # 00000 - number of allies who have acted
        atkCombatBuffs[2] += min(4 + 3 * 00000, 10)
        atkCombatBuffs[3] += min(4 + 3 * 00000, 10)
        atkCombatBuffs[4] += min(4 + 3 * 00000, 10)
        atkPostCombatHealing += 7

    if "Garfield You Fat Cat" in defSkills:
        defCombatBuffs[1] += max(4, 10 - 000000 * 3)  # 000000 - number of foes who have acted
        defCombatBuffs[2] += max(4, 10 - 000000 * 3)
        defCombatBuffs[3] += max(4, 10 - 000000 * 3)
        defCombatBuffs[4] += max(4, 10 - 000000 * 3)
        defPostCombatHealing += 7

    # Ituski - Mirage Falchion - Refined Eff
    # If unit initiates combat or is within 2 spaces of an ally:
    #  - grants Atk/Spd/Def/Res+4 to unit
    #  - unit makes a guaranteed follow-up attack
    #  - reduces damage from first attack during combat by 30%

    if "Nintendo has forgotten about Mario…" in atkSkills:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.follow_ups_skill += 1
        atkr.DR_first_hit_NSP.append(30)

    if "Nintendo has forgotten about Mario…" in defSkills and defAllyWithin2Spaces:
        map(lambda x: x + 4, defCombatBuffs)
        defr.follow_ups_skill += 1
        defr.DR_first_hit_NSP.append(30)

    if "BONDS OF FIIIIRE, CONNECT US" in atkSkills and atkHPGreaterEqual25Percent:
        titlesAmongAllies = 0
        atkCombatBuffs = list(map(lambda x: x + 5, atkCombatBuffs))
        defCombatBuffs[SPD] -= min(4 + titlesAmongAllies * 2, 12)
        defCombatBuffs[DEF] -= min(4 + titlesAmongAllies * 2, 12)

    if "BONDS OF FIIIIRE, CONNECT US" in defSkills and defHPGreaterEqual25Percent:
        titlesAmongAllies = 0
        map(lambda x: x + 5, defCombatBuffs)
        atkCombatBuffs[SPD] -= min(4 + titlesAmongAllies * 2, 12)
        atkCombatBuffs[DEF] -= min(4 + titlesAmongAllies * 2, 12)

    # Maritime Arts (SU!F!Alear)
    if "summerAlearBoost" in atkSkills and atkAllyWithin3Spaces:
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]

        ally_games_arr_3_spaces = []

        for ally in atkAllyWithin3Spaces:
            ally_games_arr_3_spaces.append(ally.game)

        num_dist_games = len(set(ally_games_arr_3_spaces))

        defCombatBuffs = [x - min(10, num_dist_games * 3 + 4) for x in defCombatBuffs]

        engaged_count = 0
        ally_games_arr_all = []

        for ally in atkAllAllies:
            ally_games_arr_all.append(ally.game)

            if ally.emblem != None:
                engaged_count += 1

        X = min(15, 5 * len(set(ally_games_arr_all)) + engaged_count)

        atkr.true_all_hits += X
        atkr.TDR_first_strikes += X

        atkr.disable_foe_guard = True

    if "summerAlearBoost" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs = [x + 5 for x in defCombatBuffs]

        ally_games_arr_3_spaces = []

        for ally in defAllyWithin3Spaces:
            ally_games_arr_3_spaces.append(ally.game)

        num_dist_games = len(set(ally_games_arr_3_spaces))

        atkCombatBuffs = [x - min(10, num_dist_games * 3 + 4) for x in atkCombatBuffs]

        engaged_count = 0
        ally_games_arr_all = []

        for ally in defAllAllies:
            ally_games_arr_all.append(ally.game)

            if ally.emblem != None:
                engaged_count += 1

        X = min(15, 5 * len(set(ally_games_arr_all)) + engaged_count)

        defr.true_all_hits += X
        defr.TDR_first_strikes += X

        defr.disable_foe_guard = True

    # Bond Blast (SU!Alear)
    if "summerAlearBonds" in atkSkills:
        # Special-piercing effect

        bonded_cond = False
        for ally in atkAllAllies:
            # Support partner present
            if ally.allySupport == attacker.intName:
                bonded_cond = True
            # Ally with bonded present
            if Status.Bonded in ally.statusPos:
                bonded_cond = True

        if bonded_cond:
            atkr.sp_pierce_DR = True

        # Special DR effect
        within_3_bonded_cond = False
        for ally in atkAllyWithin3Spaces:
            if ally.allySupport == attacker.intName or Status.Bonded in ally.statusPos:
                within_3_bonded_cond = True

        if within_3_bonded_cond:
            atkr.DR_sp_trigger_by_any_special_SP.append(40)

    # Enable for all support partners
    for ally in atkAllAllies:
        if "summerAlearBonds" in ally.getSkills() and attacker.allySupport == ally.intName:
            atkr.sp_pierce_DR = True

    # Enable for all allies with [Bonded]
    if Status.Bonded in attacker.statusPos:
        for ally in atkAllAllies:

            if "summerAlearBonds" in ally.getSkills():
                atkr.sp_pierce_DR = True

    if "summerAlearBonds" in defSkills:
        bonded_cond = False
        for ally in defAllAllies:
            # Support partner present
            if ally.allySupport == defender.intName:
                bonded_cond = True
            # Ally with bonded present
            if Status.Bonded in ally.statusPos:
                bonded_cond = True

        if bonded_cond:
            defr.sp_pierce_DR = True

        within_3_bonded_cond = False
        for ally in defAllyWithin3Spaces:
            if ally.allySupport == defender.intName or Status.Bonded in ally.statusPos:
                within_3_bonded_cond = True

        if within_3_bonded_cond:
            defr.DR_sp_trigger_by_any_special_SP.append(40)

    for ally in defAllAllies:
        if "summerAlearBonds" in ally.getSkills() and defender.allySupport == ally.intName:
            defr.sp_pierce_DR = True

    if Status.Bonded in defender.statusPos:
        for ally in defAllAllies:

            if "summerAlearBonds" in ally.getSkills():
                defr.sp_pierce_DR = True

    if "Mr. Fire Emblem" in atkSkills and atkHPGreaterEqual25Percent:
        titlesAmongAllies = 0
        atkr.brave = True
        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]
        defCombatBuffs = [x - min(titlesAmongAllies * 3 + 4, 10) for x in defCombatBuffs]
        atkr.DR_first_strikes_NSP.append(50)

    if "Mr. Fire Emblem" in defSkills and defHPGreaterEqual25Percent:
        titlesAmongAllies = 0
        defr.brave = True
        defCombatBuffs = [x + 5 for x in atkCombatBuffs]
        atkCombatBuffs = [x - min(titlesAmongAllies * 3 + 4, 10) for x in defCombatBuffs]
        defr.DR_first_strikes_NSP.append(50)

    if "Miracle O' Emblems" in atkSkills:
        if atkAllyWithin3Spaces:
            atkCombatBuffs = [x + 9 for x in atkCombatBuffs]
            atkr.DR_first_strikes_NSP.append(40)

    if "Miracle O' Emblems" in defSkills:
        ignoreRng = True
        if defAllyWithin3Spaces:
            defCombatBuffs = [x + 9 for x in defCombatBuffs]
            defr.DR_first_strikes_NSP.append(40)
        if defAllyWithin3Spaces >= 3:
            defr.pseudo_miracle = True

    if "hippity-hop" in atkSkills and atkAllyWithin3Spaces:
        Y = min(atkAllyWithin3Spaces * 3 + 5, 14)
        allies = attacker.attacking_tile.unitsWithinNSpaces(3, True)
        for x in allies:
            if x.getWeaponType() in ["RDragon", "BDragon", "GDragon", "CDragon"]:
                Y = 14
        atkCombatBuffs = [x + Y for x in atkCombatBuffs]
        atkr.disable_foe_fastcharge = True
        atkr.disable_foe_guard = True
        atkr.DR_first_strikes_NSP.append(min(atkHPCur, 60))

    if "hippity-hop" in defSkills and defAllyWithin3Spaces:
        Y = min(defAllyWithin3Spaces * 3 + 5, 14)
        allies = defender.tile.unitsWithinNSpaces(3, True)
        for x in allies:
            if x.getWeaponType() in ["RDragon", "BDragon", "GDragon", "CDragon"]:
                Y = 14
        defCombatBuffs = [x + Y for x in atkCombatBuffs]
        defr.disable_foe_fastcharge = True
        defr.disable_foe_guard = True
        defr.DR_first_strikes_NSP.append(min(defHPCur, 60))

    if "LOVE PROVIIIIDES, PROTECTS US" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        defr.spLossOnAtk -= 1
        defr.spLossWhenAtkd -= 1

    if "LOVE PROVIIIIDES, PROTECTS US" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 5, defCombatBuffs)
        atkr.spLossOnAtk -= 1
        atkr.spLossWhenAtkd -= 1

    if "sky-hopper" in atkSkills and atkHPGreaterEqual25Percent:
        charge_count = 0
        if is_in_sim:
            team = attacker.attacking_tile.unitsWithinNSpaces(n=20, lookForSameSide=True)
            for x in team:
                if Status.Charge in x.statusPos:
                    charge_count += 1

        atkCombatBuffs = [x + 5 for x in atkCombatBuffs]
        atkCombatBuffs[ATK] += min(charge_count * 4, 8)
        atkCombatBuffs[SPD] += min(charge_count * 4, 8)
        atkr.damage_reduction_reduction *= 0.5

    if "sky-hopper" in defSkills and defHPGreaterEqual25Percent:
        charge_count = 0
        if is_in_sim:
            team = defender.tile.unitsWithinNSpaces(n=20, lookForSameSide=True)
            for x in team:
                if Status.Charge in x.statusPos:
                    charge_count += 1

        defCombatBuffs = [x + 5 for x in defCombatBuffs]
        defCombatBuffs[ATK] += min(charge_count * 4, 8)
        defCombatBuffs[SPD] += min(charge_count * 4, 8)
        defr.damage_reduction_reduction *= 0.5

    if "nullBonuses" in atkSkills: defBonusesNeutralized = [True] * 5
    if "nullBonuses" in defSkills: atkBonusesNeutralized = [True] * 5

    if "nullCavBonuses" in atkSkills and defender.move == 1: defBonusesNeutralized = [True] * 5
    if "nullCavBonuses" in defSkills and attacker.move == 1: atkBonusesNeutralized = [True] * 5

    if "nullFlyBonuses" in atkSkills and defender.move == 2: defBonusesNeutralized = [True] * 5
    if "nullFlyBonuses" in defSkills and attacker.move == 2: atkBonusesNeutralized = [True] * 5

    if "nullMagicBonuses" in atkSkills and defender.wpnType in MAGICAL_WEAPONS: defBonusesNeutralized = [True] * 5
    if "nullMagicBonuses" in defSkills and attacker.wpnType in MAGICAL_WEAPONS: atkBonusesNeutralized = [True] * 5

    if "nullRangedBonuses" in atkSkills and defender.wpnType in RANGED_WEAPONS: defBonusesNeutralized = [True] * 5
    if "nullRangedBonuses" in defSkills and attacker.wpnType in RANGED_WEAPONS: atkBonusesNeutralized = [True] * 5

    if "bridal_shenanigans" in atkSkills and atkHPGreaterEqual25Percent:
        local_boost = 0
        valid_area = list(set(attacker.attacking_tile.tilesWithinNCols(3)) | set(attacker.attacking_tile.tilesWithinNRows(3)))

        for tile in valid_area:
            if tile.hero_on is not None and tile.hero_on is not attacker and tile.hero_on.side == attacker.side:
                local_boost += 1
        atkCombatBuffs = [x + min(local_boost * 3 + 5, 14) for x in atkCombatBuffs]

        atkr.prevent_self_FU_denial = True
        atkr.prevent_foe_FU = True

        atkr.true_stat_damages.append((SPD, 20))

        atkr.all_hits_heal += min(spaces_moved_by_atkr * 3, 12)

    if "bridal_shenanigans" in defSkills and defHPGreaterEqual25Percent:
        local_boost = 0
        valid_area = list(set(defender.tile.tilesWithinNCols(3)) | set(defender.tile.tilesWithinNRows(3)))

        for tile in valid_area:
            if tile.hero_on is not None and tile.hero_on is not defender and tile.hero_on.side == defender.side:
                local_boost += 1
        defCombatBuffs = [x + min(local_boost * 3 + 5, 14) for x in defCombatBuffs]

        defr.prevent_self_FU_denial = True
        defr.prevent_foe_FU = True

        defr.true_stat_damages.append((SPD, 20))

        defr.all_hits_heal += min(spaces_moved_by_atkr * 3, 12)

    if "and they were roommates" in atkSkills:
        atkCombatBuffs = [x + 4 for x in atkCombatBuffs]
        atkr.DR_all_hits_NSP.append(40)
        atkr.disable_foe_guard = True
        atkr.disable_foe_fastcharge = True

    if "and they were roommates" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs = [x + 4 for x in defCombatBuffs]
        defr.DR_all_hits_NSP.append(40)
        defr.disable_foe_guard = True
        defr.disable_foe_fastcharge = True


    if "laevBoost" in atkSkills and (atkHasBonus or atkHPGreaterEqual50Percent):
        atkCombatBuffs[1] += 5
        atkCombatBuffs[3] += 5

    if "laevPartner" in atkSkills and defHPGreaterEqual75Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[3] += 5

    if "niuBoost" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    if "niuBoost" in defSkills and defHPGreaterEqual25Percent:
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True
        map(lambda x: x + 4, defCombatBuffs)

    if "ICE UPON YOU" in atkSkills and defHasPenalty:
        atkr.follow_ups_skill += 1
        defr.follow_up_denials -= 1

    if "ICE UPON YOU" in defSkills and atkHasPenalty:
        defr.follow_ups_skill += 1
        atkr.follow_up_denials -= 1

    if "FREEZE NOW" in atkSkills and (atkHPGreaterEqual25Percent or defHasPenalty):
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5

    if "FREEZE NOW" in defSkills and (defHPGreaterEqual25Percent or atkHasPenalty):
        atkCombatBuffs[1] -= 5
        atkCombatBuffs[3] -= 5

    if "hikamiThreaten2" in atkSkills and atkHPGreaterEqual25Percent:
        defCombatBuffs[1] -= 4
        defCombatBuffs[2] -= 4
        defCombatBuffs[3] -= 4

    if "hikamiThreaten2" in defSkills and defHPGreaterEqual25Percent:
        atkCombatBuffs[1] -= 4
        atkCombatBuffs[2] -= 4
        atkCombatBuffs[3] -= 4

    if "https://youtu.be/eVTXPUF4Oz4?si=RkBGT1Gf1bGBxOPK" in atkSkills and atkAllyWithin3Spaces:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.follow_ups_skill += 1

    if "https://youtu.be/eVTXPUF4Oz4?si=RkBGT1Gf1bGBxOPK" in defSkills and defAllyWithin3Spaces:
        map(lambda x: x + 4, defCombatBuffs)
        defr.follow_ups_skill += 1

    if "https://www.youtube.com/watch?v=Gd9OhYroLN0&pp=ygUUY3Jhd2xpbmcgbGlua2luIHBhcms%3D" in atkSkills and atkAllyWithin4Spaces:
        map(lambda x: x + 6, atkCombatBuffs)
        atkr.follow_ups_skill += 1
        atkr.true_finish += 5
        atkr.finish_mid_combat_heal += 7

    if "https://www.youtube.com/watch?v=Gd9OhYroLN0&pp=ygUUY3Jhd2xpbmcgbGlua2luIHBhcms%3D" in defSkills and defAllyWithin4Spaces:
        map(lambda x: x + 6, defCombatBuffs)
        defr.follow_ups_skill += 1
        defr.true_finish += 5
        defr.finish_mid_combat_heal += 7

    if "ow" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 4, atkCombatBuffs)
        atkr.DR_first_hit_NSP.append(30)

    if "ow" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)
        defr.DR_first_hit_NSP.append(30)

    if "zzzzzzzzzzzzzzzz" in atkSkills and (defender.hasPenalty() or defHPGreaterEqual75Percent):
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5

    if "zzzzzzzzzzzzzzzz" in defSkills and (attacker.hasPenalty() or atkHPGreaterEqual75Percent):
        atkCombatBuffs[1] -= 5
        atkCombatBuffs[3] -= 5

    if "sleepy head" in atkSkills and atkHPGreaterEqual25Percent:
        defCombatBuffs[1] -= 5
        defCombatBuffs[3] -= 5
        atkr.follow_ups_skill += 1
        defPostCombatStatusesApplied[2].append(Status.Flash)

    if "sleepy head" in defSkills and defHPGreaterEqual25Percent:
        atkCombatBuffs[1] -= 5
        atkCombatBuffs[3] -= 5
        defr.follow_ups_skill += 1
        atkPostCombatStatusesApplied[2].append(Status.Flash)

    if "daydream_egg" in atkSkills and (defHPGreaterEqual75Percent or defHasPenalty):
        atkCombatBuffs[ATK] += 5
        atkCombatBuffs[DEF] += 5
        atkCombatBuffs[RES] += 5

    if "the_dose" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.capped_foe_burn_damage = max(atkr.capped_foe_burn_damage, 8)
        X = trunc(atkStats[DEF] * 0.2) + 6
        defCombatBuffs[ATK] -= X
        defCombatBuffs[DEF] -= X
        atkr.damage_reduction_reduction *= (1 - 0.5)
        atkr.true_all_hits += trunc(defStats[HP] * 0.3)
        atkr.TDR_dmg_taken_cap = 20
        if defender.getSpecialType() == "Offense":
            atkr.TDR_dmg_taken_extra_stacks += 1

        # reduce damage by Y
        # Y = damage dealt to foe, max 20
        # if hit by offensive special, reduce damage by 2Y

    if "Mario":
        "only Bros!"

    if "selfDmg" in atkSkills:  # damage to self after combat always
        atkPostCombatEffs[0].append(("damage", atkSkills["selfDmg"], "self", "one"))

    if "selfDmg" in defSkills:
        defPostCombatEffs[0].append(("damage", defSkills["selfDmg"], "self", "one"))

    # Devil Axe
    if "atkOnlySelfDmg" in atkSkills:  # damage to attacker after combat iff attacker had attacked
        atkPostCombatEffs[2].append(("damage", atkSkills["atkOnlySelfDmg"], "self", "one"))

    if "atkOnlySelfDmg" in defSkills:  # damage to attacker after combat iff attacker had attacked
        defPostCombatEffs[2].append(("damage", defSkills["atkOnlySelfDmg"], "self", "one"))

    # Pain
    if "atkOnlyOtherDmg" in atkSkills:  # damage to other unit after combat iff attacker had attacked
        atkPostCombatEffs[2].append(("damage", atkSkills["atkOnlyOtherDmg"], "foe", "one"))

    # Pain+
    if "painOther" in atkSkills:
        atkPostCombatEffs[2].append(("damage", atkSkills["painOther"], "foes_allies", "within_2_spaces_foe"))

    if "painOther" in defSkills:
        defPostCombatEffs[2].append(("damage", defSkills["painOther"], "foes_allies", "within_2_spaces_foe"))

    # Fear
    if "fear" in atkSkills: atkPostCombatEffs[2].append(("debuff_atk", atkSkills["fear"], "foe", "one"))
    if "fear" in defSkills: defPostCombatEffs[2].append(("debuff_atk", defSkills["fear"], "foe", "one"))

    # Fear+
    if "disperseFear" in atkSkills: atkPostCombatEffs[2].append(("debuff_atk", atkSkills["disperseFear"], "foes_allies", "within_2_spaces_foe"))
    if "disperseFear" in defSkills: defPostCombatEffs[2].append(("debuff_atk", defSkills["disperseFear"], "foes_allies", "within_2_spaces_foe"))

    # Slow
    if "slow" in atkSkills: atkPostCombatEffs[2].append(("debuff_spd", atkSkills["slow"], "foe", "one"))
    if "slow" in defSkills: defPostCombatEffs[2].append(("debuff_spd", defSkills["slow"], "foe", "one"))

    # Slow+
    if "disperseSlow" in atkSkills: atkPostCombatEffs[2].append(("debuff_spd", atkSkills["disperseSlow"], "foes_allies", "within_2_spaces_foe"))
    if "disperseSlow" in defSkills: defPostCombatEffs[2].append(("debuff_spd", defSkills["disperseSlow"], "foes_allies", "within_2_spaces_foe"))

    # Gravity
    if "gravity" in atkSkills: atkPostCombatEffs[2].append(("status", Status.Gravity, "foe", "one"))
    if "gravity" in defSkills: defPostCombatEffs[2].append(("status", Status.Gravity, "foe", "one"))

    if "disperseGravity" in atkSkills: atkPostCombatEffs[2].append(("status", Status.Gravity, "foe_and_foes_allies", "within_1_spaces_foe"))
    if "disperseGravity" in defSkills: defPostCombatEffs[2].append(("status", Status.Gravity, "foe_and_foes_allies", "within_1_spaces_foe"))

    # Panic
    if "panic" in atkSkills: atkPostCombatEffs[2].append(("status", Status.Panic, "foe", "one"))
    if "panic" in defSkills: defPostCombatEffs[2].append(("status", Status.Panic, "foe", "one"))

    if "dispersePanic" in atkSkills: atkPostCombatEffs[2].append(("status", Status.Panic, "foe_and_foes_allies", "within_2_spaces_foe"))
    if "dispersePanic" in defSkills: defPostCombatEffs[2].append(("status", Status.Panic, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Absorb+
    if "disperseAbsorb" in atkSkills:
        atkPostCombatEffs[2].append(("heal", atkSkills["disperseAbsorb"], "allies", "within_2_spaces_self"))
    if "disperseAbsorb" in defSkills:
        defPostCombatEffs[2].append(("heal", defSkills["disperseAbsorb"], "allies", "within_2_spaces_self"))

    # Flash/Candlelight
    if "flash" in atkSkills:
        atkPostCombatEffs[2].append(("status", Status.Flash, "foe", "one"))
    if "flash" in defSkills:
        defPostCombatEffs[2].append(("status", Status.Flash, "foe", "one"))

    if "disperseFlash" in atkSkills:
        atkPostCombatEffs[2].append(("status", Status.Flash, "foe_and_foes_allies", "within_2_spaces_foe"))
    if "disperseFlash" in defSkills:
        defPostCombatEffs[2].append(("status", Status.Flash, "foe_and_foes_allies", "within_2_spaces_foe"))

    # Triangle Adept
    if "triAdeptS" in atkSkills and atkSkills["triAdeptS"] > triAdept: triAdept = atkSkills["triAdeptS"]
    if "triAdeptW" in atkSkills and atkSkills["triAdeptW"] > triAdept: triAdept = atkSkills["triAdeptW"]

    if "triAdeptS" in defSkills and defSkills["triAdeptS"] > triAdept: triAdept = defSkills["triAdeptS"]
    if "triAdeptW" in defSkills and defSkills["triAdeptW"] > triAdept: triAdept = defSkills["triAdeptW"]

    #
    if "owlBoost" in atkSkills:
        atkCombatBuffs = [x + 2 * len(atkAdjacentToAlly) for x in atkCombatBuffs]

    if "owlBoost" in defSkills:
        defCombatBuffs = [x + 2 * len(defAdjacentToAlly) for x in defCombatBuffs]

    # Siegmund (+Eff) - Ephraim
    if "FollowUpEph" in atkSkills and atkHPCur / atkStats[0] > 0.90:
        atkr.follow_ups_skill += 1

    # Flame Siegmund (Base) - Ephraim, L!Ephraim
    if "flameEphFollowUp" in atkSkills and len(atkFoeWithin2Spaces) - 1 >= len(atkAllyWithin2Spaces):
        atkr.follow_ups_skill += 1

    if "flameEphFollowUp" in defSkills and len(defFoeWithin2Spaces) - 1 >= len(defAllyWithin2Spaces):
        defr.follow_ups_skill += 1

    # Flame Siegmund (Refine) - Ephraim, L!Ephraim
    if "refEphFU" in atkSkills:
        atkCombatBuffs[ATK] += 4
        atkCombatBuffs[DEF] += 4
        atkr.follow_ups_skill += 1

    if "refEphFU" in defSkills and not defAdjacentToAlly:
        defCombatBuffs[ATK] += 4
        defCombatBuffs[DEF] += 4
        defr.follow_ups_skill += 1

    if "ephRefineSuper" in atkSkills and atkHPGreaterEqual25Percent:
        defCombatBuffs[ATK] -= 5
        defCombatBuffs[DEF] -= 5
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

    if "ephRefineSuper" in defSkills and defHPGreaterEqual25Percent:
        atkCombatBuffs[ATK] -= 5
        atkCombatBuffs[DEF] -= 5
        defr.spGainOnAtk += 1
        defr.spGainWhenAtkd += 1

    if "BraveAW" in atkSkills or "BraveAS" in atkSkills or "BraveBW" in atkSkills:
        atkr.brave = True

    if "swordBreak" in atkSkills and defender.wpnType == "Sword" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["swordBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "lanceBreak" in atkSkills and defender.wpnType == "Lance" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["lanceBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "axeBreak" in atkSkills and defender.wpnType == "Axe" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["axeBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "rtomeBreak" in atkSkills and defender.wpnType == "RTome" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["rtomeBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "btomeBreak" in atkSkills and defender.wpnType == "BTome" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["btomeBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "gtomeBreak" in atkSkills and defender.wpnType == "GTome" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["gtomeBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "cBowBreak" in atkSkills and defender.wpnType == "CBow" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["cBowBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1
    if "cDaggerBreak" in atkSkills and defender.wpnType == "CDagger" and atkHPCur / atkStats[0] > 1.1 - (
            atkSkills["cDaggerBreak"] * 0.2): atkr.follow_ups_skill += 1; defr.follow_up_denials -= 1

    if "cDaggerBreakW" in atkSkills and defender.wpnType == "CDagger":
        atkr.follow_ups_skill += 1;
        defr.follow_up_denials -= 1
    if "cDaggerBreakW" in defSkills and attacker.wpnType == "CDagger":
        defr.follow_ups_skill += 1;
        atkr.follow_up_denials -= 1

    if "dullRangedW" in atkSkills and defender.wpnType in RANGED_WEAPONS: defBonusesNeutralized = [True] * 5
    if "dullRangedW" in defSkills and attacker.wpnType in RANGED_WEAPONS: atkBonusesNeutralized = [True] * 5

    if "dullCloseW" in atkSkills and defender.wpnType in MELEE_WEAPONS: defBonusesNeutralized = [True] * 5
    if "dullCloseW" in defSkills and attacker.wpnType in MELEE_WEAPONS: atkBonusesNeutralized = [True] * 5

    if "spDamageAdd" in atkSkills:
        atkr.true_sp += atkSkills["spDamageAdd"]

    if "firesweep" in atkSkills or "firesweep" in defSkills:
        cannotCounter = True

    if Status.Flash in defender.statusNeg:
        cannotCounter = True

    # Iron Dagger/Steel Dagger/Silver Dagger(+)
    if "dagger_single" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["dagger_single"], "foe", "one"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["dagger_single"], "foe", "one"))

    if "dagger_single" in defSkills:
        defPostCombatEffs[2].append(("debuff_def", defSkills["dagger_single"], "foe", "one"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["dagger_single"], "foe", "one"))



    # Dagger 7 (or other magnitudes)
    if "dagger" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["dagger"], "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["dagger"], "foe_and_foes_allies", "within_2_spaces_foe"))

    if "dagger" in defSkills:
        defPostCombatEffs[2].append(("debuff_def", defSkills["dagger"], "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["dagger"], "foe_and_foes_allies", "within_2_spaces_foe"))

    # Rogue Dagger

    if "rogue_boost_single" in atkSkills:
        atkPostCombatEffs[2].append(("buff_def", atkSkills["rogue_boost_single"], "self", "one"))
        atkPostCombatEffs[2].append(("buff_res", atkSkills["rogue_boost_single"], "self", "one"))

    if "rogue_boost_single" in defSkills:
        defPostCombatEffs[2].append(("buff_def", defSkills["rogue_boost_single"], "self", "one"))
        defPostCombatEffs[2].append(("buff_res", defSkills["rogue_boost_single"], "self", "one"))

    if "rogue_boost" in atkSkills:
        atkPostCombatEffs[2].append(("buff_def", atkSkills["rogue_boost"], "self_and_allies", "within_2_spaces_self"))
        atkPostCombatEffs[2].append(("buff_res", atkSkills["rogue_boost"], "self_and_allies", "within_2_spaces_self"))

    if "rogue_boost" in defSkills:
        defPostCombatEffs[2].append(("buff_def", defSkills["rogue_boost"], "self_and_allies", "within_2_spaces_self"))
        defPostCombatEffs[2].append(("buff_res", defSkills["rogue_boost"], "self_and_allies", "within_2_spaces_self"))

    # Poison Dagger

    if "poison_dagger" in atkSkills and defender.move == 0:
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["poison_dagger"], "foe", "one"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["poison_dagger"], "foe", "one"))

    if "poison_dagger" in defSkills and attacker.move == 0:
        defPostCombatEffs[2].append(("debuff_def", defSkills["poison_dagger"], "foe", "one"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["poison_dagger"], "foe", "one"))

    # Smoke Dagger
    if "smoke_others" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["smoke_others"], "foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["smoke_others"], "foes_allies", "within_2_spaces_foe"))

    if "smoke_others" in defSkills:
        defPostCombatEffs[2].append(("debuff_def", defSkills["smoke_others"], "foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["smoke_others"], "foes_allies", "within_2_spaces_foe"))

    if "spectrum_smoke" in atkSkills:
        atkPostCombatEffs[2].append(("debuff_atk", atkSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_spd", atkSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))

    if "spectrum_smoke" in defSkills:
        defPostCombatEffs[2].append(("debuff_atk", defSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_spd", defSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_def", defSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["spectrum_smoke"], "foe_and_foes_allies", "within_2_spaces_foe"))

    # Kitty Paddle
    if "dagger_magic" in atkSkills and defender.wpnType in TOME_WEAPONS:
        atkPostCombatEffs[2].append(("debuff_def", atkSkills["dagger_magic"], "foe_and_foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[2].append(("debuff_res", atkSkills["dagger_magic"], "foe_and_foes_allies", "within_2_spaces_foe"))

    if "dagger_magic" in defSkills and attacker.wpnType in TOME_WEAPONS:
        defPostCombatEffs[2].append(("debuff_def", defSkills["dagger_magic"], "foe_and_foes_allies", "within_2_spaces_foe"))
        defPostCombatEffs[2].append(("debuff_res", defSkills["dagger_magic"], "foe_and_foes_allies", "within_2_spaces_foe"))

    seals = [("seal_atk", "sealAtk"), ("seal_spd", "sealSpd"), ("seal_def", "sealDef"), ("seal_res", "sealRes"),
             ("seal_atk", "sealAtkSe"), ("seal_spd", "sealSpdSe"), ("seal_def", "sealDefSe"), ("seal_res", "sealResSe")]

    for seal_name, skill_key in seals:
        if skill_key in atkSkills: atkPostCombatEffs[0].append((seal_name, atkSkills[skill_key], "foe", "one"))
        if skill_key in defSkills: defPostCombatEffs[0].append((seal_name, defSkills[skill_key], "foe", "one"))

    if "hardyBearing" in atkSkills:
        atkr.hardy_bearing = True
        defr.hardy_bearing = atkHPCur / atkStats[0] >= 1.5 - (atkSkills["hardyBearing"] * .5)

    if "hardyBearing" in defSkills:
        defr.hardy_bearing = True
        atkr.hardy_bearing = defHPCur / defStats[0] >= 1.5 - (defSkills["hardyBearing"] * .5)

    if "cancelTA" in atkSkills:
        atkCA = atkSkills["cancelTA"]

    if "cancelTA" in defSkills:
        defCA = defSkills["cancelTA"]

    # Wrathful Staff
    if "wrathful" in atkSkills and atkHPCur/atkStats[HP] >= 1.5 - 0.5 * atkSkills["wrathful"]:
        atkr.wrathful_staff = True

    if "wrathful" in defSkills and defHPCur/defStats[HP] >= 1.5 - 0.5 * defSkills["wrathful"]:
        defr.wrathful_staff = True

    # Dazzling Staff
    if "dazzling" in atkSkills and atkHPCur/atkStats[HP] >= 1.5 - 0.5 * atkSkills["dazzling"]:
        cannotCounter = True

    # FIGHTER SKILLS
    if "wary_fighter" in atkSkills and atkHPCur/atkStats[HP] >= 1.1 - 0.2 * atkSkills["wary_fighter"]:
        atkr.follow_up_denials -= 1
        defr.follow_up_denials -= 1

    if "wary_fighter" in defSkills and defHPCur/defStats[HP] >= 1.1 - 0.2 * defSkills["wary_fighter"]:
        atkr.follow_up_denials -= 1
        defr.follow_up_denials -= 1

    # idk what he's doing here
    if "NO MORE LOSSES" in defSkills and defAllyWithin3Spaces and defHPGreaterEqual50Percent:
        defr.pseudo_miracle = True

    # Special damage tags
    atkSpEffects = {}
    for key in atkSkills:
        if key == "healSelf": atkSpEffects.update({"healSelf": atkSkills[key]})
        if key == "defReduce": atkSpEffects.update({"defReduce": atkSkills[key]})
        if key == "dmgBoost": atkSpEffects.update({"dmgBoost": atkSkills[key]})
        if key == "atkBoostSp": atkSpEffects.update({"atkBoost": atkSkills[key]})
        if key == "spdBoostSp": atkSpEffects.update({"spdBoost": atkSkills[key]})
        if key == "defBoostSp": atkSpEffects.update({"defBoost": atkSkills[key]})
        if key == "resBoostSp": atkSpEffects.update({"resBoost": atkSkills[key]})
        if key == "closeShield": atkSpEffects.update({"closeShield": atkSkills[key]})
        if key == "distantShield": atkSpEffects.update({"distantShield": atkSkills[key]})
        if key == "miracleSP": atkSpEffects.update({"distantShield": atkSkills[key]})
        if key == "numFoeAtkBoostSp": atkSpEffects.update({"NumAtkBoost": atkSkills[key]})
        if key == "atkBoostSpArmor": atkSpEffects.update({"atkBoostArmor": atkSkills[key]})
        if key == "wrathW": atkSpEffects.update({"wrathBoostW": atkSkills[key]})
        if key == "wrathSk": atkSpEffects.update({"wrathBoostSk": atkSkills[key]})
        if key == "retaliatoryBoost": atkSpEffects.update({"retaliatoryBoost": atkSkills[key]})

    defSpEffects = {}
    for key in defSkills:
        if key == "healSelf": defSpEffects.update({"healSelf": defSkills[key]})
        if key == "defReduce": defSpEffects.update({"defReduce": defSkills[key]})
        if key == "dmgBoost": defSpEffects.update({"dmgBoost": defSkills[key]})
        if key == "atkBoostSp": defSpEffects.update({"atkBoost": defSkills[key]})
        if key == "spdBoostSp": defSpEffects.update({"spdBoost": defSkills[key]})
        if key == "defBoostSp": defSpEffects.update({"defBoost": defSkills[key]})
        if key == "resBoostSp": defSpEffects.update({"resBoost": defSkills[key]})
        if key == "closeShield": defSpEffects.update({"closeShield": defSkills[key]})
        if key == "distantShield": defSpEffects.update({"distantShield": defSkills[key]})
        if key == "miracleSP": defSpEffects.update({"miracleSP": defSkills[key]})
        if key == "numFoeAtkBoostSp": defSpEffects.update({"NumAtkBoost": defSkills[key]})
        if key == "atkBoostSpArmor": defSpEffects.update({"atkBoostArmor": defSkills[key]})
        if key == "wrathW": defSpEffects.update({"wrathBoostW": defSkills[key]})
        if key == "wrathSk": atkSpEffects.update({"wrathBoostSk": atkSkills[key]})
        if key == "retaliatoryBoost": defSpEffects.update({"retaliatoryBoost": defSkills[key]})

    # COMMON A SKILLS, ENEMY PHASE ONLY

    if "atkStance" in defSkills: defCombatBuffs[1] += defSkills["atkStance"] * 2
    if "spdStance" in defSkills: defCombatBuffs[2] += defSkills["spdStance"] * 2
    if "defStance" in defSkills: defCombatBuffs[3] += defSkills["defStance"] * 2
    if "resStance" in defSkills: defCombatBuffs[4] += defSkills["resStance"] * 2

    if "breathCharge" in defSkills:
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

    # Close/Distant Def.
    if "closeDef" in defSkills and attacker.wpnType in MELEE_WEAPONS:
        defCombatBuffs[DEF] += defSkills["closeDef"] * 2
        defCombatBuffs[RES] += defSkills["closeDef"] * 2

    if "distDef" in defSkills and attacker.wpnType in RANGED_WEAPONS:
        defCombatBuffs[DEF] += defSkills["distDef"] * 2
        defCombatBuffs[RES] += defSkills["distDef"] * 2

    if "ILOVEBONUSES" in defSkills and defHPGreaterEqual50Percent or atkHasBonus:  # UPDATE WITH DEF SKILLS
        map(lambda x: x + 4, defCombatBuffs)

    if ("belovedZofia" in defSkills and defHPEqual100Percent) or "belovedZofia2" in defSkills:
        map(lambda x: x + 4, defCombatBuffs)
        defRecoilDmg += 4

    if "ALMMM" in defSkills and (not atkHPEqual100Percent or not defHPEqual100Percent):
        map(lambda x: x + 4, defCombatBuffs)
        defr.all_hits_heal += 7

    if "A man has fallen into the river in LEGO City!" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 4, defCombatBuffs)
        defPostCombatHealing += 7

    if "leafSword" in defSkills and atkHPEqual100Percent:
        defCombatBuffs[2] += 4
        defCombatBuffs[3] += 4

    if "bigHands" in defSkills and atkHPGreaterEqual50Percent:
        defCombatBuffs[1] += 5
        atkCombatBuffs[1] -= 5

    if "vassalBlade" in defSkills and defAllyWithin2Spaces:
        defCombatBuffs[2] += 5

    if "Barry B. Benson" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True

    if "stormSieglinde" in defSkills and defFoeWithin2Spaces >= defAllyWithin2Spaces:
        defCombatBuffs[3] += 3
        defCombatBuffs[4] += 3
        defr.spGainOnAtk += 1



    if "Sacred Stones Strike!" in defSkills and defAllyWithin3Spaces:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5

    if "amatsuDC" in defSkills and defHPGreaterEqual50Percent:
        ignoreRng = True

    if "Toaster" in defSkills and not defAdjacentToAlly:
        defCombatBuffs[1] += 5
        defCombatBuffs[2] += 5
        defPenaltiesNeutralized = [True] * 5

    if "laevBoost" in defSkills and (defHasBonus or atkHPGreaterEqual50Percent):
        defCombatBuffs[1] += 5
        defCombatBuffs[3] += 5

    if "laevPartner" in defSkills and atkHPGreaterEqual75Percent:
        defCombatBuffs[1] += 5
        defCombatBuffs[3] += 5

    if "cCounter" in defSkills or "dCounter" in defSkills: ignoreRng = True

    if "closePhysCounter" in defSkills and attacker.wpnType in PHYSICAL_WEAPONS:
        ignoreRng = True

    if "BraveDW" in defSkills or "BraveBW" in defSkills:
        defr.brave = True

    if "atkOnlySelfDmg" in defSkills: defRecoilDmg += defSkills["atkOnlySelfDmg"]
    if "atkOnlyOtherDmg" in defSkills:
        defPostCombatEffs[2].append(("damage", defSkills["atkOnlyOtherDmg"], "foe", "one"))

    if "QRW" in defSkills and defHPCur / defStats[0] >= 1.0 - (defSkills["QRW"] * 0.1): defr.follow_ups_skill += 1
    if "QRS" in defSkills and defHPCur / defStats[0] >= 1.0 - (defSkills["QRS"] * 0.1): defr.follow_ups_skill += 1
    if "QRSe" in defSkills and defHPCur / defStats[0] >= 1.0 - (defSkills["QRSe"] * 0.1): defr.follow_ups_skill += 1


    # Desperation
    if "desperationW" in atkSkills and atkHPCur / atkStats[0] <= 0.25 * atkSkills["desperationW"]:
        atkr.self_desperation = True

    if "desperationSk" in atkSkills and atkHPCur / atkStats[0] <= 0.25 * atkSkills["desperationSk"]:
        atkr.self_desperation = True

    if "desperationSe" in atkSkills and atkHPCur / atkStats[0] <= 0.25 * atkSkills["desperationSe"]:
        atkr.self_desperation = True

    if "stupidDesp" in atkSkills:
        defCombatBuffs[ATK] -= 5
        if (not atkHPEqual100Percent or spaces_moved_by_atkr >= 2):
            atkr.self_desperation = True

    if "stupidDesp" in defSkills:
        atkCombatBuffs[ATK] -= 5

    if "nullC4" in atkSkills:
        defCombatBuffs[ATK] -= 4
        defCombatBuffs[SPD] -= 4
        atkr.DR_first_hit_NSP.append(30)

    if "nullC4" in defSkills:
        disableCannotCounter = True
        atkCombatBuffs[ATK] -= 4
        atkCombatBuffs[DEF] -= 4
        defr.DR_first_hit_NSP.append(30)

    if "swordBreak" in defSkills and attacker.wpnType == "Sword": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "lanceBreak" in defSkills and attacker.wpnType == "Lance": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "axeBreak" in defSkills and attacker.wpnType == "Axe": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "rtomeBreak" in defSkills and attacker.wpnType == "RTome": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "btomeBreak" in defSkills and attacker.wpnType == "BTome": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "gtomeBreak" in defSkills and attacker.wpnType == "GTome": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "cBowBreak" in defSkills and attacker.wpnType == "CBow": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1
    if "cDaggerBreak" in defSkills and attacker.wpnType == "CDagger": defr.follow_ups_skill += 1; atkr.follow_up_denials -= 1

    if "spDamageAdd" in defSkills:
        defr.true_sp += defSkills["spDamageAdd"]

    if "vantage" in defSkills and defHPCur / defStats[0] <= 0.75 - (0.25 * (3 - defSkills["vantage"])):
        defr.vantage = True

    if Status.Vantage in defender.statusNeg:
        defr.vantage = True

    # 5 damage reduction from Shield Pulse, etc.
    if "trueDefsvSp" in atkSkills:
        atkr.TDR_on_def_sp += 5

    if "trueDefsvSp" in defSkills:
        defr.TDR_on_def_sp += 5

    # PART 1
    if "laguz_friend" in atkSkills:
        skill_lvl = atkSkills["laguz_friend"]
        if skill_lvl == 4: defStats[ATK] -= 5

        if attacker.getMaxSpecialCooldown() >= 3 and attacker.getSpecialType() == "Offense" or attacker.getSpecialType() == "Defense":
            defr.damage_reduction_reduction *= 0.5
            atkr.sp_charge_foe_first += 2

    if "laguz_friend" in defSkills:
        skill_lvl = defSkills["laguz_friend"]
        if skill_lvl == 4: atkStats[ATK] -= 5

        if defender.getMaxSpecialCooldown() >= 3 and defender.getSpecialType() == "Offense" or defender.getSpecialType() == "Defense":
            atkr.damage_reduction_reduction *= 0.5
            defr.sp_charge_foe_first += 2

    if "resonance" in atkSkills:
        X = max(trunc(0.2 * (atkStats[HP] - 20)), 0)

        atkr.self_burn_damage += X

        defCombatBuffs[SPD] -= 4
        defCombatBuffs[RES] -= 4

        atkr.resonance = True

    if "resonance" in defSkills:
        X = max(trunc(0.2 * (defStats[HP] - 20)), 0)

        defr.self_burn_damage += X

        atkCombatBuffs[SPD] -= 4
        atkCombatBuffs[RES] -= 4

        defr.resonance = True


    # LITERALLY EVERYTHING THAT USES EXACT BONUS AND PENALTY VALUES GOES HERE

    # exact value of buffs after buff neutralization
    atkNeutrBuffsStats = [0, 0, 0, 0, 0]
    defNeutrBuffsStats = [0, 0, 0, 0, 0]

    # exact value of buffs after debuff neutralization
    atkNeutrDebuffsStats = [0, 0, 0, 0, 0]
    defNeutrDebuffsStats = [0, 0, 0, 0, 0]

    # Values of each buff/debuff after neutralization

    for i in range(5):
        if AtkPanicFactor == 1:
            atkNeutrBuffsStats[i] += attacker.buffs[i] * int(not atkBonusesNeutralized[i])
        elif AtkPanicFactor == -1:
            atkNeutrDebuffsStats[i] += attacker.buffs[i] * -1 * int(not atkPenaltiesNeutralized[i])

        if DefPanicFactor == 1:
            defNeutrBuffsStats[i] += defender.buffs[i] * int(not defBonusesNeutralized[i])
        elif DefPanicFactor == -1:
            defNeutrDebuffsStats[i] += defender.buffs[i] * -1 * int(not defPenaltiesNeutralized[i])

        atkNeutrDebuffsStats[i] += attacker.debuffs[i] * int(not atkPenaltiesNeutralized[i])
        defNeutrDebuffsStats[i] += defender.debuffs[i] * int(not defPenaltiesNeutralized[i])

    # I think dominance does extra damage, right? well I'm not using this rn so until I do, uhhhhh
    if "dominance" in atkSkills and AtkPanicFactor == 1:
        for i in range(1, 5): atkCombatBuffs[ATK] += atkNeutrBuffsStats[i]

    if "dominance" in defSkills and DefPanicFactor == 1:
        for i in range(1, 5): defCombatBuffs[ATK] += defNeutrBuffsStats[i]

    # Blade Tomes
    if "bladeTome" in atkSkills:
        for i in range(1, 5): atkCombatBuffs[ATK] += atkNeutrBuffsStats[i]
    if "bladeTome" in defSkills:
        for i in range(1, 5): defCombatBuffs[ATK] += defNeutrBuffsStats[i]

    # Rowdy Sword (Refine Eff) - Luke
    if "BEAST MODE BABY" in atkSkills and sum(defNeutrBuffsStats) == 0:
        atkCombatBuffs[ATK] += 6
        atkCombatBuffs[DEF] += 6

    if "BEAST MODE BABY" in defSkills and sum(atkNeutrBuffsStats) == 0:
        defCombatBuffs[ATK] += 6
        defCombatBuffs[DEF] += 6

    # Sneering Axe (Base) - Legion
    if "legionBonusPunisher" in atkSkills:
        for i in range(1, 5): defCombatBuffs[i] -= defNeutrBuffsStats[i] * 2

    if "legionBonusPunisher" in defSkills:
        for i in range(1, 5): atkCombatBuffs[i] -= atkNeutrBuffsStats[i] * 2

    # Spy's Dagger (Refine Eff) - Matthew, + others reuse this effect
    if "mthwDominance" in atkSkills:
        for i in range(1, 5): atkCombatBuffs[ATK] += -1 * defNeutrDebuffsStats[i]
    if "mthwDominance" in defSkills:
        for i in range(1, 5): defCombatBuffs[ATK] += -1 * atkNeutrDebuffsStats[i]

    # Grado Poleax (Refine Eff) - Amelia
    if "ameliaBoost" in atkSkills and (sum(atkNeutrBuffsStats) or Status.MobilityUp in attacker.statusPos):
        atkCombatBuffs[SPD] += 6
        atkCombatBuffs[DEF] += 6

    if "ameliaBoost" in defSkills and (sum(defNeutrBuffsStats) or Status.MobilityUp in defender.statusPos):
        defCombatBuffs[SPD] += 6
        defCombatBuffs[DEF] += 6

    # Saizo's Star (Refine Eff) - Saizo
    if "saizoBoost" in atkSkills:
        for i in range(1, 5): atkCombatBuffs[i] += -1 * defNeutrDebuffsStats[i]
    if "saizoBoost" in defSkills:
        for i in range(1, 5): defCombatBuffs[i] += -1 * atkNeutrDebuffsStats[i]

    # oops! all bonus doubler
    if "bonusDoublerW" in atkSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] += math.trunc(
                max(AtkPanicFactor * attacker.buffs[i] * atkBonusesNeutralized[i], 0) * 0.25 * atkSkills[
                    "bonusDoublerW"] + 0.25)

    if "bonusDoublerSk" in atkSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] += math.trunc(
                max(AtkPanicFactor * attacker.buffs[i] * atkBonusesNeutralized[i], 0) * 0.25 * atkSkills[
                    "bonusDoublerSk"] + 0.25)

    if "bonusDoublerSe" in atkSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] += math.trunc(
                max(AtkPanicFactor * attacker.buffs[i] * atkBonusesNeutralized[i], 0) * 0.25 * atkSkills[
                    "bonusDoublerSe"] + 0.25)

    if Status.BonusDoubler in attacker.statusPos:
        for i in range(1, 5):
            atkCombatBuffs[i] += max(AtkPanicFactor * attacker.buffs[i] * atkBonusesNeutralized[i], 0)

    if "bonusDoublerW" in defSkills:
        for i in range(1, 5):
            defCombatBuffs[i] += math.trunc(
                max(DefPanicFactor * defender.buffs[i] * defBonusesNeutralized[i], 0) * 0.25 * defSkills[
                    "bonusDoublerW"] + 0.25)

    if "bonusDoublerSk" in defSkills:
        for i in range(1, 5):
            defCombatBuffs[i] += math.trunc(
                max(DefPanicFactor * defender.buffs[i] * defBonusesNeutralized[i], 0) * 0.25 * defSkills[
                    "bonusDoublerSk"] + 0.25)

    if "bonusDoublerSe" in defSkills:
        for i in range(1, 5):
            defCombatBuffs[i] += math.trunc(
                max(DefPanicFactor * defender.buffs[i] * defBonusesNeutralized[i], 0) * 0.25 * defSkills[
                    "bonusDoublerSe"] + 0.25)

    if Status.BonusDoubler in defender.statusPos:
        for i in range(1, 5):
            defCombatBuffs[i] += max(DefPanicFactor * defender.buffs[i] * defBonusesNeutralized[i], 0)

    # Warrior's Sword (Base) - Holst
    if "I think that enemy got THE POINT" in atkSkills and atkHPGreaterEqual25Percent:
        map(lambda x: x + 5, atkCombatBuffs)
        for i in range(1, 5): atkCombatBuffs[i] += max(attacker.buffs[i] * AtkPanicFactor * atkBonusesNeutralized[i], 0)
        defr.spLossWhenAtkd -= 1
        defr.spLossOnAtk -= 1

    if "I think that enemy got THE POINT" in defSkills and defHPGreaterEqual25Percent:
        map(lambda x: x + 5, defCombatBuffs)
        for i in range(1, 5): defCombatBuffs[i] += max(defender.buffs[i] * DefPanicFactor * defBonusesNeutralized[i], 0)
        atkr.spLossWhenAtkd -= 1
        atkr.spLossOnAtk -= 1

    if "gregorSword!" in atkSkills:
        atkr.DR_first_hit_NSP.append(40)
        for i in range(1, 5):
            defCombatBuffs -= 5 + max(defender.debuffs[i] * defPenaltiesNeutralized[i] * -1, 0) + max(
                defender.buffs[i] * DefPanicFactor * defPenaltiesNeutralized[i] * -1, 0)

    if "gregorSword!" in defSkills and defAllyWithin2Spaces:
        defr.DR_first_hit_NSP.append(40)
        for i in range(1, 5):
            atkCombatBuffs -= 5 + max(attacker.debuffs[i] * atkPenaltiesNeutralized[i] * -1, 0) + max(
                attacker.buffs[i] * AtkPanicFactor * atkPenaltiesNeutralized[i] * -1, 0)

    if "GiveMeYourBonuses" in atkSkills and DefPanicFactor == 1:
        totalBonuses = 0
        for i in range(1, 5): totalBonuses += defender.buffs[i] * defBonusesNeutralized[i]
        map(lambda x: x + math.trunc(totalBonuses / 2), atkCombatBuffs)

    if "ILoveBonusesAndWomenAndI'mAllOutOfBonuses" in atkSkills:
        tempAtkBonuses = 0
        tempDefBonuses = 0
        if AtkPanicFactor == 1:
            for i in range(1, 5): tempAtkBonuses += attacker.buffs[i] + atkBonusesNeutralized[i]
        if DefPanicFactor == 1:
            for i in range(1, 5): tempDefBonuses += defender.buffs[i] + defBonusesNeutralized[i]
        tempTotalBonuses = min(10, math.trunc((tempAtkBonuses + tempDefBonuses) * 0.4))
        map(lambda x: x + tempTotalBonuses, atkCombatBuffs)

    if "GiveMeYourBonuses" in defSkills and AtkPanicFactor == 1:
        totalBonuses = 0
        for i in range(1, 5): totalBonuses += attacker.buffs[i] * atkBonusesNeutralized[i]
        map(lambda x: x + math.trunc(totalBonuses * 0.5), defCombatBuffs)

    if "ILoveBonusesAndWomenAndI'mAllOutOfBonuses" in defSkills:
        tempAtkBonuses = 0
        tempDefBonuses = 0
        if AtkPanicFactor == 1:
            for i in range(1, 5): tempAtkBonuses += attacker.buffs[i] * atkBonusesNeutralized[i]
        if DefPanicFactor == 1:
            for i in range(1, 5): tempDefBonuses += defender.buffs[i] * defBonusesNeutralized[i]
        tempTotalBonuses = min(10, math.trunc((tempAtkBonuses + tempDefBonuses) * 0.4))
        map(lambda x: x + tempTotalBonuses, defCombatBuffs)

    if "beeeg debuff" in atkSkills:
        defCombatBuffs[1] -= 4
        defCombatBuffs[2] -= 4
        defCombatBuffs[3] -= 4
        for i in range(1, 5):
            atkCombatBuffs[ATK] += min(defender.debuffs[i] * defPenaltiesNeutralized[i], 0) * -1 + min(
                defender.buffs[i] * DefPanicFactor * defPenaltiesNeutralized[i], 0) * -1

    if "beeeg debuff" in defSkills and defAllyWithin2Spaces:
        atkCombatBuffs[1] -= 4
        atkCombatBuffs[2] -= 4
        atkCombatBuffs[3] -= 4
        for i in range(1, 5):
            defCombatBuffs[ATK] += min(attacker.debuffs[i] * atkPenaltiesNeutralized[i], 0) * -1 + min(
                attacker.buffs[i] * AtkPanicFactor * atkPenaltiesNeutralized[i], 0) * -1

    if "spectrumUnityMarth" in atkSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] += 4 + (
                        (min(attacker.debuffs[i], 0) * -2) + (min(AtkPanicFactor * attacker.buffs[i], 0) * -2)) * (
                                     not atkPenaltiesNeutralized[i])

    if "spectrumUnityMarth" in defSkills and defAllyWithin2Spaces:
        for i in range(1, 5):
            defCombatBuffs[i] += 4 + (
                        (min(defender.debuffs[i], 0) * -2) + (min(DefPanicFactor * defender.buffs[i], 0) * -2)) * (
                                     not defPenaltiesNeutralized[i])

    if "penaltyReverse" in atkSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] += ((min(attacker.debuffs[i], 0) * -2) + (
                        min(AtkPanicFactor * attacker.buffs[i], 0) * -2)) * (not atkPenaltiesNeutralized[i])

    if "penaltyReverse" in defSkills:
        for i in range(1, 5):
            defCombatBuffs[i] += ((min(defender.debuffs[i], 0) * -2) + (
                        min(DefPanicFactor * defender.buffs[i], 0) * -2)) * (not defPenaltiesNeutralized[i])

    # double check this
    if "Minecraft Gaming" in atkSkills:
        for i in range(1, 5):
            defCombatBuffs[i] -= 5 + (max(DefPanicFactor * defender.buffs[i], 0) * -2) * (not defBonusesNeutralized[i])

    if "Minecraft Gaming" in defSkills:
        for i in range(1, 5):
            atkCombatBuffs[i] -= 5 + (max(AtkPanicFactor * attacker.buffs[i], 0) * -2) * (not atkBonusesNeutralized[i])

    # Gloom Breath (Refine Eff) - F!Corrin
    if "corrinPenaltyTheft" in atkSkills:
        for i in range(1, 5): atkCombatBuffs[i] += defNeutrDebuffsStats[i] * -1

    if "corrinPenaltyTheft" in defSkills:
        for i in range(1, 5): defCombatBuffs[i] += atkNeutrDebuffsStats[i] * -1


    # WHERE BONUSES AND PENALTIES ARE NEUTRALIZED
    for i in range(1, 5):
        atkCombatBuffs[i] -= atkPenaltiesNeutralized[i] * (attacker.debuffs[i] + min(attacker.buffs[i] * AtkPanicFactor, 0))
        atkCombatBuffs[i] -= atkBonusesNeutralized[i] * max(attacker.buffs[i] * AtkPanicFactor, 0)

        defCombatBuffs[i] -= defPenaltiesNeutralized[i] * (defender.debuffs[i] + min(defender.buffs[i] * DefPanicFactor, 0))
        defCombatBuffs[i] -= defBonusesNeutralized[i] * max(defender.buffs[i] * DefPanicFactor, 0)


    # add combat buffs to stats

    i = 0
    while i < 5:
        atkStats[i] += atkCombatBuffs[i]
        defStats[i] += defCombatBuffs[i]
        i += 1

    i = 0
    while i < 5:
        atkPhantomStats[i] += atkStats[i]
        defPhantomStats[i] += defStats[i]
        i += 1

    # From this point on, use atkStats/defStats for getting direct values in combat
    # Use atkPhantomStats/defPhantomStats for comparisons
    # END OF STAT MODIFICATION SKILLS, NO MORE SHOULD EXIST BENEATH THIS LINE

    # SPECIAL CHARGE MODIFICATION

    if "heavyBlade" in atkSkills and atkPhantomStats[1] > defPhantomStats[1] + max(-2 * atkSkills["heavyBlade"] + 7, 1):
        atkr.spGainOnAtk += 1
    if "heavyBlade" in defSkills and defPhantomStats[1] > atkPhantomStats[1] + max(-2 * defSkills["heavyBlade"] + 7, 1):
        defr.spGainOnAtk += 1

    if "heavyBladeW" in atkSkills and atkPhantomStats[1] > defPhantomStats[1] + max(-2 * atkSkills["heavyBladeW"] + 7, 1):
        atkr.spGainOnAtk += 1
    if "heavyBladeW" in defSkills and defPhantomStats[1] > atkPhantomStats[1] + max(-2 * defSkills["heavyBladeW"] + 7, 1):
        defr.spGainOnAtk += 1

    if "heavyBladeSe" in atkSkills and atkPhantomStats[1] > defPhantomStats[1] + max(-2 * atkSkills["heavyBladeSe"] + 7, 1):
        atkr.spGainOnAtk += 1
    if "heavyBladeSe" in defSkills and defPhantomStats[1] > atkPhantomStats[1] + max(-2 * defSkills["heavyBladeSe"] + 7, 1):
        defr.spGainOnAtk += 1

    if "royalSword" in atkSkills and atkAllyWithin2Spaces or "royalSword2" in atkSkills:
        atkr.spGainOnAtk += 1
    if ("royalSword" in defSkills or "royalSword2" in defSkills) and defAllyWithin2Spaces:
        defr.spGainOnAtk += 1



    if "wandererer" in atkSkills and defHPGreaterEqual75Percent and atkPhantomStats[SPD] > defPhantomStats[SPD]:
        atkr.spGainOnAtk += 1
        atkr.spGainWhenAtkd += 1

    if "wandererer" in defSkills and atkHPGreaterEqual75Percent and defPhantomStats[SPD] > atkPhantomStats[SPD]:
        defr.spGainOnAtk += 1
        defr.spGainWhenAtkd += 1

    # M!Shez - Crimson Blades - Base
    # Grants Spd+5. Inflicts Def/Res-5. Unit attacks twice.
    # At start of combat, grants the following based on unit's HP:
    #  - if ≥ 20%, grants Special cooldown charge +1 to unit per attack
    #  - if ≥ 40%, reduces damage from first attack during combat by 40%
    if "shez!" in atkSkills:
        if atkHPCur / atkStats[0] >= 0.2:
            atkr.spGainOnAtk += 1
            atkr.spGainWhenAtkd += 1
        if atkHPCur / atkStats[0] >= 0.4:
            atkr.DR_first_hit_NSP.append(40)

    if "shez!" in defSkills:
        if defHPCur / defStats[0] >= 0.2:
            defr.spGainOnAtk += 1
            defr.spGainWhenAtkd += 1
        if defHPCur / defStats[0] >= 0.4:
            defr.DR_first_hit_NSP.append(40)

    if "BY MISSILETAINN!!!" in atkSkills:
        atkr.spGainWhenAtkd += 1

    if "BY MISSILETAINN!!!" in defSkills:
        defr.spGainWhenAtkd += 1

    if "flashingBlade" in atkSkills and atkPhantomStats[2] > defPhantomStats[2] + max(
            -2 * atkSkills["flashingBlade"] + 7, 1):
        atkr.spGainOnAtk += 1
    if "flashingBlade" in defSkills and defPhantomStats[2] > atkPhantomStats[2] + max(
            -2 * defSkills["flashingBlade"] + 7, 1):
        defr.spGainOnAtk += 1

    if "flashingBladeW" in atkSkills and atkPhantomStats[2] > defPhantomStats[2] + max(
            -2 * atkSkills["flashingBladeW"] + 7, 1):
        atkr.spGainOnAtk += 1
    if "flashingBladeW" in defSkills and defPhantomStats[2] > atkPhantomStats[2] + max(
            -2 * defSkills["flashingBladeW"] + 7, 1):
        defr.spGainOnAtk += 1

    # Guard
    if "guardHP" in atkSkills and atkHPCur / atkStats[0] >= atkSkills["guardHP"] / 10:
        defr.spLossWhenAtkd -= 1
        defr.spLossOnAtk -= 1

    if "guardHP" in defSkills and defHPCur / defStats[0] >= defSkills["guardHP"] / 10:
        atkr.spLossWhenAtkd -= 1
        atkr.spLossOnAtk -= 1

    if "DamageReductionPierce" in atkSkills:
        atkr.sp_pierce_DR = True

    if "DamageReductionPierce" in defSkills:
        defr.sp_pierce_DR = True

    # TEMPO WEAPONS/SKILLS

    if "tempo" in atkSkills:
        atkr.disable_foe_fastcharge = True
        atkr.disable_foe_guard = True

    if "tempo" in defSkills:
        defr.disable_foe_fastcharge = True
        defr.disable_foe_guard = True

    if atkr.disable_foe_guard:
        atkr.spLossOnAtk = 0
        atkr.spLossWhenAtkd = 0

    if atkr.disable_foe_fastcharge:
        defr.spGainOnAtk = 0
        defr.spGainWhenAtkd = 0

    if defr.disable_foe_guard:
        defr.spLossOnAtk = 0
        defr.spLossWhenAtkd = 0

    if defr.disable_foe_fastcharge:
        atkr.spGainOnAtk = 0
        atkr.spGainWhenAtkd = 0

    atkr.spGainOnAtk = min(atkr.spGainOnAtk, 1) + max(atkr.spLossOnAtk, -1)
    atkr.spGainWhenAtkd = min(atkr.spGainWhenAtkd, 1) + max(atkr.spLossWhenAtkd, -1)

    defr.spGainOnAtk = min(defr.spGainOnAtk, 1) + max(defr.spLossOnAtk, -1)
    defr.spGainWhenAtkd = min(defr.spGainWhenAtkd, 1) + max(defr.spLossWhenAtkd, -1)

    # Pre-strike SP charge/slow

    if "Mr. Fire Emblem" in atkSkills and atkHPGreaterEqual25Percent and defender.getSpecialType() == "Offense" and \
            atkPhantomStats[RES] >= defPhantomStats[RES]:
        defr.sp_charge_first -= 1

    if "Mr. Fire Emblem" in defSkills and defHPGreaterEqual25Percent and attacker.getSpecialType() == "Offense" and \
            defPhantomStats[RES] >= atkPhantomStats[RES]:
        atkr.sp_charge_first -= 1

    # Stat-Dependant Follow-Ups

    if "windsweep" in atkSkills:
        atkr.follow_up_denials -= 1

        if atkPhantomStats[SPD] >= defPhantomStats[SPD] + (-2 * atkSkills["windsweep"] + 7) and defender.wpnType in PHYSICAL_WEAPONS:
            cannotCounter = True

    if "watersweep" in atkSkills:
        atkr.follow_up_denials -= 1

        if atkPhantomStats[SPD] >= defPhantomStats[SPD] + (-2 * atkSkills["watersweep"] + 7) and defender.wpnType in MAGICAL_WEAPONS:
            cannotCounter = True

    # I hate this skill up until level 4 why does it have all those conditions
    if "brashAssault" in atkSkills and not ((cannotCounter and not disableCannotCounter) or not (attacker.getRange() == defender.getRange() or ignoreRng)) and atkHPCur / atkStats[0] <= 0.1 * atkSkills["brashAssault"] + 0.2:
        atkr.follow_ups_skill += 1

    if "brashAssaultSe" in atkSkills and not ((cannotCounter and not disableCannotCounter) or not (attacker.getRange() == defender.getRange() or ignoreRng)) and atkHPCur / atkStats[0] <= 0.1 * atkSkills["brashAssaultSe"] + 0.2:
        atkr.follow_ups_skill += 1

    if "brashAssaultLyn" in atkSkills and not ((cannotCounter and not disableCannotCounter) or not (attacker.getRange() == defender.getRange() or ignoreRng)) and atkHPCur / atkStats[0] <= 0.75:
        atkr.follow_ups_skill += 1

    # Brynhildr - Refine (Leo)

    if "leoWowThisRefineIsGarbage" in atkSkills and atkPhantomStats[DEF] > defPhantomStats[DEF] and defender.wpnType in RANGED_WEAPONS:
        defr.follow_up_denials -= 1

    if "leoWowThisRefineIsGarbage" in defSkills and defPhantomStats[DEF] > atkPhantomStats[DEF] and attacker.wpnType in RANGED_WEAPONS:
        atkr.follow_up_denials -= 1

    # Null Follow-Up
    if Status.NullFollowUp in attacker.statusPos and atkPhantomStats[2] > defPhantomStats[2]:
        atkr.prevent_foe_FU, atkr.prevent_self_FU_denial = True

    if Status.NullFollowUp in defender.statusPos and defPhantomStats[2] > atkPhantomStats[2]:
        defr.prevent_foe_FU, defr.prevent_self_FU_denial = True

    if atkr.prevent_foe_FU: defr.follow_ups_skill = 0
    if defr.prevent_foe_FU: atkr.follow_ups_skill = 0
    if atkr.prevent_self_FU_denial: atkr.follow_up_denials = 0
    if defr.prevent_self_FU_denial: defr.follow_up_denials = 0

    # Scowl-based effects
    if "waveScowl" in atkSkills:
        if atkPhantomStats[RES] >= defPhantomStats[RES] + 5 and defender.getSpecialType() == "Offense":
            defr.sp_charge_first -= 1

    if "waveScowl" in defSkills:
        if defPhantomStats[RES] >= atkPhantomStats[RES] + 5 and attacker.getSpecialType() == "Offense":
            atkr.sp_charge_first -= 1

    # TRUE DAMAGE ADDITION

    for x in atkr.true_stat_damages:
        stat, percentage = x
        atkr.true_all_hits += math.trunc(atkStats[stat] * (percentage/100))

    for x in defr.true_stat_damages:
        stat, percentage = x
        defr.true_all_hits += math.trunc(defStats[stat] * (percentage/100))

    if "SpdDmg" in atkSkills and atkPhantomStats[2] > defPhantomStats[2]:
        atkr.true_all_hits += min(math.trunc((atkPhantomStats[2] - defPhantomStats[2]) * 0.1 * atkSkills["SpdDmg"]),
                                  atkSkills["SpdDmg"])
    if "SpdDmg" in defSkills and defPhantomStats[2] > atkPhantomStats[2]:
        defr.true_all_hits += min(math.trunc((defPhantomStats[2] - atkPhantomStats[2]) * 0.1 * defSkills["SpdDmg"]),
                                  defSkills["SpdDmg"])

    if "moreeeeta" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.true_all_hits += math.trunc(atkStats[SPD] * 0.1)
    if "moreeeeta" in defSkills and defHPGreaterEqual25Percent:
        defr.true_all_hits += math.trunc(atkStats[SPD] * 0.1)

    if "thraciaMoment" in atkSkills and defStats[3] >= defStats[4] + 5:
        atkr.true_all_hits += 7
    if "thraciaMoment" in defSkills and atkStats[3] >= atkStats[4] + 5:
        defr.true_all_hits += 7

    if "LOVE PROVIIIIDES, PROTECTS US" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.true_all_hits += math.trunc(atkStats[2] * 0.15)
    if "LOVE PROVIIIIDES, PROTECTS US" in defSkills and defHPGreaterEqual25Percent:
        defr.true_all_hits += math.trunc(defStats[2] * 0.15)

    if "vassalBlade" in atkSkills:
        atkr.true_all_hits += math.trunc(atkStats[2] * 0.15)
    if "vassalBlade" in defSkills and defAllyWithin2Spaces:
        defr.true_all_hits += math.trunc(defStats[2] * 0.15)

    if "infiniteSpecial" in atkSkills:
        atkr.true_all_hits += math.trunc(atkStats[2] * 0.15)
    if "infiniteSpecial" in defSkills:
        defr.true_all_hits += math.trunc(defStats[2] * 0.15)

    if "newVTyrfing" in atkSkills and (not atkHPEqual100Percent or defHPGreaterEqual75Percent):
        atkr.true_all_hits += math.trunc(atkStats[ATK] * 0.15)
    if "newVTyrfing" in defSkills:
        defr.true_all_hits += math.trunc(defStats[ATK] * 0.15)

    if "hamburger" in atkSkills:
        atkr.true_all_hits += math.trunc(atkStats[DEF] * 0.15)
    if "hamburger" in atkSkills and defAllyWithin2Spaces:
        defr.true_all_hits += math.trunc(defStats[DEF] * 0.15)

    if "I HATE FIRE JOKES >:(" in atkSkills and spaces_moved_by_atkr:
        atkr.true_all_hits += math.trunc(math.trunc(defStats[DEF] * 0.10 * min(spaces_moved_by_atkr, 4)))
    if "I HATE FIRE JOKES >:(" in defSkills and spaces_moved_by_atkr:
        defr.true_all_hits += math.trunc(atkStats[DEF] * 0.10 * min(spaces_moved_by_atkr, 4))

    if "renaisTwins" in atkSkills and (atkHasBonus or atkHasPenalty):
        atkr.true_all_hits += math.trunc(defStats[3] * 0.20)
        atkr.all_hits_heal += math.trunc(defStats[3] * 0.20)

    if "renaisTwins" in defSkills and defAllyWithin2Spaces and (defHasBonus or defHasPenalty):
        defr.true_all_hits += math.trunc(atkStats[3] * 0.20)
        defr.all_hits_heal += math.trunc(defStats[3] * 0.20)

    if "megaAstra" in atkSkills and atkPhantomStats[1] > defPhantomStats[3]:
        atkr.true_all_hits += max(math.trunc((atkStats[1] - defStats[3]) * 0.5), 0)

    if "megaAstra" in defSkills and defPhantomStats[1] > atkPhantomStats[3]:
        defr.true_all_hits += max(math.trunc((defStats[1] - atkStats[3]) * 0.5), 0)

    if "Sacred Stones Strike!" in atkSkills and atkAllyWithin3Spaces:
        atkSpEffects.update({"spMissiletainn": 0})

    if "Sacred Stones Strike!" in defSkills and defAllyWithin3Spaces:
        defSpEffects.update({"spMissiletainn": 0})

    if "sky-hopper" in atkSkills and atkHPGreaterEqual25Percent:
        atkr.true_all_hits += trunc(0.2 * atkStats[SPD])

    if "sky-hopper" in defSkills and defHPGreaterEqual25Percent:
        defr.true_all_hits += trunc(0.2 * defStats[SPD])

    # TRUE DAMAGE SUBTRACTION

    if "daydream_egg" in atkSkills and defHPGreaterEqual75Percent:
        atkr.TDR_all_hits += trunc(0.2 * atkStats[RES])

    if "daydream_egg" in defSkills and atkHPGreaterEqual75Percent:
        defr.TDR_all_hits += trunc(0.2 * defStats[RES])

    # PART 2
    if "laguz_friend" in atkSkills:
        skill_lvl = atkSkills["laguz_friend"]

        if attacker.getMaxSpecialCooldown() >= 3 and attacker.getSpecialType() == "Offense" or attacker.getSpecialType() == "Defense":
            atkr.TDR_all_hits += trunc(0.05 * skill_lvl * max(atkStats[DEF], atkStats[RES]))

        if attacker.getMaxSpecialCooldown() >= 3 and attacker.getSpecialType() == "Offense":
            atkr.true_sp += trunc(0.05 * skill_lvl * max(atkStats[DEF], atkStats[RES]))
            if skill_lvl == 4: atkr.sp_pierce_DR = True
        if attacker.getSpecialType() == "Defense":
            atkr.true_sp_next += trunc(0.05 * skill_lvl * max(atkStats[DEF], atkStats[RES]))
            if skill_lvl == 4: atkr.sp_pierce_after_DSP = True

    if "laguz_friend" in defSkills:
        skill_lvl = defSkills["laguz_friend"]

        if defender.getMaxSpecialCooldown() >= 3 and defender.getSpecialType() == "Offense" or defender.getSpecialType() == "Defense":
            defr.TDR_all_hits += trunc(0.05 * skill_lvl * max(defStats[DEF], defStats[RES]))

        if defender.getMaxSpecialCooldown() >= 3 and defender.getSpecialType() == "Offense":
            defr.true_sp += trunc(0.05 * skill_lvl * max(defStats[DEF], defStats[RES]))
            if skill_lvl == 4: defr.sp_pierce_DR = True
        if defender.getSpecialType() == "Defense":
            defr.true_sp_next += trunc(0.05 * skill_lvl * max(defStats[DEF], defStats[RES]))
            if skill_lvl == 4: defr.sp_pierce_after_DSP = True

    # EFFECTIVENESS CHECK

    oneEffAtk = False
    oneEffDef = False

    if "effInf" in atkSkills and defender.move == 0: oneEffAtk = True
    if "effInf" in defSkills and attacker.move == 0: oneEffDef = True

    if "effCav" in atkSkills and "nullEffCav" not in defSkills and defender.move == 1: oneEffAtk = True
    if "effCav" in defSkills and "nullEffCav" not in atkSkills and attacker.move == 1: oneEffDef = True

    if "effFly" in atkSkills and "nullEffFly" not in defSkills and defender.move == 2: oneEffAtk = True
    if "effFly" in defSkills and "nullEffFly" not in atkSkills and attacker.move == 2: oneEffDef = True

    if attacker.wpnType in ["RBow", "BBow", "GBow", "CBow"] and "nullEffFly" not in defSkills and defender.move == 2:
        oneEffAtk = True

    if defender.wpnType in ["RBow", "BBow", "GBow", "CBow"] and "nullEffFly" not in atkSkills and attacker.move == 2:
        oneEffDef = True

    if "effArmor" in atkSkills and "nullEffArm" not in defSkills and defender.move == 3: oneEffAtk = True
    if "effArmor" in defSkills and "nullEffArm" not in atkSkills and attacker.move == 3: oneEffDef = True

    if ("effDragon" in atkSkills or Status.EffDragons in attacker.statusPos) and "nullEffDragon" not in defSkills and (
            defender.getTargetedDef() == 0 or "loptous" in defSkills):
        oneEffAtk = True
    if ("effDragon" in defSkills or Status.EffDragons in defender.statusPos) and "nullEffDragon" not in atkSkills and (
            attacker.getTargetedDef() == 0 or "loptous" in atkSkills):
        oneEffDef = True

    if "effMagic" in atkSkills and defender.wpnType in TOME_WEAPONS: oneEffAtk = True
    if "effMagic" in defSkills and attacker.wpnType in TOME_WEAPONS: oneEffDef = True

    if "effBeast" in atkSkills and defender.wpnType in ["RBeast", "BBeast", "GBeast", "CBeast"]:
        oneEffAtk = True
    if "effBeast" in defSkills and attacker.wpnType in ["RBeast", "BBeast", "GBeast", "CBeast"]:
        oneEffDef = True

    if "effCaeda" in atkSkills and (defender.wpnType in ["Sword", "Lance", "Axe", "CBow"] or (
            defender.move == 3 and "nullEffArm" not in defSkills)):
        oneEffAtk = True
    if "effCaeda" in defSkills and (attacker.wpnType in ["Sword", "Lance", "Axe", "CBow"] or (
            attacker.move == 3 and "nullEffArm" not in atkSkills)):
        oneEffDef = True

    if "effShez" in atkSkills:
        if defender.move == 0 and defender.wpnType not in ["RDragon", "BDragon", "GDragon", "CDragon", "RBeast",
                                                           "BBeast", "GBeast", "CBeast"]:
            threshold = defPhantomStats[2] + 20
        else:
            threshold = defPhantomStats[2] + 5

        if atkPhantomStats[2] >= threshold:
            oneEffAtk = True

    if defender.wpnType == "BTome" and "haarEff" in atkSkills:
        oneEffDef = True
    if attacker.wpnType == "BTome" and "haarEff" in defSkills:
        oneEffAtk = True

    if oneEffAtk: atkStats[1] += math.trunc(atkStats[1] * 0.5)
    if oneEffDef: defStats[1] += math.trunc(defStats[1] * 0.5)

    # COLOR ADVANTAGE

    atkr.preTriangleAtk = atkStats[1]
    defr.preTriangleAtk = defStats[1]

    if (attacker.getColor() == "Red" and defender.getColor() == "Green") or (
            attacker.getColor() == "Green" and defender.getColor() == "Blue") or \
            (attacker.getColor() == "Blue" and defender.getColor() == "Red") or (
            defender.getColor() == "Colorless" and "colorlessAdv" in atkSkills):

        if (atkCA == 1 or defCA == 1) and triAdept != -1: triAdept = -1
        if defCA == 2 and triAdept != -1: triAdept = -1
        if atkCA == 3 and triAdept != -1: triAdept = -5

        atkStats[1] += math.trunc(atkStats[1] * (0.25 + .05 * triAdept))
        defStats[1] -= math.trunc(defStats[1] * (0.25 + .05 * triAdept))

        wpnAdvHero = 0

    if (attacker.getColor() == "Blue" and defender.getColor() == "Green") or (
            attacker.getColor() == "Red" and defender.getColor() == "Blue") or \
            (attacker.getColor() == "Green" and defender.getColor() == "Red") or (
            attacker.getColor() == "Colorless" and "colorlessAdv" in defSkills):

        if (atkCA == 1 or defCA == 1) and triAdept != -1: triAdept = -1
        if atkCA == 2 and triAdept != -1: triAdept = -1
        if atkCA == 3 and triAdept != -1: triAdept = -5
        atkStats[1] -= math.trunc(atkStats[1] * (0.25 + .05 * triAdept))
        defStats[1] += math.trunc(defStats[1] * (0.25 + .05 * triAdept))

        wpnAdvHero = 1

    # WHICH DEFENSE ARE WE TARGETING?

    atkTargetingDefRes = int(attacker.getTargetedDef() == 1)

    if attacker.getTargetedDef() == 0 and not "oldDragonstone" in atkSkills and not defr.disable_foe_hexblade:
        if defender.getRange() == 2 and defStats[3] > defStats[4]:
            atkTargetingDefRes += 1
        elif defender.getRange() != 2:
            atkTargetingDefRes += 1
    elif attacker.getTargetedDef() == 0:
        atkTargetingDefRes += 1

    defTargetingDefRes = int(defender.getTargetedDef() == 1)

    if defender.getTargetedDef() == 0 and not "oldDragonstone" in defSkills and not atkr.disable_foe_hexblade:
        if attacker.getRange() == 2 and atkStats[3] > atkStats[4]:
            defTargetingDefRes += 1
        elif attacker.getRange() != 2:
            defTargetingDefRes += 1
    elif defender.getTargetedDef() == 0:
        defTargetingDefRes += 1

    if "permHexblade" in atkSkills and not defr.disable_foe_hexblade: atkTargetingDefRes = int(defStats[3] < defStats[4])
    if "permHexblade" in defSkills and not atkr.disable_foe_hexblade: defTargetingDefRes = int(atkStats[3] < atkStats[4])

    # Defensive terrain
    if atkDefensiveTerrain: atkr.TDR_all_hits += trunc(0.3 * atkStats[defTargetingDefRes + 3])
    if defDefensiveTerrain: defr.TDR_all_hits += trunc(0.3 * defStats[atkTargetingDefRes + 3])

    # Amount of speed required to double the foe
    atkOutspeedFactor = 5
    defOutspeedFactor = 5

    # Which index in the attack array holds the potent attack
    atkPotentIndex = -1
    defPotentIndex = -1

    if "FOR THE PRIDE OF BRODIA" in atkSkills:
        atkOutspeedFactor += 20
        defOutspeedFactor += 20
    if "FOR THE PRIDE OF BRODIA" in defSkills:
        atkOutspeedFactor += 20
        defOutspeedFactor += 20

    if "wyvernRift" in atkSkills and atkStats[SPD] + atkStats[DEF] >= defStats[SPD] + defStats[DEF] - 10:
        defOutspeedFactor += 20

    if "wyvernRift" in defSkills and defStats[SPD] + defStats[DEF] >= atkStats[SPD] + atkStats[DEF] - 10:
        atkOutspeedFactor += 20

    # Potent 1-4
    if "potentStrike" in atkSkills and atkStats[SPD] >= defStats[SPD] + (atkOutspeedFactor - 25):
        atkr.potent_FU = True

    if "potentStrike" in defSkills and defStats[SPD] >= atkStats[SPD] + (defOutspeedFactor - 25):
        defr.potent_FU = True

    # Lodestar Rush - E!Marth
    if "potentFix" in atkSkills:
        atkr.potent_new_percentage = atkSkills["potentFix"]

    if "potentFix" in defSkills:
        defr.potent_new_percentage = defSkills["potentFix"]

    if (atkStats[SPD] >= defStats[SPD] + atkOutspeedFactor): atkr.follow_ups_spd += 1
    if (defStats[SPD] >= atkStats[SPD] + defOutspeedFactor): defr.follow_ups_spd += 1

    atkAlive = True
    defAlive = True

    def getSpecialDamage(effs, initStats, initHP, otherStats, defOrRes, base_damage, num_foe_atks, selfPreTriAtk, otherPreTriAtk, otherMoveType):
        total = 0
        if "atkBoost" in effs:
            total += math.trunc(selfPreTriAtk * .10 * effs["atkBoost"])

        if "spdBoost" in effs:
            total += math.trunc(initStats[SPD] * .10 * effs["spdBoost"])

        if "defBoost" in effs:
            total += math.trunc(initStats[SPD] * .10 * effs["defBoost"])

        if "resBoost" in effs:
            total += math.trunc(initStats[RES] * .10 * effs["resBoost"])

        if "rupturedSky" in effs:
            total += math.trunc(otherPreTriAtk * .10 * effs["rupturedSky"])

        if "staffRes" in effs:
            total += math.trunc(otherStats[RES] * .10 * effs["staffRes"])

        if "retaliatoryBoost" in effs:
            total += math.trunc((initStats[HP] - initHP) * 0.10 * effs["retaliatoryBoost"])

        if "dmgBoost" in effs:
            total += math.trunc(base_damage * 0.1 * effs["dmgBoost"])

        targeted_defense = otherStats[defOrRes + 3]
        if "defReduce" in effs:
            reduced_def = targeted_defense - math.trunc(targeted_defense * .10 * effs["defReduce"])
            attack = initStats[ATK] - reduced_def
            total += attack - base_damage

        if "spMissiletainn" in effs:
            total += min(initStats[HP] - initHP, 30)

        if "spTimerra" in effs:
            total += math.trunc(initStats[SPD] * .10 * effs["spTimerra"])

        if "atkBoostArmor" in effs:
            if otherMoveType == 3:
                total += math.trunc(selfPreTriAtk * 0.10 * 4)
            else:
                total += math.trunc(selfPreTriAtk * 0.10 * 3)

        if "NumAtkBoost" in effs:
            total += math.trunc((effs["NumAtkBoost"] + num_foe_atks) * 0.10 * selfPreTriAtk)

        if "wrathBoostW" in effs:
            if initHP/initStats[HP] <= effs["wrathBoostW"] * 0.25:
                total += 10

        if "wrathBoostSk" in effs:
            if initHP/initStats[HP] <= effs["wrathBoostSk"] * 0.25:
                total += 10

        return total

    # COMPUTE TURN ORDER

    cannotCounterFinal = (cannotCounter and not disableCannotCounter) or not (attacker.getRange() == defender.getRange() or ignoreRng)
    # Will never counter if defender has no weapon
    if defender.getWeapon() == NIL_WEAPON: cannotCounterFinal = True

    # Follow-Up Granted if sum of allowed - denied follow-ups is > 0
    followupA = atkr.follow_ups_spd + atkr.follow_ups_skill + atkr.follow_up_denials > 0
    followupD = defr.follow_ups_spd + defr.follow_ups_skill + defr.follow_up_denials > 0

    # hardy bearing
    if atkr.hardy_bearing:
        atkr.self_desperation = False
        atkr.other_desperation = False
        atkr.vantage = False

    if defr.hardy_bearing:
        defr.self_desperation = False
        defr.other_desperation = False
        defr.vantage = False

    if atkr.vantage or defr.vantage:
        startString = "DA"
        if followupD:
            startString += "D"
        if followupA:
            startString += "A"
    else:
        startString = "AD"
        if followupA:
            startString += "A"
        if followupD:
            startString += "D"

    if startString[0] == 'A':
        firstCheck = atkr.self_desperation or defr.other_desperation
        secondCheck = defr.self_desperation or atkr.other_desperation
    else:
        firstCheck = defr.self_desperation or atkr.other_desperation
        secondCheck = atkr.self_desperation or defr.other_desperation

    if firstCheck:
        startString = move_letters(startString, startString[0])
    if secondCheck:
        startString = move_letters(startString, {"A", "D"}.difference([startString[0]]).pop())

    newString = ""

    # duplicate letters if Brave Eff
    # it makes zero sense how two D's need to be added, but only one A, but I don't care it works
    for c in startString:
        if c == 'A' and atkr.brave:
            newString += c
        if c == 'D' and defr.brave:
            newString += c * 2
        else:
            newString += c

    # potent strike
    if atkr.potent_FU:
        last_a_index = newString.rfind('A')
        newString = newString[:last_a_index + 1] + 'A' + newString[last_a_index + 1:]

    if defr.potent_FU:
        last_a_index = newString.rfind('D')
        newString = newString[:last_a_index + 1] + 'D' + newString[last_a_index + 1:]

        defPotentIndex = newString.rfind('D')

    # code don't work without these
    startString = newString
    startString2 = startString

    if cannotCounterFinal: startString2 = startString.replace("D", "")

    if atkr.potent_FU:
        atkPotentIndex = startString2.rfind('A')

    # list of attack objects
    attackList = []
    A_Count = 0
    D_Count = 0
    i = 0

    while i < len(startString2):
        if startString2[i] == "A":
            A_Count += 1
            isFollowUp = A_Count == 2 and (followupA or atkr.potent_FU) and not atkr.brave or A_Count in [3, 4, 5]
            isConsecutive = True if A_Count >= 2 and startString2[i - 1] == "A" else False

            potentRedu = 100
            if "potentStrike" in atkSkills and i == atkPotentIndex:
                potentRedu = 10 * atkSkills["potentStrike"] + 40 * int(not (atkr.brave or followupA))

            attackList.append(Attack(0, isFollowUp, isConsecutive, A_Count, A_Count + D_Count,
                                     None if A_Count + D_Count == 1 else attackList[i - 1], potentRedu))
        else:
            D_Count += 1
            isFollowUp = D_Count == 2 and (followupD or defr.potent_FU) and not defr.brave or D_Count in [3, 4, 5]
            isConsecutive = True if D_Count >= 2 and startString2[i - 1] == "D" else False
            potentRedu = 100

            if "potentStrike" in defSkills and i == defPotentIndex:
                potentRedu = 10 * defSkills["potentStrike"] + 40 * int(not (defr.brave or followupD))

            attackList.append(Attack(1, isFollowUp, isConsecutive, D_Count, A_Count + D_Count,
                                     None if A_Count + D_Count == 1 else attackList[i - 1], potentRedu))
        i += 1

    # Damage reduction calculated based on a difference between two stats (Dodge, etc.)

    if "Just Lean" in atkSkills and atkHPGreaterEqual25Percent and atkPhantomStats[2] > defPhantomStats[2]:
        atkr.DR_all_hits_NSP.append(min(4 * (atkPhantomStats[2] - defPhantomStats[2], 40)))

    if "Just Lean" in defSkills and defHPGreaterEqual25Percent and defPhantomStats[2] > atkPhantomStats[2]:
        defr.DR_all_hits_NSP.append(min(4 * (defPhantomStats[2] - atkPhantomStats[2], 40)))

    # Rutger - Wanderer Blade - Refined Eff
    if "like the university" in atkSkills and atkHPGreaterEqual25Percent and atkPhantomStats[2] > defPhantomStats[2]:
        atkr.DR_all_hits_NSP.append(min(4 * (atkPhantomStats[2] - defPhantomStats[2], 40)))

    if "like the university" in defSkills and defHPGreaterEqual25Percent and defPhantomStats[2] > atkPhantomStats[2]:
        defr.DR_all_hits_NSP.append(min(4 * (defPhantomStats[2] - atkPhantomStats[2], 40)))

    if "BONDS OF FIIIIRE, CONNECT US" in atkSkills and atkHPGreaterEqual25Percent and atkPhantomStats[2] > \
            defPhantomStats[2]:
        atkr.DR_all_hits_NSP.append(min(4 * (atkPhantomStats[2] - defPhantomStats[2], 40)))

    if "BONDS OF FIIIIRE, CONNECT US" in defSkills and defHPGreaterEqual25Percent and defPhantomStats[2] > \
            atkPhantomStats[2]:
        defr.DR_all_hits_NSP.append(min(4 * (defPhantomStats[2] - atkPhantomStats[2], 40)))

    if "LOVE PROVIIIIDES, PROTECTS US" in atkSkills and atkHPGreaterEqual25Percent and atkPhantomStats[2] > \
            defPhantomStats[2]:
        atkr.DR_all_hits_NSP.append(min(4 * (atkPhantomStats[2] - defPhantomStats[2], 40)))

    if "LOVE PROVIIIIDES, PROTECTS US" in defSkills and defHPGreaterEqual25Percent and defPhantomStats[2] > \
            atkPhantomStats[2]:
        defr.DR_all_hits_NSP.append(min(4 * (defPhantomStats[2] - atkPhantomStats[2], 40)))

    if Status.Dodge in atkSkills and atkPhantomStats[2] > defPhantomStats[2]:
        atkr.DR_all_hits_NSP.append(min(4 * (atkPhantomStats[2] - defPhantomStats[2], 40)))

    if Status.Dodge in defSkills and defPhantomStats[2] > atkPhantomStats[2]:
        defr.DR_all_hits_NSP.append(min(4 * (defPhantomStats[2] - atkPhantomStats[2], 40)))

    if "reduFU" in atkSkills and (turn % 2 == 1 or not defHPEqual100Percent):
        atkr.DR_first_hit_NSP.append(30 * (1 + int(followupD)))

    if "reduFU" in defSkills and (turn % 2 == 1 or not atkHPEqual100Percent):
        defr.DR_first_hit_NSP.append(30 * (1 + int(followupA)))

    # post combat charge
    if "A man has fallen into the river in LEGO City!" in atkSkills and atkHPGreaterEqual25Percent:
        atkPostCombatSpCharge += 1

    if "A man has fallen into the river in LEGO City!" in defSkills and defHPGreaterEqual25Percent:
        defPostCombatSpCharge += 1

    if "shine on" in atkSkills and atkr.brave:
        atkr.reduce_self_sp_damage += 8

    if "shine on" in defSkills and defr.brave:
        defr.reduce_self_sp_damage += 8

    # method to attack
    def attack(striker, strikee, stkSpEffects, steSpEffects, stkStats, steStats, defOrRes, curReduction,
               curSpecialReduction, stkHPCur, steHPCur, stkSpCount, steSpCount, I_stkr, I_ster, curAttack):

        dmgBoost = 0

        # has special triggered due to this hit
        stkr_sp_triggered = False
        ster_sp_triggered = False

        # attack minus defense or resistance
        attack = stkStats[1] - steStats[3 + defOrRes]

        if attack < 0: attack = 0

        if stkSpCount == 0 and striker.getSpecialType() == "Offense" and not I_stkr.special_disabled:
            if not is_in_sim: print(striker.name + " procs " + striker.getSpName() + ".")
            num_foe_atks = curAttack.attackNumAll - curAttack.attackNumSelf
            dmgBoost = getSpecialDamage(stkSpEffects, stkStats, stkHPCur, steStats, defOrRes, attack, num_foe_atks, atkr.preTriangleAtk, defr.preTriangleAtk, strikee.move)

            if I_stkr.brave:  # emblem marth effect
                dmgBoost = max(dmgBoost - I_stkr.reduce_self_sp_damage, 0)

            I_stkr.special_triggered = True
            stkr_sp_triggered = True

        attack += dmgBoost  # true damage by specials
        attack += I_stkr.true_all_hits  # true damage on all hits

        if I_stkr.resonance:
            resonance_damage = min(max((I_stkr.start_of_combat_HP - stkHPCur) * 2, 6), 12)
            attack += resonance_damage

        attack += I_stkr.true_sp_next_CACHE
        I_stkr.true_sp_next_CACHE = 0

        if curAttack.attackNumSelf == 1:
            attack += I_stkr.true_first_hit

        if curAttack.attackNumSelf != curAttack.attackNumAll:
            attack += I_stkr.true_after_foe_first
            I_stkr.true_after_foe_first = 0

        if stkr_sp_triggered:
            attack += I_stkr.true_sp

        if I_stkr.special_triggered or stkSpCount == 0:  # special-enabled true damage (finish)
            attack += I_stkr.true_finish

        attack += I_stkr.stacking_retaliatory_damage
        attack += I_stkr.nonstacking_retaliatory_damage

        for x in I_stkr.retaliatory_full_damages_CACHE:
            attack += math.trunc(I_stkr.most_recent_atk * (x / 100))

        # half damage if staff user without wrathful staff
        if striker.getWeaponType() == "Staff" and not I_stkr.wrathful_staff:
            attack = math.trunc(attack * 0.5)

        # potent FU reduction
        attack = trunc(attack * curAttack.potentRedu / 100)

        # the final attack in all it's glory
        full_atk = attack
        I_ster.most_recent_atk = attack

        # damage reduction
        total_reduction = 1

        stkr_DRR = I_stkr.damage_reduction_reduction

        # Resonance Piercing
        if I_stkr.resonance:
            stkr_DRR *= (min(max((I_stkr.start_of_combat_HP - stkHPCur) * 10, 30), 60)) / 100

        if not (I_stkr.always_pierce_DR or
                (stkr_sp_triggered and I_stkr.sp_pierce_DR) or
                (curAttack.isFollowUp and I_stkr.pierce_DR_FU) or
                (I_stkr.sp_pierce_after_def_sp_CACHE)):
            for x in curReduction:
                total_reduction *= 1 - (x / 100 * stkr_DRR)  # change by redu factor

        I_stkr.sp_pierce_after_def_sp_CACHE = False

        for x in curSpecialReduction:
            total_reduction *= 1 - (x / 100)

        # defensive specials
        if steSpCount == 0 and strikee.getSpecialType() == "Defense" and not I_ster.special_disabled:
            if striker.getRange() == 1 and "closeShield" in steSpEffects:
                if not is_in_sim: print(strikee.name + " procs " + strikee.getSpName() + ".")
                total_reduction *= 1 - (0.10 * steSpEffects["closeShield"])
                if I_ster.double_def_sp_charge:
                    total_reduction *= 1 - (0.10 * steSpEffects["closeShield"])

            elif striker.getRange() == 2 and "distantShield" in steSpEffects:
                if not is_in_sim: print(strikee.name + " procs " + strikee.getSpName() + ".")
                total_reduction *= 1 - (0.10 * steSpEffects["distantShield"])
                if I_ster.double_def_sp_charge:
                    total_reduction *= 1 - (0.10 * steSpEffects["distantShield"])

            I_ster.special_triggered = True
            ster_sp_triggered = True

        # rounded attack damage
        rounded_DR = (trunc(total_reduction * 100)) / 100
        attack = math.ceil(attack * rounded_DR)

        attack = max(attack - I_ster.TDR_all_hits, 0)

        if not curAtk.isFollowUp:
            attack = max(attack - I_ster.TDR_first_strikes, 0)
        else:
            attack = max(attack - I_ster.TDR_second_strikes, 0)

        # Extra true daamge only if defensive special triggered
        if ster_sp_triggered and strikee.getSpecialType() == "Defense":
            attack = max(attack - I_ster.TDR_on_def_sp, 0)

        curMiracleTriggered = False

        circlet_of_bal_cond = stkSpCount == 0 or steSpCount == 0 or I_stkr.special_triggered or I_ster.special_triggered

        # non-special Miracle
        if ((I_ster.pseudo_miracle or circlet_of_bal_cond and I_ster.circlet_miracle) and steHPCur - attack < 1 and steHPCur > 1) and not I_ster.disable_foe_miracle:
            attack = steHPCur - 1
            curMiracleTriggered = True

        # special Miracle
        if steSpCount == 0 and "miracleSP" in steSpEffects and steHPCur - attack < 1 and steHPCur > 1 and not I_ster.pseudo_miracle:
            if not is_in_sim: print(strikee.name + " procs " + strikee.getSpName() + ".")
            attack = steHPCur - 1
            I_ster.special_triggered = True
            ster_sp_triggered = True

        # non-special miracle has triggered
        if curMiracleTriggered:
            I_ster.pseudo_miracle = False

        # reduced atk
        I_ster.most_recent_reduced_atk = full_atk - attack

        # reset all retaliatory true damages
        I_stkr.stacking_retaliatory_damage = 0
        I_stkr.nonstacking_retaliatory_damage = 0
        I_stkr.retaliatory_full_damages_CACHE = []

        # set for foe

        # ice mirror i & ii, negating fang, etc.
        if "iceMirror" in steSpEffects and ster_sp_triggered:
            I_ster.stacking_retaliatory_damage += full_atk - attack

        # divine recreation, ginnungagap (weapon)
        if I_ster.retaliatory_reduced:
            I_ster.nonstacking_retaliatory_damage = full_atk - attack

        # brash assault 4, counter roar
        I_ster.retaliatory_full_damages_CACHE = I_ster.retaliatory_full_damages[:]

        # the attack™
        steHPCur -= attack  # goodness gracious

        if not is_in_sim: print(striker.name + " attacks " + strikee.name + " for " + str(attack) + " damage.")  # YES THEY DID

        # used for determining full attack damage
        presented_attack = attack
        # to evaluate noontime heal on hit that kills
        if steHPCur < 1: attack += steHPCur

        stkSpCount = max(stkSpCount - (1 + I_stkr.spGainOnAtk), 0)
        steSpCount = max(steSpCount - (1 + I_ster.spGainWhenAtkd), 0)

        if stkr_sp_triggered:
            stkSpCount = striker.specialMax
            if I_stkr.triggered_sp_charge != 0:
                stkSpCount -= I_stkr.triggered_sp_charge
                stkSpCount = max(stkSpCount, 0)
                I_stkr.triggered_sp_charge = 0

            I_stkr.true_sp_next_CACHE = I_stkr.true_sp_next

            for x in I_stkr.DR_sp_trigger_next_all_SP:
                I_stkr.DR_sp_trigger_next_all_SP_CACHE.append(x)

        if ster_sp_triggered:
            steSpCount = strikee.specialMax
            if I_ster.triggered_sp_charge != 0:
                steSpCount -= I_ster.triggered_sp_charge
                steSpCount = max(steSpCount, 0)
                I_ster.triggered_sp_charge = 0

            I_ster.true_sp_next_CACHE = I_ster.true_sp_next

            if I_ster.sp_pierce_after_def_sp:
                I_ster.sp_pierce_after_def_sp_CACHE = True

        # healing

        totalHealedAmount = 0

        mid_combat_skill_dmg = I_stkr.all_hits_heal + I_stkr.finish_mid_combat_heal * (stkSpCount == 0 or I_stkr.special_triggered)
        surge_heal = I_stkr.surge_heal

        # save for skills
        # += trunc(stkStats[0] * (min(striker.getMaxSpecialCooldown() * 20 + 10, 100) / 100))

        totalHealedAmount += mid_combat_skill_dmg

        if curAttack.isFollowUp:
            totalHealedAmount += I_stkr.follow_up_heal

        # Absorb staff
        if "absorb" in striker.getSkills():
            totalHealedAmount += math.trunc(attack * 0.5)

        # Surge heal
        if stkr_sp_triggered:
            totalHealedAmount += surge_heal

            # Specials that heal (Daylight, Sol, etc.)
            if "healSelf" in stkSpEffects:
                totalHealedAmount += math.trunc(attack * 0.1 * stkSpEffects["healSelf"])

        if Status.DeepWounds in striker.statusNeg or I_ster.disable_foe_healing:
            totalHealedAmount -= totalHealedAmount * math.trunc(1 - I_stkr.deep_wounds_allowance)

        stkHPCur += totalHealedAmount
        if not is_in_sim and totalHealedAmount: print(
            striker.name + " heals " + str(totalHealedAmount) + " HP during combat.")

        if stkHPCur > stkStats[0]: stkHPCur = stkStats[0]

        return stkHPCur, steHPCur, stkSpCount, steSpCount, presented_attack, totalHealedAmount, stkr_sp_triggered

    # burn damage

    burn_damages = [0, 0]

    if "A" in startString2:
        defHPCur = max(defHPCur - atkr.foe_burn_damage, 1)
        atkHPCur = max(atkHPCur - atkr.self_burn_damage, 1)

        burn_damages[0] += atkr.foe_burn_damage
        burn_damages[1] += atkr.self_burn_damage

    if "D" in startString2:
        atkHPCur = max(atkHPCur - defr.foe_burn_damage, 1)
        defHPCur = max(defHPCur - defr.self_burn_damage, 1)

        burn_damages[1] += defr.foe_burn_damage
        burn_damages[0] += defr.self_burn_damage



    # PERFORM THE ATTACKS

    i = 0
    while i < len(attackList) and (atkAlive and defAlive or is_in_sim):
        curAtk = attackList[i]

        # recoil damage
        if curAtk.attackOwner == 0 and curAtk.attackNumSelf == 1 and atkRecoilDmg > 0 and atkAlive: atkSelfDmg += atkRecoilDmg
        if curAtk.attackOwner == 0 and curAtk.attackNumSelf == 1 and NEWatkOtherDmg > 0 and atkAlive: atkOtherDmg += NEWatkOtherDmg
        if curAtk.attackOwner == 1 and curAtk.attackNumSelf == 1 and defRecoilDmg > 0 and defAlive: defSelfDmg += defRecoilDmg
        if curAtk.attackOwner == 1 and curAtk.attackNumSelf == 1 and NEWdefOtherDmg > 0 and defAlive: defOtherDmg += NEWdefOtherDmg

        # post-combat status effects & mid-combat special charges
        if curAtk.attackOwner == 0 and curAtk.attackNumSelf == 1 and atkAlive:
            atkPostCombatStatusesApplied[0] = atkPostCombatStatusesApplied[0] + atkPostCombatStatusesApplied[1]
            defPostCombatStatusesApplied[0] = defPostCombatStatusesApplied[0] + defPostCombatStatusesApplied[2]

            atkPostCombatEffs[0] += atkPostCombatEffs[2]
            defPostCombatEffs[0] += defPostCombatEffs[1]

            atkSpCountCur = max(0, atkSpCountCur - atkr.sp_charge_first)
            atkSpCountCur = min(atkSpCountCur, attacker.specialMax)

            defSpCountCur = max(0, defSpCountCur - defr.sp_charge_foe_first)

        # On attacker's follow-up attack
        if curAtk.attackOwner == 0 and (curAtk.attackNumSelf == 2 and not atkr.brave or curAtk.attackNumSelf == 3 and atkr.brave):
            atkSpCountCur = max(0, atkSpCountCur - atkr.sp_charge_FU)
            atkSpCountCur = min(atkSpCountCur, attacker.specialMax)

        if curAtk.attackOwner == 1 and curAtk.attackNumSelf == 1 and defAlive:
            defPostCombatStatusesApplied[0] = defPostCombatStatusesApplied[0] + defPostCombatStatusesApplied[1]
            atkPostCombatStatusesApplied[0] = atkPostCombatStatusesApplied[0] + atkPostCombatStatusesApplied[2]

            defPostCombatEffs[0] += defPostCombatEffs[2]
            atkPostCombatEffs[0] += atkPostCombatEffs[1]

            defSpCountCur = max(0, defSpCountCur - defr.sp_charge_first)
            defSpCountCur = min(defSpCountCur, defender.specialMax)

            atkSpCountCur = max(0, atkSpCountCur - atkr.sp_charge_foe_first)

        # On defender's follow-up attack
        if curAtk.attackOwner == 1 and (curAtk.attackNumSelf == 2 and not defr.brave or curAtk.attackNumSelf == 3 and defr.brave):
            defSpCountCur = max(0, defSpCountCur - defr.sp_charge_FU)
            defSpCountCur = min(defSpCountCur, defender.specialMax)

        # If unit has a percentage that changes upon special activation, set to new percentage
        # i.e. Lodestar Rush
        if (atkr.special_triggered or atkSpCountCur == 0) and atkr.potent_new_percentage != -1 and i == atkPotentIndex:
            curAtk.potentRedu = 100

        if (defr.special_triggered or defSpCountCur == 0) and defr.potent_new_percentage != -1 and i == defPotentIndex:
            curAtk.potentRedu = 100

        # damage reductions
        damage_reductions = []
        special_damage_reductions = []

        if curAtk.attackOwner == 0:
            damage_reductions += defr.DR_all_hits_NSP
            special_damage_reductions += defr.DR_all_hits_SP

            if defr.DR_great_aether_SP:
                if curAtk.isConsecutive:
                    special_damage_reductions.append(70 - (defSpCountCur * 10))
                else:
                    special_damage_reductions.append(40 - (defSpCountCur * 10))

            if atkr.special_triggered or attacker.specialCount == 0 or defr.special_triggered or defender.specialCount == 0:
                special_damage_reductions += defr.DR_sp_trigger_by_any_special_SP
                defr.DR_sp_trigger_by_any_special_SP = []

            if curAtk.attackNumSelf == 1:
                damage_reductions += defr.DR_first_hit_NSP
                damage_reductions += defr.DR_first_strikes_NSP

            if curAtk.attackNumSelf == 2:
                if atkr.brave:
                    damage_reductions += defr.DR_first_strikes_NSP
                else:
                    damage_reductions += defr.DR_second_strikes_NSP

            if curAtk.attackNumSelf >= 3:
                damage_reductions += defr.DR_second_strikes_NSP
            if curAtk.isConsecutive:
                damage_reductions += defr.DR_consec_strikes_NSP

            if defr.special_triggered and defender.getSpecialType() == "Offense":
                damage_reductions += defr.DR_sp_trigger_next_only_NSP
                defr.DR_sp_trigger_next_only_NSP = []

                special_damage_reductions += defr.DR_sp_trigger_next_only_SP
                defr.DR_sp_trigger_next_only_SP = []

                special_damage_reductions += defr.DR_sp_trigger_next_all_SP_CACHE
                defr.DR_sp_trigger_next_all_SP_CACHE = []

        if curAtk.attackOwner == 1:
            damage_reductions += atkr.DR_all_hits_NSP
            special_damage_reductions += atkr.DR_all_hits_SP

            if atkr.DR_great_aether_SP:
                if curAtk.isConsecutive:
                    special_damage_reductions.append(70 - (atkSpCountCur * 10))
                else:
                    special_damage_reductions.append(40 - (atkSpCountCur * 10))

            if atkr.special_triggered or attacker.specialCount == 0 or defr.special_triggered or defender.specialCount == 0:
                special_damage_reductions += atkr.DR_sp_trigger_by_any_special_SP
                atkr.DR_sp_trigger_by_any_special_SP = []

            if curAtk.attackNumSelf == 1:
                damage_reductions += atkr.DR_first_hit_NSP
                damage_reductions += atkr.DR_first_strikes_NSP

            if curAtk.attackNumSelf == 2:
                if defr.brave:
                    damage_reductions += atkr.DR_first_strikes_NSP
                else:
                    damage_reductions += atkr.DR_second_strikes_NSP

            if curAtk.attackNumSelf >= 3:
                damage_reductions += atkr.DR_second_strikes_NSP
            if curAtk.isConsecutive:
                damage_reductions += atkr.DR_consec_strikes_NSP

            if atkr.special_triggered and attacker.getSpecialType() == "Offense":
                damage_reductions += atkr.DR_sp_trigger_next_only_NSP
                atkr.DR_sp_trigger_next_only_NSP = []

                special_damage_reductions += atkr.DR_sp_trigger_next_only_SP
                atkr.DR_sp_trigger_next_only_SP = []


        # this should've been done at the start of the program
        roles = [attacker, defender]
        effects = [atkSpEffects, defSpEffects]
        stats = [atkStats, defStats]
        checkedDefs = [atkTargetingDefRes, defTargetingDefRes]
        curHPs = [atkHPCur, defHPCur]
        curSpCounts = [atkSpCountCur, defSpCountCur]

        # SpongebobPatrick
        spongebob = curAtk.attackOwner
        patrick = int(not curAtk.attackOwner)

        modifiers = [atkr, defr]

        strikeResult = attack(roles[spongebob], roles[patrick], effects[spongebob], effects[patrick], stats[spongebob],
                              stats[patrick], checkedDefs[spongebob],
                              damage_reductions, special_damage_reductions, curHPs[spongebob], curHPs[patrick],
                              curSpCounts[spongebob], curSpCounts[patrick],
                              modifiers[spongebob], modifiers[patrick], curAtk)

        atkHPCur = strikeResult[spongebob]
        defHPCur = strikeResult[patrick]

        atkSpCountCur = strikeResult[spongebob + 2]
        defSpCountCur = strikeResult[patrick + 2]

        damageDealt = strikeResult[4]
        healthHealed = strikeResult[5]

        stkSpecialTriggered = strikeResult[6]

        curAtk.impl_atk(stkSpecialTriggered, damageDealt, healthHealed, (atkSpCountCur, defSpCountCur), (atkHPCur, defHPCur))

        # I am dead
        if atkHPCur <= 0:
            atkHPCur = 0
            atkAlive = False
            if not is_in_sim: print(attacker.name + " falls.")
            curAtk.is_finisher = True

        if defHPCur <= 0:
            defHPCur = 0
            defAlive = False
            if not is_in_sim: print(defender.name + " falls.")
            curAtk.is_finisher = True

        i += 1  # increment buddy!

    # Post Combat Effects (that require the user to survive)

    if "specialSpiralW" in atkSkills and atkr.special_triggered:
        spiral_charge = math.ceil(atkSkills["specialSpiralW"] / 2)
        atkPostCombatEffs[0].append(("sp_charge", spiral_charge, "self", "one"))

    if "specialSpiralW" in defSkills and defSkills["specialSpiralW"] > 1 and defr.special_triggered:
        spiral_charge = math.ceil(defSkills["specialSpiralW"] / 2)
        defPostCombatEffs[0].append(("sp_charge", spiral_charge, "self", "one"))

    if "specialSpiralS" in atkSkills and atkr.special_triggered:
        atkPostCombatSpCharge += math.ceil(atkSkills["specialSpiralS"] / 2)

    if "specialSpiralS" in defSkills and defSkills["specialSpiralS"] > 1 and defr.special_triggered:
        defPostCombatSpCharge += math.ceil(defSkills["specialSpiralS"] / 2)

    if "infiniteSpecial" and atkHPGreaterEqual25Percent and attacker.specialCount == attacker.specialMax:
        atkPostCombatSpCharge += 1

    if "infiniteSpecial" and defHPGreaterEqual25Percent and defender.specialCount == defender.specialMax:
        defPostCombatSpCharge += 1

    # Cymbeline (Base) - Sanaki
    # Requires her to be alive
    if "sanakiBuff" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("buff_atk", 4, "allies", "within_1_spaces_self"))

    # Poison Strike
    if "poisonStrike" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("damage", atkSkills["poisonStrike"], "foe", "one"))

    # Breath of Life
    if "breath_of_life" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("heal", atkSkills["breath_of_life"], "allies", "within_1_spaces_self"))

    # Savage Blow
    if "savageBlow" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("damage", atkSkills["savageBlow"], "foes_allies", "within_2_spaces_foe"))

    if "easterHealA" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("heal", 4, "self", "one"))

    if "bridalBuffsA" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("buff_def", 2, "allies", "within_2_spaces_self"))
        atkPostCombatEffs[0].append(("buff_res", 2, "allies", "within_2_spaces_self"))

    if "clarisseDebuffA" in atkSkills and atkAlive:
        atkPostCombatEffs[0].append(("debuff_atk", 5, "foes_allies", "within_2_spaces_foe"))
        atkPostCombatEffs[0].append(("debuff_spd", 5, "foes_allies", "within_2_spaces_foe"))

    # ARE YA SMOKING YET?
    if "atkSmoke" in atkSkills and atkAlive: atkPostCombatEffs[0].append(("debuff_atk", atkSkills["atkSmoke"], "foes_allies", "within_2_spaces_foe"))
    if "atkSmoke" in defSkills and defAlive: defPostCombatEffs[0].append(("debuff_atk", defSkills["atkSmoke"], "foes_allies", "within_2_spaces_foe"))

    if "spdSmoke" in atkSkills and atkAlive: atkPostCombatEffs[0].append(("debuff_spd", atkSkills["spdSmoke"], "foes_allies", "within_2_spaces_foe"))
    if "spdSmoke" in defSkills and defAlive: defPostCombatEffs[0].append(("debuff_spd", defSkills["spdSmoke"], "foes_allies", "within_2_spaces_foe"))


    #if atkAlive: attacker.chargeSpecial(atkPostCombatSpCharge)
    #if defAlive: defender.chargeSpecial(defPostCombatSpCharge)

    # here ya go
    '''
    if atkAlive:
        for m in atkPostCombatStatusesApplied[0]:
            attacker.inflict(m)

    if defAlive:
        for n in defPostCombatStatusesApplied[0]:
            attacker.inflict(n)
    '''

    atkFehMath = min(max(atkStats[ATK] - defStats[atkTargetingDefRes + 3], 0) + atkr.true_all_hits, 99)
    defFehMath = min(max(defStats[ATK] - atkStats[defTargetingDefRes + 3], 0) + defr.true_all_hits, 99)

    if attacker.getWeaponType() == "Staff" and not atkr.wrathful_staff:
        atkFehMath = atkFehMath//2

    if defender.getWeaponType() == "Staff" and not defr.wrathful_staff:
        defFehMath = defFehMath//2

    atkHitCount = startString2.count("A")
    defHitCount = startString2.count("D")

    return atkHPCur, defHPCur, atkCombatBuffs, defCombatBuffs, wpnAdvHero, oneEffAtk, oneEffDef, \
        attackList, atkFehMath, atkHitCount, defFehMath, defHitCount, atkPostCombatEffs[0], defPostCombatEffs[0], burn_damages

# Get AOE damage from attacker to foe

def get_AOE_damage(attacker, defender):
    atkSkills = attacker.getSkills()
    atkStats = attacker.getStats()

    defSkills = defender.getSkills()
    defStats = defender.getStats()

    atkPhantomStats = [0] * 5
    defPhantomStats = [0] * 5

    if "phantomSpd" in atkSkills: atkPhantomStats[SPD] += atkSkills["phantomSpd"]
    if "phantomRes" in atkSkills: atkPhantomStats[RES] += atkSkills["phantomRes"]
    if "phantomSpd" in defSkills: defPhantomStats[SPD] += defSkills["phantomSpd"]
    if "phantomRes" in defSkills: defPhantomStats[RES] += defSkills["phantomRes"]

    # Panic Status Effect
    AtkPanicFactor = 1
    DefPanicFactor = 1

    # buffs + debuffs calculation
    # throughout combat, PanicFactor * buff produces the current buff value
    if Status.Panic in attacker.statusNeg: AtkPanicFactor *= -1
    if Status.Panic in defender.statusNeg: DefPanicFactor *= -1

    if Status.NullPanic in attacker.statusPos: AtkPanicFactor = 1
    if Status.NullPanic in defender.statusPos: DefPanicFactor = 1

    atkStats[ATK] += attacker.buffs[ATK] * AtkPanicFactor + attacker.debuffs[ATK]
    atkStats[SPD] += attacker.buffs[SPD] * AtkPanicFactor + attacker.debuffs[SPD]
    atkStats[DEF] += attacker.buffs[DEF] * AtkPanicFactor + attacker.debuffs[DEF]
    atkStats[RES] += attacker.buffs[RES] * AtkPanicFactor + attacker.debuffs[RES]

    defStats[ATK] += defender.buffs[ATK] * DefPanicFactor + defender.debuffs[ATK]
    defStats[SPD] += defender.buffs[SPD] * DefPanicFactor + defender.debuffs[SPD]
    defStats[DEF] += defender.buffs[DEF] * DefPanicFactor + defender.debuffs[DEF]
    defStats[RES] += defender.buffs[RES] * DefPanicFactor + defender.debuffs[RES]

    atkr_atk = atkStats[ATK]

    atkTargetingDefRes = int(attacker.getTargetedDef() == 1)

    def_disable_foe_hexblade = False

    if "disableFoeHexblade" in defSkills:
        def_disable_foe_hexblade = True

    if attacker.getTargetedDef() == 0 and not "oldDragonstone" in atkSkills and not def_disable_foe_hexblade:
        if defender.getRange() == 2 and defStats[3] > defStats[4]:
            atkTargetingDefRes += 1
        elif defender.getRange() != 2:
            atkTargetingDefRes += 1
    elif attacker.getTargetedDef() == 0:
        atkTargetingDefRes += 1

    if "permHexblade" in atkSkills and not def_disable_foe_hexblade: atkTargetingDefRes = int(defStats[3] < defStats[4])

    defr_def = defStats[3 + atkTargetingDefRes]

    power_int = atkSkills["aoe_power"]

    true_damage = 0

    if "SpdDmg" in atkSkills and atkStats[SPD] + atkPhantomStats[SPD] > defStats[SPD] + defPhantomStats[SPD]:
        difference = (atkStats[SPD] + atkPhantomStats[SPD]) - (defStats[SPD] + defPhantomStats[SPD])
        true_damage += min(math.trunc(difference * 0.1 * atkSkills["SpdDmg"]), atkSkills["SpdDmg"])

    if "gaius_damage_ref" in atkSkills and defStats[HP] == defender.HPcur:
        true_damage += 7

    if "DRINK" in atkSkills and defender.HPcur / defStats[HP] >= 0.75:
        true_damage += 7

    if "thraciaMoment" in atkSkills and defStats[DEF] >= defStats[RES] + 5:
        true_damage += 7

    if "spDamageAdd" in atkSkills:
        true_damage += atkSkills["spDamageAdd"]

    if "wrathSk" in atkSkills and attacker.HPcur/atkStats[HP] <= atkSkills["wrathSk"] * 0.25:
        true_damage += 10

    if power_int == 0:
        return max(trunc(0.8 * (atkr_atk - defr_def)), 0) + true_damage
    if power_int == 1:
        return max(atkr_atk - defr_def, 0) + true_damage
    if power_int == 2:
        return max(trunc(1.5 * (atkr_atk - defr_def)), 0) + true_damage


# FEH Math
# Atk - Def/Res + True Damage applied for all hits

# function should not deal damage to units/charge special/do post-combat things,
# these will be handled by wherever after the combat function is called

class Attack():
    def __init__(self, attackOwner, isFollowUp, isConsecutive, attackNumSelf, attackNumAll, prevAttack, potentRedu):
        self.attackOwner = attackOwner
        self.isFollowUp = isFollowUp
        self.isConsecutive = isConsecutive
        self.attackNumSelf = attackNumSelf
        self.attackNumAll = attackNumAll
        self.prevAttack = prevAttack

        self.isSpecial = False
        self.damage = -1
        self.spCharges = (-1, -1)
        self.curHPs = (-1, -1)
        self.healed = -1

        self.potentRedu = potentRedu

        self.is_finisher = False

    def impl_atk(self, isSpecial, damage, healed, spCharges, curHPs):
        self.isSpecial = isSpecial
        self.damage = damage
        self.spCharges = spCharges
        self.curHPs = curHPs
        self.healed = healed


# effects distributed to allies/foes within their combats
# this is a demo, final version should be placed within the map and initialized at the start of game

exRange1 = lambda s: lambda o: abs(s[0] - o[0]) <= 1  # within 3 columns centers on unit
exRange2 = lambda s: lambda o: abs(s[0] - o[0]) + abs(s[1] - o[1]) <= 2  # within 2 spaces
exCondition = lambda s: lambda o: o.hasPenalty()
exEffect = {"atkRein": 5, "defRein": 5}
flowerofease_base = {"atkRein": 3, "defRein": 3, "resRein": 3}
flowerofease_ref = {"atkRein": 4, "defRein": 4, "resRein": 4}


class CombatField():
    def __init__(self, owner, range, condition, affectSelf, affectedSide, effect):
        self.owner = owner
        self.range = range
        self.condition = condition(owner)
        self.affectSelf = affectSelf
        self.affectedSide = affectedSide  # 0 for same as owner, 1 otherwise
        self.effect = effect


# flowerOfEaseField = CombatField(mirabilis, exRange1, exCondition, False, True, flowerofease_base)

'''

# HIGHEST TRIANGLE ADEPT LEVEL USED
# SMALLER LEVELS DO NOT STACK WITH ONE ANOTHER
# ONLY HIGHEST LEVEL USED

sorceryBlade1 = Skill("Sorcery Blade 1",
                      "At start of combat, if unit’s HP = 100% and unit is adjacent to a magic ally, calculates damage using the lower of foe’s Def or Res.",
                      {"sorceryBlade": 1})
sorceryBlade2 = Skill("Sorcery Blade 2",
                      "At start of combat, if unit’s HP ≥ 50% and unit is adjacent to a magic ally, calculates damage using the lower of foe’s Def or Res.",
                      {"sorceryBlade": 2})
sorceryBlade3 = Skill("Sorcery Blade 3",
                      "At start of combat, if unit is adjacent to a magic ally, calculates damage using the lower of foe’s Def or Res.",
                      {"sorceryBlade": 3})
'''

# noah = Hero("Noah", 40, 42, 45, 35, 25, "Sword", 0, marthFalchion, luna, None, None, None)
# mio = Hero("Mio", 38, 39, 47, 27, 29, "BDagger", 0, tacticalBolt, moonbow, None, None, None)

player = Hero("Marth", "E!Marth", "Something", 0, "Sword", 0, [41, 45, 47, 33, 27], [50, 80, 90, 55, 40], 5, 165, 0)
enemy = Hero("Lucina", "B!Lucina", "Minecrafter", 0, "Lance", 0, [41, 34, 36, 27, 19], [50, 60, 60, 45, 35], 30, 165, 0)

player_weapon = Weapon("Hero-King Sword", "Hero-King Sword", "", 16, 1, "Sword", {"slaying": 1, "effDragon": 0}, {})
enemy_weapon = Weapon("Iron Lance", "Iron Lance", "", 6, 1, "Lance", {"shez!": 0}, {})

ragnell = Weapon("Emblem Ragnell", "Emblem Ragnell", "", 16, 1, "Sword", {"slaying": 1, "dCounter": 0, "BIGIKEFAN": 1018}, {})
GREAT_AETHER = Special("Great Aether", "", {"numFoeAtkBoostSp": 4, "AETHER_GREAT": 1018}, 4, "Offense")

lodestar_rush = Special("Lodestar Rush", "", {"spdBoostSp": 4, "tempo": 0, "potentFix": 100}, 2, "Offense")

player.set_skill(ragnell, WEAPON)
enemy.set_skill(enemy_weapon, WEAPON)

player.set_skill(GREAT_AETHER, SPECIAL)
'''
potent1 = Skill("Potent 1", "", {"potentStrike": 4})
laguz_friend4 = Skill("Laguz Friend 4", "", {"laguz_friend": 4})

player.set_skill(laguz_friend4, BSKILL)
enemy.set_skill(defStance, ASKILL)

player.chargeSpecial(1)
'''

#final_result = simulate_combat(player, enemy, False, 1, 2, [], False)

#print((final_result[0], final_result[1]))