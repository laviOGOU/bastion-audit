/* ==========================================================================
   site.js — améliorations progressives de l'interface.
   Le site reste entièrement fonctionnel sans JavaScript.
   ========================================================================== */
(function () {
  'use strict';

  /* --- Navigation mobile ------------------------------------------------- */
  var boutonMenu = document.getElementById('bouton-menu');
  var navigation = document.getElementById('navigation');
  if (boutonMenu && navigation) {
    boutonMenu.addEventListener('click', function () {
      var ouvert = navigation.classList.toggle('ouvert');
      boutonMenu.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
    });
    // Referme le menu après un clic sur un lien (navigation d'une seule page).
    navigation.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        navigation.classList.remove('ouvert');
        boutonMenu.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* --- Bascule du fond animé, mémorisée ---------------------------------- */
  var bascule = document.getElementById('bascule-fond');
  var CLE = 'bastion.fond';
  var actif = true;
  try {
    actif = window.localStorage.getItem(CLE) !== 'off';
  } catch (e) { /* stockage indisponible : on garde la valeur par défaut */ }

  function appliquer(actifMaintenant) {
    document.body.classList.toggle('sans-fond', !actifMaintenant);
    if (bascule) {
      bascule.setAttribute('aria-pressed', actifMaintenant ? 'true' : 'false');
    }
    if (window.Matrice) {
      if (actifMaintenant) { window.Matrice.reprendre(); }
      else { window.Matrice.suspendre(); }
    }
    try { window.localStorage.setItem(CLE, actifMaintenant ? 'on' : 'off'); }
    catch (e) { /* sans conséquence */ }
  }

  if (bascule) {
    bascule.addEventListener('click', function () { actif = !actif; appliquer(actif); });
  }
  appliquer(actif);

  /* --- Confirmation avant les actions irréversibles ---------------------- */
  document.querySelectorAll('[data-confirmer]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm(form.getAttribute('data-confirmer'))) { e.preventDefault(); }
    });
  });

  /* --- Compteurs animés (chiffres clés) ---------------------------------- */
  var cibles = document.querySelectorAll('[data-compteur]');
  if (cibles.length && 'IntersectionObserver' in window) {
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (!entree.isIntersecting) { return; }
        var el = entree.target;
        var valeur = parseFloat(el.getAttribute('data-compteur'));
        if (isNaN(valeur)) { observateur.unobserve(el); return; }
        var suffixe = el.getAttribute('data-suffixe') || '';
        var depart = performance.now();
        var duree = 900;
        (function animer(maintenant) {
          var t = Math.min(1, (maintenant - depart) / duree);
          var progressif = 1 - Math.pow(1 - t, 3);       // sortie adoucie
          el.textContent = Math.round(valeur * progressif) + suffixe;
          if (t < 1) { requestAnimationFrame(animer); }
        })(depart);
        observateur.unobserve(el);
      });
    }, { threshold: 0.4 });
    cibles.forEach(function (el) { observateur.observe(el); });
  }
})();
