const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");

const script = readFileSync(path.join(__dirname, "../../static/js/events.js"), "utf8");

class Element {
    constructor() {
        this.value = "";
        this.textContent = "";
        this.disabled = false;
        this.children = [];
        this.attributes = new Map();
        this.listeners = new Map();
        this.dataset = {};
    }
    addEventListener(name, handler) {
        const listeners = this.listeners.get(name) || [];
        listeners.push(handler);
        this.listeners.set(name, listeners);
    }
    emit(name) {
        return Promise.all((this.listeners.get(name) || []).map((handler) => handler({ type: name })));
    }
    replaceChildren(...children) { this.children = children; }
    append(child) { this.children.push(child); }
    setAttribute(name, value) { this.attributes.set(name, value); }
    removeAttribute(name) { this.attributes.delete(name); }
    focus() { this.focused = true; }
}

function response(data, status = 200) {
    return {
        ok: status >= 200 && status < 300,
        headers: { get: () => "application/json" },
        json: async () => data,
    };
}

function boot(fetchImplementation) {
    const names = ["id_location", "id_latitude", "id_longitude", "location-search-button", "location-search-status", "location-results"];
    const elements = Object.fromEntries(names.map((name) => [name, new Element()]));
    const search = new Element();
    search.dataset.url = "/events/locations/search/";
    const requests = [];
    vm.runInNewContext(script, {
        document: {
            querySelector: () => search,
            getElementById: (name) => elements[name],
            createElement: () => new Element(),
        },
        window: {
            location: { origin: "http://localhost:8000" },
            setTimeout: () => 1,
            clearTimeout: () => {},
        },
        fetch: (...args) => {
            requests.push(args);
            return fetchImplementation(...args);
        },
        URL,
        AbortController,
        TypeError,
    });
    return {
        address: elements.id_location,
        latitude: elements.id_latitude,
        longitude: elements.id_longitude,
        button: elements["location-search-button"],
        status: elements["location-search-status"],
        results: elements["location-results"],
        requests,
    };
}

const place = { name: "Universitas Indonesia", latitude: "-6.362123", longitude: "106.827153" };

test("typing does not search; only the explicit button calls the provider endpoint", async () => {
    const ui = boot(async () => response({ results: [place] }));
    ui.address.value = "Universitas Indonesia";
    await ui.address.emit("input");
    assert.equal(ui.requests.length, 0);
    await ui.button.emit("click");
    assert.equal(ui.requests.length, 1);
    assert.equal(ui.requests[0][0].searchParams.get("q"), "Universitas Indonesia");
    assert.equal(ui.requests[0][0].pathname, "/events/locations/search/");
});

test("selecting a result fills address and both coordinates using literal text", async () => {
    const name = "<img src=x onerror=alert(1)>";
    const ui = boot(async () => response({ results: [{ ...place, name }] }));
    ui.address.value = "Jakarta";
    await ui.button.emit("click");
    const choice = ui.results.children[0].children[0];
    assert.equal(choice.textContent, name);
    assert.equal(choice.type, "button");
    await choice.emit("click");
    assert.equal(ui.address.value, name);
    assert.equal(ui.latitude.value, "-6.362123");
    assert.equal(ui.longitude.value, "106.827153");
    assert.equal(ui.results.children.length, 0);
});

test("editing a selected address clears stale coordinates and allows manual replacements", async () => {
    const ui = boot(async () => response({ results: [place] }));
    ui.address.value = "Universitas Indonesia";
    await ui.button.emit("click");
    await ui.results.children[0].children[0].emit("click");
    ui.address.value = "Lokasi berbeda";
    await ui.address.emit("input");
    assert.equal(ui.latitude.value, "");
    assert.equal(ui.longitude.value, "");
    assert.equal(ui.results.children.length, 0);
    assert.match(ui.status.textContent, /Alamat diubah/);
    ui.latitude.value = "-7.100000";
    ui.longitude.value = "110.200000";
    assert.equal(ui.latitude.disabled, false);
    assert.equal(ui.longitude.disabled, false);
});

test("a response arriving after the address changes is ignored", async () => {
    let resolveResponse;
    const ui = boot(() => new Promise((resolve) => { resolveResponse = resolve; }));
    ui.address.value = "Alamat pertama";
    const pendingSearch = ui.button.emit("click");
    const signal = ui.requests[0][1].signal;
    ui.address.value = "Alamat kedua";
    await ui.address.emit("input");
    assert.equal(signal.aborted, true);
    resolveResponse(response({ results: [place] }));
    await pendingSearch;
    assert.equal(ui.results.children.length, 0);
    assert.equal(ui.address.value, "Alamat kedua");
    assert.equal(ui.latitude.value, "");
    assert.equal(ui.longitude.value, "");
    assert.equal(ui.status.textContent, "");
    assert.equal(ui.button.disabled, false);
});

test("network and rate-limit failures preserve manual values and restore controls", async () => {
    const scenarios = [
        { fetch: async () => { throw new TypeError("Failed to fetch"); }, message: /koneksi|manual/ },
        { fetch: async () => response({ error: "Tunggu sebentar.", retry_after: 2 }, 429), message: /Tunggu sebentar/ },
    ];
    for (const scenario of scenarios) {
        const ui = boot(scenario.fetch);
        ui.address.value = "Alamat manual";
        ui.latitude.value = "-6.100000";
        ui.longitude.value = "106.100000";
        await ui.button.emit("click");
        assert.equal(ui.address.value, "Alamat manual");
        assert.equal(ui.latitude.value, "-6.100000");
        assert.equal(ui.longitude.value, "106.100000");
        assert.equal(ui.button.disabled, false);
        assert.equal(ui.latitude.disabled, false);
        assert.equal(ui.longitude.disabled, false);
        assert.equal(ui.results.attributes.has("aria-busy"), false);
        assert.equal(ui.results.children.length, 0);
        assert.match(ui.status.textContent, scenario.message);
    }
});
