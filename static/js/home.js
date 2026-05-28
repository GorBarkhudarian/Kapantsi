/**
 * home.js — Kapantsi home page dynamic behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 */
(function () {
  'use strict';

  var LANG = window.KAPANTSI_LANG || 'en';

  // ── Load platform stats from API ──────────────────────────────────────────
  fetch('/api/dashboard/stats/')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (!data) return;
      var byStatus = data.by_status || {};
      var active = (byStatus.pending || 0) + (byStatus.under_review || 0) + (byStatus.in_progress || 0);
      var el;
      el = document.getElementById('stat-total');     if (el) el.textContent = data.total_issues || 0;
      el = document.getElementById('stat-pending');   if (el) el.textContent = active;
      el = document.getElementById('stat-completed'); if (el) el.textContent = byStatus.completed || 0;
      el = document.getElementById('stat-votes');     if (el) el.textContent = data.total_votes || 0;
    })
    .catch(function () {});

  // ── Per-category design tokens ────────────────────────────────────────────
  var CAT_BORDER = {
    road: '#4F46E5', water: '#1D4ED8', electricity: '#D97706',
    waste: '#16A34A', safety: '#DC2626', other: '#64748B'
  };
  var CAT_BG_GRAD = {
    road: 'linear-gradient(135deg,#EEF2FF,#E0E7FF)',
    water: 'linear-gradient(135deg,#DBEAFE,#BFDBFE)',
    electricity: 'linear-gradient(135deg,#FEF3C7,#FDE68A)',
    waste: 'linear-gradient(135deg,#DCFCE7,#BBF7D0)',
    safety: 'linear-gradient(135deg,#FEE2E2,#FECACA)',
    other: 'linear-gradient(135deg,#F1F5F9,#E2E8F0)'
  };
  var CAT_BADGE_BG = {
    road: '#EEF2FF', water: '#DBEAFE', electricity: '#FEF3C7',
    waste: '#DCFCE7', safety: '#FEE2E2', other: '#F1F5F9'
  };
  var CAT_BADGE_COLOR = {
    road: '#4338CA', water: '#1E40AF', electricity: '#92400E',
    waste: '#14532D', safety: '#991B1B', other: '#334155'
  };
  var CAT_BADGE_BORDER = {
    road: '#E0E7FF', water: '#BFDBFE', electricity: '#FDE68A',
    waste: '#BBF7D0', safety: '#FECACA', other: '#E2E8F0'
  };
  var CAT_ICON_PATH = {
    road:        'd="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"',
    water:       'd="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z"',
    electricity: 'd="M13 10V3L4 14h7v7l9-11h-7z"',
    waste:       'd="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"',
    safety:      'd="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"',
    other:       'd="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"'
  };

  var STATUS_CSS = {
    pending: 'status-pending', under_review: 'status-under_review',
    in_progress: 'status-in_progress', completed: 'status-completed', rejected: 'status-rejected'
  };
  var STATUS_LABELS_HY = {
    pending: 'Սպասվում է', under_review: 'Ուսումնասիրվում է',
    in_progress: 'Ընթացքի մեջ է', completed: 'Ավարտվել է', rejected: 'Մերժվել է'
  };
  var STATUS_LABELS_EN = {
    pending: 'Pending', under_review: 'Under Review',
    in_progress: 'In Progress', completed: 'Completed', rejected: 'Rejected'
  };
  var STATUS_LABELS_FR = {
    pending: 'En attente', under_review: 'En révision',
    in_progress: 'En cours', completed: 'Terminé', rejected: 'Rejeté'
  };

  // ── Fetch recent issues ───────────────────────────────────────────────────
  fetch('/api/issues/?ordering=-created_at&page_size=6')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var items = data.results || data;
      var container = document.getElementById('recent-issues');
      if (!container) return;

      if (!items || items.length === 0) {
        var emptyMsg = LANG === 'hy'
          ? 'Դեռ խնդիրներ չկան։'
          : LANG === 'fr'
            ? "Aucun problème pour l'instant. Soyez le premier à signaler !"
            : 'No issues yet. Be the first to report!';
        container.innerHTML = '<div class="col-span-3 text-center py-16 text-[#94A3B8]"><div class="text-5xl mb-3">&#128269;</div><p>' + emptyMsg + '</p></div>';
        return;
      }

      var STATUS_LABELS = LANG === 'hy' ? STATUS_LABELS_HY : LANG === 'fr' ? STATUS_LABELS_FR : STATUS_LABELS_EN;

      container.innerHTML = items.slice(0, 6).map(function (issue) {
        var cat         = issue.category || 'other';
        var border      = CAT_BORDER[cat]       || '#64748B';
        var bgGrad      = CAT_BG_GRAD[cat]      || CAT_BG_GRAD.other;
        var badgeBg     = CAT_BADGE_BG[cat]     || '#F1F5F9';
        var badgeColor  = CAT_BADGE_COLOR[cat]  || '#334155';
        var badgeBorder = CAT_BADGE_BORDER[cat] || '#E2E8F0';
        var iconPath    = CAT_ICON_PATH[cat]    || CAT_ICON_PATH.other;
        var statusCss   = STATUS_CSS[issue.status]    || 'status-pending';
        var statusLabel = STATUS_LABELS[issue.status] || issue.status;
        var title       = LANG === 'hy'
          ? (issue.title_hy || '')
          : LANG === 'fr'
            ? (issue.title_fr || issue.title_en || issue.title_hy || '')
            : (issue.title_en || issue.title_hy || '');
        var locale  = LANG === 'hy' ? 'hy-AM' : LANG === 'fr' ? 'fr-FR' : 'en-GB';
        var dateStr = new Date(issue.created_at).toLocaleDateString(locale);

        var imgSrc = issue.first_image || issue.image;
        var imgHtml = imgSrc
          ? '<div class="h-44 overflow-hidden relative flex-shrink-0">' +
              '<img src="' + imgSrc + '" alt="" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">' +
              '<div class="absolute inset-0" style="background:linear-gradient(to top,rgba(15,13,46,0.5) 0%,transparent 55%)"></div>' +
            '</div>'
          : '<div class="h-44 flex items-center justify-center relative overflow-hidden flex-shrink-0" style="background:' + bgGrad + '">' +
              '<div class="absolute inset-0 opacity-[0.07]" style="background-image:radial-gradient(circle,' + border + ' 1px,transparent 1px);background-size:20px 20px"></div>' +
              '<svg class="w-14 h-14 relative z-10 transition-transform duration-300 group-hover:scale-110" style="color:' + border + ';opacity:0.3" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" ' + iconPath + '/>' +
              '</svg>' +
            '</div>';

        var addr = issue.location_address || '';
        var locationHtml = addr
          ? '<p class="flex items-center gap-1.5 text-xs text-[#94A3B8] mb-4 truncate">' +
              '<svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>' +
              '<span class="truncate">' + addr.substring(0, 38) + (addr.length > 38 ? '…' : '') + '</span>' +
            '</p>'
          : '<div class="mb-4"></div>';

        return '<a href="/issues/' + issue.id + '/"' +
          ' class="bg-white rounded-2xl overflow-hidden flex flex-col group"' +
          ' style="border:1px solid #E2E8F0;border-top:3px solid ' + border + ';box-shadow:0 2px 8px rgba(0,0,0,0.05),0 1px 2px rgba(0,0,0,0.04);transition:box-shadow 0.2s,transform 0.2s"' +
          ' onmouseover="this.style.boxShadow=\'0 12px 32px rgba(15,13,46,0.12),0 2px 8px rgba(15,13,46,0.06)\';this.style.transform=\'translateY(-3px)\'"' +
          ' onmouseout="this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.05),0 1px 2px rgba(0,0,0,0.04)\';this.style.transform=\'translateY(0)\'">' +
          imgHtml +
          '<div class="flex flex-col flex-1 p-5">' +
            '<div class="flex items-center justify-between gap-2 mb-3">' +
              '<span class="text-xs font-semibold px-2.5 py-1 rounded-full" style="background:' + badgeBg + ';color:' + badgeColor + ';border:1px solid ' + badgeBorder + '">' + (issue.category_display || cat) + '</span>' +
              '<span class="' + statusCss + ' text-xs">' + statusLabel + '</span>' +
            '</div>' +
            '<h3 class="text-[#0F172A] font-bold text-[15px] leading-snug line-clamp-2 mb-2 flex-1" style="transition:color 0.15s" onmouseover="this.style.color=\'#4F46E5\'" onmouseout="this.style.color=\'#0F172A\'">' + title + '</h3>' +
            locationHtml +
            '<div class="flex items-center justify-between pt-3 mt-auto" style="border-top:1px solid #F1F5F9">' +
              '<div class="flex items-center gap-3">' +
                '<span class="flex items-center gap-1 text-xs font-bold" style="color:' + border + '">' +
                  '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/></svg>' +
                  (issue.upvote_count || 0) +
                '</span>' +
                '<span class="flex items-center gap-1 text-xs text-[#94A3B8]">' +
                  '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>' +
                  (issue.comments_count || 0) +
                '</span>' +
              '</div>' +
              '<span class="text-xs text-[#94A3B8]">' + dateStr + '</span>' +
            '</div>' +
          '</div>' +
        '</a>';
      }).join('');
    })
    .catch(function () {
      var container = document.getElementById('recent-issues');
      if (!container) return;
      var errMsg = LANG === 'hy'
        ? 'Չհաջողվեց բեռնել։'
        : LANG === 'fr'
          ? 'Impossible de charger les problèmes.'
          : 'Could not load issues.';
      container.innerHTML = '<div class="col-span-3 text-center py-12 text-[#94A3B8]">' + errMsg + '</div>';
    });
})();
