"""
Export PDF des messages de contact.

Isolé dans son propre module pour ne pas alourdir views.py.
Pure Python via reportlab (aucune dépendance système Windows/Linux).

L'export :
  - applique EXACTEMENT les mêmes filtres que la vue liste (statut, sujet, q)
  - produit un PDF A4 paysage avec un en-tête ENIET / ENIEG,
    la date d'export, le résumé des filtres appliqués, puis un
    tableau de tous les messages correspondants ;
  - pied de page avec « Page X sur Y » automatique.
"""

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from django.db.models import Q
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from apps.contacts.models import MessageContact
from .decorators import otp_required_dashboard


# ============================================================
# Durcissement : les valeurs qui finissent dans un Paragraph sont
# interprétées comme du mini-XML par reportlab. Un contenu non
# échappé issu du formulaire public de contact (nom, email,
# téléphone, message) ou de la barre de recherche permet :
#   - de casser le parsing (<, &, ', ") → ValueError ou PDF illisible
#   - d'injecter des balises reportlab (<img src="…">) qui peuvent
#     déclencher un fetch distant côté serveur → SSRF
# D'où _esc() : à passer sur TOUTE valeur user-controlled AVANT de
# la concaténer avec du balisage statique que, nous, on veut rendre.
# ============================================================
def _esc(value):
    """Echappe une valeur utilisateur pour inclusion sûre dans un Paragraph."""
    if value is None:
        return '—'
    s = str(value)
    return xml_escape(s, {'"': '&quot;', "'": '&apos;'})


# ============================================================
# Palette alignée sur le dashboard (greens + gold)
# ============================================================
BRAND_PRIMARY_DARKER = colors.HexColor('#1E3A2D')
BRAND_PRIMARY = colors.HexColor('#2E6B4C')
BRAND_ACCENT = colors.HexColor('#C9A96E')
BRAND_INK = colors.HexColor('#1A1A1A')
BRAND_INK_MUTED = colors.HexColor('#555555')
BRAND_CREAM = colors.HexColor('#F5F0E6')
BRAND_ROW_ALT = colors.HexColor('#FAF8F3')


def _apply_filters(request):
    """
    Réapplique les filtres de la vue liste (statut / sujet / q) et retourne
    (queryset, dict_resume_filtres) pour affichage dans l'en-tête du PDF.
    """
    qs = MessageContact.objects.all()
    filtres = {}

    statut = request.GET.get('statut', '').strip()
    if statut and statut in [s[0] for s in MessageContact.StatutChoices.choices]:
        qs = qs.filter(statut=statut)
        filtres['Statut'] = dict(MessageContact.StatutChoices.choices)[statut]

    sujet = request.GET.get('sujet', '').strip()
    if sujet and sujet in [s[0] for s in MessageContact.SujetChoices.choices]:
        qs = qs.filter(sujet=sujet)
        filtres['Sujet'] = dict(MessageContact.SujetChoices.choices)[sujet]

    recherche = request.GET.get('q', '').strip()
    if recherche:
        qs = qs.filter(
            Q(nom__icontains=recherche)
            | Q(email__icontains=recherche)
            | Q(message__icontains=recherche)
        )
        filtres['Recherche'] = recherche

    return qs.order_by('-created_at'), filtres


def _draw_header_footer(canvas, doc):
    """Pied de page avec pagination + fine ligne or au-dessus."""
    canvas.saveState()

    page_w, page_h = landscape(A4)
    # Ligne or au-dessus du pied de page
    canvas.setStrokeColor(BRAND_ACCENT)
    canvas.setLineWidth(0.4)
    canvas.line(15 * mm, 12 * mm, page_w - 15 * mm, 12 * mm)

    # Mention à gauche
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(BRAND_INK_MUTED)
    canvas.drawString(15 * mm, 8 * mm,
                      'ENIET / ENIEG — Export confidentiel des messages de contact')

    # Pagination à droite
    canvas.drawRightString(
        page_w - 15 * mm, 8 * mm,
        f'Page {doc.page}',
    )
    canvas.restoreState()


@otp_required_dashboard
def messages_export_pdf(request):
    """Télécharge un PDF listant les messages filtrés."""

    queryset, filtres = _apply_filters(request)
    total = queryset.count()

    # ---- Préparation du document ----
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title='Messages de contact — ENIET / ENIEG',
        author='Dashboard ENIET / ENIEG',
    )

    # ---- Styles ----
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'Title', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18, leading=22,
        textColor=BRAND_PRIMARY_DARKER, spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12,
        textColor=BRAND_INK_MUTED, spaceAfter=10,
    )
    style_filter = ParagraphStyle(
        'Filter', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=BRAND_INK, spaceAfter=2,
    )
    style_cell = ParagraphStyle(
        'Cell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        textColor=BRAND_INK,
    )
    style_cell_muted = ParagraphStyle(
        'CellMuted', parent=style_cell,
        textColor=BRAND_INK_MUTED,
    )

    story = []

    # ---- EN-TÊTE ----
    now_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    story.append(Paragraph('Messages de contact', style_title))
    story.append(Paragraph(
        f'Dashboard ENIET / ENIEG — Export généré le {now_str} — '
        f'<b>{total}</b> message{"s" if total != 1 else ""} au total',
        style_subtitle,
    ))

    if filtres:
        # Les clés sont des libellés figés (sûrs), mais les valeurs peuvent
        # provenir de la barre de recherche → on les échappe toutes.
        filter_str = ' · '.join(
            f'<b>{_esc(k)}</b> : {_esc(v)}' for k, v in filtres.items()
        )
        story.append(Paragraph(f'Filtres appliqués : {filter_str}', style_filter))
        story.append(Spacer(1, 6))

    # ---- Table ----
    if total == 0:
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            '<para align="center"><i>Aucun message ne correspond à ces filtres.</i></para>',
            style_cell_muted,
        ))
    else:
        header = [
            Paragraph('<b>Reçu le</b>', style_cell),
            Paragraph('<b>Expéditeur</b>', style_cell),
            Paragraph('<b>Email</b>', style_cell),
            Paragraph('<b>Téléphone</b>', style_cell),
            Paragraph('<b>Sujet</b>', style_cell),
            Paragraph('<b>Statut</b>', style_cell),
            Paragraph('<b>Message</b>', style_cell),
        ]
        data = [header]

        for msg in queryset:
            # Message : on tronque PUIS on échappe PUIS on remplace les
            # vrais sauts de ligne (déjà échappés en texte) par <br/>.
            # Ordre important : escape d'abord, markup après.
            msg_text = (msg.message or '')[:400]
            msg_text = _esc(msg_text).replace('\n', '<br/>')

            data.append([
                # La date est produite par strftime : contenu 100 % contrôlé
                # côté serveur → markup <br/> inline sans échappement.
                Paragraph(
                    msg.created_at.strftime('%d/%m/%Y<br/>%H:%M'),
                    style_cell_muted,
                ),
                Paragraph(_esc(msg.nom), style_cell),
                Paragraph(_esc(msg.email), style_cell),
                Paragraph(_esc(msg.telephone), style_cell),
                Paragraph(_esc(msg.get_sujet_display()), style_cell),
                Paragraph(_esc(msg.get_statut_display()), style_cell),
                Paragraph(msg_text or '—', style_cell),
            ])

        # Largeurs ajustées pour une page A4 paysage utile (~267mm) après marges
        col_widths = [25 * mm, 32 * mm, 52 * mm, 28 * mm, 32 * mm, 20 * mm, 78 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)

        # Style du tableau : en-tête vert sombre, lignes alternées cream
        ts = TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY_DARKER),
            ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_CREAM),
            ('BOX', (0, 0), (-1, 0), 0.5, BRAND_PRIMARY_DARKER),
            # Grille fine
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E5E5E5')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        # Zébrage une ligne sur deux
        for row_idx in range(1, len(data)):
            if row_idx % 2 == 0:
                ts.add('BACKGROUND', (0, row_idx), (-1, row_idx), BRAND_ROW_ALT)
        table.setStyle(ts)

        story.append(table)

    # ---- Génération + réponse HTTP ----
    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    today = datetime.now().strftime('%Y-%m-%d')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="messages-eniet-enieg-{today}.pdf"'
    )
    response['Content-Length'] = str(len(pdf_bytes))
    return response
