/**
 * password-toggle.js — Affiche/masque le mot de passe sur TOUS les inputs
 * de type "password" présents dans la page.
 *
 * Fonctionnement :
 *
 *   1. Au chargement, on parcourt tous les <input type="password">.
 *   2. Pour chacun :
 *        - on s'assure que son parent est positionné en `relative`
 *          (nécessaire pour poser le bouton en absolute) ;
 *        - on ajoute un padding-right à l'input pour laisser la place ;
 *        - on insère un bouton avec deux icônes (œil ouvert / œil barré)
 *          qui bascule input.type entre "password" et "text" au clic.
 *   3. Un flag `data-pw-enhanced` évite d'enhancer deux fois le même input
 *          (utile si un partial est ré-injecté par JS).
 *
 * DOM 100 % construit via document.createElement (aucun innerHTML) — donc
 * zéro surface XSS même si un jour un input avait des attributs venant
 * de données utilisateur.
 *
 * L'observateur MutationObserver couvre les cas où des champs mot de passe
 * sont ajoutés dynamiquement après le chargement (ex: modale d'édition).
 */

(function() {
    'use strict';

    // ============================================================
    // Icônes SVG créées en programmatique (namespace SVG requis)
    // ============================================================
    const SVG_NS = 'http://www.w3.org/2000/svg';

    function makeSvg(pathData) {
        const svg = document.createElementNS(SVG_NS, 'svg');
        svg.setAttribute('class', 'w-5 h-5');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('viewBox', '0 0 24 24');
        const path = document.createElementNS(SVG_NS, 'path');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-width', '1.6');
        path.setAttribute('d', pathData);
        svg.appendChild(path);
        return svg;
    }

    const EYE_PATH =
        'M15 12a3 3 0 11-6 0 3 3 0 016 0z ' +
        'M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7' +
        '-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z';
    const EYE_OFF_PATH =
        'M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7' +
        'a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878' +
        'l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59' +
        'm0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7' +
        'a10.025 10.025 0 01-4.132 5.411m0 0L21 21';

    // ============================================================
    // Assure un conteneur positionné relatif autour de l'input
    // ============================================================
    function ensureRelativeContainer(input) {
        const parent = input.parentElement;
        // Cas 1 : le parent a déjà class="relative" (ex : champs stylisés du login)
        if (parent && parent.classList.contains('relative')) {
            return parent;
        }
        // Cas 2 : le parent est positionné en absolute/relative/fixed via CSS
        if (parent && ['relative', 'absolute', 'fixed'].includes(getComputedStyle(parent).position)) {
            return parent;
        }
        // Sinon on wrappe dans un <div class="relative"> qui prend la largeur naturelle
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        return wrapper;
    }

    // ============================================================
    // Enhance : ajoute le bouton toggle sur un input password donné
    // ============================================================
    function enhance(input) {
        if (input.dataset.pwEnhanced === 'true') return;
        input.dataset.pwEnhanced = 'true';

        const container = ensureRelativeContainer(input);

        // On ménage la place à droite (le bouton fait ~40px de large)
        input.classList.add('pr-11');

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.tabIndex = -1;  // ne pollue pas la nav clavier (on garde l'input focusable)
        btn.setAttribute('aria-label', 'Afficher le mot de passe');
        btn.setAttribute('aria-pressed', 'false');
        btn.className =
            'absolute inset-y-0 right-0 flex items-center px-3 ' +
            'text-primary/45 hover:text-primary transition-colors ' +
            'cursor-pointer bg-transparent border-0';

        const iconEye = makeSvg(EYE_PATH);
        const iconOff = makeSvg(EYE_OFF_PATH);
        iconOff.classList.add('hidden');
        btn.appendChild(iconEye);
        btn.appendChild(iconOff);

        btn.addEventListener('click', () => {
            const isMasked = input.type === 'password';
            input.type = isMasked ? 'text' : 'password';
            iconEye.classList.toggle('hidden', isMasked);
            iconOff.classList.toggle('hidden', !isMasked);
            btn.setAttribute('aria-label',
                isMasked ? 'Masquer le mot de passe' : 'Afficher le mot de passe');
            btn.setAttribute('aria-pressed', String(isMasked));
        });

        container.appendChild(btn);
    }

    // ============================================================
    // Init + MutationObserver pour couvrir les champs ajoutés
    // dynamiquement plus tard (modales, formulaires AJAX, etc.)
    // ============================================================
    function scan(root) {
        root.querySelectorAll('input[type="password"]').forEach(enhance);
    }

    function init() {
        scan(document);

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((m) => {
                m.addedNodes.forEach((node) => {
                    if (node.nodeType !== 1) return;  // element only
                    if (node.matches && node.matches('input[type="password"]')) {
                        enhance(node);
                    } else if (node.querySelectorAll) {
                        scan(node);
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
