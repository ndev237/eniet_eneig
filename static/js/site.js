/**
 * site.js - Scripts globaux du site public ENIET/ENIEG
 *
 * Inclut :
 * - Gestion du menu mobile (drawer)
 * - Gestion de l'overlay
 * - Accessibilité (touche Échap, focus management)
 */

(function() {
    'use strict';

    // ============================================================
    // MENU MOBILE
    // ============================================================

    /**
     * Initialise le drawer mobile.
     * Pattern IIFE (Immediately Invoked Function Expression) :
     * tout le code est scopé localement, n'expose rien au global.
     */
    function initMobileMenu() {
        const toggleBtn = document.querySelector('[data-menu-toggle]');
        const drawer = document.querySelector('[data-menu-drawer]');
        const overlay = document.querySelector('[data-menu-overlay]');
        const closeButtons = document.querySelectorAll('[data-menu-close]');

        // Si un de ces éléments manque, on n'initialise pas (page sans menu mobile)
        if (!toggleBtn || !drawer || !overlay) return;

        /**
         * Ouvre le menu drawer.
         */
        function openMenu() {
            // Retire la translation pour faire apparaître le drawer
            drawer.classList.remove('translate-x-full');

            // Affiche l'overlay
            overlay.classList.remove('opacity-0', 'pointer-events-none');
            overlay.classList.add('opacity-100');

            // Empêche le scroll de la page derrière
            document.body.style.overflow = 'hidden';

            // Accessibilité : indique que le menu est ouvert
            toggleBtn.setAttribute('aria-expanded', 'true');
            drawer.setAttribute('aria-hidden', 'false');

            // Focus sur le premier lien pour la navigation clavier
            const firstLink = drawer.querySelector('a, button');
            if (firstLink) {
                // Petit délai pour laisser l'animation se faire
                setTimeout(() => firstLink.focus(), 100);
            }
        }

        /**
         * Ferme le menu drawer.
         */
        function closeMenu() {
            // Re-translate vers la droite (cache le drawer)
            drawer.classList.add('translate-x-full');

            // Cache l'overlay
            overlay.classList.remove('opacity-100');
            overlay.classList.add('opacity-0', 'pointer-events-none');

            // Restaure le scroll
            document.body.style.overflow = '';

            // Accessibilité
            toggleBtn.setAttribute('aria-expanded', 'false');
            drawer.setAttribute('aria-hidden', 'true');

            // Refocus sur le bouton qui a ouvert le menu (UX clavier)
            toggleBtn.focus();
        }

        // ============================================================
        // ÉVÉNEMENTS
        // ============================================================

        // Clic sur le burger : ouvre le menu
        toggleBtn.addEventListener('click', openMenu);

        // Clic sur n'importe quel bouton de fermeture
        closeButtons.forEach(btn => {
            btn.addEventListener('click', closeMenu);
        });

        // Clic sur l'overlay sombre : ferme le menu
        overlay.addEventListener('click', closeMenu);

        // Touche Échap : ferme le menu
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !drawer.classList.contains('translate-x-full')) {
                closeMenu();
            }
        });

        // Fermer le menu quand on clique sur un lien interne
        // Sinon le drawer reste ouvert après navigation
        const navLinks = drawer.querySelectorAll('a[href]');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                // On ferme avec un petit délai pour laisser l'animation
                // se finir avant le changement de page
                setTimeout(closeMenu, 100);
            });
        });

        // Si l'utilisateur redimensionne en mode desktop alors que le menu
        // mobile est ouvert, on le ferme automatiquement
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                // 1024px = breakpoint lg de Tailwind
                if (window.innerWidth >= 1024 && !drawer.classList.contains('translate-x-full')) {
                    closeMenu();
                }
            }, 100);
        });
    }

    // ============================================================
    // INITIALISATION quand le DOM est prêt
    // ============================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileMenu);
    } else {
        // DOMContentLoaded déjà passé : on init immédiatement
        initMobileMenu();
    }
})();