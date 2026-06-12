/**
 * dashboard.js — Scripts du dashboard ENIET/ENIEG
 *
 * Fonctionnalités :
 * - Toggle sidebar mobile
 * - Fermeture auto des flash messages après 5 secondes
 * - Gestion overlay mobile
 */

(function() {
    'use strict';

    // ============================================================
    // SIDEBAR MOBILE
    // ============================================================

    function initSidebar() {
        const toggle = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('dashboard-sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (!toggle || !sidebar || !overlay) return;

        function openSidebar() {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('opacity-0', 'pointer-events-none');
            overlay.classList.add('opacity-100');
            document.body.style.overflow = 'hidden';
        }

        function closeSidebar() {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.remove('opacity-100');
            overlay.classList.add('opacity-0', 'pointer-events-none');
            document.body.style.overflow = '';
        }

        toggle.addEventListener('click', openSidebar);
        overlay.addEventListener('click', closeSidebar);

        // Échap ferme la sidebar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !sidebar.classList.contains('-translate-x-full')) {
                closeSidebar();
            }
        });

        // Resize : ferme automatiquement si on passe en desktop
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (window.innerWidth >= 1024) {
                    closeSidebar();
                }
            }, 100);
        });
    }

    // ============================================================
    // TOASTS - Animation d'entrée et auto-fermeture des Messages
    // ============================================================

    function initToasts() {
        const toasts = document.querySelectorAll('[data-toast]');

        toasts.forEach((toast, index) => {
            // Animation d'entrée échelonnée (slide depuis la droite)
            setTimeout(() => {
                toast.style.transform = 'translateX(0)';
            }, 100 + (index * 150));

            // Bouton de fermeture
            const closeBtn = toast.querySelector('[data-toast-close]');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => fermerToast(toast));
            }

            // Auto-fermeture après 5 secondes
            setTimeout(() => fermerToast(toast), 5000 + (index * 150));
        });
    }

    function fermerToast(toast) {
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 400);
    }

// ============================================================
    // MODALES DE CONFIRMATION
    // ============================================================

    /**
     * Intercepte les liens/boutons avec data-confirm pour afficher
     * une modale de confirmation avant d'exécuter l'action.
     *
     * Usage HTML :
     *   <a href="..." data-confirm="Êtes-vous sûr ?">Supprimer</a>
     */
    function initModales() {
        const elements = document.querySelectorAll('[data-confirm]');

        elements.forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const message = el.dataset.confirm;
                const action = el.getAttribute('href') || el.dataset.action;

                afficherModale(message, () => {
                    // Si c'est un lien, on navigue
                    if (el.tagName === 'A') {
                        window.location.href = action;
                    }
                    // Si c'est dans un formulaire, on le soumet
                    else if (el.closest('form')) {
                        el.closest('form').submit();
                    }
                });
            });
        });
    }

    function afficherModale(message, onConfirm) {
        // Crée la modale dynamiquement
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 z-[200] bg-primary-darker/60 backdrop-blur-sm flex items-center justify-center p-6';
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.2s';

        overlay.innerHTML = `
            <div class="bg-white max-w-md w-full p-6 shadow-2xl" style="transform: scale(0.95); transition: transform 0.2s;">
                <div class="w-12 h-12 bg-amber-100 flex items-center justify-center mx-auto mb-4">
                    <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                </div>
                <p class="text-center text-ink/80 mb-6">${message}</p>
                <div class="flex gap-3">
                    <button type="button" class="flex-1 py-2.5 border border-primary/30 hover:border-primary text-primary-darker font-semibold text-sm transition-colors" data-modal-cancel>
                        Annuler
                    </button>
                    <button type="button" class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition-colors" data-modal-confirm>
                        Confirmer
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';

        // Animation d'entrée
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            overlay.querySelector('div').style.transform = 'scale(1)';
        });

        function fermer() {
            overlay.style.opacity = '0';
            document.body.style.overflow = '';
            setTimeout(() => overlay.remove(), 200);
        }

        overlay.querySelector('[data-modal-cancel]').addEventListener('click', fermer);
        overlay.querySelector('[data-modal-confirm]').addEventListener('click', () => {
            fermer();
            onConfirm();
        });
        // Clic sur le fond ferme
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) fermer();
        });
        // Échap ferme
        document.addEventListener('keydown', function onEsc(e) {
            if (e.key === 'Escape') {
                fermer();
                document.removeEventListener('keydown', onEsc);
            }
        });
    }

    // ============================================================
    // SLUG AUTO depuis le TITRE
    // ============================================================
    /**
     * Remplit le champ #id_slug en temps réel quand l'utilisateur tape
     * dans #id_titre. S'arrête dès que l'utilisateur édite manuellement
     * le slug (pour ne pas écraser un slug volontairement personnalisé).
     *
     * S'active automatiquement sur les pages article/album/utilisateur
     * dès que les deux champs sont présents.
     */
    function slugify(value) {
        return (value || '')
            .toString()
            .normalize('NFD')                       // sépare les diacritiques
            .replace(/[̀-ͯ]/g, '')        // retire les accents
            .toLowerCase()
            .trim()
            .replace(/['’"`]/g, '')                 // retire les apostrophes/quotes
            .replace(/[^a-z0-9]+/g, '-')            // tout le reste → tiret
            .replace(/^-+|-+$/g, '');               // pas de tiret en bord
    }

    function initSlugAuto() {
        const titre = document.getElementById('id_titre');
        const slug = document.getElementById('id_slug');
        if (!titre || !slug) return;

        // Si le slug est déjà rempli (mode édition), on respecte l'existant.
        let userEdited = slug.value.trim() !== '';

        // Tout input direct dans le slug = l'utilisateur prend la main.
        slug.addEventListener('input', () => { userEdited = true; });

        titre.addEventListener('input', () => {
            if (userEdited) return;
            slug.value = slugify(titre.value);
        });
    }

    // ============================================================
    // BOUTON RETOUR EN HAUT
    // ============================================================

    function initRetourHaut() {
        // Crée le bouton dynamiquement
        const btn = document.createElement('button');
        btn.className = 'fixed bottom-6 right-6 z-40 w-11 h-11 bg-primary hover:bg-primary-dark text-cream shadow-lg flex items-center justify-center transition-all opacity-0 pointer-events-none';
        btn.setAttribute('aria-label', 'Retour en haut');
        btn.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"/>
            </svg>
        `;
        document.body.appendChild(btn);

        // Affiche le bouton après 400px de scroll
        window.addEventListener('scroll', () => {
            if (window.scrollY > 400) {
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
            } else {
                btn.style.opacity = '0';
                btn.style.pointerEvents = 'none';
            }
        });

        // Clic = remonte en douceur
        btn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    // ============================================================
    // INIT au chargement du DOM
    // ============================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initSidebar();
            initToasts();
            initModales();
            initSlugAuto();
            initRetourHaut();
        });
    } else {
        initSidebar();
        initToasts();
        initModales();
        initRetourHaut();
    }
})();