#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const defaultPagePath = path.join(root, 'www/client-wins/index.html');
const defaultDataPath = path.join(root, 'content/client-wins.json');
const defaultCssPath = path.join(root, 'content/_client-wins.css');
const styleId = 'dc-client-wins-redesign';
const pageTitle = 'Construction Business Coaching Results | Develop Coaching';
const pageDescription = 'Watch builders and construction business owners share how they improved turnover, marketing, systems, teams, profit and control of their time.';
const featuredClientId = 'D-M9a1i4PQU';
const clientWinOrder = [
  'D-M9a1i4PQU',
  'Kfx-SeLmNig',
  '9i31Jk89THQ',
  'H1eWYQjMaFA',
  '1C2yT_tP-Aw',
  'yXqEwu6FEog',
  'snrx2DrLISg',
  '7iLnXeuYoMg',
  'zhoS5F5oYy4',
  'GSEM3O9HYvg',
  'r572G_WcimQ',
  'NzonAtTiHlg',
  'tZxceh60Zc8',
  'HcS63FwTv_A',
  'MGAD2pxmNrc',
  'IZYls1vXkQo',
  '4w0XjmkgUx0',
  'AePCs4liO0Q',
  'oktEjmz9B6s',
  'gKrNClKEzVU'
];

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function cardMarkup(item) {
  const watchUrl = `https://www.youtube.com/watch?v=${item.id}`;
  const thumbnail = item.thumbnailUrl || `https://i.ytimg.com/vi/${item.id}/hqdefault.jpg`;
  return `
        <article class="cw-win-card" data-client-win data-youtube-id="${item.id}">
          <button class="cw-video" type="button" data-video-play="${item.id}" aria-label="Play ${escapeHtml(item.name)} client story">
            <img src="${thumbnail}" alt="${escapeHtml(item.name)} sharing their construction business experience" loading="lazy" width="480" height="360">
            <span class="cw-video__play" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg>
            </span>
            <span class="cw-video__time">${escapeHtml(item.durationLabel)}</span>
          </button>
          <div class="cw-docket">
            <p class="cw-docket__focus">${escapeHtml(item.focus)}</p>
            <h3>${escapeHtml(item.name)}</h3>
            <p class="cw-docket__context">${escapeHtml(item.context)}</p>
            <p class="cw-docket__summary">${escapeHtml(item.summary)}</p>
            <div class="cw-docket__source">
              <a href="${watchUrl}" target="_blank" rel="noopener">Watch ${escapeHtml(item.name)}'s full story</a>
            </div>
          </div>
        </article>`;
}

function pageMarkup(items) {
  const firstCards = items.slice(0, 10).map(cardMarkup).join('');
  const remainingCards = items.slice(10).map(cardMarkup).join('');
  const featured = items.find((item) => item.id === featuredClientId);
  const featuredThumbnail = featured.thumbnailUrl || `https://i.ytimg.com/vi/${featured.id}/hqdefault.jpg`;
  return `<main id="content" class="site-main dc-client-wins">
  <section class="cw-hero" aria-labelledby="client-wins-title">
    <div class="cw-wrap cw-hero__grid">
      <div class="cw-hero__copy">
        <p class="cw-kicker">Real construction business stories</p>
        <h1 id="client-wins-title">See how builders are winning better work, building stronger teams and taking back control.</h1>
        <p class="cw-hero__lead">Hear directly from construction business owners who changed how they approached leads, cash flow, pricing, systems, people and their own time.</p>
        <div class="cw-hero__actions">
          <a class="cw-button" href="#client-stories">Find a story like yours</a>
          <a class="cw-hero__link" href="/courses/mastermind-course/">See how the Mastermind works <span aria-hidden="true">→</span></a>
        </div>
      </div>
      <aside class="cw-featured" aria-labelledby="featured-story-title">
        <button class="cw-featured__video" type="button" data-video-play="${featured.id}" aria-label="Play ${escapeHtml(featured.name)} client story">
          <img src="${featuredThumbnail}" alt="${escapeHtml(featured.name)} sharing his construction business story" width="480" height="360">
          <span class="cw-video__play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg></span>
          <span class="cw-video__time">${escapeHtml(featured.durationLabel)}</span>
        </button>
        <div class="cw-featured__copy">
          <p class="cw-kicker">Featured story</p>
          <h2 id="featured-story-title">James grew annual revenue from £1.5m to £2m, then forecast £4m.</h2>
          <p>His story focuses on stronger structure and adding property development to the group.</p>
        </div>
      </aside>
    </div>
  </section>

  <section class="cw-intro" aria-labelledby="client-stories-heading">
    <div class="cw-wrap cw-intro__inner">
      <p class="cw-kicker">Where do you recognise yourself?</p>
      <h2 id="client-stories-heading">Find the story closest to where your business is now.</h2>
      <p>Maybe you are still carrying too much yourself. Perhaps the leads are inconsistent, the margins are too tight, the team needs more structure or the business has grown without giving you more freedom. These owners started with familiar problems and explain what they changed next.</p>
    </div>
  </section>

  <section class="cw-stories" id="client-stories" aria-label="Construction business client stories">
    <div class="cw-wrap cw-story-grid">${firstCards}
    </div>

    <div class="cw-mid-cta">
      <div class="cw-wrap cw-mid-cta__inner">
        <div>
          <p class="cw-kicker">Your business can change too</p>
          <h2>Which problem would make the biggest difference if you fixed it first?</h2>
          <p>A free 15-minute Scale Session will help you identify the priority for your next 12 months.</p>
        </div>
        <a class="cw-button" href="/schedule-a-call/">Book my Scale Session</a>
      </div>
    </div>

    <div class="cw-wrap cw-story-grid cw-story-grid--second">${remainingCards}
    </div>

    <div class="cw-wrap cw-results-note">
      <p>Every construction business is different. These clients describe their own experience, and individual results will depend on your starting point, market, decisions and implementation.</p>
    </div>
  </section>

  <section class="cw-path" aria-labelledby="next-step-title">
    <div class="cw-wrap cw-path__grid">
      <div class="cw-path__copy">
        <p class="cw-kicker">Choose your next step</p>
        <h2 id="next-step-title">Get the right support for the business you want to build.</h2>
        <p>Explore the Develop Mastermind for hands-on coaching, or start with the free Five Pillars training for practical help with planning, tracking, sales, delivery and scale.</p>
      </div>
      <nav class="cw-path__links" aria-label="Coaching and training links">
        <a href="/courses/mastermind-course/">Develop Mastermind <span aria-hidden="true">→</span></a>
        <a href="/5-pillars-free-trainings/">Free Five Pillars training <span aria-hidden="true">→</span></a>
      </nav>
    </div>
  </section>

  <section class="cw-final" aria-labelledby="client-wins-cta-title">
    <div class="cw-wrap cw-final__inner">
      <div>
        <h2 id="client-wins-cta-title">Find out what your next 12 months should focus on.</h2>
        <p>Book a free 15-minute Scale Session. If the Mastermind is not the right fit, you will still leave knowing what to fix first.</p>
      </div>
      <a class="cw-button cw-button--dark" href="/schedule-a-call/">Book my free Scale Session</a>
    </div>
  </section>

  <script data-client-wins-video-loader>
  document.addEventListener('click', function(event) {
    var button = event.target.closest('[data-video-play]');
    if (!button) return;
    var id = button.getAttribute('data-video-play');
    var frame = document.createElement('iframe');
    frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?autoplay=1&rel=0';
    frame.title = button.getAttribute('aria-label');
    frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    frame.allowFullscreen = true;
    button.replaceWith(frame);
    frame.focus();
  });
  </script>
</main>`;
}

function videoSchema(item) {
  return {
    '@type': 'VideoObject',
    '@id': `https://develop-coaching.com/client-wins/#video-${item.id}`,
    name: `${item.name}: ${item.focus}`,
    description: item.summary,
    uploadDate: item.uploadDate,
    duration: item.duration,
    thumbnailUrl: item.thumbnailUrl || `https://i.ytimg.com/vi/${item.id}/hqdefault.jpg`,
    embedUrl: `https://www.youtube.com/embed/${item.id}`,
    contentUrl: `https://www.youtube.com/watch?v=${item.id}`,
    isPartOf: {'@id': 'https://develop-coaching.com/client-wins/#webpage'},
    publisher: {'@id': 'https://develop-coaching.com/#organization'},
    inLanguage: 'en-GB'
  };
}

function replaceMeta(html, attribute, key, value) {
  const pattern = new RegExp(`<meta\\s+${attribute}=["']${key}["'][^>]*>`, 'i');
  const replacement = `<meta ${attribute}="${key}" content="${escapeHtml(value)}" />`;
  if (pattern.test(html)) return html.replace(pattern, replacement);
  return html.replace(/<\/head>/i, `${replacement}\n</head>`);
}

function replaceSchema(html, items) {
  const pattern = /<script[^>]*type=["']application\/ld\+json["'][^>]*class=["']rank-math-schema-pro["'][^>]*>([\s\S]*?)<\/script>/i;
  const match = html.match(pattern);
  if (!match) throw new Error('Rank Math schema graph not found');
  const schema = JSON.parse(match[1]);
  const graph = (schema['@graph'] || []).filter((item) => {
    const types = Array.isArray(item['@type']) ? item['@type'] : [item['@type']];
    if (types.includes('VideoObject') || types.includes('Article')) return false;
    return !(types.includes('Person') && String(item['@id'] || '').includes('/author/dipti/'));
  });
  for (const item of graph) {
    const types = Array.isArray(item['@type']) ? item['@type'] : [item['@type']];
    if (types.includes('WebPage')) {
      item.name = pageTitle;
      item.description = pageDescription;
    }
    if (types.includes('BreadcrumbList')) {
      const last = item.itemListElement && item.itemListElement.at(-1);
      if (last && last.item) last.item.name = 'Client Results';
    }
  }
  schema['@graph'] = graph.concat(items.map(videoSchema));
  const replacement = `<script type="application/ld+json" class="rank-math-schema-pro">${JSON.stringify(schema)}</script>`;
  return html.replace(pattern, replacement);
}

function renderClientWins(options = {}) {
  const pagePath = options.pagePath || defaultPagePath;
  const dataPath = options.dataPath || defaultDataPath;
  const cssPath = options.cssPath || defaultCssPath;
  const sourceItems = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const css = fs.readFileSync(cssPath, 'utf8').trim();
  let html = fs.readFileSync(pagePath, 'utf8');

  if (sourceItems.length !== 20) throw new Error(`Expected 20 client stories, found ${sourceItems.length}`);
  const uniqueIds = new Set(sourceItems.map((item) => item.id));
  if (uniqueIds.size !== sourceItems.length) throw new Error('Client story video IDs must be unique');
  if (clientWinOrder.length !== sourceItems.length || clientWinOrder.some((id) => !uniqueIds.has(id))) {
    throw new Error('Client story display order must contain every approved video ID exactly once');
  }
  const itemById = new Map(sourceItems.map((item) => [item.id, item]));
  const items = clientWinOrder.map((id) => itemById.get(id));

  html = html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${pageTitle}</title>`);
  html = replaceMeta(html, 'name', 'description', pageDescription);
  html = replaceMeta(html, 'property', 'og:title', pageTitle);
  html = replaceMeta(html, 'property', 'og:description', pageDescription);
  html = replaceMeta(html, 'name', 'twitter:title', pageTitle);
  html = replaceMeta(html, 'name', 'twitter:description', pageDescription);
  html = html
    .replace(/\s*<meta\s+property=["']og:video["'][^>]*>/gi, '')
    .replace(/\s*<meta\s+property=["']ya:ovs:[^"']+["'][^>]*>/gi, '');
  html = replaceSchema(html, items);

  const mainPattern = /<main\b[\s\S]*?<\/main>/i;
  if (!mainPattern.test(html)) throw new Error('Client Wins main element not found');
  html = html.replace(mainPattern, () => pageMarkup(items));

  const style = `<style id="${styleId}">\n${css}\n</style>`;
  const stylePattern = new RegExp(`<style id="${styleId}">[\\s\\S]*?<\\/style>`, 'i');
  if (stylePattern.test(html)) html = html.replace(stylePattern, () => style);
  else html = html.replace(/<\/head>/i, `${style}\n</head>`);

  fs.writeFileSync(pagePath, html);
  return html;
}

if (require.main === module) {
  renderClientWins();
  console.log('Rendered evidence-led Client Wins page.');
}

module.exports = {renderClientWins, videoSchema};
