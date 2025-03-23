#version 300 es

precision highp float;

in vec2 vTexPos;
out vec4 pColor;

uniform vec2 uMapSize;
uniform vec4 uColorSelected;
uniform sampler2D uMapTex;
uniform sampler2D uTransTex;

vec4 getTransColor(ivec2 iTexPos)
{
    vec4 mapColor = texelFetch(uMapTex, iTexPos, 0);
    ivec3 rgbPos = ivec3(mapColor.rgb * 255.0);
    ivec2 transPos = ivec2(
        rgbPos.r + ((rgbPos.b & 240) << 4),
        rgbPos.g + ((rgbPos.b & 15) << 8)
    );
    return texelFetch(uTransTex, transPos, 0);
}

void main()
{  
    ivec2 iTexPos = ivec2(vTexPos * vec2(textureSize(uMapTex, 0)));
   
    vec4 baseColor = getTransColor(iTexPos);
    vec4 borderColor = vec4(0, 0, 0, 1.0);
    if ( baseColor * 255.0 == uColorSelected ) { borderColor = vec4(1.0, 0.8, 1.0, 1.0);};

    for(int y = -1; y <= 1; y++) {
        for(int x = -1; x <= 1; x++) {
            vec4 offsetColor = getTransColor(iTexPos + ivec2( x, y));
            if (offsetColor != baseColor) { pColor = borderColor; return; }
        }
    }

    pColor = baseColor;
}