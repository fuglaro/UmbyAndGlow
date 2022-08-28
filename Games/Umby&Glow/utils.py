## Maths utility functions ##

@micropython.viper
def abs(v: int) -> int:
    ### Fast bitwise abs ###
    m = v >> 31
    return (v + m) ^ m

@micropython.viper
def ihash(x: uint) -> int:
    ### 32 bit deterministic semi-random hash fuction
    # Credit: Thomas Wang
    ###
    x = (x ^ 61) ^ (x >> 16)
    x += (x << 3)
    x ^= (x >> 4)
    x *= 0x27d4eb2d
    return int(x ^ (x >> 15))

@micropython.viper
def shash(x: int, step: int, size: int) -> int:
    ### (smooth) deterministic semi-random hash.
    # For x, this will get two random values, one for the nearest
    # interval of 'step' before x, and one for the nearest interval
    # of 'step' after x. The result will be the interpolation between
    # the two random values for where x is positioned along the step.
    # @param x: the position to retrieve the interpolated random value.
    # @param step: the interval between random samples.
    # @param size: the maximum magnitude of the random values.
    ###
    a = int(ihash(x//step)) % size
    b = int(ihash(x//step + 1)) % size
    return a + (b-a) * (x%step) // step

@micropython.viper
def fsqrt(v: int) -> int:
    if v < 2: return v
    a = 1337
    b = v//a; a = (a+b)>>1
    b = v//a; a = (a+b)>>1
    b = v//a; a = (a+b)>>1
    b = v//a; a = (a+b)>>1
    return a

# Fast sine and cos lookup table.
# If angle is in radians*65536, then use as follows:
#     sin = (sinco[(a//1024+200)%400]-128)//128
#     cos = (sinco[(a//1024-100)%400]-128)//128
sinco = bytearray([127, 125, 123, 121, 119, 117, 115, 113, 111, 109, 107, 105,
    103, 101, 99, 97, 95, 93, 91, 89, 87, 85, 83, 82, 80, 78, 76, 74, 72, 71,
    69, 67, 65, 64, 62, 60, 58, 57, 55, 53, 52, 50, 49, 47, 46, 44, 43, 41, 40,
    38, 37, 35, 34, 33, 31, 30, 29, 27, 26, 25, 24, 23, 21, 20, 19, 18, 17, 16,
    15, 14, 13, 12, 12, 11, 10, 9, 8, 8, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1,
    1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3,
    4, 4, 5, 6, 6, 7, 8, 8, 9, 10, 11, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 34, 35, 37, 38, 39, 41, 42, 44, 45,
    47, 48, 50, 52, 53, 55, 57, 58, 60, 62, 63, 65, 67, 69, 70, 72, 74, 76, 78,
    80, 81, 83, 85, 87, 89, 91, 93, 95, 97, 99, 101, 102, 104, 106, 108, 110,
    112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140,
    142, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 170,
    171, 173, 175, 177, 179, 181, 182, 184, 186, 188, 190, 191, 193, 195, 196,
    198, 200, 201, 203, 205, 206, 208, 209, 211, 212, 214, 215, 217, 218, 220,
    221, 222, 224, 225, 226, 228, 229, 230, 231, 232, 233, 235, 236, 237, 238,
    239, 240, 241, 242, 242, 243, 244, 245, 246, 247, 247, 248, 249, 249, 250,
    250, 251, 251, 252, 252, 253, 253, 254, 254, 254, 254, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 254, 254, 254, 253,
    253, 253, 252, 252, 251, 251, 250, 249, 249, 248, 247, 247, 246, 245, 244,
    244, 243, 242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 231, 230, 229,
    228, 227, 225, 224, 223, 221, 220, 219, 217, 216, 214, 213, 211, 210, 208,
    207, 205, 203, 202, 200, 199, 197, 195, 193, 192, 190, 188, 187, 185, 183,
    181, 179, 177, 176, 174, 172, 170, 168, 166, 164, 162, 160, 159, 157, 155,
    153, 151, 149, 147, 145, 143, 141, 139, 137, 135, 133, 131, 129])