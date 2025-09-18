"""
Filename: sluggame.py
Description: Core simulation logic for Cyberslug, including agent behavior, environment interactions,
and sensory processing.
"""

import math
import random

import pygame 
import numpy as np
from scipy.ndimage import gaussian_filter

from config import (
    WIDTH, HEIGHT, PREY_RADIUS, NUM_ODOR_TYPES, 
    ALPHA_HERMI, BETA_HERMI, LAMBDA_HERMI,
    ALPHA_FLAB, BETA_FLAB, LAMBDA_FLAB, 
    ALPHA_DRUG, BETA_DRUG, LAMBDA_DRUG,
    FLAB_ODOR, HERMI_ODOR, DRUG_ODOR,
    ENCOUNTER_COOLDOWN, DEBUG_MODE
)
from utils import wrap_around

# --- Prey Class ---
class Prey:
    def __init__(self, x, y, color, odorlist):
        self.x = x
        self.y = y
        self.color = color
        self.odorlist = odorlist
        self.angle = random.uniform(0, 360)
        self.radius = PREY_RADIUS 

    def move(self):
        self.angle += random.uniform(-1, 1)
        step = 0.1
        self.x += step * math.cos(math.radians(self.angle)) # WIDTH
        self.y += step * math.sin(math.radians(self.angle)) # HEIGHT
        self.x, self.y = wrap_around(self.x, self.y)

    def respawn(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.angle = random.uniform(0, 360)

# --- Cyberslug Class ---
class Cyberslug:
    def __init__(self):
        self.x, self.y = WIDTH // 2, HEIGHT // 2
        self.angle = 0 # degrees
        self.speed = 3
        self.path = [(self.x, self.y)]
        self.image = pygame.image.load('ASIMOV_slug_sprite.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.mask_topleft = (self.x, self.y)

        # Learning and motivation variables
        self.nutrition = 0.5
        self.incentive = 0.0
        self.satiation = 0.0
        self.app_state = 0.0
        self.app_state_switch = 0.0

        # Somatic map
        self.somatic_map = 0.0

        # Learning variables
        self.Vh, self.Vf, self.Vd = 0.0, 0.0, 0.0
        self.alpha_hermi, self.beta_hermi, self.lambda_hermi = ALPHA_HERMI, BETA_HERMI, LAMBDA_HERMI
        self.alpha_flab, self.beta_flab, self.lambda_flab = ALPHA_FLAB, BETA_FLAB, LAMBDA_FLAB
        self.alpha_drug, self.beta_drug, self.lambda_drug = ALPHA_DRUG, BETA_DRUG, LAMBDA_DRUG

        # Sensor arrays
        self.sns_odors_left = [0.0] * NUM_ODOR_TYPES
        self.sns_odors_right = [0.0] * NUM_ODOR_TYPES
        self.sns_odors = [0.0] * NUM_ODOR_TYPES

        # Pain and reward mechanisms
        self.sns_pain_left = 0.0
        self.sns_pain_right = 0.0
        self.spontaneous_pain = 2.0
        self.reward_experience = 0.0

        # Counters and timers
        self.encounter_timer = 0
        self.hermi_counter, self.flab_counter, self.drug_counter = 0, 0, 0

    def update(self, sensors_left, sensors_right, encounter):
        """Updates Cyberslug's internal state and movement based on sensory input and encounters."""
        self.sns_odors_left = [0 if i <= 1e-7 else (7 + math.log10(i)) for i in sensors_left]
        self.sns_odors_right = [0 if i <= 1e-7 else (7 + math.log10(i)) for i in sensors_right]
        self.sns_odors = [(l + r) / 2 for l, r in zip(self.sns_odors_left, self.sns_odors_right)]
        
        sns_betaine, sns_hermi, sns_flab, sns_drug = self.sns_odors

        # --- Associative learning from prey encounters ---
        if encounter == "hermi":
            self.Vh += self.alpha_hermi * self.beta_hermi * (self.lambda_hermi - self.Vh)
            self.nutrition += 0.1
            if self.encounter_timer == 0:
                self.hermi_counter += 1
                self.encounter_timer = ENCOUNTER_COOLDOWN
        if encounter == "flab":
            self.Vf += self.alpha_flab * self.beta_flab * (self.lambda_flab - self.Vf)
            self.nutrition += 0.1
            if self.encounter_timer == 0:
                self.flab_counter += 1
                self.encounter_timer = ENCOUNTER_COOLDOWN
        if encounter == "drug":
            self.Vd += self.alpha_drug * self.beta_drug * (self.lambda_drug - self.Vd)
            if self.encounter_timer == 0:
                self.drug_counter += 1
                self.encounter_timer = ENCOUNTER_COOLDOWN
        
        # --- Pain Calcuations ---
        self.sns_pain = (self.sns_pain_left + self.sns_pain_right)/2
        self.pain = 10 / (1 + math.exp(-2 * (self.sns_pain + self.spontaneous_pain) + 10 ))
        self.pain_switch = 1 - 2 / (1 + math.exp(-10 * (self.sns_pain - 0.2)));
    
        # --- Nutrition, Satiation, and Incentive Calculations ---
        self.nutrition -= 0.005 * self.nutrition
        self.satiation = 1 / ((1 + 0.7 * math.exp(-4 * self.nutrition + 2)) ** 2)

        self.reward_pos = (
            sns_betaine / (1 + (0.05 * self.Vh * sns_hermi) - 0.006 / self.satiation) 
            + 3.0 * self.Vh * sns_hermi 
            + 8.0 * self.Vd * sns_drug)
        self.reward_neg = 0.59 * self.Vf * sns_flab
        self.incentive = self.reward_pos - self.reward_neg

        # --- Somatic Map Calculation ---
        self.somatic_map_senses_left = self.sns_odors_left[1:] + [self.sns_pain_left]
        self.somatic_map_senses_right = self.sns_odors_right[1:] + [self.sns_pain_right]
        self.somatic_map_senses = [(l + r) / 2 for l, r in zip(self.somatic_map_senses_left, self.somatic_map_senses_right)]
        
        # Each sensor's value relative to the total
        self.somatic_map_factors = [2 * sensor - sum(self.somatic_map_senses) for sensor in self.somatic_map_senses]
        # Replace the last factor with the computed pain value to emphasize pain
        self.somatic_map_factors[-1] = self.pain

        # Apply a sigmoid to the difference between left and right sensor values modulated by the factor
        self.somatic_map_sigmoids = [
            (r - l) / (1 + math.exp(-50 * factor))
            for l, r, factor in zip(self.somatic_map_senses_left, self.somatic_map_senses_right, self.somatic_map_factors)
        ]
        # Somatic map is the negative sum of the sigmoid values
        self.somatic_map = -sum(self.somatic_map_sigmoids)

        # --- Appetitive State and Turn Angle ---
        self.app_state = 0.01 + (
            1 / (1 + math.exp(- (1 * self.incentive - 8 * self.satiation - 0.1 * self.pain - 0.1 * self.pain_switch * self.reward_experience))) + 
            0.1 * ((self.app_state_switch - 1) * 0.5)
        )
        self.app_state_switch = (-2 / (1 + math.exp(-100 * (self.app_state - 0.245)))) + 1
        self.turn_angle = 3 * ((2 * self.app_state_switch) / (1 + math.exp(3 * self.somatic_map)) - self.app_state_switch)

        # --- Encounter Timer ---
        if self.encounter_timer > 0:
            self.encounter_timer -= 1
        
        if DEBUG_MODE and encounter != "none" and self.encounter_timer == (ENCOUNTER_COOLDOWN - 1):
            print(
                "Tick encountered", encounter, 
                "Flab:", self.flab_counter, 
                "Hermi:", self.hermi_counter, 
                "Drug:", self.drug_counter
            )
            print(
                "Satiation:", round(self.satiation, 4),
                "Nutrition:", round(self.nutrition, 2),
                "Incentive:", round(self.incentive, 2),
                "AppState:", round(self.app_state, 3),
                "AppStateSwitch:", round(self.app_state_switch, 3),
                "Somatic_Map:", round(self.somatic_map, 3),
                "Sns_Bet:", round(sns_betaine, 2),
                "Sns_Hermi:", round(sns_hermi, 2),
                "Sns_Flab:", round(sns_flab, 2),
                "Sns_Drug:", round(sns_drug, 2),
                "Vh:", round(self.Vh, 2),
                "Vf:", round(self.Vf, 2),
                "Vd:", round(self.Vd, 2)
            )
        
        return self.turn_angle