/**
 * detail-map.js — Kapantsi issue detail page Leaflet map
 * Reads data passed via json_script tags injected by the Django template.
 * Requires Leaflet (loaded before this script).
 */
(function () {
  'use strict';

  var latEl  = document.getElementById('map-lat');
  var lngEl  = document.getElementById('map-lng');
  if (!latEl || !lngEl) return;  // no coordinates — map container hidden

  var lat         = JSON.parse(latEl.textContent);
  var lng         = JSON.parse(lngEl.textContent);
  var title       = JSON.parse(document.getElementById('map-title').textContent);
  var statusLabel = JSON.parse(document.getElementById('map-status').textContent);
  var statusKey   = JSON.parse(document.getElementById('map-status-key').textContent);

  var map = L.map('detail-map', { zoomSnap: 1 }).setView([lat, lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  /* Force Leaflet to re-measure the container after layout is complete. */
  setTimeout(function () { map.invalidateSize(); }, 0);

  var statusColors = {
    pending:      '#EAB308',
    under_review: '#4F46E5',
    in_progress:  '#8B5CF6',
    completed:    '#22C55E',
    rejected:     '#EF4444'
  };
  var color = statusColors[statusKey] || '#94A3B8';

  var marker = L.circleMarker([lat, lng], {
    radius: 12, fillColor: color, color: '#fff', weight: 3, fillOpacity: 0.9
  }).addTo(map);

  /* Safely render title — avoid XSS via textContent */
  var safeDiv = document.createElement('div');
  safeDiv.textContent = title;
  marker.bindPopup(
    '<b style="font-size:13px">' + safeDiv.innerHTML + '</b>' +
    '<br><span style="font-size:11px;color:#94A3B8">' + statusLabel + '</span>'
  );
})();
