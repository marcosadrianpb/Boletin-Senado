name: Fase 0 - Reconocimiento

on:
  workflow_dispatch:

jobs:
  recon:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar Playwright
        run: |
          pip install playwright==1.47.0
          playwright install --with-deps chromium

      - name: Reconocer el sitio
        continue-on-error: true
        run: |
          cat > recon.py <<'PY'
          import json, sys, traceback
          from datetime import date, timedelta
          from pathlib import Path
          from playwright.sync_api import sync_playwright

          BASE = sys.argv[1] if len(sys.argv) > 1 else "https://www.senado.gob.ar"
          OUT = Path("salida"); OUT.mkdir(exist_ok=True)
          PAGS = [("buscador", f"{BASE}/parlamentario/parlamentaria/"),
                  ("asuntos_entrados", f"{BASE}/parlamentario/sesiones/asuntosEnt")]
          BLOQ = ["cloudflare", "captcha", "recaptcha", "Just a moment", "Access Denied", "incapsula"]

          INV = """() => {
            const t = e => (e?.innerText||'').trim().slice(0,150);
            return {
              titulo: document.title,
              campos: [...document.querySelectorAll('input,select')].map(c=>({
                tag:c.tagName.toLowerCase(), type:c.getAttribute('type')||'',
                name:c.getAttribute('name')||'', id:c.id||'',
                ph:c.getAttribute('placeholder')||'', visible:!!(c.offsetWidth||c.offsetHeight),
                opciones:c.options?[...c.options].slice(0,25).map(o=>o.value+'|'+o.text.trim()):null})),
              forms: [...document.querySelectorAll('form')].map(f=>({
                id:f.id||'', action:f.getAttribute('action')||'',
                method:(f.getAttribute('method')||'GET').toUpperCase()})),
              tablas: [...document.querySelectorAll('table')].map(x=>({
                id:x.id||'', clase:x.className||'',
                cols:[...x.querySelectorAll('th')].map(t2=>t(t2)).slice(0,25),
                filas:x.querySelectorAll('tr').length,
                fila1:[...(x.querySelectorAll('tbody tr')[0]?.querySelectorAll('td')||[])].map(td=>t(td))})),
              exportar: [...document.querySelectorAll('a,button')].filter(e=>
                /datos abiertos|excel|xlsx|csv|json|descargar|export/i.test(t(e)+' '+(e.getAttribute('href')||''))
                ).slice(0,25).map(e=>({txt:t(e), href:e.getAttribute('href')||'',
                onclick:(e.getAttribute('onclick')||'').slice(0,150)})),
              botones: [...document.querySelectorAll('button,input[type=submit],a.btn')].slice(0,30)
                .map(b=>({txt:t(b)||b.getAttribute('value')||'', id:b.id||'', tag:b.tagName.toLowerCase()}))
            }}"""

          D = {"paginas": [], "ip": {}}


          def espia(page, bolsa):
              def f(r):
                  try:
                      if r.request.resource_type in ("document", "xhr", "fetch"):
                          bolsa.append({"m": r.request.method, "url": r.url[:350], "st": r.status,
                                        "tipo": r.headers.get("content-type", "")[:60],
                                        "post": (r.request.post_data or "")[:500] or None})
                  except Exception:
                      pass
              page.on("response", f)


          with sync_playwright() as pw:
              br = pw.chromium.launch()
              ctx = br.new_context(locale="es-AR", timezone_id="America/Argentina/Buenos_Aires",
                                   viewport={"width": 1440, "height": 1000},
                                   user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                              "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
              ctx.set_default_timeout(45000)

              try:
                  p = ctx.new_page(); p.goto("https://ipapi.co/json/", timeout=25000)
                  i = json.loads(p.inner_text("body"))
                  D["ip"] = {"ip": i.get("ip"), "pais": i.get("country_name"), "org": i.get("org")}
                  p.close()
              except Exception as e:
                  D["ip"] = {"error": str(e)[:150]}
              print("IP:", D["ip"], flush=True)

              for nom, url in PAGS:
                  r = {"nombre": nom, "url": url}
                  pg = ctx.new_page(); red = []; espia(pg, red)
                  try:
                      resp = pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                      r["http"] = resp.status if resp else None
                      r["url_final"] = pg.url
                      r["redirigio"] = pg.url.rstrip("/") != url.rstrip("/")
                      pg.wait_for_timeout(3000)
                      h = pg.content()
                      (OUT / f"{nom}.html").write_text(h, encoding="utf-8")
                      r["bloqueo"] = [b for b in BLOQ if b.lower() in h.lower()]
                      pg.screenshot(path=str(OUT / f"{nom}.png"), full_page=True)
                      r["inv"] = pg.evaluate(INV)
                  except Exception as e:
                      r["error"] = f"{type(e).__name__}: {e}"[:300]
                      r["traza"] = traceback.format_exc()[-600:]
                      print("ERROR", nom, r["error"], flush=True)
                  r["red"] = red[:40]
                  D["paginas"].append(r)
                  pg.close()

              # Intento de busqueda por rango de fechas
              b = {"pasos": []}
              pg = ctx.new_page(); red = []; espia(pg, red)
              try:
                  pg.goto(PAGS[0][1], wait_until="domcontentloaded", timeout=60000)
                  pg.wait_for_timeout(3000)
                  hasta = date.today(); desde = hasta - timedelta(days=30)
                  cs = pg.evaluate("""() => [...document.querySelectorAll('input')].map(c=>({
                      name:c.getAttribute('name')||'', id:c.id||'', type:c.getAttribute('type')||'',
                      ph:c.getAttribute('placeholder')||'', vis:!!(c.offsetWidth||c.offsetHeight)}))""")
                  b["inputs"] = cs

                  def hallar(pista):
                      for c in cs:
                          if pista in (c["name"] + c["id"] + c["ph"]).lower() and c["vis"]:
                              return c
                      return None

                  for pista, val in (("desde", desde), ("hasta", hasta)):
                      c = hallar(pista)
                      b["campo_" + pista] = c
                      if c:
                          sel = f"#{c['id']}" if c["id"] else f"input[name='{c['name']}']"
                          v = val.isoformat() if c["type"] == "date" else val.strftime("%d/%m/%Y")
                          try:
                              pg.fill(sel, v); b["pasos"].append(f"ok {sel} = {v}")
                          except Exception as e:
                              b["pasos"].append(f"fallo {sel}: {str(e)[:100]}")

                  pg.screenshot(path=str(OUT / "busqueda_antes.png"), full_page=True)
                  for sel in ["button:has-text('Buscar')", "input[value='Buscar']",
                              "a:has-text('Buscar')", "button[type=submit]", "input[type=submit]"]:
                      try:
                          el = pg.locator(sel).first
                          if el.count() and el.is_visible():
                              el.click(timeout=10000)
                              b["pasos"].append("click " + sel)
                              b["disparo"] = True
                              break
                      except Exception as e:
                          b["pasos"].append(f"fallo click {sel}: {str(e)[:80]}")
                  pg.wait_for_timeout(6000)
                  b["url_result"] = pg.url
                  (OUT / "resultados.html").write_text(pg.content(), encoding="utf-8")
                  pg.screenshot(path=str(OUT / "busqueda_despues.png"), full_page=True)
                  b["inv"] = pg.evaluate(INV)
                  b["texto"] = pg.inner_text("body")[:3500]
              except Exception as e:
                  b["error"] = f"{type(e).__name__}: {e}"[:300]
                  b["traza"] = traceback.format_exc()[-600:]
                  print("ERROR busqueda", b["error"], flush=True)
              b["red"] = red[:50]
              D["busqueda"] = b
              br.close()

          (OUT / "inventario.json").write_text(json.dumps(D, indent=1, ensure_ascii=False), encoding="utf-8")

          # ---- Informe legible ----
          L = ["# Fase 0 - Reconocimiento", "",
               f"**IP saliente:** {D['ip'].get('ip','?')} ({D['ip'].get('pais','?')} / {D['ip'].get('org','?')})", "",
               "| Pagina | HTTP | Redirigio | Campos | Tablas | Exportar | Bloqueo |", "|---|---|---|---|---|---|---|"]
          for p in D["paginas"]:
              v = p.get("inv") or {}
              L.append(f"| {p['nombre']} | {p.get('http','ERROR')} | {'si' if p.get('redirigio') else 'no'} "
                       f"| {len(v.get('campos',[]))} | {len(v.get('tablas',[]))} "
                       f"| {len(v.get('exportar',[]))} | {','.join(p.get('bloqueo',[])) or '-'} |")
              if p.get("error"):
                  L.append(f"\n**Error en {p['nombre']}:** `{p['error']}`\n")

          bb = D["busqueda"]
          L += ["", "## Busqueda por fechas", "",
                f"- Disparada: **{bb.get('disparo', False)}**",
                f"- URL resultados: `{bb.get('url_result','-')}`",
                f"- Campo desde: `{bb.get('campo_desde')}`",
                f"- Campo hasta: `{bb.get('campo_hasta')}`", ""]
          if bb.get("error"):
              L.append(f"**Error:** `{bb['error']}`\n")
          L += ["Pasos:"] + [f"- {x}" for x in bb.get("pasos", [])]

          vt = bb.get("inv", {}).get("tablas", [])
          if vt:
              L += ["", "## Columnas de la tabla de resultados", ""]
              for t in vt[:4]:
                  L.append(f"- `{t.get('id') or t.get('clase')}` ({t.get('filas')} filas): "
                           f"{' | '.join(t.get('cols', []))}")
                  if t.get("fila1"):
                      L.append(f"  - ejemplo: {' | '.join(t['fila1'])[:300]}")

          L += ["", "## Peticiones POST / JSON detectadas", ""]
          vistos = set()
          for p in D["paginas"] + [bb]:
              for q in p.get("red", []):
                  k = (q["m"], q["url"])
                  if k in vistos:
                      continue
                  vistos.add(k)
                  if q["m"] == "POST" or "json" in (q.get("tipo") or ""):
                      L.append(f"- `{q['m']} {q['url']}` -> {q['st']} ({q.get('tipo')})")
                      if q.get("post"):
                          L.append(f"  - envia: `{q['post'][:250]}`")
          if len(L) and L[-1].endswith("detectadas"):
              L.append("_ninguna_")

          inf = "\n".join(L)
          Path("INFORME.md").write_text(inf, encoding="utf-8")
          (OUT / "INFORME.md").write_text(inf, encoding="utf-8")
          print(inf)

          PY
          python recon.py

      - name: Mostrar informe
        if: always()
        run: cat INFORME.md >> "$GITHUB_STEP_SUMMARY" || echo "sin informe" >> "$GITHUB_STEP_SUMMARY"

      - name: Subir resultados
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: reconocimiento
          path: salida/
          if-no-files-found: warn
