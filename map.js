const container = document.getElementById("canvas-container");
const canvas = document.getElementById("canvas");
const gl = canvas.getContext("webgl2");

const game = {
    provinces: {},
    titles: {},
    faith: {},
    culture: {}
};

const provinceMap = {
    width: 6656,
    height: 4096,
    image: null,
    pixels: null,
    at(x, y) {
        const index = 4 * (y * this.width + x); // RGBA
        const color = [this.pixels[index + 0], this.pixels[index + 1], this.pixels[index + 2]];
        return Object.values(game.provinces).find(e => e.equal(color)); // will always find a color
    }
}

const uniforms = {
    zoom: null,
    offset: null,
    transTexture: null,
    colorSelected: null,
}

async function create_program(urlVertex, urlFragment) {
    const create_shader = (type, source) => {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        const success = gl.getShaderParameter(shader, gl.COMPILE_STATUS);
        if (success) { return shader; }
        console.log(gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
    }

    const vShader = fetch(urlVertex)
        .then(r => r.text())
        .then(source => create_shader(gl.VERTEX_SHADER, source));

    const fShader = fetch(urlFragment)
        .then(r => r.text())
        .then(source => create_shader(gl.FRAGMENT_SHADER, source));

    return Promise.all([vShader, fShader]).then(values => {
        const program = gl.createProgram();
        if (values[0] == null) { console.log("Vertex Shader Fail"); return null; }
        if (values[1] == null) { console.log("Fragment Shader Fail"); return null; }
        gl.attachShader(program, values[0]);
        gl.attachShader(program, values[1]);
        gl.linkProgram(program);
        return program;
    });
}

function draw() {
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
}

const scrZoom = {
    zoom: 1,
    minZoom: null,
    ratiox: null, // keep same aspect ratio as provinceMap
    ratioy: null, // keep same aspect ratio as provinceMap
    update() {
        this.ratiox = provinceMap.width / canvas.width;
        this.ratioy = provinceMap.height / canvas.height;
        this.minZoom = 1 / Math.max(this.ratiox, this.ratioy);
    },
    apply() {
        this.zoom = Math.min(Math.max(1, this.zoom), 5);
        gl.uniform2f(uniforms.zoom, this.zoom * this.minZoom * this.ratiox, this.zoom * this.minZoom * this.ratioy);
    }
}

const scrOff = {
    x: 0,
    y: 0,
    max: null,
    // Panning
    dragging: false,
    startX: 0,
    startY: 0,
    update() {
        this.max = scrZoom.zoom - 1;
    },
    apply() {
        this.x = Math.min(Math.max(-this.max, this.x), this.max);
        this.y = Math.min(Math.max(-this.max, this.y), this.max);
        gl.uniform2f(uniforms.offset, this.x, this.y);
    }
}

const init_status = {
    canvas: false,
    map: false,
    data: false,
    program: false,
    ok: false,
    async start() {
        if (!(this.canvas && this.map && this.data && this.program)) { return; }
        this.ok = true;

        //counties();

        draw();

        return;
    }
}

const init_canvas = () => {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    gl.viewport(0, 0, canvas.width, canvas.height);

    provinceMap.image = new Image();
    provinceMap.image.onload = init_map;
    provinceMap.image.src = "/provinces.png";

    gl.clearColor(0, 0, 0, 1);

    gl.activeTexture(gl.TEXTURE0); // Province Map
    gl.activeTexture(gl.TEXTURE1); // Translation Texture

    uniforms.transTexture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGB8, 4096, 4096); // empty texture to be modified

    const region = new Float32Array([
        -1, -1, 0, 0,
        1, -1, 1, 0,
        -1, 1, 0, 1,
        1, -1, 1, 0,
        1, 1, 1, 1,
        -1, 1, 0, 1
    ]);

    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, region, gl.STATIC_DRAW);

    console.log("Canvas Initialized");
    init_status.canvas = true;
    init_status.start();
};

const init_map = async () => {
    const mapCanvas = document.createElement("canvas");
    mapCanvas.width = provinceMap.width;
    mapCanvas.height = provinceMap.height;
    const mapContext = mapCanvas.getContext("2d");
    mapContext.drawImage(provinceMap.image, 0, 0);
    provinceMap.pixels = mapContext.getImageData(0, 0, provinceMap.width, provinceMap.height).data;
    mapCanvas.remove();

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, gl.createTexture());

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true); // Flip image

    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

    gl.texImage2D(
        gl.TEXTURE_2D, 0, gl.RGB,
        provinceMap.width, provinceMap.height, 0,
        gl.RGB, gl.UNSIGNED_BYTE, provinceMap.image
    );

    console.log("Map Initialized");
    init_status.map = true;
    init_status.start();
}

const init_data = async () => {
    const url = "/data.json";
    const json = fetch(url).then(resp => resp.json());
    json.then(data => {
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);

        for (const province in data.provinces) {
            game.provinces[province] = {
                name: province,
                color: data.provinces[province],
                reference: null,
                equal(color) { // color matches this province
                    return (
                        color[0] == this.color[0]
                        && color[1] == this.color[1]
                        && color[2] == this.color[2]
                    );
                },
                update() {
                    const displayColor = this.reference === null ? [0, 0, 0] : this.reference.color;
                    const coordX = this.color[0] + ((this.color[2] & 0b11110000) << 4);
                    const coordY = this.color[1] + ((this.color[2] & 0b00001111) << 8);
                    gl.texSubImage2D(gl.TEXTURE_2D, 0,
                        coordX, coordY, 1, 1, gl.RGB, gl.UNSIGNED_BYTE,
                        new Uint8Array(displayColor));
                }
            };
            game.provinces[province].reference = game.provinces[province];
            game.provinces[province].update();
        }

        game.titles = data.titles;
        game.faith = data.faith;
        game.culture = data.culture;
        for (const [key, title] of Object.entries(game.titles)) {
            title.id = key;
            if (title.rank != "empire") {
                title.parent = game.titles[title.parent];
            }
            if (title.rank != "barony") {
                title.children = title.children.map(e => game.titles[e]);
            }
            if (title.rank == "county") {
                title.faith = game.faith[title.faith];
                title.culture = game.culture[title.culture];
            }
        }

        console.log("Data Initialized");
        init_status.data = true;
        init_status.start();
    });
};

const init_program = async () => {
    create_program("/shader.vert", "/shader.frag").then(
        program => {
            if (program == null) { console.log("Program creation fail"); return; }
            gl.useProgram(program);

            const aPos = gl.getAttribLocation(program, "aPos");
            gl.enableVertexAttribArray(aPos);
            gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 4 * 4, 0);

            const aTexPos = gl.getAttribLocation(program, "aTexPos");
            gl.enableVertexAttribArray(aTexPos);
            gl.vertexAttribPointer(aTexPos, 2, gl.FLOAT, false, 4 * 4, 2 * 4);

            const uMapTex = gl.getUniformLocation(program, "uMapTex");
            gl.uniform1i(uMapTex, 0);

            const uTransTex = gl.getUniformLocation(program, "uTransTex");
            gl.uniform1i(uTransTex, 1);

            uniforms.zoom = gl.getUniformLocation(program, "uZoom");
            scrZoom.update();
            scrZoom.apply();

            uniforms.offset = gl.getUniformLocation(program, "uOffset");
            scrOff.update();
            scrOff.apply();

            uniforms.colorSelected = gl.getUniformLocation(program, "uColorSelected");
            gl.uniform4f(uniforms.colorSelected, 0, 0, 0, 0);

            console.log("Program Initialized");
            init_status.program = true;
            init_status.start();
        }
    );
}

window.onresize = e => {
    if (!init_status.ok) { return; }

    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    gl.viewport(0, 0, canvas.width, canvas.height);

    scrZoom.update();
    scrZoom.apply();

    draw();
};

canvas.onwheel = e => {
    if (!init_status.ok) { return; }
    const zoom_direction = e.deltaY > 0 ? 1 : -1;
    scrZoom.zoom += zoom_direction * 0.3;
    scrZoom.update();
    scrZoom.apply();

    // TODO: ZOOM IN MOUSE
    scrOff.update();
    scrOff.apply();
    draw();
};

canvas.onmouseup = e => scrOff.dragging = false;
canvas.onmouseleave = e => scrOff.dragging = false;

canvas.onmousedown = (e) => {
    if (!init_status.ok) { return; }

    scrOff.dragging = true
    scrOff.startX = e.clientX;
    scrOff.startY = e.clientY;
};

canvas.onmousemove = e => {
    if (!init_status.ok) { return; }

    let offX = (canvas.width * (1 + scrOff.x) - provinceMap.width * scrZoom.zoom * scrZoom.minZoom) / 2;
    let offY = (canvas.height * (1 - scrOff.y) - provinceMap.height * scrZoom.zoom * scrZoom.minZoom) / 2;

    const posX = Math.floor((e.clientX - offX) / (scrZoom.zoom * scrZoom.minZoom));
    const posY = Math.floor((e.clientY - offY) / (scrZoom.zoom * scrZoom.minZoom));

    const province = provinceMap.at(posX, posY);
    const selectedName = province.reference === null ? province.name : province.reference.name;
    const selectedColor = province.reference === null ? province.color : province.reference.color;

    document.getElementById("realmname").innerText = selectedName;

    gl.uniform4f(uniforms.colorSelected, selectedColor[0], selectedColor[1], selectedColor[2], 255);

    if (!scrOff.dragging) { draw(); return; }

    scrOff.x += (e.clientX - scrOff.startX) / 2000;
    scrOff.startX = e.clientX;

    scrOff.y -= (e.clientY - scrOff.startY) / 2000;
    scrOff.startY = e.clientY;

    scrOff.apply();
    draw();
}

function barony() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const barony of Object.values(game.titles).filter(title => title.rank == "barony")) {
        const province = game.provinces[barony.province];
        province.reference = barony;
        province.update();
    }

    draw();
}

function county() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const county of Object.values(game.titles).filter(title => title.rank == "county")) {
        for (const barony of county.children) {
            const province = game.provinces[barony.province];
            province.reference = county;
            province.update();
        }
    }

    draw();
}

function duchy() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);

    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const duchy of Object.values(game.titles).filter(title => title.rank == "duchy")) {
        for (const county of duchy.children) {
            for (const barony of county.children) {
                const province = game.provinces[barony.province];
                province.reference = duchy;
                province.update();
            }
        }
    }

    draw();
}

function kingdom() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);

    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const kingdom of Object.values(game.titles).filter(title => title.rank == "kingdom")) {
        for (const duchy of kingdom.children) {
            for (const county of duchy.children) {
                for (const barony of county.children) {
                    const province = game.provinces[barony.province];
                    province.reference = kingdom;
                    province.update();
                }
            }
        }
    }

    draw();
}

function empire() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const empire of Object.values(game.titles).filter(title => title.rank == "empire")) {
        for (const kingdom of empire.children) {
            for (const duchy of kingdom.children) {
                for (const county of duchy.children) {
                    for (const barony of county.children) {
                        const province = game.provinces[barony.province];
                        province.reference = empire;
                        province.update();
                    }
                }
            }
        }
    }

    draw();
}

function faith() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const county of Object.values(game.titles).filter(title => title.rank == "county")) {
        for (const barony of county.children) {
            const province = game.provinces[barony.province];
            province.reference = county.faith;
            province.update();
        }
    }

    draw();
}

function culture() {
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, uniforms.transTexture);
    for (const province of Object.values(game.provinces)) { province.reference = null; province.update(); }

    for (const county of Object.values(game.titles).filter(title => title.rank == "county")) {
        for (const barony of county.children) {
            const province = game.provinces[barony.province];
            province.reference = county.culture;
            province.update();
        }
    }

    draw();
}


init_canvas();
init_data();
init_program();