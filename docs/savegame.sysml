/**
 * Dungeon Siege Save Game Data Model
 * SysML v2 Specification
 * 
 * This specification defines the structure of save game files
 * to ensure forward/backward compatibility across game versions.
 * 
 * Save Format: JSON
 * File Extension: .json
 * Location: saves/save_{slot}.json
 */

package SaveGameModel {
    
    import ScalarValues::*;
    
    // ============================================
    // METADATA & VERSIONING
    // ============================================
    
    /**
     * Root save game structure.
     * Version field MUST be incremented when breaking changes occur.
     * Loaders should handle all versions <= current.
     */
    part def SaveGame {
        attribute version : Integer;           // Schema version (increment on breaking changes)
        attribute timestamp : String;          // ISO 8601 datetime of save
        attribute gameVersion : String;        // Game version that created save (optional)
        
        // World state
        attribute dungeonLevel : Integer;      // Current dungeon depth (1-based)
        attribute dungeonSeed : Integer;       // RNG seed for deterministic generation
        attribute gold : Integer;              // Party gold pool
        
        // Party members
        part party : Character[1..*];          // At least one character required
        
        // Future expansion slots (nullable)
        attribute questState : QuestState[0..1];
        attribute worldFlags : WorldFlags[0..1];
        attribute statistics : GameStatistics[0..1];
    }
    
    // ============================================
    // CHARACTER DATA
    // ============================================
    
    /**
     * Character represents a player or party member.
     * All numeric stats should be restored exactly.
     */
    part def Character {
        // Identity
        attribute name : String;               // Display name
        attribute charClass : String;          // 'warrior', 'mage', 'ranger', 'cleric' (optional)
        attribute isPlayerControlled : Boolean;
        attribute color : Integer[3];          // RGB tuple for rendering
        
        // Position
        attribute x : Real;
        attribute y : Real;
        
        // Progression
        attribute level : Integer;
        attribute experience : Integer;
        
        // Vitals
        attribute health : Integer;
        attribute maxHealth : Integer;
        attribute mana : Integer;
        attribute maxMana : Integer;
        
        // Attributes
        attribute strength : Integer;
        attribute dexterity : Integer;
        attribute intelligence : Integer;
        
        // Skills (usage-based leveling, DS1 style)
        part skills : SkillSet;
        part skillXp : SkillXpSet;
        
        // Wealth
        attribute gold : Integer;              // Character's personal gold
        
        // Inventory & Equipment
        part inventory : Item[0..*];           // Carried items
        part equipment : EquipmentSlots;       // Currently equipped
        
        // Magic
        attribute spellsKnown : String[0..*];  // Spell IDs character has learned
        
        // State flags
        attribute isDowned : Boolean;          // Incapacitated but revivable
        attribute downTimer : Real;            // Time remaining before permadeath
        
        // AI (for non-player characters)
        attribute formationOffsetX : Real;
        attribute formationOffsetY : Real;
    }
    
    /**
     * Skill levels by type.
     * Keys: 'melee', 'ranged', 'combat_magic', 'nature_magic'
     */
    part def SkillSet {
        attribute melee : Integer default 0;
        attribute ranged : Integer default 0;
        attribute combatMagic : Integer default 0;
        attribute natureMagic : Integer default 0;
    }
    
    /**
     * Skill XP progress toward next level.
     */
    part def SkillXpSet {
        attribute melee : Integer default 0;
        attribute ranged : Integer default 0;
        attribute combatMagic : Integer default 0;
        attribute natureMagic : Integer default 0;
    }
    
    // ============================================
    // EQUIPMENT SLOTS
    // ============================================
    
    /**
     * Equipment slots matching DS1 style.
     */
    part def EquipmentSlots {
        part head : Item[0..1];
        part chest : Item[0..1];
        part hands : Item[0..1];
        part feet : Item[0..1];
        part mainHand : Item[0..1];
        part offHand : Item[0..1];
        part ring1 : Item[0..1];
        part ring2 : Item[0..1];
        part amulet : Item[0..1];
    }
    
    // ============================================
    // ITEMS
    // ============================================
    
    /**
     * Base item definition.
     * Use 'type' discriminator to determine subtype.
     */
    part def Item {
        // Common fields
        attribute name : String;
        attribute weight : Real;
        attribute value : Integer;             // Base gold value
        attribute rarity : Integer;            // 0=common, 1=uncommon, 2=rare, 3=epic, 4=legendary
        attribute type : String;               // 'equipment' or 'consumable'
        
        // Equipment-specific (when type='equipment')
        attribute slot : String;               // Equipment slot name
        attribute armor : Integer;
        attribute damage : Integer;
        attribute weaponType : String;         // 'melee', 'ranged', 'magic'
        attribute attackRange : Real;
        attribute strengthBonus : Integer;
        attribute dexterityBonus : Integer;
        attribute intelligenceBonus : Integer;
        attribute healthBonus : Integer;
        attribute manaBonus : Integer;
        attribute levelReq : Integer;          // Minimum level to equip
        
        // Consumable-specific (when type='consumable')
        attribute effectType : String;         // 'health', 'mana', etc.
        attribute effectValue : Integer;       // Amount restored/affected
    }
    
    // ============================================
    // FUTURE EXPANSION STRUCTURES
    // ============================================
    
    /**
     * Quest progress tracking (future).
     */
    part def QuestState {
        attribute activeQuests : QuestProgress[0..*];
        attribute completedQuests : String[0..*];  // Quest IDs
    }
    
    part def QuestProgress {
        attribute questId : String;
        attribute stage : Integer;
        attribute objectives : ObjectiveProgress[0..*];
    }
    
    part def ObjectiveProgress {
        attribute objectiveId : String;
        attribute current : Integer;
        attribute target : Integer;
    }
    
    /**
     * World state flags (future).
     */
    part def WorldFlags {
        attribute unlockedAreas : String[0..*];
        attribute defeatedBosses : String[0..*];
        attribute discoveredSecrets : String[0..*];
        attribute npcStates : NpcState[0..*];
    }
    
    part def NpcState {
        attribute npcId : String;
        attribute disposition : Integer;       // Friendship/reputation
        attribute flags : String[0..*];        // State flags
    }
    
    /**
     * Game statistics (future).
     */
    part def GameStatistics {
        attribute playTime : Real;             // Seconds
        attribute enemiesKilled : Integer;
        attribute damageDealt : Integer;
        attribute damageTaken : Integer;
        attribute goldCollected : Integer;
        attribute itemsFound : Integer;
        attribute deathCount : Integer;
        attribute floorsExplored : Integer;
    }
    
    // ============================================
    // VERSION HISTORY
    // ============================================
    
    /**
     * Version 1 (Initial):
     *   - Basic character data
     *   - Inventory and equipment
     *   - Dungeon level and seed
     *   - Party gold
     * 
     * Version 2 (Planned):
     *   - Add charClass field
     *   - Add isDowned/downTimer
     *   - Add formation offsets
     * 
     * Version 3 (Planned):
     *   - Add questState
     *   - Add worldFlags
     *   - Add statistics
     */
    
    // ============================================
    // MIGRATION RULES
    // ============================================
    
    comment MigrationRules {
        /**
         * When loading older saves:
         * 
         * v1 -> v2:
         *   - charClass defaults to 'warrior' if not present
         *   - isDowned defaults to false
         *   - downTimer defaults to 0
         *   - formationOffset defaults to (1.5, 1.5) for non-player chars
         * 
         * General rules:
         *   - Missing optional fields use sensible defaults
         *   - Unknown fields are preserved but ignored
         *   - Invalid values are replaced with defaults
         *   - Corrupted saves should fail gracefully with user message
         */
    }
}

