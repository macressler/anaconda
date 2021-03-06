#version 120
#define HORIZONTAL false
#define VERTICAL true
#define PANORAMA 0
#define PERSPECTIVE 1
#define SINEWAVE 2
#define SINEOFFSET 3
#define CUSTOM 4
#define CUSTOMOFFSET 5
#define LEFTRIGHTTOPBOTTOM false
#define RIGHTLEFTBOTTOMTOP true
#define delta (3.141592/180.0)
#define wave_increment (sine_waves * 360.0f)

varying vec2 texture_coordinate;
uniform sampler2D texture;
uniform vec2 texture_size;
uniform int effect;
uniform bool direction, perspective_dir;
uniform float zoom, offset;
uniform int sine_waves;

void main()
{
    float v;
    vec2 In = texture_coordinate;
    
    // What to use as input
    float pixel = (direction == VERTICAL) ? texture_size.y : texture_size.x;
    float i = ((direction == VERTICAL) ? In.x : In.y);
    
    // Effect
    if (effect == SINEOFFSET)
       v = sin((i * wave_increment - offset) * delta) * zoom; 
    
    // What to use as output
    if (direction == VERTICAL) In.y += v*pixel;
    else In.x += v*pixel;
    
    vec4 col;
    if (In.x < 0 || In.x > 1 || In.y < 0|| In.y > 1)
       col = vec4(0,0,0,1);
    else
       col = texture2D(texture, In);
    gl_FragColor = col;
}