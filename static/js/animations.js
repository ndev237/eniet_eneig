/**
 * animations.js — Système d'animation du site public ENIET/ENIEG
 *
 * Deux briques :
 *  1. Révélations au scroll     → tout élément marqué [data-reveal] apparaît
 *                                  en douceur quand il entre dans le viewport
 *                                  (one-shot, plus jamais rejoué).
 *  2. Compteurs numériques      → tout élément marqué [data-count-to="…"]
 *                                  compte de 0 vers la cible au premier
 *                                  passage dans le viewport (ease-out cubique).
 *
 * Accessibilité : si l'utilisateur a réglé prefers-reduced-motion sur reduce,
 * on court-circuite tout — les éléments sont affichés dans leur état final
 * immédiatement, sans animation.
 *
 * Zéro dépendance, un seul IIFE, aucune pollution du scope global.
 */
(function() {
    'use strict';

    // ============================================================
    // PRÉFÉRENCE UTILISATEUR — motion réduite
    // ============================================================
    const REDUCE_MOTION = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ============================================================
    // BRIQUE 1 — RÉVÉLATIONS AU SCROLL
    // ============================================================
    /**
     * Active les éléments [data-reveal] au fur et à mesure qu'ils entrent
     * dans le viewport. Chaque élément n'est révélé qu'une seule fois.
     */
    function initReveals() {
        const targets = document.querySelectorAll('[data-reveal]');
        if (!targets.length) return;

        // Fallback : motion réduite OU pas d'IntersectionObserver (navigateur ancien)
        //  → on rend tout visible d'emblée pour ne pas cacher le contenu.
        if (REDUCE_MOTION || !('IntersectionObserver' in window)) {
            targets.forEach((el) => el.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                // One-shot : on arrête d'observer, l'élément reste visible pour toujours.
                observer.unobserve(entry.target);
            });
        }, {
            // Se déclenche quand l'élément est à ~12% dans le viewport,
            // avec une marge basse négative pour anticiper un peu.
            rootMargin: '0px 0px -8% 0px',
            threshold: 0.12,
        });

        targets.forEach(function(el) { observer.observe(el); });
    }

    // ============================================================
    // BRIQUE 2 — COMPTEURS NUMÉRIQUES
    // ============================================================
    /**
     * Anime les nombres marqués <span data-count-to="2015">.
     * Formats supportés :
     *   - "2015"     → entier simple
     *   - "07"       → conserve le zéro de tête (padStart)
     *   - "100%"     → conserve le suffixe (% + etc.)
     *   - "1 250"    → conserve les espaces (via reformatage)
     *
     * Durée par défaut : 1400ms, surchargeable via data-count-duration.
     */
    function initCounters() {
        const targets = document.querySelectorAll('[data-count-to]');
        if (!targets.length) return;

        if (REDUCE_MOTION || !('IntersectionObserver' in window)) {
            // Motion réduite → affiche directement la valeur finale, pas d'anim.
            targets.forEach(function(el) {
                el.textContent = el.dataset.countTo;
            });
            return;
        }

        // Prépare l'état de départ : on écrit "0" (formaté) pour figer la largeur
        // de la cellule et éviter un reflow gênant pendant l'animation.
        targets.forEach(function(el) {
            const raw = String(el.dataset.countTo || '');
            const match = raw.match(/^(-?\d+)(.*)$/);
            const pad = match && match[1].startsWith('0') ? match[1].length : 0;
            const suffix = match ? match[2] : '';
            el.textContent = ('0').padStart(pad || 1, '0') + suffix;
        });

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (!entry.isIntersecting) return;
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.4 });

        targets.forEach(function(el) { observer.observe(el); });
    }

    /**
     * Anime un compteur vers sa cible via requestAnimationFrame.
     * Ease-out cubique : démarre vite, ralentit à l'approche du chiffre final.
     */
    function animateCounter(el) {
        const raw = String(el.dataset.countTo || '');
        const match = raw.match(/^(-?\d+)(.*)$/);
        if (!match) { el.textContent = raw; return; }

        const target = parseInt(match[1], 10);
        const suffix = match[2] || '';
        const pad = match[1].startsWith('0') ? match[1].length : 0;
        const duration = parseInt(el.dataset.countDuration || '1400', 10);

        const start = performance.now();

        function tick(now) {
            const progress = Math.min(1, (now - start) / duration);
            // Ease-out cubique — la fin ralentit, donne un effet "atterrissage".
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(target * eased);

            let str = String(value);
            if (pad) str = str.padStart(pad, '0');
            el.textContent = str + suffix;

            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    // ============================================================
    // BOOT
    // ============================================================
    function boot() {
        initReveals();
        initCounters();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
