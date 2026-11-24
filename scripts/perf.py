"""Mide el rendimiento de la web (docs/) con Playwright y Edge.

Sirve la carpeta con `python -m http.server`, abre la página en escritorio y en
celular (emulado, con la CPU limitada 4x) y mide:
  - tiempos de carga y del primer render del árbol;
  - número de nodos del DOM y del SVG;
  - tiempo entre fotogramas durante un zoom (rueda o pellizco) y un arrastre,
    con la vista completa y con la vista acercada (etiquetas visibles), y cuánto
    trabaja el hilo principal (script, estilo, layout);
  - errores de consola.

Uso:
  python -P scripts/perf.py [--docs docs] [--out perf.json] [--shots carpeta]
                            [--only desktop|mobile] [--check]

--shots guarda capturas (abanico, árbol, acercado, secciones) para comparar el aspecto.
--check además recorre las secciones, el buscador y la ficha, y falla si algo no funciona.
"""
import argparse, json, os, socket, statistics, subprocess, sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

# --------------------------------------------------------------------------- servidor
def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def start_server(docs, port):
    proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '-d', docs],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close(); return proc
        except OSError:
            time.sleep(0.1)
    proc.kill(); raise RuntimeError('el servidor no arrancó')

# --------------------------------------------------------------------------- página
INIT = r"""
(() => {
  const P = window.__perf = { firstRender: null, frames: [], recording: false, longTasks: [] };
  // primer render: el gráfico ya tiene contenido y pasaron dos fotogramas
  const check = () => {
    const c = document.querySelector('#chart');
    if (c && c.childElementCount > 0 && (c.querySelector('g g') || c.querySelector('canvas') || document.querySelector('#view-arbol canvas'))) {
      requestAnimationFrame(() => requestAnimationFrame(() => { P.firstRender = performance.now(); }));
    } else requestAnimationFrame(check);
  };
  requestAnimationFrame(check);
  const loop = t => { if (P.recording) P.frames.push(t); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  try {
    new PerformanceObserver(l => l.getEntries().forEach(e => P.recording && P.longTasks.push(e.duration)))
      .observe({ type: 'longtask', buffered: false });
  } catch (e) {}
})();
"""

def frame_stats(frames, wall_ms, long_tasks, metrics_delta):
    d = [b - a for a, b in zip(frames, frames[1:])]
    if not d:
        return {'fotogramas': 0}
    d.sort()
    p = lambda q: d[min(len(d) - 1, int(q * len(d)))]
    return {
        'fotogramas': len(d),
        'ms_medio': round(statistics.mean(d), 1),
        'ms_p50': round(p(0.5), 1),
        'ms_p95': round(p(0.95), 1),
        'ms_max': round(d[-1], 1),
        'pct_lentos_>33ms': round(100 * sum(x > 33.4 for x in d) / len(d), 1),
        'tareas_largas': len(long_tasks),
        'hilo_principal_ocupado_%': round(100 * metrics_delta.get('TaskDuration', 0) * 1000 / wall_ms, 1) if wall_ms else None,
        'script_ms': round(metrics_delta.get('ScriptDuration', 0) * 1000),
        'layout_ms': round(metrics_delta.get('LayoutDuration', 0) * 1000),
        'estilo_ms': round(metrics_delta.get('RecalcStyleDuration', 0) * 1000),
    }

def get_metrics(cdp):
    return {m['name']: m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}

def record(page, cdp, action):
    page.evaluate('() => { __perf.frames = []; __perf.longTasks = []; __perf.recording = true; }')
    m0 = get_metrics(cdp); t0 = time.perf_counter()
    action()
    page.wait_for_timeout(300)  # deja terminar los últimos fotogramas
    wall = (time.perf_counter() - t0) * 1000
    m1 = get_metrics(cdp)
    r = page.evaluate('() => { __perf.recording = false; return { f: __perf.frames, l: __perf.longTasks }; }')
    delta = {k: m1[k] - m0.get(k, 0) for k in m1 if isinstance(m1[k], (int, float))}
    return frame_stats(r['f'], wall, r['l'], delta)

STEP = 1 / 60  # un evento por fotograma

def paced(n, fn):
    t = time.perf_counter()
    for i in range(n):
        fn(i)
        t += STEP
        dt = t - time.perf_counter()
        if dt > 0:
            time.sleep(dt)

def chart_box(page):
    b = page.locator('#view-arbol').bounding_box()
    return b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, b

# ---- escritorio: rueda y ratón
def wheel_zoom(page, steps=24):
    cx, cy, _ = chart_box(page)
    page.mouse.move(cx, cy)
    paced(steps, lambda i: page.mouse.wheel(0, -100 if i < steps // 2 else 100))

def wheel_in(page, n):
    cx, cy, _ = chart_box(page)
    page.mouse.move(cx, cy)
    for _ in range(n):
        page.mouse.wheel(0, -100); page.wait_for_timeout(20)
    page.wait_for_timeout(400)

def mouse_drag(page, steps=60):
    cx, cy, _ = chart_box(page)
    page.mouse.move(cx, cy); page.mouse.down()
    paced(steps, lambda i: page.mouse.move(cx + 6 * (i if i < steps // 2 else steps - i), cy + 3 * (i if i < steps // 2 else steps - i)))
    page.mouse.up()

# ---- celular: eventos táctiles por CDP
def touch(cdp, kind, pts):
    cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})

def pinch(page, cdp, steps=40, spread=120):
    cx, cy, _ = chart_box(page)
    pos = lambda s: [(cx - 20 - s, cy), (cx + 20 + s, cy)]
    touch(cdp, 'touchStart', pos(0))
    half = steps // 2
    paced(steps, lambda i: touch(cdp, 'touchMove', pos(spread * (i if i < half else steps - i) / half)))
    touch(cdp, 'touchEnd', [])

def pinch_in(page, cdp, spread):
    cx, cy, _ = chart_box(page)
    pos = lambda s: [(cx - 20 - s, cy), (cx + 20 + s, cy)]
    touch(cdp, 'touchStart', pos(0))
    for i in range(1, 11):
        touch(cdp, 'touchMove', pos(spread * i / 10)); page.wait_for_timeout(16)
    touch(cdp, 'touchEnd', [])
    page.wait_for_timeout(400)

def touch_drag(page, cdp, steps=60):
    cx, cy, _ = chart_box(page)
    touch(cdp, 'touchStart', [(cx, cy)])
    paced(steps, lambda i: touch(cdp, 'touchMove', [(cx + 4 * (i if i < steps // 2 else steps - i), cy + 2 * (i if i < steps // 2 else steps - i))]))
    touch(cdp, 'touchEnd', [])

def zoom_k(page):
    # la escala es el producto de los transform del grupo, del <svg> y de su contenedor
    return page.evaluate("""() => { const c = document.querySelector('#chart'), g = document.querySelector('#chart > g');
      const t = [c.parentElement.style.transform, c.style.transform, g && g.getAttribute('transform')].join(' ');
      const m = [...t.matchAll(/scale\\(([\\d.e-]+)/g)]; return m.length ? +m.reduce((p, x) => p * +x[1], 1).toFixed(3) : null; }""")

def wait_still(page, timeout=8000):
    """Espera a que termine la animación del zoom (el transform deja de cambiar)."""
    page.evaluate("""(timeout) => new Promise(res => {
      const get = () => { const c = document.querySelector('#chart'), g = document.querySelector('#chart > g');
        return [c.parentElement.style.transform, c.style.transform, g && g.getAttribute('transform')].join('|'); };
      let last = get(), same = 0; const t0 = performance.now();
      const tick = () => { const now = get(); same = now === last ? same + 1 : 0; last = now;
        if (same >= 10 || performance.now() - t0 > timeout) res(); else requestAnimationFrame(tick); };
      requestAnimationFrame(tick); })""", timeout)

def counts(page):
    return page.evaluate("""() => ({
      dom_total: document.getElementsByTagName('*').length,
      svg_elementos: document.querySelectorAll('#chart *').length,
      svg_text: document.querySelectorAll('#chart text').length,
      svg_path: document.querySelectorAll('#chart path').length,
      svg_circle: document.querySelectorAll('#chart circle').length,
      canvas: document.querySelectorAll('#view-arbol canvas').length,
      heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576 * 10) / 10 : null,
    })""")

# --------------------------------------------------------------------------- escenarios
def measure_load(browser, ctx_opts, base, mobile, n=3):
    """Carga la página n veces (contexto nuevo, sin caché) y devuelve la mediana de cada tiempo."""
    runs = []
    for _ in range(n):
        ctx = browser.new_context(**ctx_opts)
        ctx.add_init_script(INIT)
        page = ctx.new_page()
        if mobile:
            ctx.new_cdp_session(page).send('Emulation.setCPUThrottlingRate', {'rate': 4})
        page.goto(base + '/index.html#/arbol', wait_until='load')
        page.wait_for_function('() => __perf.firstRender !== null', timeout=60000)
        runs.append(page.evaluate("""() => { const n = performance.getEntriesByType('navigation')[0];
          const r = performance.getEntriesByType('resource').find(e => e.name.includes('familia.json'));
          const fcp = performance.getEntriesByName('first-contentful-paint')[0];
          return { domcontentloaded_ms: n.domContentLoadedEventEnd, load_ms: n.loadEventEnd,
                   primer_pintado_ms: fcp ? fcp.startTime : null, primer_render_arbol_ms: __perf.firstRender,
                   familia_json_fin_ms: r ? r.responseEnd : null,
                   familia_json_kb: r ? (r.encodedBodySize || r.transferSize) / 1024 : null }; }"""))
        ctx.close()
    med = lambda k: round(statistics.median(r[k] for r in runs)) if runs[0][k] is not None else None
    return {k: med(k) for k in runs[0]} | {'cargas': n}

def run_profile(pw, browser, base, name, shots, check):
    mobile = name == 'mobile'
    ctx_opts = dict(pw.devices['Pixel 7']) if mobile else {'viewport': {'width': 1440, 'height': 900}}
    ctx_opts.pop('default_browser_type', None)
    out = {'perfil': name + (' (CPU 4x)' if mobile else '')}
    out['carga'] = measure_load(browser, ctx_opts, base, mobile)
    ctx = browser.new_context(**ctx_opts)
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('requestfailed', lambda r: errors.append(f'falló {r.url} ({r.failure})'))
    cdp = ctx.new_cdp_session(page)
    cdp.send('Performance.enable')
    if mobile:
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})

    page.goto(base + '/index.html#/arbol', wait_until='load')
    page.wait_for_function('() => __perf.firstRender !== null', timeout=60000)
    page.wait_for_timeout(2500)  # deja terminar el trabajo diferido de la carga
    out['nodos'] = counts(page)
    if shots: page.screenshot(path=os.path.join(shots, f'{name}-abanico.png'))

    def interactions(layout):
        res = {}
        page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
        res['k_inicial'] = zoom_k(page)
        if mobile:
            res['pellizco_vista_completa'] = record(page, cdp, lambda: pinch(page, cdp))
            page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
            res['arrastre_vista_completa'] = record(page, cdp, lambda: touch_drag(page, cdp))
            page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
            pinch_in(page, cdp, 150 if layout == 'radial' else 90)
        else:
            res['zoom_rueda_vista_completa'] = record(page, cdp, lambda: wheel_zoom(page))
            page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
            res['arrastre_vista_completa'] = record(page, cdp, lambda: mouse_drag(page))
            page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
            wheel_in(page, 7 if layout == 'radial' else 3)
        res['k_acercado'] = zoom_k(page)
        if shots: page.screenshot(path=os.path.join(shots, f'{name}-{layout}-acercado.png'))
        if mobile:
            res['arrastre_acercado'] = record(page, cdp, lambda: touch_drag(page, cdp))
            res['pellizco_acercado'] = record(page, cdp, lambda: pinch(page, cdp, spread=60))
        else:
            res['arrastre_acercado'] = record(page, cdp, lambda: mouse_drag(page))
            res['zoom_rueda_acercado'] = record(page, cdp, lambda: wheel_zoom(page, 16))
        return res

    out['abanico'] = interactions('radial')
    page.locator('.seg button[data-layout=tree]').click(); page.wait_for_timeout(1800)
    if shots:
        page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
        page.screenshot(path=os.path.join(shots, f'{name}-arbol.png'))
    out['arbol'] = interactions('tree')
    page.locator('.seg button[data-layout=radial]').click(); page.wait_for_timeout(1500)

    if check:
        out['comprobaciones'] = functional(page, mobile, shots, name)
    out['errores_consola'] = errors
    ctx.close()
    return out

def functional(page, mobile, shots, name):
    ok = {}
    # búsqueda: resultados, resaltado y centrar
    page.locator('#q').fill('Velasquez')
    page.wait_for_timeout(300)
    ok['busqueda_resultados'] = page.locator('#results button[data-id]').count()
    ok['busqueda_resalta'] = page.evaluate("() => document.querySelector('#chart').classList.contains('searching')")
    if shots: page.screenshot(path=os.path.join(shots, f'{name}-busqueda.png'))
    page.locator('#results button[data-id]').first.click()
    page.wait_for_timeout(1200)
    ok['ficha_abierta'] = page.locator('#panel').is_visible()
    ok['ficha_nombre'] = page.locator('#panelBody .p-name').inner_text() if ok['ficha_abierta'] else None
    ok['hash'] = page.evaluate('() => location.hash')
    ok['k_tras_centrar'] = zoom_k(page)
    if shots: page.screenshot(path=os.path.join(shots, f'{name}-ficha.png'))
    page.locator('#panelClose').click(); page.wait_for_timeout(300)
    # clic en una persona del gráfico
    ok['clic_persona'] = click_person(page)
    if page.locator('#panel').is_visible():
        page.locator('#panelClose').click(); page.wait_for_timeout(300)
    # leyenda
    page.locator('#legend button').nth(2).click(); page.wait_for_timeout(1200)
    ok['leyenda_abre_ficha'] = page.locator('#panel').is_visible()
    page.locator('#panelClose').click(); page.wait_for_timeout(300)
    # secciones
    for v in ['historia', 'personas', 'originales']:
        page.goto(page.url.split('#')[0] + '#/' + v); page.wait_for_timeout(700)
        ok['seccion_' + v] = page.locator('#view-' + v).is_visible() and page.locator(f'#view-{v} .wrap').count() > 0
        if shots: page.screenshot(path=os.path.join(shots, f'{name}-{v}.png'))
    page.goto(page.url.split('#')[0] + '#/personas'); page.wait_for_timeout(400)
    page.locator('#pq').fill('ruiz'); page.wait_for_timeout(300)
    ok['personas_filtro'] = page.locator('#pcount').inner_text()
    page.goto(page.url.split('#')[0] + '#/originales'); page.wait_for_timeout(400)
    page.locator('#view-originales .card').first.click(); page.wait_for_timeout(1500)
    ok['visor_cuadro'] = page.locator('#viewer').is_visible() and page.evaluate("() => document.querySelector('#viewerImg').naturalWidth > 0")
    page.keyboard.press('Escape'); page.wait_for_timeout(200)
    page.goto(page.url.split('#')[0] + '#/arbol'); page.wait_for_timeout(600)
    return ok

def click_person(page):
    """Hace clic sobre el punto de una persona visible y comprueba que se abre su ficha."""
    page.locator('#zfit').click(); page.wait_for_timeout(300); wait_still(page)
    cx, cy, b = chart_box(page)
    # acerca un poco y busca un punto en pantalla
    pt = page.evaluate("""(b) => {
      const els = [...document.querySelectorAll('#chart .node circle')];
      for (const c of els) { const r = c.getBoundingClientRect();
        const x = r.x + r.width / 2, y = r.y + r.height / 2;
        if (x > b.x + 80 && x < b.x + b.width - 80 && y > b.y + 80 && y < b.y + b.height - 160 && r.width > 2) return [x, y]; }
      return null; }""", b)
    if pt is None:  # sin nodos SVG (render en canvas): se prueba en una posición conocida
        pt = page.evaluate('() => window.__arbolPunto ? window.__arbolPunto() : null')
    if pt is None:
        return 'sin punto'
    page.mouse.click(pt[0], pt[1]); page.wait_for_timeout(500)
    return page.locator('#panel').is_visible()

# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--docs', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs'))
    ap.add_argument('--out')
    ap.add_argument('--shots')
    ap.add_argument('--only', choices=['desktop', 'mobile'])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--headed', action='store_true')
    a = ap.parse_args()
    if a.shots: os.makedirs(a.shots, exist_ok=True)
    port = free_port()
    srv = start_server(os.path.abspath(a.docs), port)
    res = []
    try:
        with sync_playwright() as pw:
            # sin vsync ni límite de fotogramas: en Edge sin ventana (Windows) el ritmo de los fotogramas depende
            # de cuándo se presenta una ventana invisible y las cifras salen erráticas; así el ritmo es estable
            # (unos 60 por segundo) y un fotograma lento se debe solo al trabajo de la página
            browser = pw.chromium.launch(channel='msedge', headless=not a.headed,
                                         args=['--disable-gpu-vsync', '--disable-frame-rate-limit'])
            for prof in ['desktop', 'mobile']:
                if a.only and a.only != prof: continue
                r = run_profile(pw, browser, f'http://127.0.0.1:{port}', prof, a.shots, a.check)
                res.append(r)
                print(json.dumps(r, ensure_ascii=False, indent=1))
            browser.close()
    finally:
        srv.terminate(); srv.wait()
    if a.out:
        json.dump(res, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    bad = [e for r in res for e in r['errores_consola']]
    if a.check:
        for r in res:
            c = r.get('comprobaciones', {})
            fails = [k for k, v in c.items() if v is False or v == 0 or v == 'sin punto']
            if fails: bad.append(f"{r['perfil']}: fallan {fails}")
    if bad:
        print('PROBLEMAS:', bad); sys.exit(1)

if __name__ == '__main__':
    main()
