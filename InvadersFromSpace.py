#!/usr/bin/env python3

'''
Homage to the arcade classic Space Invaders.
Inspired by https://www.youtube.com/watch?v=Q-__8Xw9KTM
'''

import os
import time
import random  
import pygame


#pygame initalisation--------------------------------------------------------------------------------

pygame.font.init()

WIDTH,HEIGHT = 750,750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Invaders from Space!")


# loading images--------------------------------------------------------------------------------------

RED_SPACE_SHIP =  pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP =  pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP =  pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

YELLOW_SPACE_SHIP =  pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

RED_LASER =  pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER =  pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER =  pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER =  pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

MED_PACK = pygame.image.load(os.path.join("assets", "pixel_med_pack.png"))
SHIELD_PACK = pygame.image.load(os.path.join("assets", "pixel_shield_pack.png"))

BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")),(WIDTH,HEIGHT))


#------------------------------------------------------------------------------------------------------

class Laser:
	def __init__(self, x, y, img):
		self.x = x
		self.y = y
		self.img = img
		self.mask = pygame.mask.from_surface(self.img)
	def draw(self, window):
		window.blit(self.img, (self.x, self.y))
	def move(self, vel):
		self.y += vel
	def off_screen(self, height):
		return not(self.y <= height and self.y >= 0)
	def collision(self, obj):
		return collide(self, obj)

class Ship:
	COOLDOWN = 30
	def __init__(self, x, y, health=100):
		self.x = x
		self.y = y
		self.health = health
		self.ship_img = None
		self.laser_img = None
		self.lasers = []
		self.cool_down_counter = 0
	
	def draw(self, window):
		window.blit(self.ship_img,(self.x, self.y))
		for laser in self.lasers:
			laser.draw(window)
			
	def move_lasers(self, vel, obj):
		self.cooldown()
		for laser in self.lasers[:]:
			laser.move(vel)
			if laser.off_screen(HEIGHT):
				self.lasers.remove(laser)
			elif laser.collision(obj):
				obj.change_health(-10)
				self.lasers.remove(laser)
		
	def cooldown(self,speedup=0):
		if self.cool_down_counter >= self.COOLDOWN:
			self.cool_down_counter = 0
		elif self.cool_down_counter > 0:		
			self.cool_down_counter += (1+speedup)
	def shoot(self):
		if self.cool_down_counter == 0:
			offset = 0.5*(self.get_width() - self.laser_img.get_width())
			laser = Laser(self.x+offset,self.y,self.laser_img)
			self.lasers.append(laser)
			self.cool_down_counter = 1
	
	def get_width(self):
		return self.ship_img.get_width()
	
	def get_height(self):
		return self.ship_img.get_height()

class Player(Ship):
	SHIELDS = 1200
	
	def __init__(self, x,y, health=100):
		super().__init__(x,y, health)
		self.ship_img = YELLOW_SPACE_SHIP
		self.laser_img = YELLOW_LASER 
		self.mask = pygame.mask.from_surface(self.ship_img)
		self.max_health = health
		self.shielded = False
		self.shield_counter = 0
	
	def powerdown(self):
		if self.shielded == True:
			if self.shield_counter >= self.SHIELDS:
				self.shield_counter = 0
				self.shielded = False
				
			elif self.shield_counter >= 0:
				self.shield_counter += 1
	
	def change_health(self,amount):
		if self.shielded:
			amount = max(0,amount)
		self.health = min(self.max_health, self.health + amount)
	
	def move_lasers(self, vel, objs):
		speedup=0
		if self.shielded:
			speedup=3
		self.cooldown(speedup)
		self.powerdown()
		for laser in self.lasers[:]:
			laser.move(vel)
			if laser.off_screen(HEIGHT):
				self.lasers.remove(laser)
			else:
				for obj in objs[:]:
					if laser.collision(obj):					
						obj.destroyed(objs)
						if laser in self.lasers:
							self.lasers.remove(laser)
							
	def draw(self, window):
		super().draw(window)
		if self.shielded:
			self.drawshield(window)
		self.healthbar(window)
	
	def healthbar(self, window):
		pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
		pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))
		
	def drawshield(self,window):
		def draw_circle_opaque(surface, colour, center, radius):
    			target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    			shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    			shape_surf.set_alpha(88)
    			pygame.draw.circle(shape_surf, colour, (radius, radius), radius)
    			surface.blit(shape_surf, target_rect)
    			pygame.draw.circle(surface, colour, center, radius,2) 
		
		draw_circle_opaque(window, (0,0,200), (self.x+self.ship_img.get_width()/2, self.y+ self.ship_img.get_height()/2), 100) 


class Enemy(Ship):
	COLOR_MAP = {
		     "red": (RED_SPACE_SHIP, RED_LASER,0.5),   
		     "green": (GREEN_SPACE_SHIP, GREEN_LASER,0.5),
		     "blue": (BLUE_SPACE_SHIP, BLUE_LASER,1.0)
		    }
	
	def __init__(self, x,y, colour, obj_list, health=100, level=1):
		super().__init__(x,y, health)
		self.ship_img, self.laser_img, self.vel = self.COLOR_MAP[colour]
		self.mask = pygame.mask.from_surface(self.ship_img)
		
		self.vel = min(2.5, self.vel+(level-1)*0.25)
		self.obj_list=obj_list
		
	def move(self):
	    self.y += self.vel
	    
	def destroyed(self,containinglist):
		if random.random() < 0.3:
			item = "health"
			if random.random() < 0.2:
				item = "shield" 
			self.obj_list.append(Pickups(self.x,self.y,item))
		
		containinglist.remove(self)

class Pickups():
	LIFE = 300
	TYPE = {'health': (MED_PACK,'med'),
		'shield': (SHIELD_PACK,'shield')
		}
	def __init__(self,x,y,obj_type):
		self.x = x
		self.y = y
		self.img,self.whatis = self.TYPE[obj_type]
		self.mask = pygame.mask.from_surface(self.img)
		self.life_counter = 0  
	
	def draw(self, window):
		window.blit(self.img,(self.x, self.y))
	
	
	def lifespan(self, containinglist):
		if self.life_counter >= self.LIFE:
			containinglist.remove(self)
		elif self.life_counter >= 0:
			self.life_counter += 1
		
def collide(obj1, obj2):
	offset_x = obj2.x - obj1.x
	offset_y = obj2.y - obj1.y
	return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


#------------------------------------------------------------------------------------------------------

def main():
	run = True
	FPS = 140
	level = 0
	lives = 5
	main_font = pygame.font.SysFont("comicsans",50)
	lost_font = pygame.font.SysFont("comicsans",60)
		
	enemies = []
	objects=[]
	wave_length = 5
	
	player_vel = 5
	enemy_vel = 1
	laser_vel = {'enemy': 6, 'player':-15 }   
	
	player = Player(300,635)
	
	clock = pygame.time.Clock()
	
	lost = False
	lost_count = 0
	
	def redraw_window():
		WIN.blit(BG,(0,0))
		#draw text
		level_label = main_font.render(f'Level: {level}', 1, (255,255,255))
		WIN.blit(level_label,(WIDTH - level_label.get_width() - 10, 10))
		lives_label = main_font.render(f'Lives: {lives}', 1, (255,255,255))
		WIN.blit(lives_label,(10,10))
				
		for pickup in objects:
			pickup.draw(WIN)
		for enemy in enemies:
			enemy.draw(WIN)
		player.draw(WIN)
		
		if lost:
			lost_label = lost_font.render("You Died Loser!",1,(255,255,255))
			WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350)   )
		
		pygame.display.update()
	
	while run:
		clock.tick(FPS)
		redraw_window()
		
		if lives <=0 or player.health <=0:
			lost = True
			lost_count += 1
		
		if lost:
			if lost_count > FPS * 3:
				run = False
			else:
			    continue
		
		if len(enemies) == 0:
			level += 1
			wave_length += 5
			for i in range(wave_length):
				enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500,-100), random.choice(["red","green", "blue"]),objects, level)
				enemies.append(enemy)
		
			
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				quit()
				
		keys = pygame.key.get_pressed()
		if keys[pygame.K_a] and player.x - player_vel > 0:
			player.x -= player_vel
		if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH:
			player.x += player_vel
		if keys[pygame.K_w] and player.y - player_vel > 0:
			player.y -= player_vel
		if keys[pygame.K_s] and player.y + player_vel + player.get_height() +15< HEIGHT:
			player.y += player_vel	
		if keys[pygame.K_SPACE]:
			player.shoot()	
		
		for pickup in objects[:]:
			pickup.lifespan(objects)
			if collide(pickup, player):
				if pickup.whatis == 'med':
					if player.health < player.max_health:
						player.change_health(50) 
				if pickup.whatis == 'shield':
					player.shielded = True
					player.shield_counter = 0
				
				objects.remove(pickup)
				
		
		for enemy in enemies[:]:
		    enemy.move()
		    enemy.move_lasers(laser_vel['enemy'], player)
		    
		    if random.randrange(0, max( 50,(6 - level)*60)) == 1:   #if random.randrange(0, 2*60) == 1:
		    	enemy.shoot()
		    	
		    if collide(enemy, player):
		    	player.change_health( -10)
		    	enemy.destroyed(enemies)
		    	
		    elif enemy.y + enemy.get_height() > HEIGHT:
		    	lives -= 1
		    	enemies.remove(enemy)
		    	

		mult = 1
		if player.shielded:
			mult=2.5
		player.move_lasers(mult*laser_vel['player'], enemies)
		
def main_menu():

	title_font = pygame.font.SysFont("comicsans", 70)
	run = True
	while run:
		WIN.blit(BG, (0,0))
		title_label = title_font.render("Press any key to begin...", 1, (255,255,255))
		WIN.blit(title_label,(WIDTH/2 - title_label.get_width()/2, 350))
		pygame.display.update()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				
			if event.type == pygame.KEYDOWN:
				main()
	pygame.quit()

main_menu() 
