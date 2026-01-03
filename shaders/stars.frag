#version 330
precision mediump float;
uniform vec2 u_resolution;
uniform float u_time;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 st) {
    vec2 i = floor(st);
    vec2 f = fract(st);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    vec2 u = f * f * (3.0 - 2.0 * f);

    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float star(vec2 uv, float brightness) {
    float d = length(uv);

    float m = 0.05 / (d + 0.01);

    float rays = max(0.0, 1.0 - abs(uv.x * uv.y) * 1000.0);
    m += rays * 0.3;

    m *= smoothstep(0.6, 0.0, d) * brightness;

    return m;
}

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / u_resolution.y;

    vec3 finalColor = vec3(0.0);

    vec2 dustUv1 = uv * 1.0 + u_time * 0.05;
    vec2 dustUv2 = uv * 6.0 + u_time * 0.3;

    float dust = noise(dustUv1) + noise(dustUv2) * 0.2;

    finalColor += dust * vec3(0.1, 0.12, 0.18);

    for (float i = 0.0; i < 3.0; i++) {
        float scale = 15.0 + i * 20.0;
        float speed = 0.05 + i * 0.1;

        vec2 uv_stars = uv * scale;
        uv_stars.x += u_time * speed;

        vec2 grid = fract(uv_stars) - 0.5;
        vec2 id = floor(uv_stars);

        float h = hash(id);

        if (h > 0.992) {
            float size = fract(h * 345.32) * 0.6 + 0.4;
            float brightness = 0.5 + i * 0.2;

            float star_val = star(grid, size * brightness);

            float twinkle = sin(u_time * 3.0 + h * 100.0) * 0.2 + 0.8;
            star_val *= twinkle;

            vec3 starColor = mix(
                vec3(0.8, 0.8, 1.0),
                vec3(1.0, 0.9, 0.7),
                fract(h * 123.45)
            );

            finalColor += starColor * star_val;
        }
    }

    finalColor = pow(finalColor, vec3(0.8));

    gl_FragColor = vec4(finalColor, 1.0);
}