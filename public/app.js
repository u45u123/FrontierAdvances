const page = document.querySelector('#top');
const select = document.querySelector('#daySelect');
const languageSelect = document.querySelector('#languageSelect');
const template = document.querySelector('#entryTemplate');
const closingTemplate = document.querySelector('#closingTemplate');
const assetVersion = Date.now();
const requestedLanguage = new URLSearchParams(window.location.search).get('lang');
const language = ['en', 'es', 'ko', 'zh-Hant', 'zh-Hans'].includes(requestedLanguage) ? requestedLanguage : 'ko';
const copy = language === 'ko' ? {
  language: '언어', today: '오늘의 기도', selectDay: '기도 일자 선택',
  statistics: '통계', information: '일반 정보', scripture: '성경 구절', prayers: '기도제목', map: '지도', day: '일차',
  install: '📱 홈 화면에 앱 설치하기', installAria: '앱 설치하기',
  iosInstall: '이 앱을 설치하려면 아래의 <strong>공유 아이콘</strong>을 누른 후 <strong>\'홈 화면에 추가\'</strong>를 선택하세요.', close: '닫기',
} : language === 'es' ? {
  language: 'Idioma', today: 'Oración de hoy', selectDay: 'Selecciona el día de oración',
  statistics: 'Estadísticas', information: 'Información general', scripture: 'Escritura', prayers: 'Puntos de oración', map: 'Mapa', day: 'Día',
  install: '📱 Instalar la aplicación', installAria: 'Instalar la aplicación',
  iosInstall: 'Para instalar esta aplicación, toca el <strong>icono Compartir</strong> y luego selecciona <strong>\'Añadir a la pantalla de inicio\'</strong>.', close: 'Cerrar',
} : language === 'zh-Hant' ? {
  language: '語言', today: '今日禱告', selectDay: '選擇禱告日',
  statistics: '統計資料', information: '一般資訊', scripture: '經文', prayers: '代禱事項', map: '地圖', day: '第',
  install: '📱 安裝應用程式', installAria: '安裝應用程式',
  iosInstall: '如要安裝此應用程式，請點選底部的<strong>分享圖示</strong>，然後選擇<strong>「加入主畫面」</strong>。', close: '關閉',
} : language === 'zh-Hans' ? {
  language: '语言', today: '今日祷告', selectDay: '选择祷告日',
  statistics: '统计资料', information: '一般信息', scripture: '经文', prayers: '代祷事项', map: '地图', day: '第',
  install: '📱 安装应用程序', installAria: '安装应用程序',
  iosInstall: '如要安装此应用程序，请点击底部的<strong>分享图标</strong>，然后选择<strong>“添加到主屏幕”</strong>。', close: '关闭',
} : {
  language: 'Language', today: "Today's Prayer", selectDay: 'Select prayer day',
  statistics: 'Statistics', information: 'General information', scripture: 'Scripture', prayers: 'Prayer points', map: 'Map', day: 'Day',
  install: '📱 Install App to Home Screen', installAria: 'Install App',
  iosInstall: "To install this app, tap the <strong>Share icon</strong> (square with an up arrow) at the bottom, then select <strong>'Add to Home Screen'</strong>.", close: 'Close',
};

document.documentElement.lang = language;
languageSelect.value = language;
document.querySelector('#languageLabel').textContent = copy.language;
document.querySelector('#dayPickerLabel').textContent = copy.today;
select.setAttribute('aria-label', copy.selectDay);
const installButton = document.querySelector('#install-btn');
installButton.textContent = copy.install;
installButton.setAttribute('aria-label', copy.installAria);
document.querySelector('#ios-install-message').innerHTML = copy.iosInstall;
document.querySelector('#ios-install-close').textContent = copy.close;

function freshAsset(path) {
  return `${path}?updated=${assetVersion}`;
}

function dayLabel(day) {
  if (language === 'ko') return `${day}일차`;
  if (language === 'es') return `Día ${day}`;
  if (language === 'zh-Hant' || language === 'zh-Hans') return `第${day}天`;
  return `Day ${day}`;
}

function dayBadge(day) {
  if (language === 'ko') return `${day}일차`;
  if (language === 'es') return `DÍA ${String(day).padStart(2, '0')}`;
  if (language === 'zh-Hant' || language === 'zh-Hans') return `第${day}天`;
  return `DAY ${String(day).padStart(2, '0')}`;
}

function runsToElement(block, element) {
  block.runs.forEach((run) => {
    const node = document.createElement(run.bold ? 'strong' : 'span');
    // Spacing is preserved in the source run. Adding a space here separates
    // Korean particles from a preceding bold word (e.g. 유목민 + 들).
    node.textContent = run.text;
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
  node.querySelector('.stats-section h2').textContent = copy.statistics;
  node.querySelector('.general-section h2').textContent = copy.information;
  node.querySelector('.scripture-section h2').textContent = copy.scripture;
  node.querySelector('.prayer-section h2').textContent = copy.prayers;
  node.querySelector('.map-section h2').textContent = copy.map;
  node.querySelector('.prayer-entry').style.setProperty('--region-color', region.color);
  node.querySelector('.eyebrow').textContent = dayBadge(entry.day);
  node.querySelector('h1').textContent = entry.peopleName;
  node.querySelector('.region').textContent = entry.region;
  const person = node.querySelector('.person-image');
  person.src = freshAsset(entry.personImage.src);
  person.alt = `${entry.peopleName} people`;
  person.onerror = () => person.closest('.photo-section').hidden = true;
  addCredit(node.querySelector('.credit'), entry.personImage);
  const statsIntro = node.querySelector('.stats-intro');
  if (entry.statisticsIntro) {
    statsIntro.textContent = entry.statisticsIntro;
    statsIntro.hidden = false;
  }
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
  if (entry.mapImage.layout === 'portrait') {
    map.closest('.map-section').classList.add('map-section--portrait');
  }
  map.src = freshAsset(entry.mapImage.src);
  map.alt = `${entry.peopleName} map`;
  map.onerror = () => map.closest('.map-section').hidden = true;
  addCredit(node.querySelector('.map-credit'), entry.mapImage);
  if (entry.closing) {
    const closing = closingTemplate.content.cloneNode(true);
    const closingImage = closing.querySelector('.closing-commission');
    closingImage.src = freshAsset(entry.closing.image);
    closingImage.alt = entry.closing.alt;
    if (entry.closing.scriptureQuotation) {
      const quotation = closing.querySelector('.closing-quotation');
      quotation.textContent = entry.closing.scriptureQuotation;
      quotation.hidden = false;
    }
    if (entry.closing.scriptureQuotations) {
      const quotations = closing.querySelector('.scripture-quotations');
      const heading = document.createElement('h2');
      heading.textContent = entry.closing.scriptureQuotations.heading;
      quotations.append(heading);
      entry.closing.scriptureQuotations.items.forEach(({ title, text }) => {
        const paragraph = document.createElement('p');
        const strong = document.createElement('strong');
        strong.textContent = title;
        paragraph.append(strong, document.createElement('br'), document.createTextNode(text));
        quotations.append(paragraph);
      });
      quotations.hidden = false;
    }
    node.append(closing);
  }
  page.replaceChildren(node);
  document.title = `${dayLabel(entry.day)}: ${entry.peopleName} | Acts Now Prayer`;
}

const freshJson = (path) => fetch(`${path}?updated=${Date.now()}`, {
  cache: 'no-store',
  headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate' },
}).then((response) => {
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
});

try {
  const payload = await freshJson(`data/${language}/index.json`);
  const { regions, days: entries } = payload;
  entries.forEach((entry) => {
    const option = new Option(`${dayLabel(String(entry.day).padStart(2, '0'))} · ${entry.peopleName}`, entry.day);
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
  languageSelect.addEventListener('change', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('lang', languageSelect.value);
    window.location.href = url.toString();
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
