import random
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.animation as animation
import planisuss_constants
from matplotlib.widgets import Button
import os

EMPTY = 0 #midnight blue
VEGETOB = 1 #VEGETOB bright green
ERBAST = 2 #ERBAST dark green
CARVIZ = 3 #CARVIZ red

#creature color in the above order
colors = ['#191970', '#00FF00', '#016301', '#FF0000']
n_bin = 4
cm = LinearSegmentedColormap.from_list(
        'wator_cmap', colors, N=n_bin)

# PRNG seed for controlling randomness 
SEED = 10
random.seed(SEED)


initial_energies = {VEGETOB: 30, ERBAST: 30, CARVIZ: 30}
lifetime_thresholds = {VEGETOB: 100, ERBAST: 100, CARVIZ: 100}

class Creature():

    def __init__(self, id, x, y, init_energy, lifetime_threshold):
        '''
        Creature class holds vegetob, erbast and carviz.
        Vegetob holds density. Erbast/Carviz hold energy and lifetime.
        '''

        self.id = id
        self.x, self.y = x, y
        if self.id == VEGETOB:
            self.density = init_energy
            self.lifetime_threshold = None 
        else:
            self.energy = init_energy
            self.lifetime_threshold = lifetime_threshold
            self.lifetime = 0
        self.dead = False


class World():
    def __init__(self, NUMCELLS=100):
        self.NUMCELLS = NUMCELLS
        self.ncells = NUMCELLS * NUMCELLS
        self.grid = [[EMPTY]*NUMCELLS for y in range(NUMCELLS)]
        self.creatures = []

    def spawn_creature(self, creature_id, x, y, old_energy):
        '''
        this spawns a creature of type creature_id at location x,y
        also takes care of the spawning offsprings with the energy of their parent.
        '''

        if old_energy == None:
            if creature_id != VEGETOB:
                creature = Creature(creature_id, x, y,
                                    initial_energies[creature_id],
                                    lifetime_thresholds[creature_id])
            else:
                creature = Creature(creature_id, x, y,
                    initial_energies[creature_id],
                    None)
        else:
            creature = Creature(creature_id, x, y,
                                old_energy,
                                lifetime_thresholds[creature_id])


        self.creatures.append(creature)
        self.grid[y][x] = creature

    def populate_world(self, nVEGETOB=2000, nERBAST=1000, nCARVIZ = 100):
        '''
        populates and places the creatures

        '''
        self.nVEGETOB, self.nERBAST, self.nCARVIZ = nVEGETOB, nERBAST, nCARVIZ
        
        def place_creatures(ncreatures, creature_id):
            for i in range(ncreatures):
                while True:
                    x, y = divmod(random.randrange(self.ncells), self.NUMCELLS)
                    if not self.grid[y][x] and 1 <= x < self.NUMCELLS - 1 and 1 <= y < self.NUMCELLS - 1:
                        self.spawn_creature(creature_id, x, y, None)
                        break

        place_creatures(self.nVEGETOB, VEGETOB)
        place_creatures(self.nERBAST, ERBAST)
        place_creatures(self.nCARVIZ, CARVIZ)
        
        

    def get_world_image_array(self):
        #generates 2d array with creature types in a grid 
        return [[self.grid[y][x].id if self.grid[y][x] else 0
                    for x in range(self.NUMCELLS)] for y in range(self.NUMCELLS)]
    

    def get_neighbours(self, x, y):
        '''
        returns a dictionary of the contents of cells that neighbour around [x,y]

        it's a dictionary that contains the neighbour cell position and EMPTY/the 
        instance of the creature occupying the cell
        '''

        neighbours = {}
        for dx, dy in ((0,-1), (1,0), (0,1), (-1,0)):
            xp, yp = (x+dx) % self.NUMCELLS, (y+dy) % self.NUMCELLS
            neighbours[xp,yp] = self.grid[yp][xp]
        return neighbours


    def evolve_creature(self, creature):
        #main function evolving creatures

        neighbours = self.get_neighbours(creature.x, creature.y) 

        #add density or lifetime to each creature based on needs as this is the beggining of the day
        if creature.id == VEGETOB:
            creature.density = creature.density + 1
        else:
            creature.lifetime += 1
                


        moved = False


        if creature.id == ERBAST:
            #erbast tries to eat vegetob
            try:
                xp, yp = random.choice([pos
                            for pos in neighbours if neighbours[pos]!=EMPTY
                                                and neighbours[pos].id==VEGETOB])

                creature.energy += 1 #erbast energy goes up
                self.grid[yp][xp].density -= 1 #vegetob density goes down
                
                if self.grid[yp][xp].density < 0:
                    self.grid[yp][xp].dead = True
                    self.grid[yp][xp] = EMPTY
                moved = True
            except IndexError:
                # if there is no vegetob to eat in the neighbours, then it simply moves if it can do that
                pass
        elif creature.id == CARVIZ:
            try:
                #carviz tries to eat erbast
                xp, yp = random.choice([pos
                            for pos in neighbours if neighbours[pos]!=EMPTY
                                                and neighbours[pos].id==ERBAST])
                
                creature.energy += 1 #carviz energy goes up and then erbast dies.
                self.grid[yp][xp].dead = True
                self.grid[yp][xp] = EMPTY
                moved = True
            except IndexError:
                # if there is no vegetob to eat in the neighbours, then it simply moves if it can do that
                pass


        '''
        this part tries to move any non vegetob creature
        if it suceeds, it moves the creature and decreases its energy
        '''

        if not moved and creature.id != VEGETOB:
            try:
                xp, yp = random.choice([pos
                            for pos in neighbours if neighbours[pos]==EMPTY])
                creature.energy -= 1
                moved = True
            except IndexError:
                #if surrounding cells are full there is no movement
                xp, yp = creature.x, creature.y

        #age decreasing and population dynamic evolution through respawning 
        if creature.id != VEGETOB:
            if creature.lifetime and creature.lifetime%10 == 0:
                creature.energy = creature.energy - planisuss_constants.AGING
            if moved:
                x, y = creature.x, creature.y #creature's old position and set new position
                creature.x, creature.y = xp, yp
                self.grid[yp][xp] = creature

                '''
                check if it exceeds lifetime and if it does, reset current creature and spawn new one
                this basically kills current creature and we get two new ones.
                '''
                if creature.lifetime >= creature.lifetime_threshold:
                    creature.lifetime = 1
                    old_energy = creature.energy
                    self.spawn_creature(creature.id, x, y, old_energy)
                else:
                    #leave the old cell vacant.
                    self.grid[y][x] = EMPTY



    def evolve_world(self):
        '''
        this evolves the world one day in time.
        it shuffles creatures so that the same ones are not evolved every time in the same order.
        '''
        random.shuffle(self.creatures)
        ncreatures = len(self.creatures)
        for i in range(ncreatures):
            creature = self.creatures[i]
            if creature.dead:
                #skip cause it's dead
                continue
            self.evolve_creature(creature)

        #removing dead creatures
        self.creatures = [creature for creature in self.creatures
                                                if not creature.dead]



#creating an instance of the World class, populating and plotting fig and axes.

world = World()
world.populate_world()
fig, ax = plt.subplots()

#variable to track animation status
anim_running = True

# Specify the directory to save the screenshots
screenshot_directory = "screenshots"
os.makedirs(screenshot_directory, exist_ok=True)


#function to pause/resume animation when button is clicked
def onClick(event):
    global anim_running
    if anim_running:
        ani.event_source.stop()
        anim_running = False
    else:
        ani.event_source.start()
        anim_running = True

#rest of the button
axbutton = fig.add_axes([0.81, 0.05, 0.1, 0.075])
button = Button(axbutton, 'Pause/Resume')
button.on_clicked(onClick)

def update(frame):

    #evolving world by one day
    world.evolve_world()

    #clearing the axis
    ax.clear()
    
    #main plot
    ax.imshow(world.get_world_image_array(), interpolation='nearest', cmap=cm)

    #title/day thingy 
    ax.set_title(f"Day {frame + 1}")

    #saving screenshots
    screenshot_path = os.path.join(screenshot_directory, f"frame_{frame:04d}.png")
    fig.savefig(screenshot_path)


#creating the FuncAnimation
ani = animation.FuncAnimation(fig, update, frames=planisuss_constants.NUMDAYS, interval=1, repeat=False)

plt.show()

