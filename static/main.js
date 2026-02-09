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
