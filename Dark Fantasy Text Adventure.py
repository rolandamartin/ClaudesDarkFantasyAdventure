import pygame
import random
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum, auto
from pygame import mixer, freetype
import os
from pathlib import Path

# File paths - Update these to match your actual file locations
if os.path.exists("background.png"):
    # If files are in the same folder as the script
    BASE_PATH = Path(".")
else:
    #If files are not found
    print ("Files are improperly placed.")
    pygame.quit()

BACKGROUND_IMG = BASE_PATH / "background.png"
TYPEWRITER_SOUND = BASE_PATH / "typewriter.mp3"
BACKGROUND_AMBIANCE = BASE_PATH / "backgroundambiance.mp3"
FONT_PATH = BASE_PATH / "NIGHTMARE_PILLS.ttf"

# Colors
PARCHMENT_YELLOW = (230, 213, 167)  # #E6D5A7
DARK_PARCHMENT = (168, 159, 129)    # #A89F81
DARKER_BG = (42, 38, 34)            # #2A2622
TRANSPARENT_BLACK = (0, 0, 0, 128)   # For overlay effects

# UI Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
STATS_BOX_WIDTH = 250
STATS_BOX_HEIGHT = 300
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 60
TEXT_AREA_WIDTH = 700

class Skill(Enum):
    OCCULTISM = ("Occultism", "Knowledge of forbidden arts")
    COMBAT = ("Combat", "Martial prowess")
    PERSUASION = ("Persuasion", "Social influence")
    SURVIVAL = ("Survival", "Adaptability in harsh conditions")
    LORE = ("Lore", "Ancient knowledge")
    WILLPOWER = ("Willpower", "Mental fortitude")
    
    def __init__(self, display_name: str, description: str):
        self.display_name = display_name
        self.description = description

@dataclass
class Location:
    name: str
    description: str
    is_discovered: bool = False
    is_cleared: bool = False
    required_trials: int = 0
    trials_completed: int = 0

class TextRenderer:
    def __init__(self, screen, font, sound):
        self.screen = screen
        self.font = font
        self.sound = sound
        self.current_text = ""
        self.target_text = ""
        self.text_pos = (300, 200)  # Moved right to avoid skills box
        self.char_delay = 50
        self.last_char_time = 0
        self.text_color = PARCHMENT_YELLOW
        self.line_spacing = 30
        self.max_line_width = 650  # Reduced to avoid right side stats
        self.next_char_index = 0
        
    def set_text(self, text: str):
        """Set new text to be rendered."""
        self.target_text = text.replace('\\n', '\n')  # Handle explicit line breaks
        self.current_text = ""
        self.next_char_index = 0
        
    def update(self, current_time):
        """Update the current text being displayed."""
        if self.next_char_index < len(self.target_text):
            if current_time - self.last_char_time > self.char_delay:
                # Add next character
                self.current_text += self.target_text[self.next_char_index]
                self.next_char_index += 1
                
                # Play sound with random pitch for non-space characters
                if self.target_text[self.next_char_index - 1] not in [' ', '\n']:
                    pitch = random.uniform(0.8, 1.2)
                    self.sound.set_volume(0.3)
                    self.sound.play()
                    # Note: In newer Pygame versions, you might be able to use:
                    # pygame.mixer.Sound.play(self.sound, pitch=pitch)
                
                self.last_char_time = current_time
                
    def render(self):
        """Render the current text to the screen with proper word wrapping."""
        words = self.current_text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Handle explicit line breaks in words
            if '\n' in word:
                subwords = word.split('\n')
                for i, subword in enumerate(subwords):
                    if subword:  # If not empty
                        current_line.append(subword)
                    if i < len(subwords) - 1:  # Don't add after last subword
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = []
                continue
                
            test_line = ' '.join(current_line + [word])
            test_surface = self.font.render(test_line, True, self.text_color)
            
            if test_surface.get_width() > self.max_line_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)
                
        if current_line:
            lines.append(' '.join(current_line))
            
        # Render each line
        y = self.text_pos[1]
        for line in lines:
            if line:  # Only render non-empty lines
                text_surface = self.font.render(line, True, self.text_color)
                self.screen.blit(text_surface, (self.text_pos[0], y))
            y += self.line_spacing

class StatsDisplay:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = pygame.font.Font(None, 20)  # Smaller font for stats
        # Core stats display (top right)
        self.core_stats_rect = pygame.Rect(
            WINDOW_WIDTH - STATS_BOX_WIDTH - 10,
            10,
            STATS_BOX_WIDTH,
            100
        )
        # Skills display (top left)
        self.skills_rect = pygame.Rect(
            10,
            10,
            STATS_BOX_WIDTH,
            STATS_BOX_HEIGHT
        )
        self.bar_height = 12  # Reduced from 15
        self.bar_padding = 4  # Reduced from 5
        self.section_padding = 15  # Reduced from 20

    def draw_stat_bar(self, pos, value, max_value, name, color=PARCHMENT_YELLOW):
        """Draw a labeled stat bar."""
        x, y = pos
        width = self.core_stats_rect.width - 20  # Reduced padding
        
        # Draw label
        label = self.font.render(name, True, PARCHMENT_YELLOW)
        self.screen.blit(label, (x, y))
        
        # Draw bar background
        bar_bg_rect = pygame.Rect(x, y + 15, width, self.bar_height)  # Adjusted spacing
        pygame.draw.rect(self.screen, DARKER_BG, bar_bg_rect)
        
        # Draw bar fill
        fill_width = int((value / max_value) * width)
        bar_fill_rect = pygame.Rect(x, y + 15, fill_width, self.bar_height)
        pygame.draw.rect(self.screen, color, bar_fill_rect)
        
        # Draw value text in smaller font
        value_text = self.font.render(f"{value}%", True, PARCHMENT_YELLOW)
        text_pos = (x + width + 5, y + 8)
        self.screen.blit(value_text, text_pos)

    def render(self, core_stats: Dict, skills: Dict):
        """Render both core stats and skills."""
        # Draw backgrounds with reduced alpha
        s = pygame.Surface((self.core_stats_rect.width, self.core_stats_rect.height))
        s.set_alpha(100)
        s.fill((0, 0, 0))
        self.screen.blit(s, self.core_stats_rect)
        
        s = pygame.Surface((self.skills_rect.width, self.skills_rect.height))
        s.set_alpha(100)
        s.fill((0, 0, 0))
        self.screen.blit(s, self.skills_rect)
        
        # Draw core stats
        y_offset = self.core_stats_rect.top + 8
        for stat_name, value in core_stats.items():
            self.draw_stat_bar(
                (self.core_stats_rect.left + 10, y_offset),
                value,
                100,
                stat_name
            )
            y_offset += 30  # Reduced spacing
            
        # Draw skills
        y_offset = self.skills_rect.top + 8
        title = self.font.render("SKILLS", True, PARCHMENT_YELLOW)
        self.screen.blit(title, (self.skills_rect.left + 10, y_offset))
        y_offset += 25  # Reduced spacing
        
        for skill, value in skills.items():
            self.draw_stat_bar(
                (self.skills_rect.left + 10, y_offset),
                value,
                20,  # Max skill value
                skill.display_name,
                DARK_PARCHMENT
            )
            y_offset += 30  # Reduced spacing
        
    def draw_stat_bar(self, pos, value, max_value, name, color=PARCHMENT_YELLOW):
        """Draw a labeled stat bar."""
        x, y = pos
        width = self.core_stats_rect.width - 40
        
        # Draw label
        label = self.font.render(name, True, PARCHMENT_YELLOW)
        self.screen.blit(label, (x, y))
        
        # Draw bar background
        bar_bg_rect = pygame.Rect(x, y + 20, width, self.bar_height)
        pygame.draw.rect(self.screen, DARKER_BG, bar_bg_rect)
        
        # Draw bar fill
        fill_width = int((value / max_value) * width)
        bar_fill_rect = pygame.Rect(x, y + 20, fill_width, self.bar_height)
        pygame.draw.rect(self.screen, color, bar_fill_rect)
        
        # Draw value text
        value_text = self.font.render(f"{value}%", True, PARCHMENT_YELLOW)
        text_pos = (x + width + 5, y + 10)
        self.screen.blit(value_text, text_pos)
        
    def render(self, core_stats: Dict, skills: Dict):
        """Render both core stats and skills."""
        # Draw backgrounds
        pygame.draw.rect(self.screen, TRANSPARENT_BLACK, self.core_stats_rect)
        pygame.draw.rect(self.screen, TRANSPARENT_BLACK, self.skills_rect)
        
        # Draw core stats
        y_offset = self.core_stats_rect.top + 10
        for stat_name, value in core_stats.items():
            self.draw_stat_bar(
                (self.core_stats_rect.left + 20, y_offset),
                value,
                100,
                stat_name
            )
            y_offset += 35
            
        # Draw skills
        y_offset = self.skills_rect.top + 10
        title = self.font.render("SKILLS", True, PARCHMENT_YELLOW)
        self.screen.blit(title, (self.skills_rect.left + 20, y_offset))
        y_offset += 30
        
        for skill, value in skills.items():
            self.draw_stat_bar(
                (self.skills_rect.left + 20, y_offset),
                value,
                20,  # Max skill value
                skill.display_name,
                DARK_PARCHMENT
            )
            y_offset += 40

class Button:
    def __init__(self, rect, text, action, font):
        self.rect = rect
        self.text = text
        self.action = action
        self.font = font
        self.is_hovered = False
        self.normal_color = DARKER_BG
        self.hover_color = (62, 58, 54)  # Slightly lighter than DARKER_BG
        self.text_color = PARCHMENT_YELLOW
        self.border_color = DARK_PARCHMENT
        
    def draw(self, screen):
        # Draw button background
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)  # Border
        
        # Draw text centered on button
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return self.action
        return None

class DarkFantasyGame:
    def __init__(self):
        pygame.init()
        mixer.init()
        
        # Set up display
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Dark Path")

        # Load font with smaller sizes
        try:
            self.font = pygame.font.Font("NIGHTMARE_PILLS.ttf", 24)  # Reduced from 32
            self.button_font = pygame.font.Font("NIGHTMARE_PILLS.ttf", 20)  # Reduced from 28
        except:
            print("Warning: Custom font not found, using default font")
            self.font = pygame.font.Font(None, 24)
            self.button_font = pygame.font.Font(None, 20)
        
        # Load and scale background
        self.background = pygame.image.load(str(BACKGROUND_IMG))
        self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Apply strong blur effect
        small = pygame.transform.smoothscale(self.background, (256, 192))
        smaller = pygame.transform.smoothscale(small, (128, 96))
        self.background = pygame.transform.smoothscale(smaller, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Add dark overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)
        self.background.blit(overlay, (0, 0))
        
        # Set up audio
        self.typewriter_sound = mixer.Sound(str(TYPEWRITER_SOUND))
        mixer.music.load(str(BACKGROUND_AMBIANCE))
        mixer.music.play(-1)
        mixer.music.set_volume(0.3)
        
        # Set up UI elements
        self.text_renderer = TextRenderer(self.screen, self.font, self.typewriter_sound)
        self.stats_display = StatsDisplay(self.screen, self.font)
        self.buttons = []
        
        # Initialize game state
        self.initialize_game_state()
        
        # Game flow control
        self.current_state = 'intro'
        self.awaiting_choice = False
        self.current_encounter = None

    def initialize_game_state(self):
        """Initialize all game variables."""
        # Core stats
        self.health = 100
        self.sanity = 100
        self.corruption = 0
        self.encounters_completed = 0
        
        # Generate character skills
        self.skills = {}
        available_skills = list(Skill)
        primary_skill, secondary_skill = random.sample(available_skills, 2)
        
        for skill in available_skills:
            if skill == primary_skill:
                self.skills[skill] = sum(random.randint(1, 6) for _ in range(4))
            elif skill == secondary_skill:
                self.skills[skill] = sum(random.randint(1, 6) for _ in range(3))
            else:
                self.skills[skill] = sum(random.randint(1, 6) for _ in range(2))
        
        # Game state flags
        self.flags = {
            'has_ritual_knowledge': False,
            'encountered_witch': False,
            'priest_alive': True,
            'ancient_door_opened': False,
            'made_deal_with_creature': False,
            'found_ancient_tome': False,
            'cursed_by_witch': False
        }
        
        # Procedural elements
        self.current_weather = random.choice(['stormy', 'misty', 'clear but dark'])
        self.moon_phase = random.choice(['new', 'waxing', 'full', 'waning'])
        self.village_state = random.choice(['fearful', 'hostile', 'desperate'])
        
        # Location tracking
        self.locations = {
            'ancient_ruins': Location(
                'Ancient Ruins',
                'A crumbling structure emanating dark energy',
                required_trials=3
            ),
            'witch_hut': Location(
                'Witch\'s Hut',
                'A crooked cottage deep in the woods'
            ),
            'forbidden_grove': Location(
                'Forbidden Grove',
                'A twisted grove where the trees whisper'
            )
        }

    def create_choice_buttons(self, options):
        """Create buttons for current choices."""
        self.buttons.clear()
        button_spacing = 20
        total_height = (BUTTON_HEIGHT * len(options)) + (button_spacing * (len(options) - 1))
        start_y = WINDOW_HEIGHT - total_height - 100
        
        for i, (key, (text, _, _, _)) in enumerate(options.items()):
            button_rect = pygame.Rect(
                (WINDOW_WIDTH - BUTTON_WIDTH) // 2,
                start_y + (BUTTON_HEIGHT + button_spacing) * i,
                BUTTON_WIDTH,
                BUTTON_HEIGHT
            )
            self.buttons.append(Button(button_rect, text, key, self.button_font))

    def handle_input(self) -> Optional[str]:
        """Handle mouse and keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
                
            # Handle button events when awaiting choice
            if self.awaiting_choice:
                for button in self.buttons:
                    result = button.handle_event(event)
                    if result:
                        return result
                        
            # Handle space to continue when not awaiting choice
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return 'continue'
                
        return None

    def update_display(self):
        """Update the game display."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Update and render text
        self.text_renderer.update(pygame.time.get_ticks())
        self.text_renderer.render()
        
        # Render stats
        core_stats = {
            'HEALTH': self.health,
            'SANITY': self.sanity,
            'CORRUPTION': self.corruption
        }
        self.stats_display.render(core_stats, self.skills)
        
        # Draw buttons if awaiting choice
        for button in self.buttons:
            button.draw(self.screen)
            
        # Draw continue prompt if not awaiting choice
        if not self.awaiting_choice and self.current_state not in ['game_over', 'ending']:
            continue_text = self.font.render("Press SPACE to continue", True, PARCHMENT_YELLOW)
            text_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
            self.screen.blit(continue_text, text_rect)
        
        pygame.display.flip()

    def skill_check(self, skill: Skill, difficulty: int) -> bool:
        """Perform a skill check with visual feedback."""
        roll = random.randint(1, 20) + self.skills[skill]
        result = roll >= difficulty
        
        # Create skill check result text
        roll_text = f"Skill Check - {skill.display_name}: {roll} vs {difficulty}"
        result_text = "SUCCESS!" if result else "FAILURE..."
        
        # Display skill check result
        self.text_renderer.set_text(f"{roll_text}\n{result_text}")
        pygame.time.wait(1500)  # Pause to show result
        
        return result

    def get_ancient_ruin_trial(self) -> Dict:
        """Generate a trial for the ancient ruins."""
        trials = [
            {
                'description': "A mystical barrier of swirling darkness blocks your path...",
                'skill': Skill.OCCULTISM,
                'difficulty': 15,
                'options': {
                    '1': ('Attempt to dispel it with dark magic', -10, -15, +10),
                    '2': ('Search for a way around', -5, -5, 0),
                    '3': ('Force your way through', -20, -10, +15)
                }
            },
            {
                'description': "Ancient guardians, their armor crumbling with age, rise from their eternal slumber...",
                'skill': Skill.COMBAT,
                'difficulty': 14,
                'options': {
                    '1': ('Face them in combat', -15, -5, +5),
                    '2': ('Try to sneak past', -5, -10, +10),
                    '3': ('Attempt to command them', -10, -15, +20)
                }
            },
            {
                'description': "A creature of shadow and wisdom bars your path, its eyes gleaming with ancient knowledge...",
                'skill': Skill.LORE,
                'difficulty': 16,
                'options': {
                    '1': ('Answer its riddle', 0, -15, +10),
                    '2': ('Offer it a trade', -10, -5, +15),
                    '3': ('Try to outsmart it', -5, -20, +20)
                }
            }
        ]
        return random.choice(trials)

    def get_random_encounter(self) -> Dict:
        """Generate a random encounter based on current game state."""
        base_encounters = [
            {
                'description': f"In the {self.current_weather} night, ethereal whispers emanate from behind a twisted tree...",
                'skill': Skill.WILLPOWER,
                'difficulty': 13,
                'options': {
                    '1': ('Investigate the whispers', -10, -15, +5),
                    '2': ('Hurry past, covering your ears', 0, -5, 0),
                    '3': ('Leave an offering by the tree', -5, 0, +10)
                }
            },
            {
                'description': "You discover a small shrine, its sacred symbols defaced with marks of dark power...",
                'skill': Skill.OCCULTISM,
                'difficulty': 14,
                'options': {
                    '1': ('Try to restore the shrine', -5, +10, -5),
                    '2': ('Study the corrupted symbols', 0, -10, +15),
                    '3': ('Destroy the shrine completely', 0, -15, +20)
                }
            },
            {
                'description': "A wounded traveler, their eyes filled with desperation, begs for your aid...",
                'skill': Skill.PERSUASION,
                'difficulty': 13,
                'options': {
                    '1': ('Offer assistance', -15, +5, 0),
                    '2': ('Ignore their pleas', 0, -10, +5),
                    '3': ('End their suffering', -5, -20, +25)
                }
            }
        ]

        # Add conditional encounters based on game state
        if self.flags['ancient_door_opened'] and not self.locations['ancient_ruins'].is_cleared:
            return self.get_ancient_ruin_trial()
            
        if self.flags['cursed_by_witch'] and random.random() < 0.3:
            base_encounters.append({
                'description': "The witch's curse manifests, reality warping around you...",
                'skill': Skill.WILLPOWER,
                'difficulty': 15,
                'options': {
                    '1': ('Resist the curse', -15, -20, 0),
                    '2': ('Channel its power', -10, -15, +25),
                    '3': ('Seek immediate refuge', -5, -10, +10)
                }
            })

        return random.choice(base_encounters)

    def handle_special_encounter(self, encounter_type: str) -> Dict:
        """Handle special story encounters."""
        if encounter_type == 'witch':
            return {
                'description': "Deep in the woods, you discover a crooked cottage. An ancient witch, her form shifting between shadow and substance, beckons you inside...",
                'skill': Skill.WILLPOWER,
                'difficulty': 15,
                'options': {
                    '1': ('Enter the cottage', -10, -15, +20),
                    '2': ('Refuse and leave', -15, -10, +10),
                    '3': ('Attack the witch', -40, -30, +30)
                }
            }
        elif encounter_type == 'priest':
            return {
                'description': "The village priest, his eyes reflecting knowledge of your recent actions, confronts you in the candlelit church...",
                'skill': Skill.PERSUASION,
                'difficulty': 14,
                'options': {
                    '1': ('Seek his blessing', +20, +20, -10),
                    '2': ('Ignore his warnings', 0, -15, +5),
                    '3': ('Silence him permanently', -10, -25, +40)
                }
            }
        return None

    def handle_ending(self) -> Dict:
        """Determine and return appropriate ending sequence."""
        if self.locations['ancient_ruins'].is_cleared:
            return {
                'description': "Ancient power courses through your veins, reality bending to your will. The knowledge of ages fills your mind, threatening to overflow...",
                'skill': Skill.OCCULTISM,
                'difficulty': 18,
                'options': {
                    '1': ('Harness the power to reshape reality', 0, -30, +40),
                    '2': ('Use the power to seal away the darkness', -20, -20, -20),
                    '3': ('Release the power into the world', -30, -40, +50)
                }
            }
        elif self.flags['cursed_by_witch'] and self.corruption >= 75:
            return {
                'description': "The witch's curse and your own corruption reach their peak, your very essence teetering between humanity and something... else.",
                'skill': Skill.WILLPOWER,
                'difficulty': 16,
                'options': {
                    '1': ('Embrace the transformation', -20, -40, +50),
                    '2': ('Try to control and direct it', -30, -30, +30),
                    '3': ('Fight against it', -40, -20, -20)
                }
            }
        elif self.sanity <= 25:
            return {
                'description': "Your fractured mind reveals impossible truths, reality splitting into countless possibilities before your eyes...",
                'skill': Skill.LORE,
                'difficulty': 15,
                'options': {
                    '1': ('Embrace the madness and transcend', -30, -50, +40),
                    '2': ('Try to find meaning in the chaos', -20, -30, +30),
                    '3': ('Attempt to reconstruct your sanity', -10, +20, -10)
                }
            }
        else:
            return {
                'description': "You stand at the crossroads of fate, the weight of your journey heavy upon your shoulders...",
                'skill': Skill.SURVIVAL,
                'difficulty': 14,
                'options': {
                    '1': ('Seek to heal the cursed land', -30, +20, -20),
                    '2': ('Leave and never return', -10, +10, 0),
                    '3': ('Continue your dark research', -20, -20, +30)
                }
            }

    def handle_encounter(self, encounter: Dict, choice: str) -> str:
        """Handle player choice in an encounter."""
        action, health_mod, sanity_mod, corruption_mod = encounter['options'][choice]
        success = self.skill_check(encounter['skill'], encounter['difficulty'])
        
        # Modify outcome based on skill check
        if success:
            health_mod = int(health_mod * 0.5)  # Reduce negative health impact
            sanity_mod = int(sanity_mod * 0.5)  # Reduce negative sanity impact
            result = f"Success! {action}\n"
        else:
            health_mod = int(health_mod * 1.5)  # Increase negative health impact
            sanity_mod = int(sanity_mod * 1.5)  # Increase negative sanity impact
            result = f"Failure! {action}\n"
            
        self.modify_stats(health_mod, sanity_mod, corruption_mod)
        return result

    def modify_stats(self, health=0, sanity=0, corruption=0):
        """Modify player stats within bounds."""
        self.health = max(0, min(100, self.health + health))
        self.sanity = max(0, min(100, self.sanity + sanity))
        self.corruption = max(0, min(100, self.corruption + corruption))

    def check_game_over(self) -> Tuple[bool, str]:
        """Check if game should end based on current stats."""
        if self.health <= 0:
            return True, "ENDING: Death claims another soul..."
        if self.sanity <= 0:
            return True, "ENDING: Your mind shatters into countless pieces..."
        if self.corruption >= 100:
            return True, "ENDING: The darkness consumes you completely..."
        return False, ""

    def get_ending_text(self, ending_type: str, success: bool, choice: str) -> str:
        """Get the appropriate ending text based on the type and success."""
        endings = {
            'ancient_power': {
                True: {
                    '1': "ENDING: ASCENDED MASTER\nYou master the ancient power, ascending beyond mortal understanding...",
                    '2': "ENDING: GUARDIAN OF REALITY\nYou become the eternal jailer of darkness, forever vigilant...",
                    '3': "ENDING: CHAOS UNLEASHED\nReality bends and breaks as power floods the world..."
                },
                False: {
                    '1': "ENDING: FAILED ASCENSION\nThe power proves too great, consuming your very essence...",
                    '2': "ENDING: PYRRHIC VICTORY\nThe darkness is sealed, but claims you as its final victim...",
                    '3': "ENDING: CATACLYSM\nThe power spirals beyond control, doom cascading across reality..."
                }
            },
            'curse': {
                True: {
                    '1': "ENDING: DARK METAMORPHOSIS\nYour humanity fades as you embrace a new, terrible form...",
                    '2': "ENDING: CURSE MASTER\nYou bend the dark energies to your will, though your soul may never recover...",
                    '3': "ENDING: CURSE BREAKER\nThrough sheer force of will, you shatter the witch's curse..."
                },
                False: {
                    '1': "ENDING: CONSUMED\nThe curse devours your being, leaving only darkness...",
                    '2': "ENDING: LOST CONTROL\nThe curse overwhelms your attempts at mastery...",
                    '3': "ENDING: FAILED RESISTANCE\nYour rebellion against the curse ends in tragedy..."
                }
            },
            'madness': {
                True: {
                    '1': "ENDING: TRANSCENDENT MADNESS\nYou find enlightenment in chaos, becoming something beyond...",
                    '2': "ENDING: CHAOS PROPHET\nYou emerge as a herald of cosmic truth, forever changed...",
                    '3': "ENDING: RECONSTRUCTED\nFrom the fragments of your mind, you forge a new understanding..."
                },
                False: {
                    '1': "ENDING: SHATTERED REALITY\nYour grasp on reality dissolves completely...",
                    '2': "ENDING: LOST PROPHET\nThe truths you glimpse drive you deeper into madness...",
                    '3': "ENDING: FRACTURED\nYour mind splinters beyond any hope of recovery..."
                }
            },
            'redemption': {
                True: {
                    '1': "ENDING: SALVATION\nYour sacrifice brings healing to this cursed land...",
                    '2': "ENDING: CLEAN ESCAPE\nYou find peace far from the shadows of Ravencross...",
                    '3': "ENDING: ENLIGHTENED SEEKER\nYou master the balance between light and dark..."
                },
                False: {
                    '1': "ENDING: NOBLE SACRIFICE\nYour attempt at redemption claims your life...",
                    '2': "ENDING: HAUNTED ESCAPE\nThough you flee, the darkness follows...",
                    '3': "ENDING: CONSUMED SEEKER\nYour research leads you back into darkness..."
                }
            }
        }

        # Determine ending type based on game state
        if self.locations['ancient_ruins'].is_cleared:
            ending_category = 'ancient_power'
        elif self.flags['cursed_by_witch'] and self.corruption >= 75:
            ending_category = 'curse'
        elif self.sanity <= 25:
            ending_category = 'madness'
        else:
            ending_category = 'redemption'

        return endings[ending_category][success][choice]

    def play(self):
        """Main game loop."""
        running = True
        
        # Initial setup
        intro_text = (f"Welcome to the Dark Path...\n\n"
                     f"You arrive at the village of Ravencross on a {self.current_weather} night.\n"
                     f"The {self.moon_phase} moon hangs above, and the villagers seem {self.village_state}.\n\n"
                     f"Press SPACE to continue...")
        self.text_renderer.set_text(intro_text)
        
        while running:
            choice = self.handle_input()
            
            if choice == 'quit':
                running = False
                
            elif choice == 'continue':
                if self.current_state == 'intro':
                    self.current_encounter = self.get_random_encounter()
                    self.text_renderer.set_text(self.current_encounter['description'])
                    self.create_choice_buttons(self.current_encounter['options'])
                    self.current_state = 'encounter'
                    self.awaiting_choice = True
                    
                elif self.current_state == 'result':
                    if self.current_state != 'game_over' and self.current_state != 'ending':
                        self.current_encounter = self.get_random_encounter()
                        self.text_renderer.set_text(self.current_encounter['description'])
                        self.create_choice_buttons(self.current_encounter['options'])
                        self.current_state = 'encounter'
                        self.awaiting_choice = True
                
            elif choice in ['1', '2', '3'] and self.awaiting_choice:
                # Handle special encounters
                if self.encounters_completed == 5 and not self.flags['encountered_witch']:
                    self.current_encounter = self.handle_special_encounter('witch')
                    if choice == '1':
                        self.flags['has_ritual_knowledge'] = True
                    elif choice == '3':
                        self.flags['cursed_by_witch'] = True
                    self.flags['encountered_witch'] = True
                    
                elif self.encounters_completed == 10 and self.flags['priest_alive']:
                    self.current_encounter = self.handle_special_encounter('priest')
                    if choice == '3':
                        self.flags['priest_alive'] = False
                
                # Process choice
                result = self.handle_encounter(self.current_encounter, choice)
                self.buttons.clear()  # Clear buttons after choice
                
                # Handle ancient ruins progress
                if self.flags['ancient_door_opened'] and not self.locations['ancient_ruins'].is_cleared:
                    self.locations['ancient_ruins'].trials_completed += 1
                    if self.locations['ancient_ruins'].trials_completed >= self.locations['ancient_ruins'].required_trials:
                        self.locations['ancient_ruins'].is_cleared = True
                        result += "\nYou have conquered the ancient ruins!"
                        self.modify_stats(+20, +20, +30)
                
                # Check for game over or ending
                game_over, message = self.check_game_over()
                if game_over:
                    self.text_renderer.set_text(message)
                    self.current_state = 'game_over'
                elif self.encounters_completed >= 20:
                    ending_encounter = self.handle_ending()
                    success = self.skill_check(ending_encounter['skill'], ending_encounter['difficulty'])
                    ending_text = self.get_ending_text(
                        'ending_type',  # This will be determined inside get_ending_text
                        success,
                        choice
                    )
                    self.text_renderer.set_text(ending_text)
                    self.current_state = 'ending'
                else:
                    self.text_renderer.set_text(f"{result}\n\nPress SPACE to continue...")
                    self.current_state = 'result'
                    self.awaiting_choice = False
                    self.encounters_completed += 1
            
            self.update_display()
            pygame.time.Clock().tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = DarkFantasyGame()
    game.play()
