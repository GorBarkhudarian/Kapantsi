/**
 * login.js — Kapantsi login page behaviour
 * Reads window.KAPANTSI_LANG set inline by the Django template.
 */
(function () {
  'use strict';

  var L    = window.KAPANTSI_LANG || 'en';
  var lang = L === 'hy' ? 'hy' : L === 'fr' ? 'fr' : 'en';

  var placeholders = {
    id_username: { hy: 'Մուտքանուն',  fr: "Nom d'utilisateur", en: 'Username' },
    id_password: { hy: 'Գաղտնաբառ',  fr: 'Mot de passe',      en: 'Password' }
  };

  Object.keys(placeholders).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.placeholder = placeholders[id][lang];
  });
})();
