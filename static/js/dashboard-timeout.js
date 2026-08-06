/**
 * dashboard-timeout.js — Avertissement d'expiration de session.
 *
 * Fonctionnement, en synthèse :
 *
 *   1. On lit `data-session-max="600"` sur <body> (secondes, aligné sur
 *      SESSION_COOKIE_AGE côté serveur).
 *   2. On track la dernière activité utilisateur (mousemove, keydown, click,
 *      touchstart, scroll — throttlé à 1 par seconde).
 *   3. Toutes les 5 secondes on regarde combien de temps s'est écoulé
 *      depuis la dernière activité.
 *        - Si idle >= (max - 60s) → on affiche un toast avec un compte à
 *          rebours de 60 secondes.
 *        - Si idle >= max → on recharge la page (le serveur redirigera
 *          vers /dashboard/login/ car la session a expiré).
 *   4. Le toast propose « Rester connecté » qui POST /dashboard/session/heartbeat/
 *      → le middleware Session redémarre la fenêtre glissante de 10 min.
 *   5. Toute activité pendant que le toast est affiché déclenche aussi
 *      un heartbeat + ferme le toast (comportement attendu par l'utilisateur).
 *
 * Le DOM du toast est construit via document.createElement pour éviter tout
 * innerHTML — aucune surface d'attaque XSS même si des attributs étaient
 * un jour dérivés de données utilisateur.
 */

(function() {
    'use strict';

    // ============================================================
    // CONFIGURATION lue depuis <body data-session-max="…">
    // ============================================================
    const body = document.body;
    const MAX_AGE = parseInt(body.dataset.sessionMax || '0', 10);
    const HEARTBEAT_URL = body.dataset.sessionHeartbeatUrl || '';
    if (!MAX_AGE || !HEARTBEAT_URL) return;

    const WARN_BEFORE = 60;           // secondes d'avance de l'alerte
    const CHECK_INTERVAL = 5000;      // vérif toutes les 5 s
    const ACTIVITY_THROTTLE = 1000;   // 1 s entre 2 mises à jour d'activité

    // ============================================================
    // ÉTAT
    // ============================================================
    let lastActivity = Date.now();
    let lastActivityWrite = 0;
    let toast = null;
    let countdownEl = null;
    let countdownTimer = null;

    // ============================================================
    // CSRF — lu depuis le cookie posé par Django
    // ============================================================
    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    // ============================================================
    // ACTIVITÉ UTILISATEUR (throttlée)
    // ============================================================
    function recordActivity() {
        const now = Date.now();
        if (now - lastActivityWrite < ACTIVITY_THROTTLE) return;
        lastActivityWrite = now;
        lastActivity = now;
        if (toast) refreshSession();   // interaction pendant alerte = « je suis là »
    }

    ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'].forEach(evt => {
        window.addEventListener(evt, recordActivity, { passive: true });
    });

    // ============================================================
    // Petit helper createElement pour rester lisible
    // ============================================================
    function el(tag, attrs, children) {
        const node = document.createElement(tag);
        if (attrs) {
            for (const key in attrs) {
                if (key === 'className') node.className = attrs[key];
                else if (key === 'text') node.textContent = attrs[key];
                else node.setAttribute(key, attrs[key]);
            }
        }
        (children || []).forEach(c => {
            if (typeof c === 'string') node.appendChild(document.createTextNode(c));
            else if (c) node.appendChild(c);
        });
        return node;
    }

    // ============================================================
    // TOAST — construit via createElement, aucun innerHTML
    // ============================================================
    function showWarning(secondsLeft) {
        if (toast) return;

        // Barre or au-dessus
        const bar = el('div', { className: 'h-1 bg-accent' });

        // Icône horloge (SVG créé en programmatique)
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('class', 'w-5 h-5 text-accent');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('viewBox', '0 0 24 24');
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-width', '1.8');
        path.setAttribute('d', 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z');
        svg.appendChild(path);
        const iconBox = el('div', {
            className: 'w-10 h-10 bg-accent/15 flex items-center justify-center flex-shrink-0',
        }, [svg]);

        // Titre + corps du message (avec countdown en <strong>)
        const title = el('div', {
            className: 'font-display text-base font-semibold text-primary-darker mb-1',
            text: 'Session bientôt expirée',
        });

        countdownEl = el('strong', {
            className: 'text-primary-darker',
            text: String(secondsLeft),
        });
        const text = el('p', {
            className: 'text-sm text-ink/65 leading-relaxed',
        }, [
            'Vous serez déconnecté pour inactivité dans ',
            countdownEl,
            ' s.',
        ]);

        const messageCol = el('div', { className: 'flex-1 min-w-0' }, [title, text]);
        const messageRow = el('div', {
            className: 'flex items-start gap-3 mb-3',
        }, [iconBox, messageCol]);

        // Boutons
        const keepAliveBtn = el('button', {
            type: 'button',
            className: 'bg-primary hover:bg-primary-dark text-cream font-semibold text-sm px-4 py-2 transition-colors',
            text: 'Rester connecté',
        });
        keepAliveBtn.addEventListener('click', refreshSession);

        const dismissBtn = el('button', {
            type: 'button',
            className: 'text-sm text-ink/50 hover:text-ink transition-colors',
            text: 'Fermer',
        });
        dismissBtn.addEventListener('click', dismissToast);

        const actions = el('div', {
            className: 'flex items-center gap-3',
        }, [keepAliveBtn, dismissBtn]);

        const panel = el('div', { className: 'p-5' }, [messageRow, actions]);

        toast = el('div', {
            role: 'alertdialog',
            'aria-live': 'assertive',
            className:
                'fixed bottom-6 right-6 z-[150] max-w-sm bg-white ' +
                'border border-primary/15 shadow-2xl shadow-primary/10 ' +
                'transform transition-all duration-300 translate-y-4 opacity-0',
        }, [bar, panel]);

        document.body.appendChild(toast);

        // Animation d'entrée
        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-4', 'opacity-0');
        });

        startCountdown(secondsLeft);
    }

    function dismissToast() {
        if (!toast) return;
        toast.classList.add('translate-y-4', 'opacity-0');
        const dying = toast;
        toast = null;
        countdownEl = null;
        if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
        setTimeout(() => dying.remove(), 350);
    }

    // ============================================================
    // COMPTE À REBOURS visuel dans le toast
    // ============================================================
    function startCountdown(seconds) {
        let s = seconds;
        countdownTimer = setInterval(() => {
            s -= 1;
            if (s <= 0) {
                clearInterval(countdownTimer);
                countdownTimer = null;
                window.location.reload();
                return;
            }
            if (countdownEl) countdownEl.textContent = String(s);
        }, 1000);
    }

    // ============================================================
    // HEARTBEAT — POST vers le serveur pour prolonger la session
    // ============================================================
    function refreshSession() {
        fetch(HEARTBEAT_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        }).then(response => {
            if (response.ok || response.status === 204) {
                lastActivity = Date.now();
                dismissToast();
            } else if (response.status === 401 || response.status === 403) {
                window.location.reload();
            }
        }).catch(() => {
            // Réseau perdu : on laisse le compte à rebours continuer ;
            // au pire, la prochaine action rechargera la page.
        });
    }

    // ============================================================
    // BOUCLE DE VÉRIFICATION — toutes les 5 secondes
    // ============================================================
    function tick() {
        const idleSeconds = Math.floor((Date.now() - lastActivity) / 1000);
        if (idleSeconds >= MAX_AGE) {
            window.location.reload();
            return;
        }
        const remaining = MAX_AGE - idleSeconds;
        if (remaining <= WARN_BEFORE && !toast) {
            showWarning(remaining);
        }
    }

    setInterval(tick, CHECK_INTERVAL);
})();
