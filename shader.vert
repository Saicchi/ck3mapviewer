#version 300 es

precision highp float;

layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aTexPos;
out vec2 vTexPos;

uniform vec2 uZoom;
uniform vec2 uOffset;

void main(void)
{
    vTexPos = aTexPos;
    gl_Position = vec4(aPos * uZoom + uOffset, 0.0, 1.0);
}