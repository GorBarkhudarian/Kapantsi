/**
 * admin-dashboard.js — Kapantsi admin dashboard behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 */
(function () {
  'use strict';

  // ── Update-status modal ───────────────────────────────────────────────────
  window.openModalFromBtn = function (btn) {
    openModal(btn.dataset.issueId, btn.dataset.status, btn.dataset.notes);
  };

  function openModal(id, status, notes) {
    document.getElementById('modal-issue-id').value = id;
    document.getElementById('modal-status').value   = status;
    document.getElementById('modal-notes').value    = notes || '';
    var modal = document.getElementById('update-modal');
    modal.style.display        = 'flex';
    document.body.style.overflow = 'hidden';
  }

  window.closeModal = function () {
    document.getElementById('update-modal').style.display = 'none';
    document.body.style.overflow = '';
  };

  var updateModal = document.getElementById('update-modal');
  if (updateModal) {
    updateModal.addEventListener('click', function (e) {
      if (e.target === this) window.closeModal();
    });
  }

  // ── Delete modal ──────────────────────────────────────────────────────────
  window.openDeleteModal = function (btn) {
    var id    = btn.dataset.issueId;
    var title = btn.dataset.issueTitle;
    document.getElementById('delete-modal-title').textContent = '#' + id + ' — ' + title;
    document.getElementById('delete-form').action = '/admin-dashboard/delete/' + id + '/';
    var modal = document.getElementById('delete-modal');
    modal.style.display          = 'flex';
    document.body.style.overflow = 'hidden';
  };

  window.closeDeleteModal = function () {
    document.getElementById('delete-modal').style.display = 'none';
    document.body.style.overflow = '';
  };

  var deleteModal = document.getElementById('delete-modal');
  if (deleteModal) {
    deleteModal.addEventListener('click', function (e) {
      if (e.target === this) window.closeDeleteModal();
    });
  }

  // Global Escape handler
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      window.closeModal();
      window.closeDeleteModal();
    }
  });

  // ── Table search ──────────────────────────────────────────────────────────
  var searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      var q = this.value.toLowerCase();
      document.querySelectorAll('#issues-table tbody tr').forEach(function (row) {
        if (row.querySelector('td[colspan]')) return;
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
})();
