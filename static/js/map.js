/**
 * map.js — Kapantsi issues map page behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 * Requires MapLibre GL JS (loaded before this script).
 */
(function () {
  'use strict';

  var LANG = window.KAPANTSI_LANG || 'en';

  /* ── Map init (MapLibre GL JS + OpenFreeMap vector tiles) ── */
  var map = new maplibregl.Map({
    container: 'kapan-map',
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [46.4058, 39.2067],
    zoom: 13,
    attributionControl: false
  });

  /* ── Controls ── */
  map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
  map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');

  /* ── Status & category colours ── */
  var STATUS_COLORS = {
    pending:      '#EAB308',
    under_review: '#4F46E5',
    in_progress:  '#8B5CF6',
    completed:    '#22C55E',
    rejected:     '#EF4444'
  };
  var CAT_COLORS = {
    road:        '#4F46E5',
    water:       '#0EA5E9',
    electricity: '#F59E0B',
    waste:       '#22C55E',
    safety:      '#EF4444',
    other:       '#64748B'
  };

  /* ── Localized status labels ── */
  var STATUS_LABELS = {
    hy: { pending: 'Սպասվում է', under_review: 'Քննության փուլ', in_progress: 'Ընթացքի մեջ', completed: 'Ավարտված', rejected: 'Մերժված' },
    fr: { pending: 'En attente', under_review: "En cours d'examen", in_progress: 'En cours', completed: 'Terminé', rejected: 'Rejeté' },
    en: { pending: 'Pending', under_review: 'Under Review', in_progress: 'In Progress', completed: 'Completed', rejected: 'Rejected' }
  };
  var STATUS_LABEL_MAP = STATUS_LABELS[LANG] || STATUS_LABELS.en;

  /* ── Marker + popup registry ── */
  var activeMarkers = [];
  var activePopup   = null;

  function clearMarkers() {
    activeMarkers.forEach(function (m) { m.remove(); });
    activeMarkers = [];
    if (activePopup) { activePopup.remove(); activePopup = null; }
  }

  /* ── Sanitise text for innerHTML ── */
  function esc(str) {
    var d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
  }

  /* ── Render ── */
  function renderMarkers(issues) {
    clearMarkers();
    var pinned = issues.filter(function (i) { return i.latitude && i.longitude; });

    /* Count header */
    var countEl = document.getElementById('issue-count-header');
    if (countEl) {
      countEl.textContent = LANG === 'hy'
        ? pinned.length + ' Հաղորդում քարտեզի վրա'
        : LANG === 'fr'
          ? pinned.length + ' problèmes sur la carte'
          : pinned.length + ' issues on map';
    }

    /* Sidebar top-10 */
    var top = issues.slice().sort(function (a, b) {
      return (b.upvote_count || 0) - (a.upvote_count || 0);
    }).slice(0, 10);

    var sidebarEl = document.getElementById('sidebar-issues');
    if (sidebarEl) {
      sidebarEl.innerHTML = top.map(function (issue) {
        var title = LANG === 'hy'
          ? (issue.title_hy || '')
          : LANG === 'fr'
            ? (issue.title_fr || issue.title_en || issue.title_hy || '')
            : (issue.title_en || issue.title_hy || '');
        var color = STATUS_COLORS[issue.status] || '#9CA3AF';
        return '<a href="/issues/' + issue.id + '/" class="sb-issue-row">' +
          '<div class="sb-issue-vote">' +
            '<span class="sb-issue-vote-num">' + (issue.upvote_count || 0) + '</span>' +
            '<span class="sb-issue-vote-lbl">' + (LANG === 'hy' ? 'ձայն' : 'votes') + '</span>' +
          '</div>' +
          '<div style="flex:1;min-width:0;">' +
            '<p style="font-size:12px;font-weight:600;color:#1E293B;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px;">' + esc(title) + '</p>' +
            '<span style="display:inline-block;background:' + color + '22;color:' + color + ';border:1px solid ' + color + '55;padding:1px 7px;border-radius:999px;font-size:10px;font-weight:700;">' + esc(STATUS_LABEL_MAP[issue.status] || issue.status_display || issue.status) + '</span>' +
          '</div>' +
          '<svg style="width:14px;height:14px;color:#CBD5E1;flex-shrink:0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>' +
          '</svg>' +
        '</a>';
      }).join('');
    }

    /* Issue markers */
    pinned.forEach(function (issue) {
      var sColor = STATUS_COLORS[issue.status] || '#9CA3AF';
      var cColor = CAT_COLORS[issue.category]  || '#64748B';
      var votes  = issue.upvote_count || 0;
      var size   = Math.round(18 + Math.min(votes * 1.2, 22));
      var title  = LANG === 'hy'
        ? (issue.title_hy || '')
        : LANG === 'fr'
          ? (issue.title_fr || issue.title_en || issue.title_hy || '')
          : (issue.title_en || issue.title_hy || '');
      var viewLbl = LANG === 'hy' ? 'Տեսնել' : LANG === 'fr' ? 'Voir' : 'View';

      /* Wrapper — this is what MapLibre anchors; overflow:visible so badge doesn't shift layout */
      var el = document.createElement('div');
      el.style.cssText =
        'width:' + size + 'px;height:' + size + 'px;' +
        'position:relative;overflow:visible;' +
        'cursor:pointer;';

      /* Inner circle — the visible dot */
      var dot = document.createElement('div');
      dot.className = 'issue-marker';
      dot.style.cssText =
        'width:100%;height:100%;background:' + sColor + ';' +
        'border-radius:50%;border:2.5px solid #fff;box-sizing:border-box;' +
        'box-shadow:0 2px 10px rgba(0,0,0,0.28);';
      el.appendChild(dot);

      /* Vote badge */
      if (votes > 0) {
        var badge = document.createElement('div');
        badge.style.cssText =
          'position:absolute;top:-6px;right:-6px;' +
          'background:#0F172A;color:#fff;' +
          'font-size:9px;font-weight:800;' +
          'width:16px;height:16px;' +
          'border-radius:50%;' +
          'display:flex;align-items:center;justify-content:center;' +
          'border:2px solid #fff;line-height:1;' +
          "font-family:'Inter',sans-serif;pointer-events:none;";
        badge.textContent = votes > 99 ? '99+' : votes;
        el.appendChild(badge);
      }

      /* Popup content */
      var locationHtml = issue.location_address
        ? '<div style="display:flex;align-items:flex-start;gap:5px;margin-bottom:10px;">' +
            '<svg width="12" height="12" style="color:#94A3B8;flex-shrink:0;margin-top:2px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
              '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>' +
              '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>' +
            '</svg>' +
            '<span style="font-size:11px;color:#64748B;line-height:1.4;">' + esc(issue.location_address) + '</span>' +
          '</div>'
        : '';

      var popupNode = document.createElement('div');
      popupNode.style.cssText = 'min-width:220px;font-family:"Inter",sans-serif;overflow:hidden;border-radius:14px;';
      popupNode.innerHTML =
        '<div style="background:' + cColor + ';padding:10px 14px 8px;position:relative;">' +
          '<button onclick="this.closest(\'.maplibregl-popup\').querySelector(\'.maplibregl-popup-close-button\')?.click()"' +
                  ' style="position:absolute;top:6px;right:8px;background:none;border:none;color:rgba(255,255,255,0.7);font-size:18px;cursor:pointer;line-height:1;padding:0;">×</button>' +
          '<span style="display:inline-block;background:rgba(255,255,255,0.22);color:#fff;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:700;letter-spacing:.04em;margin-bottom:6px;">' +
            esc(issue.category_display || issue.category) +
          '</span>' +
          '<p style="font-size:13px;font-weight:700;color:#fff;line-height:1.35;margin:0;padding-right:20px;">' + esc(title) + '</p>' +
        '</div>' +
        '<div style="padding:10px 14px 12px;background:#fff;">' +
          '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">' +
            '<span style="background:' + sColor + '22;color:' + sColor + ';border:1px solid ' + sColor + '66;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:700;">' +
              esc(STATUS_LABEL_MAP[issue.status] || issue.status_display || issue.status) +
            '</span>' +
            '<span style="display:flex;align-items:center;gap:3px;font-size:11px;font-weight:700;color:#4338CA;">' +
              '<svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"/></svg>' +
              votes +
            '</span>' +
          '</div>' +
          locationHtml +
          '<a href="/issues/' + issue.id + '/"' +
             ' style="display:flex;align-items:center;justify-content:center;gap:5px;' +
                     'background:linear-gradient(135deg,#4F46E5,#3730A3);' +
                     'color:#fff;padding:7px 14px;border-radius:8px;' +
                     'font-size:12px;font-weight:700;text-decoration:none;">' +
            esc(viewLbl) +
            '<svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>' +
          '</a>' +
        '</div>';

      var popup = new maplibregl.Popup({
        offset: [0, -(size / 2 + 4)],
        closeButton: true,
        closeOnClick: false,
        maxWidth: '260px'
      }).setDOMContent(popupNode);

      var marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([parseFloat(issue.longitude), parseFloat(issue.latitude)])
        .addTo(map);

      el.addEventListener('click', function (e) {
        e.stopPropagation();
        if (activePopup) { activePopup.remove(); activePopup = null; }
        popup.setLngLat([parseFloat(issue.longitude), parseFloat(issue.latitude)]).addTo(map);
        activePopup = popup;
      });

      activeMarkers.push(marker);
    });
  }

  /* ── Load issues from API ── */
  function loadIssues(params) {
    var loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'flex';
    var url = '/api/issues/?page_size=500';
    if (params) {
      if (params.category) url += '&category=' + encodeURIComponent(params.category);
      if (params.status)   url += '&status='   + encodeURIComponent(params.status);
      if (params.area)     url += '&area='     + encodeURIComponent(params.area);
    }
    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) { renderMarkers(data.results || data || []); })
      .catch(function () {
        var countEl = document.getElementById('issue-count-header');
        if (countEl) countEl.textContent = LANG === 'hy' ? 'Չhajoghtsvets bérnel' : 'Could not load issues';
      })
      .finally(function () {
        if (loadingEl) loadingEl.style.display = 'none';
      });
  }

  /* Load once map style is ready */
  map.on('load', function () { loadIssues(); });

  var applyBtn = document.getElementById('apply-filters');
  if (applyBtn) {
    applyBtn.addEventListener('click', function () {
      loadIssues({
        category: document.getElementById('filter-category').value,
        status:   document.getElementById('filter-status').value,
        area:     document.getElementById('filter-area').value
      });
    });
  }

  var resetBtn = document.getElementById('reset-filters');
  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      ['filter-category', 'filter-status', 'filter-area'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.value = '';
      });
      loadIssues();
    });
  }

  /* ── Village reference labels ── */
  var villages = [
    { name: 'Geghanush', lat: 39.2400, lon: 46.3600 },
    { name: 'Davit Bek', lat: 39.2700, lon: 46.3200 },
    { name: 'Tatev',     lat: 39.3800, lon: 46.2400 },
    { name: 'Shinuhayr', lat: 39.1800, lon: 46.2800 }
  ];

  map.on('load', function () {
    villages.forEach(function (v) {
      var el = document.createElement('div');
      el.className = 'village-label';
      el.textContent = v.name;
      new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat([v.lon, v.lat])
        .addTo(map);
    });
  });
})();
