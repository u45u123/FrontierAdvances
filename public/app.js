const page = document.querySelector('#top');
const select = document.querySelector('#daySelect');
const template = document.querySelector('#entryTemplate');
const assetVersion = Date.now();

function freshAsset(path) {
  return `${path}?updated=${assetVersion}`;
}

function runsToElement(block, element) {
  block.runs.forEach((run) => {
    const node = document.createElement(run.bold ? 'strong' : 'span');
    node.textContent = run.text + ' ';
    element.append(node);
  });
}

function addBlocks(blocks, container, list = false) {
  blocks.forEach((block) => {
    const item = document.createElement(list ? 'li' : 'p');
    runsToElement(block, item);
    container.append(item);
  });
}

function addCredit(element, image) {
  element.textContent = image.source ? `Image source: ${image.source}` : '';
}

function render(entry, region) {
  const node = template.content.cloneNode(true);
  node.querySelector('.prayer-entry').style.setProperty('--region-color', region.color);
  node.querySelector('.eyebrow').textContent = `DAY ${String(entry.day).padStart(2, '0')}`;
  node.querySelector('h1').textContent = entry.peopleName;
  node.querySelector('.region').textContent = entry.region;
  const person = node.querySelector('.person-image');
  person.src = freshAsset(entry.personImage.src);
  person.alt = `${entry.peopleName} people`;
  person.onerror = () => person.closest('.photo-section').hidden = true;
  addCredit(node.querySelector('.credit'), entry.personImage);
  const stats = node.querySelector('.stats');
  entry.statistics.forEach(({ label, value }) => {
    const term = document.createElement('dt'); term.textContent = label;
    const description = document.createElement('dd'); description.textContent = value;
    stats.append(term, description);
  });
  addBlocks(entry.generalInformation, node.querySelector('.general'));
  addBlocks(entry.scripture, node.querySelector('.scripture'));
  addBlocks(entry.prayerPoints, node.querySelector('.prayers'), true);
  const map = node.querySelector('.map-image');
  map.src = freshAsset(entry.mapImage.src);
  map.alt = `${entry.peopleName} map`;
  map.onerror = () => map.closest('.map-section').hidden = true;
  addCredit(node.querySelector('.map-credit'), entry.mapImage);
  page.replaceChildren(node);
  document.title = `Day ${entry.day}: ${entry.peopleName} | Acts Now Prayer`;
}

const freshJson = (path) => fetch(`${path}?updated=${Date.now()}`, {
  cache: 'no-store',
  headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate' },
}).then((response) => {
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
});

try {
  const payload = await freshJson('data/index.json');
  const { regions, days: entries } = payload;
  entries.forEach((entry) => {
    const option = new Option(`Day ${String(entry.day).padStart(2, '0')} · ${entry.peopleName}`, entry.day);
    select.add(option);
  });
  const today = new Date().getDate();
  async function loadDay(summary) {
    const entry = await freshJson(summary.file);
    render(entry, regions[entry.region]);
  }

  function dayFromUrl() {
    const match = window.location.hash.match(/^#day-(\d{1,2})$/);
    return match ? Number(match[1]) : null;
  }

  function setDayInUrl(day) {
    history.replaceState(null, '', `#day-${String(day).padStart(2, '0')}`);
  }

  const initial = entries.find(({ day }) => day === today) || entries[0];
  const requestedDay = dayFromUrl();
  const selected = entries.find(({ day }) => day === requestedDay) || initial;
  select.value = selected.day;
  setDayInUrl(selected.day);
  await loadDay(selected);
  select.addEventListener('change', async () => {
    const summary = entries.find(({ day }) => day === Number(select.value));
    setDayInUrl(summary.day);
    await loadDay(summary);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
} catch (error) {
  page.innerHTML = `<p class="load-error">Could not load prayer data. Open this app at <strong>http://localhost:8000/</strong>, not as a file. (${error.message})</p>`;
}
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js', { updateViaCache: 'none' })
      .then((registration) => registration.update())
      .catch(() => {});
  });
}
