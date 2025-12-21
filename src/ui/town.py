"""Town scene with trader NPC - Isometric style matching dungeon."""

import pygame
import math
from ..entities.item import create_weapon, create_armor, create_potion
from ..engine.constants import RARITY_COLORS


class Merchant:
    """NPC trader in town."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.name = "Valdris"
        self.color = (180, 140, 80)
        self.buy_rate = 0.5  # Pays 50% of item value
        self.sell_rate = 1.0  # Sells at full price
        self.radius = 0.5
        self.stock = []  # Items for sale
    
    def generate_stock(self, player_level):
        """Generate items appropriate for player level."""
        import random
        from ..entities.item import (
            RARITY_COMMON, RARITY_UNCOMMON, RARITY_RARE
        )
        
        self.stock = []
        
        # Always have potions (scaled quantity)
        num_health = 3 + player_level // 2
        num_mana = 2 + player_level // 3
        for _ in range(num_health):
            potion = create_potion('health', level=max(1, player_level))
            if potion:
                self.stock.append(potion)
        for _ in range(num_mana):
            potion = create_potion('mana', level=max(1, player_level))
            if potion:
                self.stock.append(potion)
        
        # Determine rarities available based on level
        # Low level: mostly common, High level: uncommon/rare available
        def pick_rarity():
            roll = random.random()
            if player_level >= 10 and roll < 0.1:
                return RARITY_RARE
            elif player_level >= 5 and roll < 0.3:
                return RARITY_UNCOMMON
            elif player_level >= 3 and roll < 0.2:
                return RARITY_UNCOMMON
            return RARITY_COMMON
        
        # WEAPONS - All main types, quantity scales with level
        weapon_types = [
            'short_sword', 'longsword', 'battle_axe', 'mace', 'dagger',
            'short_bow', 'longbow', 'crossbow', 'staff', 'wand'
        ]
        # Unlock more weapon types at higher levels
        available_weapons = weapon_types[:min(len(weapon_types), 4 + player_level // 2)]
        num_weapons = min(8, 3 + player_level // 3)
        
        for _ in range(num_weapons):
            wtype = random.choice(available_weapons)
            rarity = pick_rarity()
            weapon = create_weapon(wtype, rarity=rarity, level=player_level)
            if weapon:
                self.stock.append(weapon)
        
        # SHIELDS (off_hand) 
        shield_types = ['buckler', 'kite_shield', 'tower_shield']
        available_shields = shield_types[:min(len(shield_types), 1 + player_level // 4)]
        for stype in available_shields:
            rarity = pick_rarity()
            shield = create_armor(stype, rarity=rarity, level=player_level)
            if shield:
                self.stock.append(shield)
        
        # ARMOR - All slots
        # Head
        helm_types = ['leather_cap', 'chain_coif', 'plate_helm']
        available_helms = helm_types[:min(len(helm_types), 1 + player_level // 4)]
        for htype in available_helms:
            rarity = pick_rarity()
            helm = create_armor(htype, rarity=rarity, level=player_level)
            if helm:
                self.stock.append(helm)
        
        # Chest
        chest_types = ['leather_armor', 'chain_mail', 'plate_armor']
        available_chests = chest_types[:min(len(chest_types), 1 + player_level // 4)]
        for ctype in available_chests:
            rarity = pick_rarity()
            chest = create_armor(ctype, rarity=rarity, level=player_level)
            if chest:
                self.stock.append(chest)
        
        # Hands
        glove_types = ['leather_gloves', 'chain_gloves', 'plate_gauntlets']
        available_gloves = glove_types[:min(len(glove_types), 1 + player_level // 5)]
        for gtype in available_gloves:
            rarity = pick_rarity()
            gloves = create_armor(gtype, rarity=rarity, level=player_level)
            if gloves:
                self.stock.append(gloves)
        
        # Feet
        boot_types = ['leather_boots', 'chain_boots', 'plate_boots']
        available_boots = boot_types[:min(len(boot_types), 1 + player_level // 5)]
        for btype in available_boots:
            rarity = pick_rarity()
            boots = create_armor(btype, rarity=rarity, level=player_level)
            if boots:
                self.stock.append(boots)
        
        # Legs
        leg_types = ['leather_pants', 'chain_leggings', 'plate_greaves']
        available_legs = leg_types[:min(len(leg_types), 1 + player_level // 5)]
        for ltype in available_legs:
            rarity = pick_rarity()
            legs = create_armor(ltype, rarity=rarity, level=player_level)
            if legs:
                self.stock.append(legs)
        
        # Accessories at higher levels
        if player_level >= 5:
            # Ring
            ring = create_armor('ring', rarity=pick_rarity(), level=player_level)
            if ring:
                self.stock.append(ring)
        
        if player_level >= 8:
            # Amulet
            amulet = create_armor('amulet', rarity=pick_rarity(), level=player_level)
            if amulet:
                self.stock.append(amulet)
    
    def get_sell_price(self, item):
        """Get price trader will pay for item."""
        base_value = getattr(item, 'value', 10)
        return max(1, int(base_value * self.buy_rate))
    
    def get_buy_price(self, item):
        """Get price to buy item from trader."""
        base_value = getattr(item, 'value', 10)
        return int(base_value * self.sell_rate)
    
    def distance_to(self, other):
        if hasattr(other, 'x'):
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        return math.sqrt((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2)


class TownScene:
    """Town area with NPCs - Isometric view."""
    
    GRASS = 0
    PATH = 1
    WALL = 2
    WATER = 3
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active = False
        
        self.width = 20
        self.height = 15
        self.tile_width = 64
        self.tile_height = 32
        
        self.tiles = self._generate_town()
        self.merchant = Merchant(10, 8)
        self.portal_pos = (3, 8)
        
        # Trading state
        self.trading = False
        self.player_scroll = 0
        self.merchant_scroll = 0
        self.hovered_player_item = -1
        self.hovered_merchant_item = -1
        self.active_panel = 'player'  # 'player' or 'merchant'
        
        # Current trading character (player or ally)
        self.trading_character = None
        self.party = None  # Reference to full party
        self.party_index = 0  # Which party member is trading
        
        self.font_large = pygame.font.Font(None, 36)
        self.font_med = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        self.show_interact_prompt = False
        self.interact_target = None
        self.cam_x = 0
        self.cam_y = 0
    
    def _generate_town(self):
        tiles = [[self.GRASS for _ in range(self.width)] for _ in range(self.height)]
        
        for y in range(5, 12):
            for x in range(2, 18):
                tiles[y][x] = self.PATH
        
        for x in range(self.width):
            tiles[0][x] = self.WALL
            tiles[1][x] = self.WALL
            tiles[self.height - 1][x] = self.WALL
            tiles[self.height - 2][x] = self.WALL
        for y in range(self.height):
            tiles[y][0] = self.WALL
            tiles[y][self.width - 1] = self.WALL
        
        for y in range(2, 5):
            for x in range(8, 13):
                tiles[y][x] = self.WALL
        
        tiles[8][9] = self.WATER
        tiles[8][10] = self.WATER
        tiles[9][9] = self.WATER
        tiles[9][10] = self.WATER
        
        return tiles
    
    def _world_to_screen(self, wx, wy):
        sx = (wx - wy) * (self.tile_width // 2)
        sy = (wx + wy) * (self.tile_height // 2)
        sx += self.screen_width // 2 + self.cam_x
        sy += self.screen_height // 3 + self.cam_y
        return int(sx), int(sy)
    
    def _screen_to_world(self, sx, sy):
        sx -= self.screen_width // 2 + self.cam_x
        sy -= self.screen_height // 3 + self.cam_y
        wx = (sx / (self.tile_width // 2) + sy / (self.tile_height // 2)) / 2
        wy = (sy / (self.tile_height // 2) - sx / (self.tile_width // 2)) / 2
        return wx, wy
    
    def enter(self, player, party=None):
        """Enter town with player and party."""
        self.active = True
        self.trading = False
        self.party = party if party else [player]
        self.party_index = 0
        self.trading_character = player
        player.x = self.portal_pos[0] + 2
        player.y = self.portal_pos[1]
        player.path = []
        self._update_camera(player)
        # Generate merchant stock based on player level
        self.merchant.generate_stock(player.level)
    
    def exit(self):
        self.active = False
        self.trading = False
    
    def is_walkable(self, x, y):
        if x < 1 or x >= self.width - 1 or y < 2 or y >= self.height - 2:
            return False
        tile = self.tiles[int(y)][int(x)]
        return tile in (self.GRASS, self.PATH)
    
    def _update_camera(self, player):
        target_x, target_y = self._world_to_screen(player.x, player.y)
        self.cam_x += (self.screen_width // 2 - target_x) * 0.1
        self.cam_y += (self.screen_height // 2 - target_y) * 0.1
    
    def update(self, dt, player):
        if not self.active:
            return
        
        self._update_camera(player)
        
        dist_to_merchant = self.merchant.distance_to(player)
        if dist_to_merchant < 2.0:
            self.show_interact_prompt = True
            self.interact_target = 'merchant'
        elif abs(player.x - self.portal_pos[0]) < 1.5 and abs(player.y - self.portal_pos[1]) < 1.5:
            self.show_interact_prompt = True
            self.interact_target = 'portal'
        else:
            self.show_interact_prompt = False
            self.interact_target = None
    
    def handle_event(self, event, player):
        if not self.active:
            return None
        
        if self.trading:
            return self._handle_trading_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return self._try_interact(player)
            elif event.key == pygame.K_ESCAPE:
                return 'exit'
            elif event.key == pygame.K_UP:
                self._move_player(player, 0, -0.5)
            elif event.key == pygame.K_DOWN:
                self._move_player(player, 0, 0.5)
            elif event.key == pygame.K_LEFT:
                self._move_player(player, -0.5, 0)
            elif event.key == pygame.K_RIGHT:
                self._move_player(player, 0.5, 0)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                return self._handle_click(mx, my, player)
        
        return None
    
    def _move_player(self, player, dx, dy):
        new_x = player.x + dx
        new_y = player.y + dy
        if self.is_walkable(new_x, new_y):
            player.x = new_x
            player.y = new_y
    
    def _try_interact(self, player):
        if self.interact_target == 'merchant':
            self.trading = True
            self.player_scroll = 0
            self.merchant_scroll = 0
            self.hovered_player_item = -1
            self.hovered_merchant_item = -1
            self.trading_character = player
            self.party_index = 0
            return None
        elif self.interact_target == 'portal':
            return 'exit'
        return None
    
    def _handle_click(self, mx, my, player):
        world_x, world_y = self._screen_to_world(mx, my)
        
        if self.merchant.distance_to((world_x, world_y)) < 1.5:
            self.trading = True
            self.player_scroll = 0
            self.merchant_scroll = 0
            self.trading_character = player
            return None
        
        if abs(world_x - self.portal_pos[0]) < 1.5 and abs(world_y - self.portal_pos[1]) < 1.5:
            return 'exit'
        
        if self.is_walkable(world_x, world_y):
            player.x = world_x
            player.y = world_y
        
        return None
    
    def _handle_trading_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.trading = False
                return None
            elif event.key == pygame.K_TAB:
                # Cycle through party members
                if self.party and len(self.party) > 1:
                    self.party_index = (self.party_index + 1) % len(self.party)
                    self.trading_character = self.party[self.party_index]
                    self.player_scroll = 0
                    self.hovered_player_item = -1
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Close button
            if self._close_btn_rect().collidepoint(mx, my):
                self.trading = False
                return None
            
            # Character switch buttons
            if self.party and len(self.party) > 1:
                for i, char in enumerate(self.party):
                    btn_rect = pygame.Rect(40 + i * 80, 55, 70, 25)
                    if btn_rect.collidepoint(mx, my):
                        self.party_index = i
                        self.trading_character = char
                        self.player_scroll = 0
                        self.hovered_player_item = -1
                        return None
            
            # Sell item from player inventory
            if self.hovered_player_item >= 0:
                inv = self.trading_character.inventory
                if self.hovered_player_item < len(inv):
                    item = inv[self.hovered_player_item]
                    price = self.merchant.get_sell_price(item)
                    self.trading_character.gold += price
                    inv.remove(item)
                    self.hovered_player_item = -1
                    return None
            
            # Buy item from merchant
            if self.hovered_merchant_item >= 0:
                if self.hovered_merchant_item < len(self.merchant.stock):
                    item = self.merchant.stock[self.hovered_merchant_item]
                    price = self.merchant.get_buy_price(item)
                    if self.trading_character.gold >= price:
                        self.trading_character.gold -= price
                        self.trading_character.inventory.append(item)
                        self.merchant.stock.remove(item)
                        self.hovered_merchant_item = -1
                    return None
        
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._update_hover(mx, my)
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll whichever panel mouse is over
            if self.active_panel == 'player':
                max_scroll = max(0, len(self.trading_character.inventory) - 8)
                self.player_scroll = max(0, min(max_scroll, self.player_scroll - event.y))
            else:
                max_scroll = max(0, len(self.merchant.stock) - 8)
                self.merchant_scroll = max(0, min(max_scroll, self.merchant_scroll - event.y))
        
        return None
    
    def _close_btn_rect(self):
        return pygame.Rect(self.screen_width - 50, 15, 35, 35)
    
    def _update_hover(self, mx, my):
        self.hovered_player_item = -1
        self.hovered_merchant_item = -1
        
        # Left panel - player inventory
        left_x = 30
        left_start_y = 120
        item_h = 36
        
        for i in range(8):
            idx = self.player_scroll + i
            if idx >= len(self.trading_character.inventory):
                break
            item_rect = pygame.Rect(left_x, left_start_y + i * item_h, 340, 33)
            if item_rect.collidepoint(mx, my):
                self.hovered_player_item = idx
                self.active_panel = 'player'
                return
        
        # Right panel - merchant stock  
        right_x = self.screen_width // 2 + 30
        right_start_y = 120
        
        for i in range(8):
            idx = self.merchant_scroll + i
            if idx >= len(self.merchant.stock):
                break
            item_rect = pygame.Rect(right_x, right_start_y + i * item_h, 340, 33)
            if item_rect.collidepoint(mx, my):
                self.hovered_merchant_item = idx
                self.active_panel = 'merchant'
                return
        
        # Check which panel mouse is in for scrolling
        if mx < self.screen_width // 2:
            self.active_panel = 'player'
        else:
            self.active_panel = 'merchant'
    
    def render(self, screen, camera, player):
        if not self.active:
            return
        
        # Sky gradient
        for y in range(self.screen_height):
            ratio = y / self.screen_height
            r = int(135 + (100 - 135) * ratio)
            g = int(180 + (140 - 180) * ratio)
            b = int(220 + (180 - 220) * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (self.screen_width, y))
        
        for y in range(self.height):
            for x in range(self.width):
                self._render_tile(screen, x, y)
        
        self._render_portal(screen)
        self._render_merchant(screen)
        self._render_player(screen, player)
        
        if self.show_interact_prompt and not self.trading:
            self._render_interact_prompt(screen)
        
        self._render_hud(screen, player)
        
        if self.trading:
            self._render_trading_ui(screen)
    
    def _render_tile(self, screen, x, y):
        tile = self.tiles[y][x]
        sx, sy = self._world_to_screen(x, y)
        
        if tile == self.GRASS:
            top_color = (90, 160, 90)
        elif tile == self.PATH:
            top_color = (180, 160, 130)
        elif tile == self.WALL:
            top_color = (120, 100, 80)
        elif tile == self.WATER:
            time = pygame.time.get_ticks() / 1000
            wave = int(math.sin(time * 2 + x + y) * 15)
            top_color = (60 + wave, 120 + wave, 180 + wave)
        else:
            top_color = (100, 100, 100)
        
        hw = self.tile_width // 2
        hh = self.tile_height // 2
        
        top_points = [(sx, sy - hh), (sx + hw, sy), (sx, sy + hh), (sx - hw, sy)]
        pygame.draw.polygon(screen, top_color, top_points)
        pygame.draw.polygon(screen, (40, 40, 40), top_points, 1)
        
        if tile == self.WALL:
            height = 20
            left_pts = [(sx - hw, sy), (sx, sy + hh), (sx, sy + hh + height), (sx - hw, sy + height)]
            right_pts = [(sx + hw, sy), (sx, sy + hh), (sx, sy + hh + height), (sx + hw, sy + height)]
            pygame.draw.polygon(screen, (80, 65, 50), left_pts)
            pygame.draw.polygon(screen, (60, 45, 30), right_pts)
    
    def _render_portal(self, screen):
        sx, sy = self._world_to_screen(self.portal_pos[0], self.portal_pos[1])
        time = pygame.time.get_ticks() / 1000
        
        for i in range(3):
            radius = 20 + i * 8 + int(math.sin(time * 3 + i) * 4)
            alpha = 180 - i * 50
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (80, 140, 255, alpha), (radius, radius), radius, 3)
            screen.blit(surf, (sx - radius, sy - 10 - radius))
        
        pygame.draw.circle(screen, (150, 200, 255), (sx, sy - 10), 12)
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy - 10), 6)
        
        label = self.font_small.render("Dungeon", True, (200, 220, 255))
        screen.blit(label, (sx - label.get_width() // 2, sy - 45))
    
    def _render_merchant(self, screen):
        sx, sy = self._world_to_screen(self.merchant.x, self.merchant.y)
        
        shadow = pygame.Surface((30, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
        screen.blit(shadow, (sx - 15, sy + 5))
        
        body = pygame.Rect(sx - 10, sy - 25, 20, 30)
        pygame.draw.ellipse(screen, self.merchant.color, body)
        pygame.draw.ellipse(screen, (40, 40, 40), body, 2)
        pygame.draw.circle(screen, (220, 180, 140), (sx, sy - 30), 8)
        
        name = self.font_small.render(self.merchant.name, True, (255, 220, 150))
        rect = name.get_rect(center=(sx, sy - 50))
        bg = rect.inflate(10, 4)
        pygame.draw.rect(screen, (40, 35, 30, 200), bg)
        screen.blit(name, rect)
    
    def _render_player(self, screen, player):
        sx, sy = self._world_to_screen(player.x, player.y)
        
        shadow = pygame.Surface((24, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
        screen.blit(shadow, (sx - 12, sy + 3))
        
        body = pygame.Rect(sx - 8, sy - 20, 16, 24)
        pygame.draw.ellipse(screen, player.color, body)
        pygame.draw.ellipse(screen, (40, 40, 40), body, 2)
    
    def _render_interact_prompt(self, screen):
        if self.interact_target == 'merchant':
            sx, sy = self._world_to_screen(self.merchant.x, self.merchant.y)
            text = "SPACE / Click to Trade"
        else:
            sx, sy = self._world_to_screen(self.portal_pos[0], self.portal_pos[1])
            text = "SPACE / Click to Return"
        
        prompt = self.font_med.render(text, True, (255, 255, 200))
        rect = prompt.get_rect(center=(sx, sy - 70))
        bg = rect.inflate(16, 8)
        pygame.draw.rect(screen, (30, 30, 50, 220), bg)
        pygame.draw.rect(screen, (100, 100, 140), bg, 2)
        screen.blit(prompt, rect)
    
    def _render_hud(self, screen, player):
        gold = self.font_med.render(f"Gold: {player.gold}", True, (255, 215, 0))
        pygame.draw.rect(screen, (30, 30, 40, 180), (15, 15, gold.get_width() + 20, 35))
        screen.blit(gold, (25, 22))
        
        title = self.font_large.render("Stonebrook Village", True, (220, 200, 180))
        screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))
    
    def _render_trading_ui(self, screen):
        # Full screen overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        char = self.trading_character
        
        # === HEADER ===
        header = self.font_large.render(f"Trading with {self.merchant.name}", True, (220, 200, 160))
        screen.blit(header, (self.screen_width // 2 - header.get_width() // 2, 15))
        
        # Party member tabs (if party exists)
        if self.party and len(self.party) > 1:
            for i, member in enumerate(self.party):
                btn_rect = pygame.Rect(40 + i * 100, 50, 90, 28)
                if i == self.party_index:
                    pygame.draw.rect(screen, (80, 70, 100), btn_rect)
                    pygame.draw.rect(screen, (140, 130, 170), btn_rect, 2)
                else:
                    pygame.draw.rect(screen, (50, 45, 60), btn_rect)
                    pygame.draw.rect(screen, (80, 75, 95), btn_rect, 1)
                
                name = self.font_small.render(member.name[:10], True, (200, 200, 200))
                screen.blit(name, (btn_rect.x + 5, btn_rect.y + 5))
            
            tab_hint = self.font_small.render("TAB to switch", True, (120, 120, 140))
            screen.blit(tab_hint, (40 + len(self.party) * 100 + 10, 55))
        
        # === LEFT PANEL: Player Inventory (SELL) ===
        left_panel = pygame.Rect(25, 90, 370, 430)
        pygame.draw.rect(screen, (45, 40, 55), left_panel)
        pygame.draw.rect(screen, (100, 90, 120), left_panel, 2)
        
        # Title
        sell_title = self.font_med.render(f"{char.name}'s Inventory (SELL)", True, (200, 180, 160))
        screen.blit(sell_title, (left_panel.x + 10, left_panel.y + 8))
        
        # Gold
        gold = self.font_small.render(f"Gold: {char.gold}", True, (255, 215, 0))
        screen.blit(gold, (left_panel.right - 90, left_panel.y + 10))
        
        pygame.draw.line(screen, (80, 70, 100),
                        (left_panel.x + 5, left_panel.y + 35),
                        (left_panel.right - 5, left_panel.y + 35), 1)
        
        # Items
        item_y = left_panel.y + 42
        item_h = 36
        items_shown = 8
        
        inv = char.inventory
        if len(inv) == 0:
            empty = self.font_med.render("Empty", True, (100, 100, 110))
            screen.blit(empty, (left_panel.x + 150, left_panel.y + 150))
        else:
            for i in range(items_shown):
                idx = self.player_scroll + i
                if idx >= len(inv):
                    break
                
                item = inv[idx]
                rect = pygame.Rect(left_panel.x + 5, item_y + i * item_h, left_panel.width - 10, item_h - 3)
                
                if idx == self.hovered_player_item:
                    pygame.draw.rect(screen, (70, 65, 85), rect)
                    pygame.draw.rect(screen, (150, 140, 180), rect, 2)
                else:
                    pygame.draw.rect(screen, (55, 50, 65), rect)
                
                # Rarity color (rarity is an int, use RARITY_COLORS dict)
                rarity = getattr(item, 'rarity', 0)
                color = RARITY_COLORS.get(rarity, (200, 200, 200))
                
                name = self.font_small.render(item.name[:28], True, color)
                screen.blit(name, (rect.x + 8, rect.y + 8))
                
                price = self.merchant.get_sell_price(item)
                price_text = self.font_small.render(f"+{price}g", True, (100, 255, 100))
                screen.blit(price_text, (rect.right - 55, rect.y + 8))
            
            if len(inv) > items_shown:
                scroll = self.font_small.render(f"↕ {self.player_scroll+1}-{min(self.player_scroll+items_shown, len(inv))}/{len(inv)}", True, (120, 120, 140))
                screen.blit(scroll, (left_panel.x + 140, left_panel.bottom - 25))
        
        # === RIGHT PANEL: Merchant Stock (BUY) ===
        right_panel = pygame.Rect(self.screen_width // 2 + 15, 90, 370, 430)
        pygame.draw.rect(screen, (50, 45, 40), right_panel)
        pygame.draw.rect(screen, (120, 100, 80), right_panel, 2)
        
        buy_title = self.font_med.render(f"{self.merchant.name}'s Goods (BUY)", True, (255, 220, 180))
        screen.blit(buy_title, (right_panel.x + 10, right_panel.y + 8))
        
        pygame.draw.line(screen, (100, 85, 70),
                        (right_panel.x + 5, right_panel.y + 35),
                        (right_panel.right - 5, right_panel.y + 35), 1)
        
        stock = self.merchant.stock
        if len(stock) == 0:
            empty = self.font_med.render("Sold Out!", True, (140, 120, 100))
            screen.blit(empty, (right_panel.x + 130, right_panel.y + 150))
        else:
            for i in range(items_shown):
                idx = self.merchant_scroll + i
                if idx >= len(stock):
                    break
                
                item = stock[idx]
                rect = pygame.Rect(right_panel.x + 5, item_y + i * item_h, right_panel.width - 10, item_h - 3)
                
                price = self.merchant.get_buy_price(item)
                can_afford = char.gold >= price
                
                if idx == self.hovered_merchant_item:
                    bg_color = (75, 70, 60) if can_afford else (70, 50, 50)
                    pygame.draw.rect(screen, bg_color, rect)
                    pygame.draw.rect(screen, (180, 160, 120) if can_afford else (150, 80, 80), rect, 2)
                else:
                    pygame.draw.rect(screen, (60, 55, 50), rect)
                
                # Rarity color
                rarity = getattr(item, 'rarity', 0)
                color = RARITY_COLORS.get(rarity, (200, 200, 200))
                
                if not can_afford:
                    color = tuple(c // 2 for c in color)
                
                name = self.font_small.render(item.name[:28], True, color)
                screen.blit(name, (rect.x + 8, rect.y + 8))
                
                price_color = (255, 215, 0) if can_afford else (180, 100, 100)
                price_text = self.font_small.render(f"{price}g", True, price_color)
                screen.blit(price_text, (rect.right - 50, rect.y + 8))
            
            if len(stock) > items_shown:
                scroll = self.font_small.render(f"↕ {self.merchant_scroll+1}-{min(self.merchant_scroll+items_shown, len(stock))}/{len(stock)}", True, (140, 130, 110))
                screen.blit(scroll, (right_panel.x + 140, right_panel.bottom - 25))
        
        # Close button
        close = self._close_btn_rect()
        pygame.draw.rect(screen, (120, 50, 50), close)
        pygame.draw.rect(screen, (180, 80, 80), close, 2)
        x = self.font_large.render("X", True, (255, 255, 255))
        screen.blit(x, (close.x + 9, close.y + 3))
        
        # Instructions
        instr = self.font_small.render("Click items to buy/sell | Scroll with mouse wheel | ESC to close", True, (140, 140, 150))
        screen.blit(instr, (self.screen_width // 2 - instr.get_width() // 2, self.screen_height - 30))


class PortalButton:
    """Blue portal button on HUD."""
    
    def __init__(self, x, y, size=50):
        self.rect = pygame.Rect(x, y, size, size)
        self.pulse = 0
    
    def update(self, dt):
        self.pulse += dt * 3
    
    def handle_click(self, mx, my):
        return self.rect.collidepoint(mx, my)
    
    def render(self, screen):
        pulse_size = int(5 * abs(math.sin(self.pulse)))
        glow = self.rect.inflate(pulse_size * 2, pulse_size * 2)
        glow_surf = pygame.Surface((glow.width, glow.height), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (50, 100, 200, 80), glow_surf.get_rect())
        screen.blit(glow_surf, glow.topleft)
        
        pygame.draw.ellipse(screen, (30, 60, 120), self.rect)
        pygame.draw.ellipse(screen, (80, 140, 220), self.rect, 3)
        
        center = self.rect.center
        inner = self.rect.inflate(-15, -15)
        pygame.draw.ellipse(screen, (60, 120, 200), inner)
        
        for i in range(4):
            angle = self.pulse + i * (math.pi / 2)
            dx = int(math.cos(angle) * 12)
            dy = int(math.sin(angle) * 12)
            pygame.draw.line(screen, (150, 200, 255), center, (center[0] + dx, center[1] + dy), 2)
        
        pygame.draw.circle(screen, (200, 230, 255), center, 5)
        
        font = pygame.font.Font(None, 18)
        label = font.render("Town", True, (255, 255, 255))
        screen.blit(label, (center[0] - 14, center[1] + 25))
