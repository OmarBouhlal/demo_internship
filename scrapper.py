import time
import csv
import logging
import unicodedata
from dataclasses import dataclass, asdict
from typing import Optional

from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

BASE_URL = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch"
DELAY_SECONDS = 2.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

@dataclass
class Consultation:
    reference: str
    objet: str
    organisme: Optional[str] = None
    categorie: Optional[str] = None
    lieu_execution: Optional[str] = None
    date_limite: Optional[str] = None
    date_publication: Optional[str] = None
    lien_detail: Optional[str] = None
    ref_interne: Optional[str] = None      
    org_acronyme: Optional[str] = None     

# --- Sélecteurs ---
SEL_ORG_NAME_INPUT = "#ctl0_CONTENU_PAGE_AdvancedSearch_orgName"
SEL_ORG_AUTOCOMPLETE_RESULT = "#ctl0_CONTENU_PAGE_AdvancedSearch_orgName_result"
SEL_KEYWORD_INPUT = "#ctl0_CONTENU_PAGE_AdvancedSearch_keywordSearch"
SEL_SEARCH_BUTTON = "#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche"
SEL_NO_RESULTS = "#ctl0_CONTENU_PAGE_resultSearch_panelNoElementFound"
SEL_RESULTS_TABLE = "table.table-results"
SEL_NEXT_PAGE = "#ctl0_CONTENU_PAGE_resultSearch_PagerTop_ctl2"
BASE_SITE_URL = "https://www.marchespublics.gov.ma/"

def _clean(text: str) -> str:
    return " ".join(text.split())

def _strip_label(text: str, label: str) -> str:
    text = _clean(text)
    prefix = f"{label} :"
    if text.startswith(prefix):
        text = text[len(prefix):]
    return text.strip()

def normalize(text: str) -> str:
    """Normalise le texte pour la comparaison (gère les accents, casses et apostrophes)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    return text.upper().replace("’", "'").strip()

def get_target_companies(page: Page, keyword: str = "al omrane") -> list[str]:
    """Extrait la liste complète des filiales depuis le menu d'autocomplétion."""
    log.info(f"Récupération de la liste des entités pour '{keyword}'...")
    page.goto(BASE_URL, wait_until="networkidle")
    
    page.click(SEL_ORG_NAME_INPUT)
    page.fill(SEL_ORG_NAME_INPUT, "")
    page.type(SEL_ORG_NAME_INPUT, keyword, delay=100)
    
    try:
        page.wait_for_selector(f"{SEL_ORG_AUTOCOMPLETE_RESULT} li", state="visible", timeout=15000)
        options = page.locator(f"{SEL_ORG_AUTOCOMPLETE_RESULT} li")
        names = options.all_inner_texts()
        return [n.strip() for n in names if n.strip()]
    except Exception as e:
        log.error(f"Impossible de récupérer la liste des entreprises : {e}")
        return []

def parse_results(html: str) -> list[Consultation]:
    """Extraction BeautifulSoup de la table des résultats."""
    soup = BeautifulSoup(html, "html.parser")

    if soup.select_one(SEL_NO_RESULTS):
        return []

    table = soup.select_one(SEL_RESULTS_TABLE)
    if not table:
        return []

    results = []
    rows = table.select("tbody > tr")

    for row in rows:
        ref_input = row.select_one("input[name*='refCons']")
        org_input = row.select_one("input[name*='orgCons']")

        cell_ref = row.select_one("td[headers='cons_ref']")
        cell_intitule = row.select_one("td[headers='cons_intitule']")
        cell_lieu = row.select_one("td[headers='cons_lieuExe']")
        cell_date_end = row.select_one("td[headers='cons_dateEnd']")
        cell_actions = row.select_one("td.actions")

        if not cell_intitule:
            continue

        reference_span = cell_intitule.select_one("span.ref")
        reference = _clean(reference_span.get_text()) if reference_span else ""

        objet_div = cell_intitule.select_one("div[id*='panelBlocObjet']")
        objet = _strip_label(objet_div.get_text(), "Objet") if objet_div else ""

        organisme_div = cell_intitule.select_one("div[id*='panelBlocDenomination']")
        organisme = _strip_label(organisme_div.get_text(), "Acheteur public") if organisme_div else None

        categorie = None
        if cell_ref:
            cat_div = cell_ref.select_one("div[id*='panelBlocCategorie']")
            categorie = _clean(cat_div.get_text()) if cat_div else None

        lieu_execution = None
        if cell_lieu:
            lieu_div = cell_lieu.select_one("div[id*='panelBlocLieuxExec']")
            if lieu_div:
                lieu_execution = _clean(lieu_div.get_text())

        date_limite = None
        if cell_date_end:
            cloture_div = cell_date_end.select_one("div.cloture-line")
            if cloture_div:
                date_limite = _clean(cloture_div.get_text(separator=" "))

        lien_detail = None
        if cell_actions:
            detail_link = cell_actions.select_one("a[href*='EntrepriseDetailConsultation']")
            if detail_link and detail_link.get("href"):
                href = detail_link["href"]
                lien_detail = href if href.startswith("http") else BASE_SITE_URL + href.lstrip("/")

        results.append(
            Consultation(
                reference=reference,
                objet=objet,
                organisme=organisme,
                categorie=categorie,
                lieu_execution=lieu_execution,
                date_limite=date_limite,
                lien_detail=lien_detail,
                ref_interne=ref_input["value"] if ref_input else None,
                org_acronyme=org_input["value"] if org_input else None,
            )
        )

    return results

def has_next_page(page: Page) -> bool:
    locator = page.locator(SEL_NEXT_PAGE)
    if locator.count() == 0:
        return False
    try:
        return locator.first.is_visible()
    except Exception:
        return False

def scrape_for_organisation(page: Page, organisation: str, max_pages: int = 5) -> list[Consultation]:
    """Effectue la recherche et la pagination pour une entité spécifique."""
    page.goto(BASE_URL, wait_until="networkidle")
    time.sleep(1)

    page.click(SEL_ORG_NAME_INPUT)
    page.fill(SEL_ORG_NAME_INPUT, "")
    # On tape pour déclencher l'autocomplétion PRADO
    page.type(SEL_ORG_NAME_INPUT, "al omrane", delay=100)

    try:
        # Attente de l'apparition de la liste
        page.wait_for_selector(f"{SEL_ORG_AUTOCOMPLETE_RESULT} li", state="visible", timeout=15000)
        options_locator = page.locator(f"{SEL_ORG_AUTOCOMPLETE_RESULT} li")
        
        target_norm = normalize(organisation)
        clicked = False
        
        # Extraction de tous les textes pour chercher le bon
        all_texts = options_locator.all_inner_texts()
        
        for i, text in enumerate(all_texts):
            if normalize(text) == target_norm:
                element = options_locator.nth(i)
                # On scrolle dessus si c'est caché en bas de la liste
                element.scroll_into_view_if_needed()
                # force=True pour ignorer les éléments superposés
                element.click(force=True) 
                clicked = True
                log.info(f"👉 Suggestion sélectionnée avec succès : {text}")
                break
                
        if not clicked:
            log.warning(f"Entité '{organisation}' introuvable dans le dropdown. Ignorée.")
            return []
            
        # CRITIQUE : Laisser le temps à PRADO de mettre à jour son ID caché
        time.sleep(1.5)

    except Exception as e:
        log.warning(f"Erreur d'autocomplétion pour '{organisation}': {e}")
        return []

    # Lancement de la recherche
    log.info(f"🖱️ Clic sur Rechercher pour {organisation}...")
    page.click(SEL_SEARCH_BUTTON)
    page.wait_for_load_state("networkidle")
    time.sleep(DELAY_SECONDS)

    # Aspiration avec pagination
    all_page_results = []
    page_num = 1
    
    while page_num <= max_pages:
        page_results = parse_results(page.content())
        if not page_results:
            log.info(f"[{organisation}] Aucun résultat trouvé ou fin des résultats.")
            break
            
        all_page_results.extend(page_results)
        log.info(f"[{organisation}] Page {page_num} : {len(page_results)} résultats extraits.")

        if not has_next_page(page):
            break
            
        page.click(SEL_NEXT_PAGE)
        page.wait_for_load_state("networkidle")
        time.sleep(DELAY_SECONDS)
        page_num += 1

    return all_page_results

def save_to_csv(consultations: list[Consultation], filepath: str):
    if not consultations:
        log.warning("Aucune donnée à sauvegarder.")
        return
    fieldnames = list(asdict(consultations[0]).keys())
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in consultations:
            writer.writerow(asdict(c))
    log.info(f"✅ {len(consultations)} consultations uniques sauvegardées dans {filepath}")

def main():
    all_consultations = []

    with sync_playwright() as p:
        # Mettre headless=True pour cacher le navigateur une fois que tout marche
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        # Etape 1 : Récupérer toutes les filiales Al Omrane
        companies = get_target_companies(page, "al omrane")
        log.info(f"{len(companies)} entités trouvées pour le groupe Al Omrane.")

        # Etape 2 & 3 & 4 : Itérer et scraper chaque filiale
        for company in companies:
            log.info(f"\n--- Démarrage scraping pour : {company} ---")
            results = scrape_for_organisation(page, company)
            all_consultations.extend(results)

        browser.close()

    # Etape 5 : Déduplication basée sur la référence interne ou la référence textuelle
    log.info("\nNettoyage et déduplication des résultats...")
    unique = {}
    for c in all_consultations:
        key = c.ref_interne or c.reference
        if key not in unique:
            unique[key] = c

    final_consultations = list(unique.values())
    log.info(f"Avant déduplication : {len(all_consultations)} | Après déduplication : {len(final_consultations)}")

    # Etape 6 : Sauvegarde finale
    save_to_csv(final_consultations, "al_omrane_group.csv")

if __name__ == "__main__":
    main()