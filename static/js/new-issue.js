/**
 * new-issue.js — Kapantsi "Report an Issue" page behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 * Requires Leaflet (loaded before this script).
 */
(function () {
  'use strict';

  var LANG = window.KAPANTSI_LANG || 'en';

  var DEFAULT_LAT = 39.2067;
  var DEFAULT_LNG = 46.4058;

  // ── Map initialisation ────────────────────────────────────────────────────
  var map = L.map('new-issue-map', { zoomSnap: 1 }).setView([DEFAULT_LAT, DEFAULT_LNG], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  setTimeout(function () { map.invalidateSize(); }, 0);

  var markerIcon = L.divIcon({
    html: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32" viewBox="0 0 24 32" style="display:block;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.30))">' +
            '<circle cx="12" cy="12" r="11" fill="#F97316" stroke="#ffffff" stroke-width="2.5"/>' +
            '<polygon points="6,18 18,18 12,32" fill="#F97316"/>' +
          '</svg>',
    iconSize:    [24, 32],
    iconAnchor:  [12, 32],
    popupAnchor: [0, -34],
    className:   ''
  });

  var marker = L.marker([DEFAULT_LAT, DEFAULT_LNG], { draggable: true, icon: markerIcon }).addTo(map);

  function updateCoords(lat, lng) {
    var latEl = document.getElementById('id_latitude');
    var lngEl = document.getElementById('id_longitude');
    if (latEl) latEl.value = lat.toFixed(6);
    if (lngEl) lngEl.value = lng.toFixed(6);
    var display = document.getElementById('coords-display');
    if (display) {
      display.innerHTML =
        '<svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>' +
        lat.toFixed(5) + ', ' + lng.toFixed(5);
    }
  }
  updateCoords(DEFAULT_LAT, DEFAULT_LNG);

  map.on('click', function (e) {
    marker.setLatLng(e.latlng);
    updateCoords(e.latlng.lat, e.latlng.lng);
  });
  marker.on('dragend', function () {
    var pos = marker.getLatLng();
    updateCoords(pos.lat, pos.lng);
  });

  // ── Village field toggle ──────────────────────────────────────────────────
  var areaSelect = document.querySelector('[name="area"]');
  if (areaSelect) {
    areaSelect.addEventListener('change', function () {
      var vf = document.getElementById('village-field');
      if (vf) vf.classList.toggle('hidden', this.value !== 'village');
    });
  }

  // ── Category quick-select ─────────────────────────────────────────────────
  window.selectCategory = function (val) {
    var sel = document.querySelector('[name="category"]');
    if (sel) sel.value = val;
    document.querySelectorAll('.cat-btn').forEach(function (btn) {
      var isActive = btn.dataset.cat === val;
      btn.style.borderColor = isActive ? '#4F46E5' : '#E2E8F0';
      btn.style.background  = isActive ? 'linear-gradient(145deg,#EEF2FF 0%,#E0E7FF 100%)' : '#F8FAFC';
      btn.style.boxShadow   = isActive ? '0 6px 20px rgba(79,70,229,0.28)' : 'none';
      btn.style.transform   = isActive ? 'translateY(-3px) scale(1.04)' : 'translateY(0) scale(1)';
      var check = btn.querySelector('.cat-check');
      if (check) check.style.display = isActive ? 'flex' : 'none';
      var label = btn.querySelector('.cat-label');
      if (label) {
        label.style.color      = isActive ? '#3730A3' : '#334155';
        label.style.fontWeight = isActive ? '800'     : '700';
      }
    });
  };

  // ── Drop zone hover ───────────────────────────────────────────────────────
  var dz = document.getElementById('drop-zone');
  if (dz) {
    dz.addEventListener('dragover', function (e) {
      e.preventDefault();
      dz.style.borderColor = '#4F46E5';
      dz.style.background  = '#EEF2FF';
    });
    dz.addEventListener('dragleave', function () {
      dz.style.borderColor = '#E2E8F0';
      dz.style.background  = '#F8FAFC';
    });
    dz.addEventListener('drop', function () {
      dz.style.borderColor = '#E2E8F0';
      dz.style.background  = '#F8FAFC';
    });
  }

  // ── Multiple image preview ────────────────────────────────────────────────
  var extraInput  = document.getElementById('extra-images-input');
  var dropZone    = document.getElementById('drop-zone');
  var previewGrid = document.getElementById('preview-grid');
  var previewBox  = document.getElementById('image-preview-grid');
  var addMoreBtn  = document.getElementById('add-more-btn');
  var allFiles    = [];   // accumulated DataTransfer list

  function renderPreviews() {
    if (!previewGrid) return;
    previewGrid.innerHTML = '';
    allFiles.forEach(function (file, idx) {
      var reader = new FileReader();
      reader.onload = function (ev) {
        var cell = document.createElement('div');
        cell.style.cssText = 'position:relative';
        cell.innerHTML =
          '<img src="' + ev.target.result + '" style="width:100%;height:90px;object-fit:cover;border-radius:0.75rem;border:1px solid #E2E8F0">' +
          '<button type="button" data-idx="' + idx + '" style="position:absolute;top:4px;right:4px;background:rgba(0,0,0,0.55);border:none;border-radius:50%;width:20px;height:20px;cursor:pointer;color:#fff;font-size:12px;line-height:20px;text-align:center">×</button>' +
          '<p style="font-size:10px;color:#94A3B8;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + file.name + '</p>';
        cell.querySelector('button').addEventListener('click', function () {
          allFiles.splice(Number(this.dataset.idx), 1);
          syncInputFiles();
          renderPreviews();
          if (allFiles.length === 0) {
            previewBox.classList.add('hidden');
            dropZone.classList.remove('hidden');
          }
        });
        previewGrid.appendChild(cell);
      };
      reader.readAsDataURL(file);
    });
  }

  function syncInputFiles() {
    var dt = new DataTransfer();
    allFiles.forEach(function (f) { dt.items.add(f); });
    if (extraInput) extraInput.files = dt.files;
  }

  function handleFiles(fileList) {
    Array.from(fileList).forEach(function (f) { allFiles.push(f); });
    syncInputFiles();
    renderPreviews();
    if (allFiles.length > 0) {
      dropZone.classList.add('hidden');
      previewBox.classList.remove('hidden');
    }
  }

  if (extraInput) {
    extraInput.addEventListener('change', function () {
      handleFiles(this.files);
    });
  }

  if (addMoreBtn) {
    addMoreBtn.addEventListener('click', function () {
      // Create a fresh temporary input so user can pick additional files
      var tmp = document.createElement('input');
      tmp.type = 'file';
      tmp.accept = 'image/*';
      tmp.multiple = true;
      tmp.addEventListener('change', function () {
        handleFiles(this.files);
      });
      tmp.click();
    });
  }

  if (dropZone) {
    dropZone.addEventListener('dragover', function (e) {
      e.preventDefault();
      dropZone.style.borderColor = '#4F46E5';
      dropZone.style.background  = '#EEF2FF';
    });
    dropZone.addEventListener('dragleave', function () {
      dropZone.style.borderColor = '#E2E8F0';
      dropZone.style.background  = '#F8FAFC';
    });
    dropZone.addEventListener('drop', function (e) {
      e.preventDefault();
      dropZone.style.borderColor = '#E2E8F0';
      dropZone.style.background  = '#F8FAFC';
      handleFiles(e.dataTransfer.files);
    });
  }

  // ── Form submit loading state ─────────────────────────────────────────────
  var form      = document.getElementById('report-form');
  var submitBtn = document.getElementById('submit-btn');
  if (form && submitBtn) {
    form.addEventListener('submit', function () {
      submitBtn.disabled = true;
      var sendingLabel = LANG === 'hy' ? 'Ուղարկվում է...' : LANG === 'fr' ? 'Envoi...' : 'Sending...';
      submitBtn.innerHTML =
        '<svg class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">' +
          '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>' +
          '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>' +
        '</svg>' + sendingLabel;
    });
  }
})();
