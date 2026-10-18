#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Attend la fin du traitement YouTube : ferme la boîte « Traitement de la
vidéo » quand 100 % est atteint, puis attend la confirmation « Vidéo mise en
ligne ». Retourne le lien si disponible."""

import json
import sys
import time

HERE = __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0]
sys.path.insert(0, HERE)

from cdp import Tab, find_tab  # noqa: E402

JS_STATE = """(() => {
  const dialogs = [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog')]
    .filter(d => d.getBoundingClientRect().width > 0);
  const state = {visible: [], link: null};
  for (const d of dialogs) {
    const t = (d.innerText || '').trim();
    if (t) state.visible.push(t.slice(0, 400));
    const a = [...d.querySelectorAll('a[href]')].map(x => x.href)
      .find(h => /youtu\\.(be|com)\\/(shorts|video)|youtu\\.be/.test(h));
    if (a && /mise en ligne/i.test(t)) state.link = a;
    if (a && !state.link) state.link = a;
  }
  const trait = /Traitement de la vid/i.test(document.body.innerText || '');
  return JSON.stringify({...state, traitementPage: trait});
})()"""

JS_CLOSE_VISIBLE = """(() => {
  const d = [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog')]
    .find(x => x.getBoundingClientRect().width > 0 &&
      (x.innerText || '').trim().length > 10);
  if (!d) return 'aucune';
  const b = [...d.querySelectorAll('ytcp-button, button')]
    .find(x => /^(Fermer|Terminer|Close)$/i.test((x.innerText || '').trim())
      && x.getBoundingClientRect().width > 0);
  if (!b) return 'pas-de-fermer';
  b.click();
  return 'ok';
})()"""


def main():
    page = find_tab("studio.youtube.com")
    if not page:
        print("onglet Studio introuvable")
        return 1
    tab = Tab(page["webSocketDebuggerUrl"])
    deadline = time.time() + int(sys.argv[1]) if len(sys.argv) > 1 else time.time() + 1500
    last = ""
    try:
        while time.time() < deadline:
            raw = tab.evaluate(JS_STATE)
            st = json.loads(raw) if raw else {}
            txt = " || ".join(st.get("visible", []))
            if txt != last:
                print(time.strftime("%H:%M:%S"), "->", txt[:300])
                last = txt
            if st.get("link") and "mise en ligne" in txt.lower():
                print("LIEN:", st["link"])
                tab.evaluate(JS_CLOSE_VISIBLE)
                return 0
            if not txt:
                print("plus aucune boîte visible (traitement terminé ?)")
                return 0
            time.sleep(15)
        print("délai dépassé")
        return 2
    finally:
        tab.close()


if __name__ == "__main__":
    sys.exit(main())
