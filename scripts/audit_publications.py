"""Contrôle factuel des publications : lit le DOM de TikTok Studio, n'invente rien.

09/10/2026 — audit demandé par le patron. But :ursing comparer ce que la BASE affirme
et ce que le COMPTE montre réellement, et sortir les URL publiques sans les deviner.

Sortie : pour chaque carte lue -> durée, légende (début), date affichée, URL publique
réellement présente dans le DOM, et identifiant auto_NNN déduit du numéro d'épisode.
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video_pipeline"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import publish_studio as ps  # noqa: E402

JS_CARTES = r"""
var out = [], vus = {};
document.querySelectorAll('span').forEach(function(el){
  var t = (el.innerText||'').trim();
  if (!/^\d{2}:\d{2}$/.test(t)) return;
  var p = el, meilleur = null;
  for (var i=0;i<12 && p;i++){
    p = p.parentElement; if (!p) break;
    var tx = (p.innerText||'');
    if (tx.length >= 60 && /\d{1,2}:\d{2}/.test(tx)) { meilleur = p; break; }
  }
  if (!meilleur) return;
  var tx = (meilleur.innerText||'').replace(/\s+/g,' ').trim();
  var coupe = -1, re = /\d{2}:\d{2}/g, m;
  while ((m = re.exec(tx)) !== null) {
    if (m.index === 0) continue;
    var avant = tx.slice(Math.max(0, m.index - 24), m.index);
    if (/\d{1,2}\s+[^0-9:]{2,8}\s*$/.test(avant)) continue;
    coupe = m.index; break;
  }
  if (coupe > 0) tx = tx.slice(0, coupe).trim();
  var cle = tx.slice(0, 100);
  if (tx.length < 8 || vus[cle]) return; vus[cle] = 1;
  // URL publique réellement présente dans le DOM (lien « Voir » / menu de la carte).
  var lien = '';
  var anc = meilleur;
  for (var j=0;j<8 && anc;j++){
    var a = anc.querySelector && anc.querySelector('a[href*="/video/"]');
    if (a) { lien = a.href; break; }
    anc = anc.parentElement;
  }
  var date = (tx.match(/\d{1,2}\s+[a-zA-Zéû]+\.?,\s*\d{1,2}:\d{2}/) || [''])[0];
  out.push({duree: t, carte: tx.slice(0, 300), url: lien, date: date});
});
return JSON.stringify(out);
"""


def main():
    d = ps.ensure_chrome()
    d.get(ps.CONTENT_URL)
    time.sleep(8)
    try:
        d.set_script_timeout(30)
    except Exception:
        pass
    brut = None
    for _ in range(4):
        try:
            brut = json.loads(d.execute_script(JS_CARTES) or "[]")
            if brut:
                break
        except Exception as exc:
            print(f"  (lecture échouée : {exc.__class__.__name__}, on réessaie)")
            time.sleep(3)
    cartes = brut or []

    # Compteur global, seul volume fiable (la liste ne charge que quelques cartes).
    try:
        d.execute_script("window.scrollTo(0,0)")
        time.sleep(1)
        corps = d.execute_script("return document.body.innerText") or ""
        m = re.search(r"Publications\s+(\d+)", corps)
        compteur = m.group(1) if m else "?"
    except Exception:
        compteur = "?"

    print(f"Compteur « Publications » du compte : {compteur}")
    print(f"Cartes lisibles dans la fenêtre    : {len(cartes)}")
    print()
    for c in cartes:
        carte = c.get("carte", "")
        vid = ps._id_depuis_carte(carte)
        print(f"- {c.get('duree')} | {c.get('date') or 'date ?'} | {vid or 'id NON identifiable'}")
        print(f"    légende : {carte[:150]}")
        print(f"    URL     : {c.get('url') or '(aucun lien /video/ dans cette carte)'}")
    Path(ROOT / "logs" / "audit_publications.json").write_text(
        json.dumps({"compteur": compteur, "cartes": cartes}, ensure_ascii=False, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()