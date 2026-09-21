/* ==========================================================================
   matrix.js — fond animé « pluie de caractères ».
   Contraintes tenues : aucune dépendance, aucun impact sur la lisibilité
   (opacité globale gérée en CSS), arrêt automatique si l'onglet est masqué,
   et désactivation complète si l'utilisateur préfère réduire les animations.
   ========================================================================== */
(function () {
  'use strict';

  var canvas = document.getElementById('matrix');
  if (!canvas) { return; }

  var mouvementReduit = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (mouvementReduit) { canvas.style.display = 'none'; return; }

  var ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) { canvas.style.display = 'none'; return; }

  // Katakana, chiffres et quelques lettres latines : le rendu classique.
  var CARACTERES = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワンｦｧｨ0123456789ABCDEFGHJKLMNPQRSTUVWXYZ<>=/\\|*+';
  var TAILLE = 15;
  var VITESSE_MS = 55;                 // une étape toutes les 55 ms : ~18 i/s
  var colonnes, gouttes, largeur, hauteur, dpr;

  function dimensionner() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);   // plafonné : coût GPU
    largeur = canvas.clientWidth;
    hauteur = canvas.clientHeight;
    canvas.width = Math.floor(largeur * dpr);
    canvas.height = Math.floor(hauteur * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var nb = Math.max(1, Math.floor(largeur / TAILLE));
    if (!colonnes || nb !== colonnes.length) {
      gouttes = new Array(nb);
      for (var i = 0; i < nb; i++) {
        // Départ échelonné : évite que toutes les colonnes tombent ensemble.
        gouttes[i] = Math.random() * -60;
      }
    }
    colonnes = nb;
  }

  function dessiner() {
    // Voile de fond semi-transparent : crée la traînée derrière les caractères.
    // Plus le canal alpha est faible, plus la traînée est longue — donc plus le
    // fond est visible. 0.055 donne une traînée franche sans empâter l'écran.
    ctx.fillStyle = 'rgba(5, 8, 7, 0.055)';
    ctx.fillRect(0, 0, largeur, hauteur);

    ctx.font = TAILLE + 'px "JetBrains Mono", monospace';
    ctx.textBaseline = 'top';

    for (var i = 0; i < colonnes; i++) {
      var x = i * TAILLE;
      var y = gouttes[i] * TAILLE;
      if (y > hauteur + TAILLE) {
        gouttes[i] = Math.random() * -20;
        y = gouttes[i] * TAILLE;
      }
      var caractere = CARACTERES.charAt(
        Math.floor(Math.random() * CARACTERES.length));

      // Tête de colonne en blanc verdâtre, traînée en vert.
      if (Math.random() > 0.97) {
        ctx.fillStyle = 'rgba(215, 255, 235, 0.95)';
      } else {
        ctx.fillStyle = 'rgba(52, 211, 153, 0.7)';
      }
      ctx.fillText(caractere, x, y);
      gouttes[i] += 1;
    }
  }

  var minuteur = null;
  var enPause = false;

  function demarrer() {
    if (minuteur !== null || enPause) { return; }
    minuteur = window.setInterval(dessiner, VITESSE_MS);
  }
  function arreter() {
    if (minuteur !== null) { window.clearInterval(minuteur); minuteur = null; }
  }

  // Arrêt quand l'onglet passe en arrière-plan : économise le processeur.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { arreter(); } else { demarrer(); }
  });

  var attente;
  window.addEventListener('resize', function () {
    window.clearTimeout(attente);
    attente = window.setTimeout(function () {
      dimensionner();
      ctx.clearRect(0, 0, largeur, hauteur);
    }, 180);
  });

  // Exposé pour la bascule « Fond animé ».
  window.Matrice = {
    suspendre: function () { enPause = true; arreter(); },
    reprendre: function () { enPause = false; demarrer(); }
  };

  dimensionner();
  // Premier dessin immédiat, puis rythme normal.
  ctx.fillStyle = 'rgba(5, 8, 7, 1)';
  ctx.fillRect(0, 0, largeur, hauteur);
  demarrer();
})();
