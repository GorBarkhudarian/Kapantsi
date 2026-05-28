/**
 * register.js — Kapantsi registration page behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 */
(function () {
  'use strict';

  var L    = window.KAPANTSI_LANG || 'en';
  var lang = L === 'hy' ? 'hy' : L === 'fr' ? 'fr' : 'en';

  // ── 1. Static field placeholder localisation ─────────────────────────────
  var placeholders = {
    id_first_name: { hy: 'Անուն',              fr: 'Prénom',                  en: 'First name' },
    id_last_name:  { hy: 'Ազգանուն',           fr: 'Nom de famille',          en: 'Last name' },
    id_username:   { hy: 'Մուտքանուն',         fr: "Nom d'utilisateur",       en: 'Username' },
    id_email:      { hy: 'օգտ@example.com',    fr: 'email@example.com',       en: 'email@example.com' },
    id_phone:      { hy: '+374-XX-XXXXXX',     fr: '+374-XX-XXXXXX',          en: '+374-XX-XXXXXX' },
    id_address:    { hy: 'Կապան, Սյունիք',    fr: 'Kapan, Syunik',           en: 'Kapan, Syunik' },
    id_password:   { hy: 'Նվազ. 6 նիշ',       fr: 'Min. 6 caractères',       en: 'Min 6 characters' },
    id_password2:  { hy: 'Կրկնել գաղտնաբառը', fr: 'Répétez le mot de passe', en: 'Repeat password' }
  };
  Object.keys(placeholders).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.placeholder = placeholders[id][lang];
  });

  // ── 2. Document-type data ─────────────────────────────────────────────────
  var HINTS = {
    national_id_card: {
      hy: 'Ֆորմատ՝ 9 թիվ (օր. 123456789)',
      fr: 'Format : 9 chiffres (ex. 123456789)',
      en: 'Format: 9 digits (e.g. 123456789)'
    },
    passport: {
      hy: 'Ֆորմատ՝ 2 մեծ լատ. տառ + 7 թիվ (օր. AB1234567)',
      fr: 'Format : 2 lettres maj. + 7 chiffres (ex. AB1234567)',
      en: 'Format: 2 uppercase letters + 7 digits (e.g. AB1234567)'
    }
  };
  var DOC_PLACEHOLDERS = {
    national_id_card: { hy: '123456789', fr: '123456789', en: '123456789' },
    passport:         { hy: 'AB1234567', fr: 'AB1234567', en: 'AB1234567' }
  };
  var BADGE_LABELS = {
    national_id_card: { hy: 'Նույնականացման քարտ', fr: "Carte d'identité", en: 'National ID Card' },
    passport:         { hy: 'Անձնագիր',             fr: 'Passeport',        en: 'Physical Passport' }
  };
  var PATTERNS = {
    national_id_card: /^\d{9}$/,
    passport:         /^[A-Z]{2}\d{7}$/
  };

  // DOM refs
  var docTypeInput    = document.getElementById('id_doc_type');
  var nationalIdInput = document.getElementById('id_national_id');
  var panel           = document.getElementById('doc-type-panel');
  var hintBar         = document.getElementById('doc-format-hint');
  var hintText        = document.getElementById('doc-format-hint-text');
  var badge           = document.getElementById('doc-type-badge');
  var validIcon       = document.getElementById('doc-valid-icon');
  var invalidIcon     = document.getElementById('doc-invalid-icon');
  var btnCard         = document.getElementById('btn-national-id-card');
  var btnPassport     = document.getElementById('btn-passport');

  var BTN_BASE     = 'display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.75rem;border-radius:0.5rem;font-size:0.75rem;font-weight:600;transition:all 0.15s;width:100%;cursor:pointer';
  var ACTIVE_BTN   = BTN_BASE + ';border:2px solid #4F46E5;background:#EEF2FF;color:#3730A3';
  var INACTIVE_BTN = BTN_BASE + ';border:2px solid #E5E7EB;background:#F9FAFB;color:#6B7280';

  // ── 3. Panel open / close ─────────────────────────────────────────────────
  function openPanel() {
    if (!panel) return;
    panel.style.display = 'block';
    requestAnimationFrame(function () {
      panel.style.maxHeight = '200px';
      panel.style.opacity   = '1';
    });
  }
  function closePanel() {
    if (!panel) return;
    panel.style.maxHeight = '0';
    panel.style.opacity   = '0';
    setTimeout(function () {
      if (panel.style.opacity === '0') panel.style.display = 'none';
    }, 230);
  }

  var blurTimer = null;
  function scheduleClose() { blurTimer = setTimeout(closePanel, 160); }
  function cancelClose()   { if (blurTimer) { clearTimeout(blurTimer); blurTimer = null; } }

  if (nationalIdInput) {
    nationalIdInput.addEventListener('focus', function () { cancelClose(); openPanel(); });
    nationalIdInput.addEventListener('blur',  scheduleClose);
  }
  if (panel) {
    panel.addEventListener('focusin',   cancelClose);
    panel.addEventListener('focusout',  scheduleClose);
    panel.addEventListener('mousedown', cancelClose);
  }

  // ── 4. Set document type ──────────────────────────────────────────────────
  function kapantsiSetDocType(type) {
    if (!docTypeInput) return;
    docTypeInput.value = type;

    if (btnCard)     btnCard.setAttribute('style',     type === 'national_id_card' ? ACTIVE_BTN : INACTIVE_BTN);
    if (btnPassport) btnPassport.setAttribute('style', type === 'passport'         ? ACTIVE_BTN : INACTIVE_BTN);

    if (hintBar && hintText) {
      hintText.textContent = HINTS[type][lang];
      hintBar.classList.remove('hidden');
      hintBar.style.cssText = (type === 'passport')
        ? 'border-radius:0.5rem;padding:0.375rem 0.625rem;font-size:0.6875rem;font-weight:500;display:flex;align-items:center;gap:0.375rem;background:#FEF9C3;color:#854D0E;border:1px solid #FDE68A'
        : 'border-radius:0.5rem;padding:0.375rem 0.625rem;font-size:0.6875rem;font-weight:500;display:flex;align-items:center;gap:0.375rem;background:#EEF2FF;color:#3730A3;border:1px solid #C7D2FE';
    }

    if (badge) {
      badge.textContent = BADGE_LABELS[type][lang];
      badge.classList.remove('hidden');
      badge.style.cssText = (type === 'passport')
        ? 'font-size:0.6875rem;font-weight:600;padding:0.125rem 0.5rem;border-radius:9999px;background:#FEF9C3;color:#854D0E;border:1px solid #FDE68A'
        : 'font-size:0.6875rem;font-weight:600;padding:0.125rem 0.5rem;border-radius:9999px;background:#EEF2FF;color:#4338CA;border:1px solid #C7D2FE';
    }

    if (nationalIdInput) {
      nationalIdInput.placeholder         = DOC_PLACEHOLDERS[type][lang];
      nationalIdInput.value               = '';
      nationalIdInput.style.textTransform = (type === 'passport') ? 'uppercase' : 'none';
      nationalIdInput.style.borderColor   = '';
      nationalIdInput.focus();
    }
    if (validIcon)   validIcon.classList.add('hidden');
    if (invalidIcon) invalidIcon.classList.add('hidden');
  }

  window.kapantsiSetDocType = kapantsiSetDocType;

  // ── 5. Live validation while typing ──────────────────────────────────────
  if (nationalIdInput) {
    nationalIdInput.addEventListener('input', function () {
      var type = (docTypeInput && docTypeInput.value) || 'national_id_card';
      var val  = nationalIdInput.value;

      if (type === 'passport') {
        var pos = nationalIdInput.selectionStart;
        nationalIdInput.value = val.toUpperCase();
        try { nationalIdInput.setSelectionRange(pos, pos); } catch (e) {}
        val = nationalIdInput.value;
      }

      var ok = PATTERNS[type] && PATTERNS[type].test(val);
      if (val.length === 0) {
        if (validIcon)   validIcon.classList.add('hidden');
        if (invalidIcon) invalidIcon.classList.add('hidden');
        nationalIdInput.style.borderColor = '';
      } else if (ok) {
        if (validIcon)   validIcon.classList.remove('hidden');
        if (invalidIcon) invalidIcon.classList.add('hidden');
        nationalIdInput.style.borderColor = '#22C55E';
      } else {
        if (invalidIcon) invalidIcon.classList.remove('hidden');
        if (validIcon)   validIcon.classList.add('hidden');
        nationalIdInput.style.borderColor = '#F87171';
      }
    });
  }

  // ── 6. Phone input mask (+374-XX-XXXXXX) ─────────────────────────────────
  var phoneInput   = document.getElementById('id_phone');
  var phoneValid   = document.getElementById('phone-valid-icon');
  var phoneInvalid = document.getElementById('phone-invalid-icon');
  var PHONE_PREFIX  = '+374-';
  var PHONE_PATTERN = /^\+374-\d{2}-\d{6}$/;

  function applyPhoneMask(raw) {
    var digits = raw.replace(/\D/g, '');
    if (digits.startsWith('374')) digits = digits.slice(3);
    var part1  = digits.slice(0, 2);
    var part2  = digits.slice(2, 8);
    var masked = PHONE_PREFIX + part1;
    if (part2.length > 0) masked += '-' + part2;
    return masked;
  }

  if (phoneInput) {
    phoneInput.addEventListener('focus', function () {
      if (!phoneInput.value.startsWith(PHONE_PREFIX)) phoneInput.value = PHONE_PREFIX;
    });

    phoneInput.addEventListener('input', function () {
      var caretPos = phoneInput.selectionStart;
      var raw = phoneInput.value;

      if (!raw.startsWith(PHONE_PREFIX)) {
        var digits = raw.replace(/\D/g, '');
        if (digits.startsWith('374')) digits = digits.slice(3);
        phoneInput.value = applyPhoneMask(digits);
      } else {
        var afterPrefix = raw.slice(PHONE_PREFIX.length);
        phoneInput.value = applyPhoneMask(afterPrefix);
      }

      var newLen = phoneInput.value.length;
      var newPos = Math.min(caretPos, newLen);
      try { phoneInput.setSelectionRange(newPos, newPos); } catch (e) {}

      var val = phoneInput.value;
      if (val === PHONE_PREFIX || val.length === 0) {
        phoneValid.classList.add('hidden');
        phoneInvalid.classList.add('hidden');
        phoneInput.style.borderColor = '';
      } else if (PHONE_PATTERN.test(val)) {
        phoneValid.classList.remove('hidden');
        phoneInvalid.classList.add('hidden');
        phoneInput.style.borderColor = '#22C55E';
      } else {
        phoneInvalid.classList.remove('hidden');
        phoneValid.classList.add('hidden');
        phoneInput.style.borderColor = '#F87171';
      }
    });

    phoneInput.addEventListener('blur', function () {
      if (phoneInput.value === PHONE_PREFIX) {
        phoneInput.value = '';
        phoneInput.style.borderColor = '';
        phoneValid.classList.add('hidden');
        phoneInvalid.classList.add('hidden');
      }
    });
  }

  // ── 7. Silent initialisation ──────────────────────────────────────────────
  var initial = (docTypeInput && docTypeInput.value) || 'national_id_card';
  if (btnCard)     btnCard.setAttribute('style',     initial === 'national_id_card' ? ACTIVE_BTN : INACTIVE_BTN);
  if (btnPassport) btnPassport.setAttribute('style', initial === 'passport'         ? ACTIVE_BTN : INACTIVE_BTN);
  if (nationalIdInput) {
    nationalIdInput.placeholder         = DOC_PLACEHOLDERS[initial][lang];
    nationalIdInput.style.textTransform = (initial === 'passport') ? 'uppercase' : 'none';
  }
})();
