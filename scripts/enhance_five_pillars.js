#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const hubRoot = path.join(root, 'www/5-pillars-free-trainings');
const mastermindPath = path.join(root, 'www/courses/mastermind-course/index.html');
const {renderHub} = require('./render_five_pillars_hub');

const pillars = {
  plan: {
    number: 1,
    title: 'Plan',
    h1: 'Plan Your Construction Business Growth',
    intro: 'Turn ambition into a practical direction for the business. These free resources cover targets, financial visibility, priorities and the routines that keep a construction company moving towards its goals.',
    use: 'Start here if the team is busy but priorities, numbers or the next stage of growth are unclear.',
    supporting: [
      ['/profit-and-loss-statement-for-small-construction-company/', 'Use a profit and loss statement', 'Understand what the numbers show about income, costs and business performance.'],
      ['/construction-profit-margin-uk/', 'Understand construction profit margins', 'Review the difference between turnover, gross profit and net profit in a UK construction business.']
    ],
    image: 'https://i.ytimg.com/vi/Gygj47Sk_ck/maxresdefault.jpg',
    faqs: [
      ['What does the Plan pillar cover?', 'It brings together resources on business goals, financial visibility, strategic priorities and turning a longer-term direction into practical action.'],
      ['Where should I start?', 'Choose the resource that matches the clearest current gap, then record one action to apply before moving to another topic.'],
      ['How does Plan connect to the other pillars?', 'Planning sets the direction and measures that guide what the business needs to attract, convert, deliver and scale.']
    ]
  },
  attract: {
    number: 2,
    title: 'Attract',
    h1: 'Attract Better-Fit Construction Clients',
    intro: 'Build a clearer market position and a more dependable flow of suitable enquiries. These free resources cover brand, reviews, referrals, digital marketing and relationship-led lead generation.',
    use: 'Start here if lead flow is inconsistent or too dependent on a single channel or relationship.',
    supporting: [
      ['/attract-the-right-clients/', 'Attract the right construction clients', 'Focus marketing on suitable projects and clients rather than enquiry volume alone.'],
      ['/construction-lead-generation/', 'Improve construction lead generation', 'Build a more dependable route from marketing activity to suitable enquiries.']
    ],
    image: 'https://i.ytimg.com/vi/Paw7cjpopHY/maxresdefault.jpg',
    faqs: [
      ['What does the Attract pillar cover?', 'It covers positioning, brand, reviews, content, referrals and marketing channels that help suitable prospects find and trust a construction business.'],
      ['Is Attract only about paid advertising?', 'No. The resources include owned, earned and relationship-led approaches as well as digital marketing.'],
      ['What should I improve first?', 'Begin with the point that most limits suitable enquiries, such as unclear positioning, weak proof or over-reliance on one source.']
    ]
  },
  convert: {
    number: 3,
    title: 'Convert',
    h1: 'Convert Enquiries Into Profitable Construction Projects',
    intro: 'Create a consistent route from first enquiry to a well-qualified, properly priced project. These free resources cover qualification, sales conversations, estimating, proposals and follow-up.',
    use: 'Start here if good enquiries stall, quotes consume too much time or the work being won does not protect the intended margin.',
    supporting: [
      ['/construction-job-pricing/', 'Price construction jobs properly', 'Connect estimating, costs and intended margin before committing to a project.']
    ],
    image: 'https://i.ytimg.com/vi/RKMnmz9JW2M/hqdefault.jpg',
    faqs: [
      ['What does the Convert pillar cover?', 'It covers qualification, sales process, estimating, proposals, follow-up and the decisions that connect an enquiry to a suitable project.'],
      ['Is conversion only about closing more work?', 'No. A useful conversion process also helps identify poor-fit opportunities before they consume estimating and management time.'],
      ['Where should I begin?', 'Map the current enquiry-to-project journey and choose the stage where suitable opportunities most often slow down or drop out.']
    ]
  },
  deliver: {
    number: 4,
    title: 'Deliver',
    h1: 'Deliver Construction Projects With Control',
    intro: 'Protect the promise made during the sale by improving how work is handed over, planned, procured, managed and reviewed. These free resources focus on project control and consistent delivery.',
    use: 'Start here if projects drift after handover, site information is inconsistent or the margin achieved differs from the margin quoted.',
    supporting: [
      ['/construction-project-management/', 'Strengthen construction project management', 'Improve the planning and control used from handover through delivery.'],
      ['/software/costtracker-pro/', 'Track live project costs', 'See how CostTracker Pro supports purchase, cost and project financial visibility.'],
      ['/streamlined-procurement-system/', 'Streamline construction procurement', 'Create a more consistent process for buying and managing project materials.']
    ],
    image: 'https://i.ytimg.com/vi/9bvw3Ki8jl4/hqdefault.jpg',
    faqs: [
      ['What does the Deliver pillar cover?', 'It covers handover, project planning, procurement, site management, communication and the controls used while work is in progress.'],
      ['Why connect delivery to profitability?', 'The commercial result depends on how the agreed scope, programme, buying and changes are controlled throughout the project.'],
      ['Where should I start?', 'Choose the repeated delivery problem that creates the most rework, delay or uncertainty, then document the expected process and owner.']
    ]
  },
  scale: {
    number: 5,
    title: 'Scale',
    h1: 'Scale a Construction Business Beyond the Owner',
    intro: 'Build the people, responsibilities and operating systems needed for growth that does not rely on the owner making every decision. These free resources cover delegation, leadership, team structure and management rhythm.',
    use: 'Start here if growth creates more firefighting or important work still waits for the owner.',
    supporting: [
      ['/construction-business-systems/', 'Build construction business systems', 'Document repeatable ways of working so the business depends less on the owner.'],
      ['/podcast/the-perfect-week-with-emma-mills/', 'Create a practical weekly rhythm', 'Use a structured week to protect priorities, leadership time and follow-through.']
    ],
    image: 'https://i.ytimg.com/vi/pkIndbf_w4E/hqdefault.jpg',
    faqs: [
      ['What does the Scale pillar cover?', 'It covers roles, delegation, leadership, team structure, systems and the management routines that reduce dependence on the owner.'],
      ['When is a business ready to work on Scale?', 'The warning sign is not a particular size. It is that growth repeatedly adds owner workload, unclear responsibility or inconsistent decisions.'],
      ['How does Scale connect to the other pillars?', 'Scaling relies on clear direction, dependable demand, a consistent sales process and controlled project delivery.']
    ]
  }
};

const routes = Object.keys(pillars).map((slug) => `/5-pillars-free-trainings/${slug}/`);
const primaryResources = new Map([
  ['/podcast/how-jamie-mills-built-a-multi-million-pound-construction-company/', 'scale'],
  ['/podcast/protect-your-profit-margin-podcast/', 'plan'],
  ['/podcast/improve-subcontractor-procurement-with-paul-heming/', 'deliver'],
  ['/streamlined-procurement-system/', 'deliver'],
  ['/attract-the-best/', 'scale'],
  ['/the-architect-attractor/', 'attract'],
  ['/the-sales-mastery/', 'convert'],
  ['/construction-lead-generation/', 'attract'],
  ['/podcast/a-construction-team-that-runs-your-business-without-you/', 'scale']
]);

const sharedStyle = `
<style id="five-pillars-seo-geo">
  .five-pillars-guide{--ink:#17232b;--blue:#087f86;--signal:#f2b94b;--paper:#f4f7f8;--line:#d9e2e5;background-color:var(--paper);background-image:linear-gradient(rgba(23,35,43,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(23,35,43,.035) 1px,transparent 1px);background-size:48px 48px;color:var(--ink);padding:76px 24px;font-family:"Source Sans Pro",Arial,sans-serif}
  .five-pillars-guide__inner{max-width:1120px;margin:0 auto}
  .five-pillars-guide h2{font-size:clamp(30px,4vw,48px);line-height:1.02;letter-spacing:-.025em;margin:0;color:var(--ink)}
  .five-pillars-guide h3{font-size:22px;line-height:1.2;margin:0;color:var(--ink)}
  .five-pillars-guide p,.five-pillars-guide summary,.five-pillars-guide dd{font-size:18px;line-height:1.55}
  .five-pillars-guide__eyebrow{margin:0 0 10px!important;color:var(--blue);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px!important;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
  .five-pillars-guide__header{display:grid;grid-template-columns:150px minmax(0,1fr);gap:38px;align-items:stretch;margin-bottom:28px}
  .five-pillars-guide__stamp{position:relative;display:flex;min-height:168px;flex-direction:column;justify-content:space-between;overflow:hidden;background:var(--ink);color:#fff;padding:22px}
  .five-pillars-guide__stamp:after{content:"";position:absolute;right:-32px;bottom:-36px;width:110px;height:110px;border:16px solid var(--signal);transform:rotate(45deg);opacity:.95}
  .five-pillars-guide__stamp-number{font-size:64px;font-weight:900;letter-spacing:-.08em;line-height:.8}
  .five-pillars-guide__stamp-name{position:relative;z-index:1;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
  .five-pillars-guide__heading{display:flex;flex-direction:column;justify-content:center;border-top:6px solid var(--signal);border-bottom:1px solid var(--line);padding:20px 0}
  .five-pillars-guide__lead{max-width:790px;margin:18px 0 0!important;color:#42545e;font-size:20px!important}
  .five-pillars-guide__start{display:grid;grid-template-columns:150px minmax(0,1fr);gap:38px;align-items:center;background:var(--blue);color:#fff;margin-bottom:58px;padding:24px 28px}
  .five-pillars-guide__start-label{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
  .five-pillars-guide__start h3{color:#fff;margin-bottom:5px}
  .five-pillars-guide__start p{margin:0;color:#fff}
  .five-pillars-guide__routes-head{display:flex;justify-content:space-between;gap:36px;align-items:end;margin-bottom:22px}
  .five-pillars-guide__routes-note{max-width:390px;margin:0;color:#50636e;font-size:16px!important}
  .five-pillars-guide__resources{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:14px;margin:0 0 64px}
  .five-pillars-guide__resource{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:18px;align-items:start;min-height:180px;background:#fff;border:1px solid var(--line);border-top:5px solid var(--ink);padding:22px;color:var(--ink);text-decoration:none;box-shadow:0 8px 0 rgba(23,35,43,.06);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
  .five-pillars-guide__resource:only-child{max-width:560px}
  .five-pillars-guide__resource-number{color:var(--blue);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;font-weight:800}
  .five-pillars-guide__resource-copy strong{display:block;margin-bottom:8px;color:var(--ink);font-size:21px;line-height:1.2;text-decoration:underline;text-decoration-color:var(--signal);text-decoration-thickness:3px;text-underline-offset:5px}
  .five-pillars-guide__resource-copy span{display:block;color:#50636e;font-size:16px;line-height:1.5}
  .five-pillars-guide__resource-arrow{color:var(--blue);font-size:24px;font-weight:800;line-height:1}
  .five-pillars-guide__resource:hover,.five-pillars-guide__resource:focus-visible{border-color:var(--blue);box-shadow:0 8px 0 rgba(8,127,134,.16);transform:translateY(-3px)}
  .five-pillars-guide__faq{display:grid;grid-template-columns:minmax(220px,.65fr) minmax(0,1.35fr);gap:46px;align-items:start;border-top:1px solid var(--line);padding-top:48px}
  .five-pillars-guide__questions details{background:#fff;border:1px solid var(--line);margin:0 0 10px;padding:0 22px}
  .five-pillars-guide__questions summary{cursor:pointer;font-weight:800;padding:18px 34px 18px 0}
  .five-pillars-guide__questions dd{margin:0;padding:0 0 20px;color:#50636e}
  .five-pillars-guide__cta{display:flex;align-items:center;justify-content:space-between;gap:22px;margin-top:46px;padding:30px;background:var(--ink);border-left:8px solid var(--signal);color:#fff}
  .five-pillars-guide__cta p{margin:0;color:#fff}
  .five-pillars-guide__cta a{display:inline-flex;align-items:center;justify-content:center;background:var(--signal);color:var(--ink);font-weight:900;padding:14px 22px;text-decoration:none;white-space:nowrap;box-shadow:5px 5px 0 var(--blue)}
  .five-pillars-guide__transcript{border-left:4px solid var(--blue);padding-left:18px;max-width:850px}
  .five-pillars-primary{display:block;margin-top:6px;font-size:13px;font-weight:700;color:#50636e}
  @media(prefers-reduced-motion:reduce){.five-pillars-guide__resource{transition:none}}
  @media(max-width:767px){
    .five-pillars-guide{padding:52px 18px;background-size:32px 32px}
    .five-pillars-guide__header{grid-template-columns:84px minmax(0,1fr);gap:18px}
    .five-pillars-guide__stamp{min-height:150px;padding:16px 12px}
    .five-pillars-guide__stamp-number{font-size:46px}
    .five-pillars-guide__stamp-name{font-size:10px;writing-mode:vertical-rl;transform:rotate(180deg)}
    .five-pillars-guide__heading{padding:15px 0}
    .five-pillars-guide__lead{font-size:17px!important}
    .five-pillars-guide__start{grid-template-columns:1fr;gap:8px;margin-bottom:44px;padding:22px}
    .five-pillars-guide__routes-head{display:block}
    .five-pillars-guide__routes-note{margin-top:12px}
    .five-pillars-guide__resources{grid-template-columns:1fr}
    .five-pillars-guide__resource{min-height:0}
    .five-pillars-guide__resource:only-child{max-width:none}
    .five-pillars-guide__faq{grid-template-columns:1fr;gap:22px;padding-top:38px}
    .five-pillars-guide__cta{align-items:flex-start;flex-direction:column;padding:24px}
    .five-pillars-guide__cta a{white-space:normal;text-align:center;width:100%}
    .e-loop-item .e-con-inner,.e-loop-item .e-con{min-width:0}
    .jet-listing-grid__items.grid-col-mobile-2>.jet-listing-grid__item{width:100%;max-width:100%;flex:0 0 100%}
    .elementor-loop-container.elementor-grid{grid-template-columns:1fr!important}
  }
</style>`;

function read(file) { return fs.readFileSync(file, 'utf8'); }
function write(file, value) { fs.writeFileSync(file, value); }
function assertReplace(value, pattern, replacement, label) {
  const next = value.replace(pattern, replacement);
  if (next === value) throw new Error(`Could not replace ${label}`);
  return next;
}
function htmlEscape(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

function normalizeSchema(html, canonical, title, description, image, faqs, hubVideo) {
  const match = html.match(/<script type="application\/ld\+json" class="rank-math-schema-pro">([\s\S]*?)<\/script>/);
  if (!match) throw new Error(`Schema not found in ${canonical}`);
  const current = JSON.parse(match[1]);
  const graph = current['@graph'] || [];
  const breadcrumb = graph.find((node) => node['@type'] === 'BreadcrumbList');
  const existingPage = graph.find((node) => node['@type'] === 'WebPage');
  const existingVideos = graph.filter((node) => node['@type'] === 'VideoObject' && node['@id'] !== hubVideo?.['@id']).map((video) => ({
    ...video,
    description: `A video resource included in the ${title} training collection for construction business owners.`,
    thumbnailUrl: video.thumbnailUrl || `https://i.ytimg.com/vi/${String(video.embedUrl || '').split('/').pop()}/hqdefault.jpg`,
    publisher: {'@id': 'https://develop-coaching.com/#organization'}
  }));
  const organization = {
    '@type': 'Organization', '@id': 'https://develop-coaching.com/#organization', name: 'Develop Coaching',
    url: 'https://develop-coaching.com',
    sameAs: ['https://www.facebook.com/developcoach/','https://twitter.com/developcoaching','https://www.instagram.com/develop_coaching_greg_wilkes/','https://www.linkedin.com/company/developcoaching/','https://www.youtube.com/@DevelopCoaching'],
    logo: {'@type':'ImageObject','@id':'https://develop-coaching.com/#logo',url:'https://develop-coaching.com/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg',contentUrl:'https://develop-coaching.com/wp-content/uploads/2022/11/Screenshot-2022-08-15-at-11.07-1.svg',caption:'Develop Coaching',inLanguage:'en-GB',width:259,height:82},
    image: {'@id':'https://develop-coaching.com/#logo'}, telephone: '+442086109674'
  };
  const page = {
    '@type': ['WebPage','CollectionPage'], '@id': `${canonical}#webpage`, url: canonical, name: title,
    description, isPartOf: {'@id':'https://develop-coaching.com/#website'}, publisher: {'@id':'https://develop-coaching.com/#organization'},
    inLanguage: 'en-GB', primaryImageOfPage: {'@type':'ImageObject',url:image},
    ...(existingPage?.datePublished ? {datePublished: existingPage.datePublished} : {}),
    dateModified: '2026-08-25',
    ...(breadcrumb ? {breadcrumb:{'@id':breadcrumb['@id']}} : {})
  };
  const faq = {
    '@type':'FAQPage', '@id':`${canonical}#faq`, isPartOf:{'@id':`${canonical}#webpage`},
    mainEntity: faqs.map(([question, answer]) => ({'@type':'Question',name:question,acceptedAnswer:{'@type':'Answer',text:answer}}))
  };
  const nextGraph = [
    organization,
    {'@type':'WebSite','@id':'https://develop-coaching.com/#website',url:'https://develop-coaching.com',name:'Develop Coaching',publisher:{'@id':'https://develop-coaching.com/#organization'},inLanguage:'en-GB'},
    ...(breadcrumb ? [breadcrumb] : []), page, faq, ...(hubVideo ? [hubVideo] : []), ...existingVideos
  ];
  const schema = `<script type="application/ld+json" class="rank-math-schema-pro">${JSON.stringify({'@context':'https://schema.org','@graph':nextGraph})}</script>`;
  return html.replace(match[0], () => schema);
}

function addSocialImage(html, image, title) {
  if (!html.includes('property="og:image"')) {
    html = assertReplace(html, /(<meta property="og:site_name"[^>]*>)/, `$1\n<meta property="og:image" content="${image}" />\n<meta property="og:image:alt" content="${htmlEscape(title)}" />`, 'Open Graph image');
  }
  if (!html.includes('name="twitter:image"')) {
    html = assertReplace(html, /(<meta name="twitter:description"[^>]*>)/, `$1\n<meta name="twitter:image" content="${image}" />`, 'Twitter image');
  }
  return html;
}

function faqMarkup(faqs) {
  return faqs.map(([q,a]) => `<details><summary>${htmlEscape(q)}</summary><dl><dt class="elementor-screen-only">Answer</dt><dd>${htmlEscape(a)}</dd></dl></details>`).join('\n');
}

function supportingResourcesMarkup(slug, resources) {
  return resources.map(([href, title, description], index) => `<a class="five-pillars-guide__resource" href="${href}" data-primary-pillar="${slug}"><span class="five-pillars-guide__resource-number">${String(index + 1).padStart(2, '0')}</span><span class="five-pillars-guide__resource-copy"><strong>${htmlEscape(title)}</strong><span>${htmlEscape(description)}</span></span><span class="five-pillars-guide__resource-arrow" aria-hidden="true">→</span></a>`).join('\n');
}

function trackingScript(sourcePage) {
  return `<script id="five-pillars-analytics">
(function(w,d){
  w.ga4EventLayer=w.ga4EventLayer||[];
  w.ga4Event=w.ga4Event||function(){w.ga4EventLayer.push(arguments);};
  var s=d.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=G-PXT2VCVFLW&l=ga4EventLayer';d.head.appendChild(s);
  w.ga4Event('js',new Date());w.ga4Event('config','G-PXT2VCVFLW',{send_page_view:false});
  d.addEventListener('click',function(e){
    var a=e.target.closest('a[href]');if(!a||!a.closest('main'))return;
    var href=a.getAttribute('href')||'';var text=(a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,120);
    var match=href.match(/^\\/5-pillars-free-trainings\\/(plan|attract|convert|deliver|scale)\\/?$/);
    if(match){w.ga4Event('event','five_pillars_pillar_select',{source_page:'${sourcePage}',pillar_name:match[1],link_text:text});return;}
    if(href.indexOf('/courses/mastermind-course/')===0||href.indexOf('/schedule-a-call/')===0){w.ga4Event('event','five_pillars_mastermind_click',{source_page:'${sourcePage}',pillar_name:'${sourcePage}',link_text:text,destination_url:href});return;}
    if(href.charAt(0)==='/'&&!href.startsWith('/5-pillars-free-trainings/')&&!href.startsWith('/#')){
      w.ga4Event('event','five_pillars_resource_click',{source_page:'${sourcePage}',pillar_name:'${sourcePage}',resource_title:text,resource_url:href,primary_pillar:a.dataset.primaryPillar||''});
    }
  });
})(window,document);
</script>`;
}

function annotatePrimaryResources(html, currentPillar) {
  html = html.replace(/\sdata-primary-pillar="[^"]*"/g, '').replace(/<span class="five-pillars-primary">[\s\S]*?<\/span>/g, '');
  for (const [href, primary] of primaryResources) {
    const escaped = href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const anchor = new RegExp(`<a([^>]*href=["']${escaped}["'][^>]*)>`, 'g');
    html = html.replace(anchor, `<a$1 data-primary-pillar="${primary}">`);
    if (currentPillar !== primary) {
      const heading = new RegExp(`(<h3[^>]*>\\s*<a[^>]*href=["']${escaped}["'][^>]*>[\\s\\S]*?<\\/a>\\s*<\\/h3>)`, 'g');
      html = html.replace(heading, `$1<span class="five-pillars-primary">Primary pillar: ${pillars[primary].title}</span>`);
      const podcastCard = new RegExp(`(<div class="jet-engine-listing-overlay-wrap" data-url=["']${escaped}["'][\\s\\S]*?<h2 class="elementor-heading-title elementor-size-default">[\\s\\S]*?<\\/h2>)`, 'g');
      html = html.replace(podcastCard, `$1<span class="five-pillars-primary">Primary pillar: ${pillars[primary].title}</span>`);
    }
  }
  return html;
}

function enhancePillar(slug, data) {
  const file = path.join(hubRoot, slug, 'index.html');
  let html = read(file);
  const canonical = `https://develop-coaching.com/5-pillars-free-trainings/${slug}/`;
  const description = `${data.intro} Pillar ${data.number} of the free Five Pillars training hub.`;
  html = html.replaceAll('/5-pillars-plan/', routes[0]).replaceAll('/the-5-pillars-attract/', routes[1]).replaceAll('/the-5-pillars-convert/', routes[2]).replaceAll('/the-5-pillars-deliver/', routes[3]).replaceAll('/the-5-pillars-scale/', routes[4]);
  const legacyHeading = `<h2 class="elementor-heading-title elementor-size-default">${data.title.toUpperCase()}</h2>`;
  const desiredHeading = `<h1 class="elementor-heading-title elementor-size-default">${data.h1}</h1>`;
  if (html.includes(legacyHeading)) html = html.replace(legacyHeading, desiredHeading);
  else if (!html.includes(desiredHeading)) throw new Error(`Could not replace ${slug} H1`);
  html = html.replace(/<h1 class="elementor-heading-title elementor-size-default">(<a[\s\S]*?<\/a>)<\/h1>/g, '<h3 class="elementor-heading-title elementor-size-default">$1</h3>');
  html = addSocialImage(html, data.image, data.h1);
  html = normalizeSchema(html, canonical, data.h1, description, data.image, data.faqs);
  html = annotatePrimaryResources(html, slug);
  const guide = `${sharedStyle}
<section class="five-pillars-guide" data-pillar="${slug}" aria-labelledby="${slug}-guide-title">
  <div class="five-pillars-guide__inner">
    <header class="five-pillars-guide__header">
      <div class="five-pillars-guide__stamp" aria-hidden="true"><span class="five-pillars-guide__stamp-number">0${data.number}</span><span class="five-pillars-guide__stamp-name">${data.title}</span></div>
      <div class="five-pillars-guide__heading">
        <p class="five-pillars-guide__eyebrow">Your site briefing</p>
        <h2 id="${slug}-guide-title">Use ${data.title} to move the business forward</h2>
        <p class="five-pillars-guide__lead">${data.intro}</p>
      </div>
    </header>
    <div class="five-pillars-guide__start"><span class="five-pillars-guide__start-label">Start here</span><div><h3>Your first move</h3><p>${data.use}</p></div></div>
    <div class="five-pillars-guide__routes-head"><div><p class="five-pillars-guide__eyebrow">Recommended next reads</p><h2>Go deeper on ${data.title}</h2></div><p class="five-pillars-guide__routes-note">Choose the guide closest to the constraint you are dealing with now. One useful change is better than ten saved tabs.</p></div>
    <nav class="five-pillars-guide__resources" aria-label="Recommended ${data.title} guides">
      ${supportingResourcesMarkup(slug, data.supporting)}
    </nav>
    <div class="five-pillars-guide__faq"><div><p class="five-pillars-guide__eyebrow">Quick answers</p><h2>Before you start</h2></div><div class="five-pillars-guide__questions">${faqMarkup(data.faqs)}</div></div>
    <div class="five-pillars-guide__cta"><p><strong>Want help applying the Five Pillars to your business?</strong><br>See how the Develop Mastermind combines planning, coaching and accountability.</p><a href="/courses/mastermind-course/">Explore the Develop Mastermind</a></div>
  </div>
</section>`;
  html = html.replace(/<style id="five-pillars-seo-geo">[\s\S]*?<\/style>\s*/g, '');
  html = html.replace(/<section class="five-pillars-guide"[\s\S]*?<\/section>\s*/g, '');
  html = assertReplace(html, '</main>', `${guide}\n</main>`, `${slug} guide`);
  html = html.replace(/\n{3,}(?=<style id="five-pillars-seo-geo">)/g, '\n\n');
  const analytics = trackingScript(slug);
  if (html.includes('id="five-pillars-analytics"')) html = html.replace(/<script id="five-pillars-analytics">[\s\S]*?<\/script>/, analytics);
  else html = assertReplace(html, '</body>', `${analytics}\n</body>`, `${slug} analytics`);
  write(file, html);
}

function enhanceHub() {
  const file = path.join(hubRoot, 'index.html');
  let html = read(file);
  const canonical = 'https://develop-coaching.com/5-pillars-free-trainings/';
  const title = 'Free Construction Business Training: The Five Pillars';
  const description = 'A free training hub for construction business owners, organised around Plan, Attract, Convert, Deliver and Scale.';
  const image = 'https://i.ytimg.com/vi/B3EHS8OHdhM/maxresdefault.jpg';
  const faqs = [
    ['What are the Five Pillars?', 'Plan, Attract, Convert, Deliver and Scale are five connected areas used to organise the free construction business resources in this hub.'],
    ['Who is this training hub for?', 'It is for builders and construction business owners looking for practical resources on running and growing their companies.'],
    ['Does the training need to be completed in order?', 'No. Start with the pillar that best matches the current constraint, then use the other pillars to understand the connected parts of the business.']
  ];
  html = html.replaceAll('/5-pillars-plan/', routes[0]).replaceAll('/the-5-pillars-attract/', routes[1]).replaceAll('/the-5-pillars-convert/', routes[2]).replaceAll('/the-5-pillars-deliver/', routes[3]).replaceAll('/the-5-pillars-scale/', routes[4]);
  const legacyHeading = '<h2 class="elementor-heading-title elementor-size-default">Free Trainings - The 5 Pillars</h2>';
  if (html.includes(legacyHeading)) {
    html = html.replace(legacyHeading, `<h1 class="elementor-heading-title elementor-size-default">${title}</h1>`);
  } else if (!html.includes('class="fp-hub"')) {
    throw new Error('Could not replace hub H1');
  }
  html = addSocialImage(html, image, title);
  const video = {
    '@type':'VideoObject','@id':`${canonical}#welcome-video`,name:'Welcome To The 5 Pillars Hub',
    description:'Greg Wilkes introduces the free Develop Coaching knowledge hub and explains how its resources are organised around Plan, Attract, Convert, Deliver and Scale.',
    thumbnailUrl:image,uploadDate:'2025-10-28',duration:'PT2M9S',embedUrl:'https://www.youtube.com/embed/B3EHS8OHdhM',
    publisher:{'@id':'https://develop-coaching.com/#organization'},isPartOf:{'@id':`${canonical}#webpage`},inLanguage:'en-GB'
  };
  html = normalizeSchema(html, canonical, title, description, image, faqs, video);
  // Visible hub content comes from content/five-pillars-hub.html via renderHub().
  // Keep this step focused on metadata, schema and analytics outside <main>.
  const analytics = trackingScript('hub');
  if (html.includes('id="five-pillars-analytics"')) html = html.replace(/<script id="five-pillars-analytics">[\s\S]*?<\/script>/, analytics);
  else html = assertReplace(html, '</body>', `${analytics}\n</body>`, 'hub analytics');
  write(file, html);
}

function enhanceMastermind() {
  let html = read(mastermindPath);
  Object.entries(pillars).forEach(([slug, data]) => {
    if (html.includes(`data-pillar-name="${slug}"`)) return;
    const pattern = new RegExp(`<li><span>0${data.number}<\\/span>([\\s\\S]*?)<div><h3>${data.title}<\\/h3>([\\s\\S]*?)<\\/div><\\/li>`);
    html = assertReplace(html, pattern, `<li><a class="dc2-pillar-link" href="/5-pillars-free-trainings/${slug}/" data-pillar-name="${slug}"><span>0${data.number}</span>$1<div><h3>${data.title}</h3>$2</div></a></li>`, `Mastermind ${slug} link`);
  });
  const linkStyle = `<style id="mastermind-pillar-links">
.dc2-pillars li{padding:0;display:block}
.dc2-pillar-link{display:grid;grid-template-rows:auto 64px 1fr;align-content:start;gap:1.15rem;min-height:255px;padding:1.35rem 1.2rem 1.5rem;color:inherit;text-decoration:none}
.dc2-pillar-link:focus-visible{outline:3px solid #f2b94b;outline-offset:-3px}
.dc2-pillars .dc2-pillar-link>span{color:var(--dc2-blue);font-family:var(--dc2-mono);font-size:.68rem;font-weight:700}
@media(max-width:1024px){.dc2-pillar-link{min-height:180px}}
</style>`;
  if (html.includes('id="mastermind-pillar-links"')) html = html.replace(/<style id="mastermind-pillar-links">[\s\S]*?<\/style>/, linkStyle);
  else html = assertReplace(html, '</head>', `${linkStyle}\n</head>`, 'Mastermind pillar link style');
  const analytics = `<script id="mastermind-pillar-analytics">document.addEventListener('click',function(e){var a=e.target.closest('.dc2-pillar-link');if(!a||typeof window.ga4Event!=='function')return;window.ga4Event('event','five_pillars_pillar_select',{source_page:'mastermind',pillar_name:a.dataset.pillarName,link_text:(a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,120)});});</script>`;
  if (html.includes('id="mastermind-pillar-analytics"')) html = html.replace(/<script id="mastermind-pillar-analytics">[\s\S]*?<\/script>/, analytics);
  else html = assertReplace(html, '</body>', `${analytics}\n</body>`, 'Mastermind pillar analytics');
  write(mastermindPath, html);
}

enhanceHub();
renderHub();
Object.entries(pillars).forEach(([slug, data]) => enhancePillar(slug, data));
enhanceMastermind();
console.log('Enhanced Five Pillars hub, pillar pages and Mastermind links.');
