const view_toggle = document.getElementById("view_toggle");
const view_all = document.getElementById("view_all");
const container_nav = document.getElementById("container_nav");
const container_viewer = document.getElementById("container_viewer");

function showNavOnly() {
    container_nav.style.display = "flex";
    container_viewer.style.display = "none";
}

function showViewerOnly() {
    container_nav.style.display = "none";
    container_viewer.style.display = "block";
}

function showBoth() {
    container_nav.style.display = "flex";
    container_viewer.style.display = "block";
}

function resetViewByOrientation() {
    if (window.matchMedia("(orientation: portrait)").matches) {
        showNavOnly();
    } else {
        showBoth();
    }
}

// 初期表示
resetViewByOrientation();

// 画面回転
window
    .matchMedia("(orientation: portrait)")
    .addEventListener("change", resetViewByOrientation);

// 表示切替
view_toggle.addEventListener("click", function(e) {
    e.preventDefault();

    if (container_nav.style.display !== "none") {
        showViewerOnly();
    } else {
        showNavOnly();
    }
});

// 全表示
view_all.addEventListener("click", function(e) {
    e.preventDefault();
    showBoth();
});

// bookクリック
document.querySelectorAll(".bookbtn.internal").forEach(bookbtn => {
    bookbtn.addEventListener("click", function() {

        if (window.matchMedia("(orientation: portrait)").matches) {
            showViewerOnly();
        }

    });
});