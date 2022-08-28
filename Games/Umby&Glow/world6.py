class W:
    @micropython.viper
    def pattern_biomechanical_hall_wall(self, x: int, oY: int) -> int:
        ### PATTERN [biomechanical_hall_wall]:
        # Alien background wall with repetative feel
        ###
        buff = ptr32(_buf)
        v = 0
        if oY == 0:
            buff[0] = int(shash(x,32,48))
        v = 0
        for y in range(oY, oY+32):
            v |= (
                int(y > (11313321^(x*(y+buff[0]))) % 64 + 5)
            ) << (y-oY)
    
        return v
    
    @micropython.viper
    def pattern_alien_totem_plants(self, x: int, oY: int) -> int:
        ### PATTERN [alien_totem_plants]:
        # Tended garden of alien plants good for mid background
        ###
        buff = ptr32(_buf)
        if oY == 0:
            buff[0] = int(shash(x,128,40)) + int(shash(x,16,16)) + int(shash(x,4,4)) - 16
        v = 0
        for y in range(oY, oY+32):
            y1 = y-20 if y>32 else 44-y
            v |= (
                int(y1 > (32423421^(x*x*(y1-buff[0])))%64) if y1 > buff[0] else 0
             ) << (y-oY)
        return v
    
    @micropython.viper
    def pattern_alien_totem_floor(self, x: int, oY: int) -> int:
        ### PATTERN [alien_totem_floor]:
        # Floor and roofing matching the style of alien_totem_plants.
        ###
        buff = ptr32(_buf)
        if oY == 0:
            buff[0] = int(shash(x,128,10)) + int(shash(x,16,8)) + int(shash(x,4,4)) + 40
        v = 0
        for y in range(oY, oY+32):
            y1 = y if y>32 else 64-y
            v |= (
                int(y1 > (32423421^(x*x*(y1-buff[0])))%64) if y1 > buff[0] else 0
             ) << (y-oY)
        return v
w = W()