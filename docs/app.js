/* Genealogía Álvarez del Pino — árbol interactivo */
(() => {
'use strict';
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const LCOL = ['#1f6f78', '#a23b48', '#b07a12', '#4d5fa3', '#3f7d3a', '#8a4f9e'];
const INK = '#2a2622';
const isMobile = () => matchMedia('(max-width: 760px)').matches;

let D, P = {}, ROOT, MANUEL, TERESA, H, LINES, TREE = {}, INV = null, HZ = {};
const color = p => (p && p.line >= 0 ? LCOL[p.line] : INK);

/* ---------------- relaciones ---------------- */
const ORD = ['', '', '', '', 'cuarto', 'quinto', 'sexto', 'séptimo', 'octavo', 'noveno', 'décimo', 'undécimo',
  'duodécimo', 'decimotercer', 'decimocuarto', 'decimoquinto', 'decimosexto', 'decimoséptimo', 'decimoctavo'];
const ordFem = (w, f) => (!f ? w : w.endsWith('o') ? w.slice(0, -1) + 'a' : w.endsWith('er') ? w + 'a' : w.replace('.º', '.ª'));
function relWord(g, f, m) {
  const o = (a, b) => (f ? b : m ? a : a + '/' + b.slice(-1));
  return g === 1 ? o('Padre', 'Madre') : g === 2 ? o('Abuelo', 'Abuela') : g === 3 ? o('Bisabuelo', 'Bisabuela')
    : g === 4 ? o('Tatarabuelo', 'Tatarabuela') : ordFem(ORD[g - 1] || `${g - 1}.º`, f).replace(/^./, c => c.toUpperCase()) + ' ' + o('abuelo', 'abuela');
}
function rel(p) {
  const f = p.sex === 'F', m = p.sex === 'M';
  if (p.id === ROOT) return 'Los once hijos de Manuel Salvador Álvarez Ruiz y María Teresa Ruiz Maya';
  if (p.id === MANUEL) return 'Padre · esposo de María Teresa Ruiz Maya';
  if (p.id === TERESA) return 'Madre · esposa de Manuel Salvador Álvarez Ruiz';
  if (p.sibling) return (f ? 'Hermana' : 'Hermano') + ' de Manuel Salvador';
  if (p.child) return (f ? 'Hija' : 'Hijo') + ' de Manuel Salvador y María Teresa';
  const parts = [];
  if (p.genM != null) parts.push(relWord(p.genM, f, m) + ' de Manuel Salvador');
  if (p.genT != null) parts.push((parts.length ? relWord(p.genT, f, m).toLowerCase() : relWord(p.genT, f, m)) + ' de María Teresa');
  if (!parts.length && p.gen != null) parts.push(relWord(p.gen, f, m) + ' de los hijos');
  return parts.length ? parts.join(' y ') : 'Persona de los cuadros (sin enlace directo)';
}
const genTitle = g => g === 1 ? 'Padres' : g === 2 ? 'Abuelos' : g === 3 ? 'Bisabuelos' : g === 4 ? 'Tatarabuelos'
  : (ORD[g - 1] || `${g - 1}.º`).replace(/^./, c => c.toUpperCase()) + 's abuelos';
const meta = p => [p.year, p.place].filter(Boolean).join(' · ');

/* ---------------- carga ---------------- */
fetch('data/familia.json').then(r => r.json()).then(init).catch(err => {
  document.body.insertAdjacentHTML('beforeend', `<p style="position:fixed;top:80px;left:20px">No se pudieron cargar los datos (${esc(err.message)}). Si abriste el archivo directamente, usa un servidor web o GitHub Pages.</p>`);
});

function init(data) {
  D = data; H = data.historia; ROOT = data.root; MANUEL = data.manuel; TERESA = data.teresa; LINES = data.lines;
  data.trees.forEach(t => { TREE[t.n] = t; });
  INV = data.investigacion || null;
  if (INV) INV.hallazgos.forEach(h => { HZ[h.id] = h; });
  data.people.forEach(p => { P[p.id] = p; p._n = norm([p.name, ...(p.variants || [])].join(' | ')); });
  buildChart();
  buildLegend();
  setupSearch();
  setupViewer();
  $('#panelClose').onclick = closePanel;
  addEventListener('keydown', e => { if (e.key === 'Escape') { if (!$('#viewer').hidden) closeViewer(); else closePanel(); } });
  addEventListener('hashchange', route);
  route();
}

/* ---------------- rutas ---------------- */
const rendered = {};
function show(view) {
  $$('.view').forEach(v => (v.hidden = v.id !== 'view-' + view));
  $$('.tabs a').forEach(a => a.classList.toggle('on', a.dataset.view === view));
  if (!rendered[view]) { rendered[view] = true; ({ historia: renderHistoria, personas: renderPersonas, originales: renderOriginales, investigacion: renderInvestigacion })[view]?.(); }
}
function route() {
  const h = location.hash.replace(/^#\/?/, '').split('/');
  const v = h[0] || 'arbol';
  if (v === 'persona' && P[h[1]]) { show('arbol'); openPanel(h[1], false); focusNode(h[1]); return; }
  closePanel(true);
  if (['arbol', 'historia', 'personas', 'originales', 'investigacion'].includes(v)) show(v); else show('arbol');
  if (v === 'investigacion' && h[1]) setTimeout(() => document.getElementById('inv-' + h[1])?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
  if (v === 'historia' && h[1]) setTimeout(() => document.getElementById(h[1])?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
}

/* ---------------- gráfico ---------------- */
let svg, gRoot, zoom, nodesSel, linksSel, hier, layout = 'radial', nodeIndex = new Map();
function buildHierarchy() {
  const seen = new Set([ROOT]);
  const root = { pid: ROOT, children: [] };
  let frontier = [root];
  while (frontier.length) {
    const next = [];
    for (const n of frontier) {
      const p = P[n.pid];
      for (const k of ['father', 'mother']) {
        const q = p[k];
        if (!q || !P[q]) continue;
        if (seen.has(q)) n.children.push({ pid: q, stub: true, children: [] });
        else { seen.add(q); const c = { pid: q, children: [] }; n.children.push(c); next.push(c); }
      }
    }
    frontier = next;
  }
  return d3.hierarchy(root, n => (n.children.length ? n.children : null));
}

function computeLayouts() {
  // abanico
  const R = 250;
  d3.tree().size([2 * Math.PI, hier.height * R])
    .separation((a, b) => (a.parent === b.parent ? 1 : 1.35) / Math.max(1, a.depth))(hier);
  hier.each(d => {
    const a = d.x - Math.PI / 2, r = RR(d.depth);
    d.rad = { x: r * Math.cos(a), y: r * Math.sin(a), ang: d.x, r };
  });
  // árbol horizontal
  d3.tree().nodeSize([24, 280]).separation((a, b) => (a.parent === b.parent ? 1 : 1.3))(hier);
  hier.each(d => { d.tre = { x: d.y, y: d.x }; });
}
const pos = d => (layout === 'radial' ? d.rad : d.tre);
// los anillos más lejanos (linajes medievales, con pocas personas) se acercan para no alejar el resto
function RR(d) { return d <= 13 ? d * 250 : 13 * 250 + (d - 13) * 120; }

function labelTransform(d) {
  if (layout === 'tree') return d.depth === 0 ? 'translate(-14,0)' : 'translate(9,0)';
  if (d.depth === 0) return 'translate(0,30)';
  const deg = d.rad.ang * 180 / Math.PI;
  return deg > 180 ? 'rotate(' + (deg + 90) + ') translate(-9,0)' : 'rotate(' + (deg - 90) + ') translate(9,0)';
}
function labelAnchor(d) {
  if (layout === 'tree') return d.depth === 0 ? 'end' : 'start';
  if (d.depth === 0) return 'middle';
  return d.rad.ang > Math.PI ? 'end' : 'start';
}

function buildChart() {
  hier = buildHierarchy();
  computeLayouts();
  svg = d3.select('#chart');
  gRoot = svg.append('g');
  const rings = gRoot.append('g').attr('class', 'rings');
  linksSel = gRoot.append('g').selectAll('path').data(hier.links()).join('path')
    .attr('class', 'link').attr('stroke', d => color(P[d.target.data.pid]));
  nodesSel = gRoot.append('g').selectAll('g').data(hier.descendants()).join('g')
    .attr('class', d => {
      const p = P[d.data.pid];
      return 'node' + (d.data.stub ? ' stub' : '') + (p.invAdded ? ' added' : '') + (p.bio && !d.data.stub ? ' bio' : '') + (d.depth === 0 ? ' root big' : d.depth <= 2 ? ' big' : '');
    })
    .on('click', (e, d) => { e.stopPropagation(); const id = d.data.pid; if (d.data.stub) focusNode(id); openPanel(id); });
  nodesSel.append('circle').attr('r', d => (d.depth === 0 ? 10 : d.depth <= 2 ? 7 : 5)).attr('fill', d => color(P[d.data.pid]));
  const t = nodesSel.append('text').attr('dy', '0.33em');
  t.append('tspan').text(d => (d.data.stub ? '↺ ' : '') + short(P[d.data.pid].name, d.depth === 0 ? 60 : 38));
  t.filter(d => !d.data.stub && P[d.data.pid].year && d.depth > 0).append('tspan').attr('class', 'yr').text(d => '  ' + P[d.data.pid].year);
  hier.descendants().forEach(d => { if (!d.data.stub) nodeIndex.set(d.data.pid, d); });

  // anillos de generaciones (solo abanico)
  const maxD = hier.height;
  const ringData = d3.range(1, maxD + 1);
  rings.selectAll('circle').data(ringData).join('circle').attr('class', 'ring').attr('r', RR);
  rings.selectAll('text').data(ringData.filter(d => d <= 13)).join('text').attr('class', 'ringlbl').attr('text-anchor', 'middle')
    .attr('y', d => -(RR(d) + RR(d - 1)) / 2).text(d => genTitle(d));

  let lastS = 1;
  const baseR = d => (d.depth === 0 ? 10 : d.depth <= 2 ? 7 : 5);
  zoom = d3.zoom().scaleExtent([0.025, 4]).on('zoom', e => {
    const k = e.transform.k;
    gRoot.attr('transform', e.transform);
    svg.classed('nolabels', k < 0.3);
    // los puntos mantienen un tamaño visible al alejarse
    const s = k < 0.6 ? Math.round(Math.min(6, 0.6 / k) * 4) / 4 : 1;
    if (s !== lastS) { lastS = s; nodesSel.select('circle').attr('r', d => baseR(d) * s); }
  });
  svg.call(zoom).on('dblclick.zoom', null);
  svg.on('click', () => { if (!isMobile()) return; });
  applyLayout(false);
  fit(false);
  setTimeout(() => $('#hint').classList.add('gone'), 6000);
  svg.on('pointerdown.hint', () => $('#hint').classList.add('gone'));

  $$('.seg button').forEach(b => b.onclick = () => {
    layout = b.dataset.layout;
    $$('.seg button').forEach(x => x.classList.toggle('on', x === b));
    applyLayout(true);
    setTimeout(() => (selected ? focusNode(selected, true) : fit(true)), 50);
  });
  $('#zin').onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 1.5);
  $('#zout').onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 1 / 1.5);
  $('#zfit').onclick = () => fit(true);
  addEventListener('resize', () => {});
}
const short = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

function applyLayout(animate) {
  const tr = sel => (animate ? sel.transition().duration(750).ease(d3.easeCubicInOut) : sel);
  const linkGen = layout === 'radial'
    ? d3.linkRadial().angle(d => d.rad.ang).radius(d => d.rad.r)
    : d3.linkHorizontal().x(d => d.tre.x).y(d => d.tre.y);
  tr(linksSel).attr('d', linkGen);
  tr(nodesSel).attr('transform', d => `translate(${pos(d).x},${pos(d).y})`);
  tr(nodesSel.select('text')).attr('transform', labelTransform).attr('text-anchor', labelAnchor);
  gRoot.select('.rings').style('display', layout === 'radial' ? null : 'none');
}

function fit(animate) {
  const el = svg.node(), w = el.clientWidth, h = el.clientHeight;
  if (!w || !h) return;
  // se encuadra la parte central (hasta 13 generaciones); el resto se ve al alejar
  const pts = hier.descendants().filter(d => layout !== 'radial' || d.depth <= 13).map(pos);
  const x0 = d3.min(pts, p => p.x) - 120, x1 = d3.max(pts, p => p.x) + 120, y0 = d3.min(pts, p => p.y) - 60, y1 = d3.max(pts, p => p.y) + 60;
  const b = { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  const pad = 30;
  const k = Math.min((w - pad * 2) / b.width, (h - pad * 2) / b.height, 1.2);
  const t = d3.zoomIdentity.translate(w / 2 - (b.x + b.width / 2) * k, h / 2 - (b.y + b.height / 2) * k).scale(k);
  (animate ? svg.transition().duration(700) : svg).call(zoom.transform, t);
}

let selected = null;
function focusNode(pid, keepScale) {
  const d = nodeIndex.get(pid);
  if (!d || !svg) return;
  const el = svg.node(), w = el.clientWidth, h = el.clientHeight;
  const cur = d3.zoomTransform(el);
  const k = keepScale ? cur.k : Math.max(cur.k, layout === 'radial' ? 1.3 : 1.15);
  const p = pos(d);
  const cx = isMobile() ? w / 2 : (w - ($('#panel').hidden ? 0 : 420)) / 2;
  const cy = isMobile() ? h * 0.24 : h / 2;
  svg.transition().duration(800).ease(d3.easeCubicInOut)
    .call(zoom.transform, d3.zoomIdentity.translate(cx - p.x * k, cy - p.y * k).scale(k));
  markSelected(pid);
  gRoot.selectAll('.pulse').remove();
  gRoot.append('circle').attr('class', 'pulse').attr('cx', p.x).attr('cy', p.y).attr('r', 6);
}
function markSelected(pid) {
  selected = pid;
  nodesSel.classed('sel', d => d.data.pid === pid && !d.data.stub);
}

function buildLegend() {
  const el = $('#legend');
  el.innerHTML = `<span class="t">Líneas</span>` +
    LINES.map((n, i) => `<button data-l="${i}"><i class="dot" style="background:${LCOL[i]}"></i>${esc(n)}</button>`).join('') +
    `<span><i class="bioring"></i>Con historia</span><span><i class="stubring"></i>Repetido</span>`;
  $$('button', el).forEach(b => b.onclick = () => {
    const l = +b.dataset.l;
    // ir al abuelo/abuela de esa línea
    const gp = D.lineRoots[l];
    focusNode(gp); openPanel(gp);
  });
}

/* ---------------- búsqueda ---------------- */
function searchPeople(q, limit = 40) {
  const nq = norm(q).trim();
  if (nq.length < 2) return [];
  const toks = nq.split(/\s+/);
  const out = [];
  for (const p of D.people) {
    if (!toks.every(t => p._n.includes(t))) continue;
    let s = 0;
    if (norm(p.name).startsWith(nq)) s -= 3;
    if (p._n.includes(nq)) s -= 2;
    s += (p.gen ?? 20) / 20;
    out.push([s, p]);
  }
  return out.sort((a, b) => a[0] - b[0]).slice(0, limit).map(x => x[1]);
}
function setupSearch() {
  const q = $('#q'), box = $('#results');
  let active = -1, items = [];
  const render = () => {
    items = searchPeople(q.value);
    highlight(q.value);
    if (q.value.trim().length < 2) { box.hidden = true; return; }
    box.hidden = false;
    box.innerHTML = items.length ? items.map((p, i) =>
      `<button role="option" data-id="${p.id}" class="${i === active ? 'active' : ''}"><i class="dot" style="background:${color(p)}"></i><span class="r-text"><span class="r-name">${esc(p.name)}</span><span class="r-meta">${esc(rel(p))}${meta(p) ? ' · ' + esc(meta(p)) : ''}</span></span></button>`).join('')
      : `<div class="empty">No se encontró «${esc(q.value)}».</div>`;
  };
  q.addEventListener('input', () => { active = -1; render(); });
  q.addEventListener('focus', render);
  q.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown') { active = Math.min(items.length - 1, active + 1); render(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); render(); e.preventDefault(); }
    else if (e.key === 'Enter' && items.length) { choose(items[Math.max(0, active)].id); }
  });
  box.addEventListener('click', e => { const b = e.target.closest('button[data-id]'); if (b) choose(b.dataset.id); });
  document.addEventListener('click', e => { if (!e.target.closest('.search')) box.hidden = true; });
  function choose(id) {
    box.hidden = true; q.blur(); q.value = ''; highlight('');
    goPerson(id);
  }
}
function highlight(qs) {
  if (!svg) return;
  const hits = new Set(searchPeople(qs, 1000).map(p => p.id));
  svg.classed('searching', hits.size > 0);
  nodesSel.classed('hit', d => hits.has(d.data.pid));
}
function goPerson(id) {
  if (location.hash.replace(/^#\/?/, '').split('/')[0] !== 'arbol') { history.pushState(null, '', '#/arbol'); show('arbol'); }
  openPanel(id);
  setTimeout(() => focusNode(id), 30);
}

/* ---------------- panel ---------------- */
function personLink(id, extra = '') {
  const p = P[id]; if (!p) return '';
  return `<button class="plink" data-go="${id}"><i class="dot" style="background:${color(p)}"></i><span class="r-text"><span class="r-name">${esc(p.name)}</span>${extra ? `<span class="r-meta" style="margin:0;text-align:left">${esc(extra)}</span>` : ''}</span><span class="r-meta">${esc(p.year || '')}</span></button>`;
}
function openPanel(id, updateHash = true) {
  const p = P[id]; if (!p) return;
  const panel = $('#panel'), body = $('#panelBody');
  const lineName = p.line >= 0 ? 'Línea ' + LINES[p.line] : p.id === ROOT || p.child ? 'Los hijos' : p.line === -3 ? 'Línea directa de María Teresa' : 'Línea directa de Manuel Salvador';
  let html = `<span class="p-line"><i class="dot" style="background:${color(p)}"></i>${esc(lineName)}${p.gen > 0 ? ' · Generación ' + p.gen : ''}</span>
    <h2 class="p-name">${esc(p.name)}</h2><p class="p-rel">${esc(rel(p))}</p><div class="p-facts">`;
  if (p.both) html += `<span class="chip both" title="Aparece en la ascendencia de los dos">Antepasado de ambos</span>`;
  if (p.born) html += `<span class="chip">Nació el ${esc(p.born)}</span>`;
  else if (p.year) html += `<span class="chip">${esc(p.year)}</span>`;
  if (p.place) html += `<span class="chip">${esc(p.place)}</span>`;
  if (p.nick) html += `<span class="chip">«${esc(p.nick)}»</span>`;
  if (p.conq) html += `<span class="chip">Conquistador</span>`;
  if (p.invAdded) html += `<span class="chip inv-added" title="Esta persona no está en los cuadros originales: la añadió la investigación">Añadida por la investigación</span>`;
  else if (p.inv) html += `<a class="chip inv-chip" href="#inv-sec" data-scroll="inv-sec">Investigación (${p.inv.length})</a>`;
  html += `</div>`;
  if (p.note) html += `<p>${esc(p.note)}.</p>`;
  const raws = [...new Map((p.raw || []).filter(r => !/^[X?\s.]*$/.test(r)).map(r => [r.replace(/[\s.\-]/g, ''), r])).values()];
  if (raws.length)
    html += `<p class="note">Dato en los cuadros: ${esc(raws.join(' / '))}. En los cuadros originales no siempre se indica si el año es de nacimiento o de muerte.</p>`;
  html += origNote(p);

  if (p.bio) {
    const s = H.linaje.find(x => x.n === p.bio);
    html += `<div class="p-sec p-bio"><h4>Historia</h4>`;
    if (s.subtitulo) html += `<p><i>${esc(s.subtitulo)}</i></p>`;
    if (s.parrafos[0]) html += `<p>${esc(s.parrafos[0])}</p>`;
    if (s.fotos) html += `<div class="p-photos">${s.fotos.map(f => `<img src="img/${f}" alt="${esc(H.fotos[f] || '')}" data-photo="${f}" loading="lazy">`).join('')}</div>`;
    html += `<p><a class="more" href="#/historia/gen-${s.n}">Leer la historia completa →</a></p></div>`;
  }
  const par = [p.father, p.mother].filter(Boolean);
  if (par.length) html += `<div class="p-sec"><h4>Padres</h4>${par.map(x => personLink(x)).join('')}</div>`;
  const sp = (p.spouses || []).filter(x => P[x]);
  if (sp.length || p.spouseName) html += `<div class="p-sec"><h4>${sp.length > 1 ? 'Cónyuges' : 'Cónyuge'}</h4>${sp.map(x => personLink(x)).join('')}${p.spouseName ? `<div class="plain">${esc(p.spouseName)}</div>` : ''}</div>`;
  const kids = (p.children || []).filter(x => P[x]);
  if (kids.length) {
    const sorted = kids.slice().sort((a, b) => (P[a].year || '9999').localeCompare(P[b].year || '9999'));
    html += `<div class="p-sec"><h4>${p.id === ROOT ? 'Los hijos' : p.id === MANUEL || p.id === TERESA ? 'Hijos' : 'Hijos en este árbol'}</h4>${sorted.map(x => personLink(x, P[x].born ? 'Nació el ' + P[x].born : '')).join('')}</div>`;
  }
  const sibs = new Set();
  if (id !== ROOT) for (const k of ['father', 'mother']) if (p[k] && P[p[k]]) (P[p[k]].children || []).forEach(c => c !== id && sibs.add(c));
  if (sibs.size) html += `<div class="p-sec"><h4>Hermanos</h4>${[...sibs].map(x => personLink(x)).join('')}</div>`;
  if (p.inv && p.inv.length) html += invSection(p);
  if (p.trees && p.trees.length) html += `<div class="p-sec"><h4>Aparece en los cuadros originales</h4><div class="p-facts">${p.trees.map(t => `<button class="chip btn" data-tree="${t}">${esc(treeName(t))}</button>`).join('')}</div></div>`;
  if (p.variants && p.variants.length) html += `<div class="p-sec"><h4>También escrito como</h4><p class="note">${p.variants.map(esc).join(' · ')}</p></div>`;
  html += `<div class="p-actions">${nodeIndex.has(id) ? `<button class="btn-primary" data-focus="${id}">Ver en el gráfico</button>` : ''}<button class="btn-ghost" data-copy="${id}">Copiar enlace</button></div>`;
  body.innerHTML = html;
  body.scrollTop = 0;
  panel.hidden = false;
  document.body.classList.add('panel-open');
  if (nodeIndex.has(id)) markSelected(id);
  if (updateHash) history.replaceState(null, '', '#/persona/' + id);
  body.onclick = e => {
    const go = e.target.closest('[data-go]'); if (go) { const gid = go.dataset.go; openPanel(gid); if (!$('#view-arbol').hidden) focusNode(gid); return; }
    const tr = e.target.closest('[data-tree]'); if (tr) { openTree(+tr.dataset.tree); return; }
    const im = e.target.closest('[data-img]'); if (im) { e.preventDefault(); openImage(im.dataset.img, im.dataset.title || ''); return; }
    const sc = e.target.closest('[data-scroll]'); if (sc) { e.preventDefault(); document.getElementById(sc.dataset.scroll)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    const f = e.target.closest('[data-focus]'); if (f) { if ($('#view-arbol').hidden) { history.pushState(null, '', '#/persona/' + f.dataset.focus); show('arbol'); } focusNode(f.dataset.focus); if (isMobile()) closePanel(true); return; }
    const ph = e.target.closest('[data-photo]'); if (ph) { openImage('img/' + ph.dataset.photo, H.fotos[ph.dataset.photo] || ''); return; }
    const c = e.target.closest('[data-copy]'); if (c) { navigator.clipboard?.writeText(location.href.split('#')[0] + '#/persona/' + c.dataset.copy); c.textContent = '¡Copiado!'; }
  };
}
/* ---------------- investigación ---------------- */
const CLAS = { 'CONFIRMADO': 'ok', 'PROBABLE': 'prob', 'EN CONFLICTO': 'conf' };
const TIPO = { extraccion: 'Corrección de la extracción', correccion: 'Corrección', verificacion: 'Verificación', adicion: 'Adición', contexto: 'Contexto', duda: 'Duda' };
const FIELD = { year: 'Año', place: 'Lugar', name: 'Nombre', father: 'Padre', mother: 'Madre', spouses: 'Cónyuges' };
function srcLink(k) {
  const f = INV.fuentes[k]; if (!f) return '';
  const orig = f.tipo === 'documento original';
  if (f.u.startsWith('arboles/')) return `<li class="src orig"><a href="${esc(f.u)}" data-img="${esc(f.u)}" data-title="${esc(f.t)}">${esc(f.t)}</a></li>`;
  if (f.u.startsWith('#')) return `<li class="src orig"><a href="${esc(f.u)}">${esc(f.t)}</a></li>`;
  return `<li class="src${orig ? ' orig' : ''}"><a href="${esc(f.u)}" target="_blank" rel="noopener">${esc(f.t)}</a> <span class="src-t">${esc(f.tipo)}</span></li>`;
}
function badge(h) { return `<span class="inv-badge ${CLAS[h.c]}">${esc(h.c)}</span>${h.tipo ? `<span class="inv-tipo">${esc(TIPO[h.tipo] || h.tipo)}</span>` : ''}${h.a ? '<span class="inv-tipo applied">aplicado al árbol</span>' : ''}`; }
function invCard(h, withPerson) {
  let x = `<article class="inv-card ${CLAS[h.c]}" id="inv-${esc(h.id)}"><div class="inv-head">${badge(h)}<span class="inv-id">${esc(h.id)}</span></div><h5>${esc(h.titulo)}</h5>`;
  if (h.o || h.n) x += `<p class="inv-diff">${h.o ? `<span class="was">Original: ${esc(h.o)}</span>` : ''}${h.n ? `<span class="now">${h.a ? 'Ahora' : 'Propuesta'}: ${esc(h.n)}</span>` : ''}</p>`;
  x += `<p>${esc(h.t)}</p>`;
  if (withPerson && h.p && P[h.p]) x += `<div class="inv-person">${personLink(h.p)}</div>`;
  x += `<ul class="srcs">${h.f.map(srcLink).join('')}</ul></article>`;
  return x;
}
function invSection(p) {
  return `<div class="p-sec p-inv" id="inv-sec"><h4>Investigación</h4><p class="note">Lo que sigue no viene de los cuadros originales: es el resultado de contrastarlos con fuentes publicadas. Solo lo «confirmado» modifica el árbol.</p>${p.inv.map(id => HZ[id]).filter(Boolean).map(h => invCard(h, false)).join('')}<p><a class="more" href="#/investigacion">Ver todos los hallazgos →</a></p></div>`;
}
function origNote(p) {
  const o = p.orig; if (!o && !p.merged) return '';
  const parts = Object.entries(o || {}).map(([k, v]) => `${FIELD[k] || k}: ${Array.isArray(v) ? v.join(', ') : (v || '—')}`);
  return `<p class="note inv-orig">${parts.length ? `Dato original de los cuadros, corregido por la investigación — ${esc(parts.join(' · '))}.` : ''}${p.merged ? ` En los cuadros aparecía también por separado como: ${esc(p.merged.join(', '))}.` : ''}</p>`;
}
function invNotes(sec) {
  if (!INV) return '';
  const hs = INV.hallazgos.filter(h => h.seccion === sec);
  return hs.length ? `<div class="inv-notes"><b class="inv-notes-t">Investigación</b>${hs.map(h => invCard(h, true)).join('')}</div>` : '';
}
function renderInvestigacion() {
  const el = $('#view-investigacion');
  if (!INV) { el.innerHTML = '<div class="wrap"><p>No hay datos de investigación.</p></div>'; return; }
  const hs = INV.hallazgos, cnt = c => hs.filter(h => h.c === c).length;
  const added = D.people.filter(p => p.invAdded);
  const groups = [...LINES, 'General'];
  el.innerHTML = `<div class="wrap"><span class="kicker">Contraste con fuentes</span><h1 class="display" style="font-size:44px">${esc(INV.meta.titulo)}</h1>
    <p class="lede" style="font-size:18px">${esc(INV.meta.resumen)}</p>
    <div class="stats"><div class="stat"><b>${hs.length}</b><span>hallazgos</span></div><div class="stat"><b>${cnt('CONFIRMADO')}</b><span>confirmados</span></div><div class="stat"><b>${cnt('PROBABLE')}</b><span>probables</span></div><div class="stat"><b>${cnt('EN CONFLICTO')}</b><span>en conflicto</span></div></div>
    <div class="box"><ul class="inv-legend">${Object.entries(INV.meta.clasificaciones).map(([k, v]) => `<li><span class="inv-badge ${CLAS[k]}">${esc(k)}</span> ${esc(v)}</li>`).join('')}<li><span class="inv-tipo">Corrección de la extracción</span> ${esc(INV.meta.tipos.extraccion)}</li></ul>
    ${added.length ? `<p><b>Personas añadidas por la investigación:</b> ${added.map(p => `<button class="plink-inline" data-go="${p.id}">${esc(p.name)}</button>`).join(', ')}.</p>` : ''}</div>
    <div class="toolbar">${['Todas', 'CONFIRMADO', 'PROBABLE', 'EN CONFLICTO'].map((c, i) => `<button class="fchip${i ? '' : ' on'}" data-c="${c}">${esc(c === 'Todas' ? c : c.toLowerCase())}</button>`).join('')}</div>
    <div id="invlist">${groups.map(g => { const l = hs.filter(h => (h.linea || 'General') === g); return l.length ? `<section class="inv-group" data-g="${esc(g)}"><h2 class="sec">${g === 'General' ? 'Historia y apellido' : 'Línea ' + esc(g)}</h2>${l.map(h => invCard(h, true)).join('')}</section>` : ''; }).join('')}</div>
    <h2 class="sec">Fuentes consultadas</h2><ul class="srcs all">${Object.keys(INV.fuentes).map(srcLink).join('')}</ul></div>`;
  $$('.fchip[data-c]', el).forEach(b => b.onclick = () => {
    $$('.fchip[data-c]', el).forEach(x => x.classList.toggle('on', x === b));
    $$('.inv-card', el).forEach(c => { c.hidden = b.dataset.c !== 'Todas' && HZ[c.id.slice(4)].c !== b.dataset.c; });
    $$('.inv-group', el).forEach(g => { g.hidden = !$$('.inv-card', g).some(c => !c.hidden); });
  });
  el.onclick = e => {
    const g = e.target.closest('[data-go]'); if (g) { openPanel(g.dataset.go); return; }
    const im = e.target.closest('[data-img]'); if (im) { e.preventDefault(); openImage(im.dataset.img, im.dataset.title || ''); }
  };
}
function closePanel(keepHash) {
  $('#panel').hidden = true;
  document.body.classList.remove('panel-open');
  if (nodesSel) nodesSel.classed('sel', false);
  selected = null;
  if (!keepHash && location.hash.startsWith('#/persona')) history.replaceState(null, '', '#/arbol');
}

/* ---------------- Historia ---------------- */
function renderHistoria() {
  const anc = D.people.filter(p => p.gen > 1 || ((p.id === MANUEL || p.id === TERESA)));
  const maxGen = Math.max(...anc.map(p => p.gen));
  const years = anc.map(p => parseInt(p.year)).filter(Boolean);
  const minY = Math.min(...years);
  const both = D.people.filter(p => p.both).length;
  const s = H;
  let h = `<div class="wrap">
  <span class="kicker">Genealogía de los hijos de</span>
  <h1 class="display">Manuel Salvador Álvarez Ruiz y María Teresa Ruiz Maya</h1>
  <p class="lede">${esc(s.subtitulo)}. Una investigación familiar que reúne a ${anc.length} personas de la ascendencia de los dos, en ${maxGen - 1} generaciones: de las familias antioqueñas de la Colonia a los linajes de la España medieval.</p>
  <div class="stats">
    <div class="stat"><b>${anc.length}</b><span>antepasados identificados</span></div>
    <div class="stat"><b>${both}</b><span>son antepasados de los dos</span></div>
    <div class="stat"><b>${D.trees.length}</b><span>cuadros genealógicos</span></div>
    <div class="stat"><b>${maxGen - 1}</b><span>generaciones</span></div>
  </div>
  <div class="box kin"><b>Parientes antes de casarse.</b> ${esc(kinText())}</div>
  <details class="box"><summary>${esc(s.metodologia.titulo)} y notas del autor</summary>
    <ol>${s.metodologia.items.map(i => `<li>${esc(i)}</li>`).join('')}</ol>
    <ul>${s.metodologia.notas.map(i => `<li>${esc(i)}</li>`).join('')}</ul></details>${invNotes('metodologia')}
  <h2 class="sec">${esc(s.origen.titulo)}</h2>
  <div class="prose">${s.origen.parrafos.map(p => `<p>${esc(p)}</p>`).join('')}</div>${invNotes('origen')}
  <h2 class="sec">El linaje Álvarez del Pino</h2>
  <p class="lede" style="font-size:18px">Diez generaciones por línea de varón, desde el fundador de la familia en Antioquia hasta Manuel Salvador.</p>
  <div class="timeline">`;
  for (const g of s.linaje) {
    const pid = D.people.find(p => p.bio === g.n)?.id;
    h += `<article class="gen" id="gen-${g.n}"><span class="gen-n">${g.n}</span>
      <h3>${esc(g.titulo)}</h3>${g.fechas ? `<div class="dates">${esc(g.fechas)}</div>` : ''}<p class="sub">${esc(g.subtitulo)}</p>
      ${g.parrafos.map(p => `<p>${esc(p)}</p>`).join('')}`;
    if (g.fotos) h += `<div class="${g.fotos.length > 1 ? 'phrow' : ''}">${g.fotos.map(f => `<figure class="ph"><img src="img/${f}" alt="${esc(H.fotos[f])}" data-photo="${f}" loading="lazy"><figcaption>${esc(H.fotos[f])}</figcaption></figure>`).join('')}</div>`;
    if (g.testimonio) h += `<blockquote class="testi"><p>«${esc(g.testimonio.texto)}»</p><cite>${esc(g.testimonio.titulo)} — ${esc(g.testimonio.autor)}</cite></blockquote>`;
    if (g.hijos && g.hijos.length) h += `<details ${g.n >= 9 ? 'open' : ''}><summary>${esc(g.hijos_titulo)}</summary><ol>${g.hijos.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
    if (g.hijos2) h += `<details><summary>${esc(g.hijos2_titulo)}</summary><ol>${g.hijos2.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
    if (g.n === 10) {
      h += `<p style="margin-top:14px">${esc(g.hijos_titulo)}</p><div class="kids">${D.people.filter(p => p.child).map(k =>
        `<button class="kid" data-go="${k.id}" style="text-align:left"><b>${esc(k.name)}${k.nick ? ` <small>(«${esc(k.nick)}»)</small>` : ''}</b><span>Nació el ${esc(k.born)}</span>${k.spouseName ? `<span>Casado/a con ${esc(k.spouseName)}</span>` : ''}${k.note ? `<span>${esc(k.note)}</span>` : ''}</button>`).join('')}</div>
        <figure class="ph" style="max-width:560px"><img src="img/familia-final.jpg" alt="${esc(H.fotos['familia-final.jpg'])}" data-photo="familia-final.jpg" loading="lazy"><figcaption>${esc(H.fotos['familia-final.jpg'])}</figcaption></figure>`;
    }
    h += invNotes('linaje-' + g.n);
    if (pid) h += `<div class="foot"><button class="btn-ghost" data-person="${pid}">Ver en el árbol</button></div>`;
    h += `</article>`;
  }
  h += `</div></div>`;
  const el = $('#view-historia');
  el.innerHTML = h;
  el.onclick = e => {
    const b = e.target.closest('[data-person]'); if (b) { goPerson(b.dataset.person); return; }
    const k = e.target.closest('[data-go]'); if (k) { openPanel(k.dataset.go); return; }
    const ph = e.target.closest('[data-photo]'); if (ph) openImage('img/' + ph.dataset.photo, H.fotos[ph.dataset.photo] || '');
    const im = e.target.closest('[data-img]'); if (im) { e.preventDefault(); openImage(im.dataset.img, im.dataset.title || ''); }
  };
}

/* ---------------- Personas ---------------- */
function renderPersonas() {
  const el = $('#view-personas');
  el.innerHTML = `<div class="wrap">
    <span class="kicker">Índice</span><h1 class="display" style="font-size:44px">Todas las personas</h1>
    <p class="lede" style="font-size:18px">Los hijos de Manuel Salvador y María Teresa, sus padres y todos sus antepasados, ordenados por generación. Toca un nombre para ver su ficha.</p>
    <div class="toolbar"><input id="pq" type="search" placeholder="Filtrar por nombre o apellido…" aria-label="Filtrar personas">
      <button class="fchip on" data-f="all">Todas</button>
      <button class="fchip" data-f="M">Lado de Manuel Salvador</button><button class="fchip" data-f="T">Lado de María Teresa</button><button class="fchip" data-f="B">De ambos</button>
      ${LINES.map((n, i) => `<button class="fchip" data-f="${i}"><i class="dot" style="background:${LCOL[i]}"></i>${esc(n)}</button>`).join('')}
      <button class="fchip" data-sort="az">A–Z</button></div>
    <p class="count" id="pcount"></p><div class="plist" id="plist"></div></div>`;
  let f = 'all', az = false;
  const draw = () => {
    const q = $('#pq').value;
    let list = q.trim().length >= 2 ? searchPeople(q, 2000) : D.people.slice();
    if (f === 'M') list = list.filter(p => p.genM != null || p.id === MANUEL || p.sibling);
    else if (f === 'T') list = list.filter(p => p.genT != null || p.id === TERESA);
    else if (f === 'B') list = list.filter(p => p.both);
    else if (f !== 'all') list = list.filter(p => p.line === +f);
    const key = p => (p.id === ROOT ? -1 : p.child ? -0.5 : p.sibling ? 1.2 : p.gen ?? 99);
    let html = '';
    if (az) {
      list.sort((a, b) => a.name.localeCompare(b.name, 'es'));
      html = list.map(row).join('');
    } else {
      list.sort((a, b) => key(a) - key(b) || a.name.localeCompare(b.name, 'es'));
      let last = null;
      for (const p of list) {
        const g = p.gen === 0 ? 'Los hijos' : p.gen === 1 ? 'Manuel Salvador, María Teresa y los hermanos de Manuel Salvador'
          : p.gen == null ? 'Otras personas de los cuadros' : `Generación ${p.gen} · ${genTitle(p.gen)} de los hijos`;
        if (g !== last) { html += `<h5>${esc(g)}</h5>`; last = g; }
        html += row(p);
      }
    }
    $('#plist').innerHTML = html || '<p style="padding:14px">Sin resultados.</p>';
    $('#pcount').textContent = `${list.length} personas`;
  };
  const row = p => `<button class="row" data-id="${p.id}"><i class="dot" style="background:${color(p)}"></i><span class="r-text"><span class="r-name">${esc(p.name)}${p.invAdded ? ' <span class="mini-tag added">añadida</span>' : p.inv ? ' <span class="mini-tag">investigación</span>' : ''}</span><span class="r-meta" style="margin:0;text-align:left;max-width:none">${esc(rel(p))}</span></span><span class="r-meta">${esc(meta(p))}</span></button>`;
  $('#pq').addEventListener('input', draw);
  $$('.fchip[data-f]', el).forEach(b => b.onclick = () => { f = b.dataset.f; $$('.fchip[data-f]', el).forEach(x => x.classList.toggle('on', x === b)); draw(); });
  $('.fchip[data-sort]', el).onclick = e => { az = !az; e.currentTarget.classList.toggle('on', az); draw(); };
  $('#plist').onclick = e => { const b = e.target.closest('[data-id]'); if (b) openPanel(b.dataset.id); };
  draw();
}

/* ---------------- Cuadros originales ---------------- */
function treeTitle(t) { return t.title || t.roots.map(id => P[id]?.name).filter(Boolean).join(' y '); }
function treeName(n) { const t = TREE[n]; return !t ? `Cuadro ${n}` : t.name ? t.name : t.side === 'T' ? `Cuadro ${t.label} de María Teresa` : `Cuadro n.º ${t.label}`; }
function kinText() {
  const m = P[MANUEL], t = P[TERESA]; if (!m || !t) return '';
  const best = D.people.filter(p => p.both).sort((a, b) => (a.genM + a.genT) - (b.genM + b.genT));
  if (!best.length) return '';
  const b = best[0], sp = (b.spouses || []).map(x => P[x]).find(x => x && x.both);
  const who = sp ? `${b.name} y ${sp.name}` : b.name;
  return `Según los cuadros, Manuel Salvador y María Teresa compartían antepasados: ${who} eran ${relWord(b.genM, false, true).toLowerCase()}s de Manuel Salvador y ${relWord(b.genT, false, true).toLowerCase()}s de María Teresa. Por eso ${best.length} personas aparecen en las dos ramas del árbol.`;
}
const card = t => `<button class="card" data-tree="${t.n}"><img src="arboles/${t.img.replace('.webp', '-mini.webp')}" alt="${esc(treeName(t.n))}" loading="lazy"><div><b>${esc(treeName(t.n))}</b><span>${esc(treeTitle(t))}</span></div></button>`;
function renderOriginales() {
  const el = $('#view-originales');
  el.innerHTML = `<div class="wrap wide"><span class="kicker">Facsímil</span><h1 class="display" style="font-size:44px">Los cuadros originales</h1>
    <p class="lede" style="font-size:18px">Los cuadros de ascendientes tal como fueron elaborados en la investigación original. Toca un cuadro para verlo en grande y hacer zoom.</p>
    <h2 class="sec">Manuel Salvador Álvarez Ruiz</h2>
    <p class="note">28 cuadros. En el cuadro n.º 1, cada integrante de la última fila lleva el número del cuadro en el que continúa su ascendencia.</p>
    <div class="grid">${D.trees.filter(t => t.side === 'M').map(card).join('')}</div>
    <h2 class="sec">María Teresa Ruiz Maya</h2>
    <p class="note">Cuadros n.º 1 a 11 y 16 a 19, con sus continuaciones (3A, 3B…). Los cuadros 17A a 17G llegan a los linajes medievales de España (Ponce de León, Guzmán, reyes de León, Castilla y Navarra, visigodos). Al final están, solo como imagen, las páginas de la parte 2 que no se pudieron leer automáticamente.</p>
    <div class="grid">${D.trees.filter(t => t.side === 'T').map(card).join('')}</div></div>`;
  el.onclick = e => { const b = e.target.closest('[data-tree]'); if (b) openTree(+b.dataset.tree); };
}

/* ---------------- visor con zoom ---------------- */
let vzoom;
function setupViewer() {
  const stage = d3.select('#viewerStage'), img = $('#viewerImg');
  vzoom = d3.zoom().scaleExtent([0.05, 6]).on('zoom', e => { img.style.transform = `translate(${e.transform.x}px,${e.transform.y}px) scale(${e.transform.k})`; });
  stage.call(vzoom);
  img.onload = () => {
    const s = $('#viewerStage'), w = s.clientWidth, h = s.clientHeight;
    const k = Math.min(w / img.naturalWidth, h / img.naturalHeight) * 0.96;
    stage.call(vzoom.transform, d3.zoomIdentity.translate((w - img.naturalWidth * k) / 2, (h - img.naturalHeight * k) / 2).scale(k));
  };
  $('#viewerClose').onclick = closeViewer;
}
function openImage(src, title) {
  $('#viewerTitle').textContent = title;
  $('#viewerOpen').href = src;
  $('#viewer').hidden = false;
  const img = $('#viewerImg');
  img.removeAttribute('src');
  img.alt = title;
  img.src = src;
}
function openTree(n) {
  const t = D.trees.find(x => x.n === n);
  openImage('arboles/' + t.img, `${treeName(n)}${treeTitle(t) ? ' — ' + treeTitle(t) : ''}`);
}
function closeViewer() { $('#viewer').hidden = true; }
})();
