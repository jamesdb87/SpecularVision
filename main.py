import sys

HEADLESS = True

if HEADLESS:
    import time
    import board
    import busio
    import adafruit_dotstar as dotstar
    dot = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)
    serial = busio.UART(board.TX, board.RX, baudrate=115200)
else:
    import colorsys
    import pygame
    from datetime import datetime

start_time = time.monotonic() if HEADLESS else datetime.now()

HEADFUL_MILLISECONDS_PER_REVOLUTION = 15 * 1000
HEADLESS_TICKS_PER_REVOLUTION = 5
FLARE_HUE_SPREAD = 0.2 # The flare ranges from hue x to hue x + FLARE_HUE_SPREAD (hues range from 0 to 1)
BACKGROUND_VALUE_1 = 0
BACKGROUND_VALUE_2 = .5
BACKGROUND_HUE_1 = 0 # Red
BACKGROUND_HUE_2 = 0.5 # Aqua
BACKGROUND_VALUE = .5 # Darken it a bit

colors = [
    [0, 0, 0], # DNA pairs (pointed directly at viewer)
    [236, 106, 229], # Petal outer
    [0, 64, 0], # Background 2
    [255, 253, 84], # Flare 6 (outside)
    [246, 195, 67], # Flare 5
    [237, 97, 43], # Flare 3
    [167, 40, 27], # Flare 1 (inside)
    [235, 60, 37], # Flare 2 (second from inside)
    [240, 143, 53], # Flare 4
    [0, 50, 0], # Background 1
    [95, 32, 182], # Petal outline
    [239, 144, 249], # Petal center
]
FLARE_INDICES = [6, 7, 5, 8, 4, 3] # The indices into the color array of the flare, starting from innermost
BACKGROUND_INDICES = [9, 2]

def hsv2rgb(h, s, v):
    # if HEADLESS:
    return hsv2rgb_with_math(h, s, v)
    # else:
        # return hsv2rgb_with_library(h, s, v)

def hsv2rgb_with_library(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

# http://www.easyrgb.com/en/math.php
def hsv2rgb_with_math(H, S, V):
    # H, S and V input range = 0 to 1.0
    # R, G and B output range = 0 to 255
    R = 0
    G = 0
    B = 0
    if S == 0:
        R = V * 255
        G = V * 255
        B = V * 255
    else:
        var_h = H * 6
        if var_h == 6:
            var_h = 0      # H must be < 1
        var_i = int( var_h )             # Or ... var_i = floor( var_h )
        var_1 = V * ( 1 - S )
        var_2 = V * ( 1 - S * ( var_h - var_i ) )
        var_3 = V * ( 1 - S * ( 1 - ( var_h - var_i ) ) )

        if var_i == 0:
            var_r = V
            var_g = var_3
            var_b = var_1 
        elif var_i == 1:
            var_r = var_2
            var_g = V
            var_b = var_1
        elif var_i == 2:
            var_r = var_1
            var_g = V
            var_b = var_3
        elif var_i == 3:
            var_r = var_1
            var_g = var_2
            var_b = V
        elif var_i == 4:
            var_r = var_3
            var_g = var_1
            var_b = V
        else:
            var_r = V
            var_g = var_1
            var_b = var_2

        R = int(var_r * 255)
        G = int(var_g * 255)
        B = int(var_b * 255)

    return (R, G, B)



def computeColors(timePercent):
    # Flare
    dna_1_hue = 0
    dna_2_hue = 0
    for i in range(len(FLARE_INDICES)):
        flarePercent = (i / float(len(FLARE_INDICES)))
        hueOffset = flarePercent * FLARE_HUE_SPREAD
        iPercent = ((1 - timePercent) + hueOffset) % 1
        v = 1 # - flarePercent / 3 # Dim the edges a bit
        rgb = hsv2rgb(iPercent, 1, v)
        flareIndex = FLARE_INDICES[i]
        colors[flareIndex] = rgb
        # Set the value for the DNA strands as an offset of the inner-most and outer-most flare
        if i == 0:
            dna_1_hue = iPercent
        elif i == len(FLARE_INDICES) - 1:
            dna_2_hue = iPercent
    
    # DNA Strands (uses Background colors, even though we don't have a background)
    colors[BACKGROUND_INDICES[0]] = hsv2rgb((dna_1_hue + .5) % 1, 1, 1)
    colors[BACKGROUND_INDICES[1]] = hsv2rgb((dna_2_hue + .5) % 1, 1, 1)

    # Background (No background for now)
    # bounceTimePercent goes from 0 to 1 then back to 0 (instead of 0 to 1 like timePercent)
    # bounceTimePercent = timePercent * 2 if timePercent < .5 else (1 - timePercent) * 2
    # backgroundValue1 = (BACKGROUND_VALUE_2 - BACKGROUND_VALUE_1) * bounceTimePercent + BACKGROUND_VALUE_1
    # backgroundValue2 = BACKGROUND_VALUE_2 - (BACKGROUND_VALUE_2 - BACKGROUND_VALUE_1) * bounceTimePercent
    # colors[BACKGROUND_INDICES[0]] = hsv2rgb(BACKGROUND_HUE_1, 1, backgroundValue1)
    # colors[BACKGROUND_INDICES[1]] = hsv2rgb(BACKGROUND_HUE_2, 1, backgroundValue2)
    
    

## Only used when running on a computer with a screen ##
def drawToImage(image):
    layoutFile = open("layout.csv", "r")
    layoutRows = layoutFile.readlines()
    y = -1
    for layoutRow in layoutRows:
        y = y + 1
        colorIndices = layoutRow.split(',')
        for x in range(len(colorIndices)):
            colorIndexString = colorIndices[x]
            if colorIndexString.isdigit():
                colorIndex = int(colorIndexString)
                color = colors[colorIndex]
                image.set_at((x, y), color)

def drawFrameToScreen():
    SCREEN_SIZE = (1200, 800)
    BG_COLOR = (0, 0, 0)
    SCALE = 12

    width = 58
    height = 59

    image = pygame.Surface((width, height))

    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    screen.fill(BG_COLOR)

    # Draw the image off-screen
    drawToImage(image)

    # Optimize the images after they're drawn
    image.convert()

    # Get the area in the middle of the visible screen where our images would fit
    draw_area = image.get_rect().move(SCREEN_SIZE[0] / 2 - width * SCALE / 2,
                                    SCREEN_SIZE[1] / 2 - height * SCALE / 2)

    # Scale the image up
    scaledImage = pygame.transform.scale(image, (width * SCALE, height * SCALE))

    # Draw our off-screen image to the visible screen
    screen.blit(scaledImage, draw_area)

    # Display changes to the visible screen
    pygame.display.flip()
    
def pushToLEDs():
    dot[0] = colors[3] # Make the test LED light up the same as the third light
    array = [] # Make a linear array containing the colors for all the bulbs (r1, g1, b1, r2, g2, b2, etc)
    time.sleep(.001)
    for color in colors:
        array.extend(color)
    serial.write(bytes(array))
    
# Initialize pygame if we're on a computer
if (not HEADLESS):
    import pygame
    pygame.init()

# Keep the window from closing as soon as it's finished drawing
while True:
    # Handle window events if we're in a window
    if (not HEADLESS):
        # Close the window gracefully upon hitting the close button
        import pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

    timePercent = 0
    if HEADLESS: 
        elapsed_since_start = time.monotonic() - start_time
        timePercent = elapsed_since_start / HEADLESS_TICKS_PER_REVOLUTION % 1
    else:
        elapsed_since_start = datetime.now() - start_time
        milliseconds = elapsed_since_start.total_seconds() * 1000
        timePercent = (milliseconds / HEADFUL_MILLISECONDS_PER_REVOLUTION) % 1
    
    computeColors(timePercent)
        
    if HEADLESS:
        pushToLEDs()
    else:
        drawFrameToScreen()
        