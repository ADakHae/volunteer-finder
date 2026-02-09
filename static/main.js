document.addEventListener("DOMContentLoaded", function () {
    // 시/도 선택 시 시군구 드롭다운 로딩
    var regionSel = document.getElementById("region");
    var districtSel = document.getElementById("district");

    if (regionSel && districtSel) {
        regionSel.addEventListener("change", function () {
            var code = this.value;
            districtSel.innerHTML = '<option value="">전체</option>';
            if (!code) return;

            fetch("/api/districts/" + code)
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.error) return;
                    Object.keys(data).forEach(function (k) {
                        var opt = document.createElement("option");
                        opt.value = k;
                        opt.textContent = data[k];
                        districtSel.appendChild(opt);
                    });
                    // 이전 선택값 복원
                    var prev = districtSel.dataset.selected;
                    if (prev) districtSel.value = prev;
                });
        });

        // 페이지 로드 시 이미 시/도가 선택되어 있으면 시군구 로딩
        if (regionSel.value) {
            regionSel.dispatchEvent(new Event("change"));
        }
    }

    // 동기화 버튼
    var syncBtn = document.getElementById("syncBtn");
    if (syncBtn) {
        syncBtn.addEventListener("click", function () {
            syncBtn.disabled = true;
            syncBtn.textContent = "동기화 중...";

            // 현재 필터 폼의 값을 수집
            var filterForm = document.querySelector(".filter-form");
            var body = filterForm ? new URLSearchParams(new FormData(filterForm)).toString() : "";

            fetch("/api/sync", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: body,
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.error) {
                        alert(data.error);
                        syncBtn.disabled = false;
                        syncBtn.textContent = "동기화";
                        return;
                    }
                    pollSync();
                });
        });

        function pollSync() {
            fetch("/api/sync-status")
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.running) {
                        var progress = data.total_pages
                            ? Math.round(data.page / data.total_pages * 100)
                            : 0;
                        syncBtn.textContent = "동기화 중... " + progress + "%";
                        var countEl = document.getElementById("syncCount");
                        if (countEl) countEl.textContent = data.fetched;
                        setTimeout(pollSync, 2000);
                    } else if (data.error) {
                        alert("동기화 오류: " + data.error);
                        syncBtn.disabled = false;
                        syncBtn.textContent = "동기화";
                    } else {
                        syncBtn.textContent = data.fetched + "건 완료!";
                        setTimeout(function () { location.reload(); }, 1000);
                    }
                });
        }
    }

    // 저장 버튼
    var saveBtn = document.getElementById("saveBtn");
    if (saveBtn) {
        saveBtn.addEventListener("click", function () {
            var id = this.dataset.id;
            fetch("/api/save/" + id, { method: "POST" })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    saveBtn.dataset.saved = data.saved ? "1" : "0";
                    saveBtn.textContent = data.saved ? "저장됨" : "저장하기";
                });
        });
    }
});
