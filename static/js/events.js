(() => {
    "use strict";

    const search = document.querySelector("[data-location-search]");
    if (!search) return;

    const address = document.getElementById("id_location");
    const latitude = document.getElementById("id_latitude");
    const longitude = document.getElementById("id_longitude");
    const button = document.getElementById("location-search-button");
    const status = document.getElementById("location-search-status");
    const results = document.getElementById("location-results");
    if (!address || !latitude || !longitude || !button || !status || !results) return;

    let activeSearch = null;

    address.addEventListener("input", () => {
        if (activeSearch) {
            activeSearch.controller.abort();
            activeSearch = null;
            button.disabled = false;
            results.removeAttribute("aria-busy");
        }
        results.replaceChildren();
        const hadCoordinates = latitude.value !== "" || longitude.value !== "";
        latitude.value = "";
        longitude.value = "";
        status.textContent = hadCoordinates
            ? "Alamat diubah. Pilih lokasi lagi untuk memperbarui titik di peta."
            : "";
    });

    button.addEventListener("click", async () => {
        const query = address.value.trim();
        results.replaceChildren();
        if (query.length < 3) {
            status.textContent = "Masukkan sedikitnya 3 karakter nama tempat atau alamat.";
            address.focus();
            return;
        }

        button.disabled = true;
        results.setAttribute("aria-busy", "true");
        status.textContent = "Mencari lokasi…";
        const controller = new AbortController();
        const currentSearch = { controller };
        activeSearch = currentSearch;
        const timeout = window.setTimeout(() => controller.abort(), 12000);
        try {
            const url = new URL(search.dataset.url, window.location.origin);
            url.searchParams.set("q", query);
            const response = await fetch(url, {
                headers: { Accept: "application/json" },
                signal: controller.signal,
                credentials: "same-origin",
            });
            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                throw new Error("Sesi berakhir. Muat ulang halaman dan masuk kembali sebagai EO.");
            }
            const data = await response.json();
            if (activeSearch !== currentSearch) return;
            if (!response.ok) throw new Error(data.error || "Pencarian lokasi belum tersedia. Coba lagi sebentar.");
            if (!Array.isArray(data.results)) throw new Error("Hasil pencarian tidak dapat dibaca. Coba lagi.");
            if (!data.results.length) {
                status.textContent = "Lokasi tidak ditemukan. Coba alamat lebih lengkap atau isi alamat manual.";
                return;
            }

            data.results.forEach((place) => {
                const lat = Number(place.latitude);
                const lon = Number(place.longitude);
                if (typeof place.name !== "string" || !Number.isFinite(lat) || !Number.isFinite(lon)
                    || Math.abs(lat) > 90 || Math.abs(lon) > 180) return;
                const item = document.createElement("li");
                const choice = document.createElement("button");
                choice.type = "button";
                choice.className = "location-result";
                choice.textContent = place.name;
                choice.addEventListener("click", () => {
                    address.value = place.name;
                    latitude.value = lat.toFixed(6);
                    longitude.value = lon.toFixed(6);
                    results.replaceChildren();
                    status.textContent = "Lokasi dipilih.";
                    address.focus();
                });
                item.append(choice);
                results.append(item);
            });
            status.textContent = results.children.length
                ? "Pilih lokasi yang sesuai."
                : "Lokasi tidak ditemukan. Coba alamat lain atau isi alamat manual.";
        } catch (error) {
            if (activeSearch !== currentSearch) return;
            status.textContent = error.name === "AbortError"
                ? "Pencarian terlalu lama. Coba lagi atau isi alamat manual."
                : error instanceof TypeError
                    ? "Pencarian gagal. Periksa koneksi atau isi alamat manual."
                    : error.message || "Pencarian gagal. Coba lagi atau isi alamat manual.";
        } finally {
            window.clearTimeout(timeout);
            if (activeSearch === currentSearch) {
                activeSearch = null;
                button.disabled = false;
                results.removeAttribute("aria-busy");
            }
        }
    });
})();
