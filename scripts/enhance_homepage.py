#!/usr/bin/env python3
"""Replace the legacy homepage body with an owned, evidence-led experience."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "www" / "index.html"
STYLE_ID = "dc-homepage-control-board-styles"
TITLE = "Construction Business Coach for Builders | Develop Coaching"
DESCRIPTION = (
    "Construction business coaching for established builders and contractors who want "
    "better profit, stronger systems, a capable team and more control of their time."
)

FAQS = [
    (
        "What is a construction business coach?",
        "A construction business coach helps builders, contractors and trade business owners improve the commercial and operational side of the company. The work can include planning, job pricing, cash flow, lead generation, sales, project delivery, team structure and leadership.",
    ),
    (
        "Who is construction business coaching for?",
        "It is for construction business owners who have proven demand but feel the business still depends on them for too many decisions. Develop Coaching works with established builders, contractors and trade businesses that want more predictable profit, stronger systems and controlled growth.",
    ),
    (
        "How is a construction coach different from a general business coach?",
        "A construction coach understands job margins, variations, subcontractors, project delivery, site teams, estimating and the uneven cash flow that comes with construction. That industry context makes the advice easier to apply to real projects and teams.",
    ),
    (
        "What does Develop Coaching help with?",
        "Develop Coaching organises the work around five connected areas: Plan, Attract, Convert, Deliver and Scale. The aim is to identify the part of the business creating the most pressure, install the right system and review its effect on profit, people and owner time.",
    ),
    (
        "How quickly should a construction business expect results?",
        "The timing depends on the starting point and the system being improved. Clearer priorities can happen quickly, while stronger financial, sales and delivery results usually require consistent implementation and review over several months.",
    ),
    (
        "What is the first step?",
        "Start by reviewing where the business is now, what is creating the most pressure and what the next twelve months need to achieve. A call with Develop Coaching can help decide whether the Mastermind is the right level of support.",
    ),
]

STYLES = r'''<style id="dc-homepage-control-board-styles">
.dc-home{--dc-ink:#25262a;--dc-yellow:#f6c944;--dc-blue:#0069b1;--dc-paper:#f5f3ec;--dc-white:#fff;--dc-orange:#f5a623;overflow:clip;background:var(--dc-white);color:var(--dc-ink);font-family:"Source Sans Pro","Helvetica Neue",Arial,sans-serif}
.dc-home,.dc-home *{box-sizing:border-box}
.dc-home a:focus-visible,.dc-home summary:focus-visible{outline:4px solid var(--dc-yellow);outline-offset:4px}
.dc-home__wrap{width:min(calc(100% - 48px),1180px);margin-inline:auto}
.dc-home__eyebrow{margin:0 0 14px;color:var(--dc-blue);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.76rem;font-weight:900;letter-spacing:.13em;line-height:1.4;text-transform:uppercase}
.dc-home__eyebrow--light{color:var(--dc-yellow)}
.dc-home h1,.dc-home h2,.dc-home h3,.dc-home p{margin-top:0}
.dc-home h1,.dc-home h2,.dc-home h3{font-family:"Roboto Condensed","Arial Narrow","Source Sans Pro",sans-serif;font-weight:800}
.dc-home h2{font-size:clamp(2.2rem,5vw,4.4rem);letter-spacing:-.035em;line-height:.98}
.dc-home__button{display:inline-flex;min-height:54px;align-items:center;justify-content:center;padding:14px 20px;border:2px solid var(--dc-ink);background:var(--dc-yellow);box-shadow:6px 6px 0 var(--dc-blue);color:var(--dc-ink)!important;font-weight:900;line-height:1.15;text-decoration:none!important;transition:transform 160ms ease,box-shadow 160ms ease,background 160ms ease}
.dc-home__button:hover{background:var(--dc-orange);box-shadow:3px 3px 0 var(--dc-blue);transform:translate(3px,3px)}
.dc-home__button--ghost{border-color:rgba(255,255,255,.75);background:transparent;box-shadow:none;color:var(--dc-white)!important}
.dc-home__button--ghost:hover{background:var(--dc-white);color:var(--dc-ink)!important;transform:none}
.dc-home-hero{position:relative;padding:64px 0;background-color:var(--dc-ink);background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:32px 32px;color:var(--dc-white)}
.dc-home-hero:after{content:"";position:absolute;right:0;bottom:0;left:0;height:10px;background:linear-gradient(90deg,var(--dc-yellow) 0 63%,var(--dc-blue) 63% 100%)}
.dc-home-hero__grid{display:grid;grid-template-columns:minmax(0,1.06fr) minmax(360px,.94fr);gap:72px;align-items:center}
.dc-home-hero h1{max-width:760px;margin-bottom:20px;color:var(--dc-white);font-size:clamp(2.8rem,4.8vw,4.9rem);letter-spacing:-.045em;line-height:.92;text-wrap:balance}
.dc-home-hero h1 span{color:var(--dc-yellow)}
.dc-home-hero__answer{max-width:690px;margin-bottom:24px;color:#e5e7e9;font-size:clamp(1.08rem,2vw,1.28rem);line-height:1.55}
.dc-home-hero__actions{display:flex;flex-wrap:wrap;gap:18px;align-items:center}
.dc-home-hero__visual{position:relative;align-self:stretch;padding:20px 20px 0;border:1px solid rgba(255,255,255,.32);background:rgba(255,255,255,.07);box-shadow:16px 16px 0 var(--dc-blue)}
.dc-home-hero__visual:before{content:"SITE CONTROL / OWNER VIEW";display:block;margin-bottom:14px;color:var(--dc-yellow);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.7rem;font-weight:900;letter-spacing:.12em}
.dc-home-hero__visual img{display:block;width:100%;height:clamp(260px,30vw,360px);object-fit:cover;object-position:center;border:8px solid var(--dc-white);filter:saturate(.86) contrast(1.04)}
.dc-home-hero__status{position:relative;margin:-46px 18px 0;padding:22px;background:var(--dc-paper);box-shadow:8px 8px 0 var(--dc-yellow);color:var(--dc-ink)}
.dc-home-hero__status strong{display:block;margin-bottom:14px;font-family:"Roboto Condensed","Arial Narrow",sans-serif;font-size:1.45rem;line-height:1}
.dc-home-hero__pills{display:flex;flex-wrap:wrap;gap:7px}
.dc-home-hero__pills span{padding:5px 8px;border:1px solid var(--dc-ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.66rem;font-weight:800;text-transform:uppercase}
.dc-home-intro{padding:40px 0;background:var(--dc-yellow);border-bottom:1px solid var(--dc-ink)}
.dc-home-intro__grid{display:grid;grid-template-columns:auto 1fr;gap:30px;align-items:center}
.dc-home-intro__label{padding:8px 11px;border:2px solid var(--dc-ink);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.74rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;transform:rotate(-1deg)}
.dc-home-intro p{max-width:920px;margin-bottom:0;font-size:1.22rem;font-weight:700;line-height:1.5}
.dc-home-problems{padding:104px 0;background:var(--dc-paper)}
.dc-home-problems__head{display:grid;grid-template-columns:minmax(0,.8fr) minmax(280px,.45fr);gap:80px;align-items:end;margin-bottom:48px}
.dc-home-problems__head p:last-child{margin-bottom:4px;font-size:1.1rem;line-height:1.6}
.dc-home-problems__grid{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--dc-ink);border-left:1px solid var(--dc-ink)}
.dc-home-problem{min-height:250px;padding:28px;border-right:1px solid var(--dc-ink);border-bottom:1px solid var(--dc-ink);background:var(--dc-white)}
.dc-home-problem:before{content:"";display:block;width:42px;height:7px;margin-bottom:42px;background:var(--dc-yellow)}
.dc-home-problem:nth-child(2):before,.dc-home-problem:nth-child(4):before{background:var(--dc-blue)}
.dc-home-problem h3{margin-bottom:12px;font-size:1.55rem;line-height:1.05}
.dc-home-problem p{margin-bottom:0;color:#55585e;line-height:1.55}
.dc-home-pillars{padding:110px 0;background:var(--dc-blue);color:var(--dc-white)}
.dc-home-pillars__grid{display:grid;grid-template-columns:minmax(280px,.72fr) minmax(0,1.28fr);gap:84px;align-items:start}
.dc-home-pillars__copy{position:sticky;top:32px}
.dc-home-pillars h2{color:var(--dc-white)}
.dc-home-pillars__copy>p:last-of-type{max-width:470px;color:#dceaf5;font-size:1.1rem;line-height:1.65}
.dc-home-pillars__route{margin-top:26px;color:var(--dc-yellow)!important;font-weight:800}
.dc-home-pillars__board{border-top:1px solid rgba(255,255,255,.55)}
.dc-home-pillar{display:grid;grid-template-columns:112px minmax(0,1fr) auto;gap:24px;align-items:center;min-height:122px;padding:22px 4px;border-bottom:1px solid rgba(255,255,255,.55);color:var(--dc-white)!important;text-decoration:none!important;transition:padding 160ms ease,background 160ms ease}
.dc-home-pillar:hover{padding-right:16px;padding-left:16px;background:rgba(0,0,0,.13)}
.dc-home-pillar__name{color:var(--dc-yellow);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.8rem;font-weight:900;letter-spacing:.09em;text-transform:uppercase}
.dc-home-pillar strong{display:block;margin-bottom:6px;font-family:"Roboto Condensed","Arial Narrow",sans-serif;font-size:1.65rem;line-height:1}
.dc-home-pillar small{display:block;color:#dceaf5;font-size:.98rem;line-height:1.45}
.dc-home-pillar__arrow{font-size:2rem;line-height:1}
.dc-home-proof{padding:110px 0;background:var(--dc-white)}
.dc-home-proof__header{display:grid;grid-template-columns:minmax(0,.8fr) minmax(280px,.45fr);gap:80px;align-items:end;margin-bottom:48px}
.dc-home-proof__header p:last-child{margin-bottom:5px;font-size:1.08rem;line-height:1.6}
.dc-home-proof__grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.dc-home-proof__card{display:flex;min-height:330px;flex-direction:column;padding:30px;border:1px solid var(--dc-ink);box-shadow:7px 7px 0 var(--dc-paper)}
.dc-home-proof__card:nth-child(2){box-shadow:7px 7px 0 var(--dc-yellow)}
.dc-home-proof__card:nth-child(3){box-shadow:7px 7px 0 var(--dc-blue)}
.dc-home-proof__focus{margin-bottom:36px!important;color:var(--dc-blue);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase}
.dc-home-proof__card h3{margin-bottom:15px;font-size:2rem;line-height:1}
.dc-home-proof__card p:nth-of-type(2){font-size:1.08rem;line-height:1.58}
.dc-home-proof__source{margin-top:auto;margin-bottom:0!important;padding-top:24px;border-top:1px solid #ccd0d3;color:#60646a;font-size:.83rem;font-weight:700}
.dc-home-proof__link{display:inline-flex;margin-top:34px;color:var(--dc-blue)!important;font-weight:900;text-decoration-thickness:2px;text-underline-offset:5px}
.dc-home-method{padding:110px 0;background:var(--dc-ink);color:var(--dc-white)}
.dc-home-method__head{max-width:760px;margin-bottom:48px}
.dc-home-method h2{color:var(--dc-white)}
.dc-home-method__steps{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid rgba(255,255,255,.45);border-left:1px solid rgba(255,255,255,.45)}
.dc-home-method__step{padding:32px;border-right:1px solid rgba(255,255,255,.45);border-bottom:1px solid rgba(255,255,255,.45)}
.dc-home-method__step span{display:block;margin-bottom:50px;color:var(--dc-yellow);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;font-weight:900;letter-spacing:.1em}
.dc-home-method__step h3{margin-bottom:12px;color:var(--dc-white);font-size:1.8rem;line-height:1}
.dc-home-method__step p{margin-bottom:0;color:#d9dcdf;line-height:1.55}
.dc-home-method__cta{display:flex;flex-wrap:wrap;gap:24px;align-items:center;justify-content:space-between;margin-top:42px;padding:30px;background:var(--dc-yellow);color:var(--dc-ink)}
.dc-home-method__cta p{max-width:660px;margin-bottom:0;font-size:1.18rem;font-weight:800;line-height:1.45}
.dc-home-method__cta .dc-home__button{background:var(--dc-ink);box-shadow:5px 5px 0 var(--dc-blue);color:var(--dc-white)!important}
.dc-home-about{padding:96px 0;background:var(--dc-paper)}
.dc-home-about__grid{display:grid;grid-template-columns:minmax(280px,.72fr) minmax(0,1.28fr);gap:70px;align-items:center}
.dc-home-about__image{position:relative;padding:16px;background:var(--dc-yellow);box-shadow:12px 12px 0 var(--dc-blue)}
.dc-home-about__image img{display:block;width:100%;height:auto;aspect-ratio:1.25/1;object-fit:cover}
.dc-home-about h2{max-width:780px}
.dc-home-about__copy>p:not(.dc-home__eyebrow){font-size:1.1rem;line-height:1.65}
.dc-home-about__copy a{color:var(--dc-blue);font-weight:900;text-underline-offset:5px}
.dc-home-faq{padding:104px 0;background:var(--dc-white)}
.dc-home-faq__grid{display:grid;grid-template-columns:minmax(260px,.56fr) minmax(0,1fr);gap:76px;align-items:start}
.dc-home-faq__intro{position:sticky;top:32px}
.dc-home-faq__intro p:last-child{font-size:1.08rem;line-height:1.6}
.dc-home-faq details{border-top:1px solid var(--dc-ink)}
.dc-home-faq details:last-child{border-bottom:1px solid var(--dc-ink)}
.dc-home-faq summary{display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;padding:24px 4px;cursor:pointer;font-family:"Roboto Condensed","Arial Narrow",sans-serif;font-size:1.35rem;font-weight:800;line-height:1.15;list-style:none}
.dc-home-faq summary::-webkit-details-marker{display:none}
.dc-home-faq summary:after{content:"+";display:grid;width:32px;height:32px;place-items:center;background:var(--dc-yellow);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:1.2rem}
.dc-home-faq details[open] summary:after{content:"−";background:var(--dc-blue);color:var(--dc-white)}
.dc-home-faq details p{max-width:760px;padding:0 48px 24px 4px;color:#55585e;font-size:1.04rem;line-height:1.65}
@media(max-width:960px){.dc-home-hero__grid,.dc-home-pillars__grid,.dc-home-about__grid,.dc-home-faq__grid{grid-template-columns:1fr}.dc-home-hero__grid{gap:54px}.dc-home-hero__visual{max-width:660px}.dc-home-problems__head,.dc-home-proof__header{grid-template-columns:1fr;gap:20px}.dc-home-problems__grid{grid-template-columns:repeat(2,1fr)}.dc-home-pillars__copy,.dc-home-faq__intro{position:static}.dc-home-proof__grid{grid-template-columns:1fr}.dc-home-proof__card{min-height:0}.dc-home-method__steps{grid-template-columns:1fr}}
@media(max-width:600px){.dc-home__wrap{width:min(calc(100% - 32px),1180px)}.dc-home-hero{padding:62px 0 58px}.dc-home-hero__grid{gap:44px}.dc-home-hero h1{font-size:clamp(2.85rem,14vw,4.3rem)}.dc-home-hero__actions{align-items:stretch;flex-direction:column}.dc-home__button{width:100%}.dc-home-hero__visual{padding:12px 12px 0;box-shadow:8px 8px 0 var(--dc-blue)}.dc-home-hero__visual img{height:270px;border-width:5px}.dc-home-hero__status{margin:-28px 8px 0;padding:18px}.dc-home-intro__grid{grid-template-columns:1fr}.dc-home-intro__label{justify-self:start}.dc-home-problems,.dc-home-pillars,.dc-home-proof,.dc-home-method,.dc-home-about,.dc-home-faq{padding:76px 0}.dc-home-problems__grid{grid-template-columns:1fr}.dc-home-problem{min-height:0}.dc-home-problem:before{margin-bottom:28px}.dc-home-pillar{grid-template-columns:86px minmax(0,1fr) auto;gap:12px}.dc-home-pillar small{font-size:.88rem}.dc-home-method__cta{align-items:stretch}.dc-home-about__grid{gap:48px}.dc-home-faq summary{font-size:1.2rem}}
@media(prefers-reduced-motion:reduce){.dc-home *{scroll-behavior:auto!important;transition:none!important}}
</style>'''

FAQ_HTML = "\n".join(
    f'''      <details{" open" if index == 0 else ""}>
        <summary>{question}</summary>
        <p>{answer}</p>
      </details>'''
    for index, (question, answer) in enumerate(FAQS)
)

MAIN = f'''<main id="content" class="dc-home">
  <section class="dc-home-hero" aria-labelledby="dc-home-title">
    <div class="dc-home__wrap dc-home-hero__grid">
      <div>
        <p class="dc-home__eyebrow dc-home__eyebrow--light">Construction business coaching for established builders and contractors</p>
        <h1 id="dc-home-title">Build a more profitable construction business that <span>does not depend on you</span> for everything.</h1>
        <p class="dc-home-hero__answer">Develop Coaching helps construction business owners strengthen five connected areas: Plan, Attract, Convert, Deliver and Scale. The aim is better control of profit, people, projects and your own time.</p>
        <div class="dc-home-hero__actions">
          <a class="dc-home__button" href="/courses/mastermind-course/">See how the Mastermind works</a>
          <a class="dc-home__button dc-home__button--ghost" href="/client-wins/">Watch real client stories</a>
        </div>
      </div>
      <div class="dc-home-hero__visual">
        <img src="/wp-content/uploads/2022/12/IMG_9990-1.jpg" alt="Greg Wilkes discussing a construction business plan with a contractor" width="537" height="430" fetchpriority="high">
        <div class="dc-home-hero__status">
          <strong>Your business control plan</strong>
          <div class="dc-home-hero__pills" aria-label="The Five Pillars">
            <span>Plan</span><span>Attract</span><span>Convert</span><span>Deliver</span><span>Scale</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="dc-home-intro" aria-label="Develop Coaching approach">
    <div class="dc-home__wrap dc-home-intro__grid">
      <span class="dc-home-intro__label">Direct answer</span>
      <p>A construction business coach helps you build the commercial systems behind the work, so growth is supported by clear numbers, suitable leads, reliable delivery and a team that can operate without every decision returning to the owner.</p>
    </div>
  </section>

  <section class="dc-home-problems" aria-labelledby="dc-home-problems-title">
    <div class="dc-home__wrap">
      <div class="dc-home-problems__head">
        <div>
          <p class="dc-home__eyebrow">What usually breaks first</p>
          <h2 id="dc-home-problems-title">A busy construction business can still be out of control.</h2>
        </div>
        <p>More work does not solve a weak system. It usually makes the pressure easier to see.</p>
      </div>
      <div class="dc-home-problems__grid">
        <article class="dc-home-problem"><h3>Profit feels uncertain</h3><p>Turnover grows, but job margin, cash and retained profit remain difficult to see.</p></article>
        <article class="dc-home-problem"><h3>Leads are the wrong fit</h3><p>Enquiries arrive, but too many waste estimating time or never become suitable projects.</p></article>
        <article class="dc-home-problem"><h3>The team waits for you</h3><p>People can do the work, but important decisions and problem solving still return to the owner.</p></article>
        <article class="dc-home-problem"><h3>Your time disappears</h3><p>You remain the estimator, manager, salesperson and final safety net, even as the business grows.</p></article>
      </div>
    </div>
  </section>

  <section class="dc-home-pillars" aria-labelledby="dc-home-pillars-title">
    <div class="dc-home__wrap dc-home-pillars__grid">
      <div class="dc-home-pillars__copy">
        <p class="dc-home__eyebrow dc-home__eyebrow--light">The Develop operating system</p>
        <h2 id="dc-home-pillars-title">Five areas. One controlled business.</h2>
        <p>Each pillar solves a different constraint, but they work together. Better leads are only useful when pricing, delivery and capacity can support them.</p>
        <a class="dc-home-pillars__route" href="/5-pillars-free-trainings/">Start with the free Five Pillars training</a>
      </div>
      <nav class="dc-home-pillars__board" aria-label="Explore the Five Pillars">
        <a class="dc-home-pillar" href="/5-pillars-free-trainings/plan/"><span class="dc-home-pillar__name">Plan</span><span><strong>Know the numbers and the next priority</strong><small>Goals, commercial visibility and a plan the team can follow.</small></span><span class="dc-home-pillar__arrow" aria-hidden="true">→</span></a>
        <a class="dc-home-pillar" href="/5-pillars-free-trainings/attract/"><span class="dc-home-pillar__name">Attract</span><span><strong>Create a steadier flow of suitable enquiries</strong><small>Positioning, lead sources and follow-up built around your ideal work.</small></span><span class="dc-home-pillar__arrow" aria-hidden="true">→</span></a>
        <a class="dc-home-pillar" href="/5-pillars-free-trainings/convert/"><span class="dc-home-pillar__name">Convert</span><span><strong>Turn the right enquiries into profitable projects</strong><small>Qualification, pricing, proposals and a consistent sales process.</small></span><span class="dc-home-pillar__arrow" aria-hidden="true">→</span></a>
        <a class="dc-home-pillar" href="/5-pillars-free-trainings/deliver/"><span class="dc-home-pillar__name">Deliver</span><span><strong>Run work with clearer systems and accountability</strong><small>Project control, team roles and job-level commercial discipline.</small></span><span class="dc-home-pillar__arrow" aria-hidden="true">→</span></a>
        <a class="dc-home-pillar" href="/5-pillars-free-trainings/scale/"><span class="dc-home-pillar__name">Scale</span><span><strong>Build capacity without adding owner dependence</strong><small>Leadership, structure and systems that protect your time.</small></span><span class="dc-home-pillar__arrow" aria-hidden="true">→</span></a>
      </nav>
    </div>
  </section>

  <section class="dc-home-proof" aria-labelledby="dc-home-proof-title">
    <div class="dc-home__wrap">
      <div class="dc-home-proof__header">
        <div><p class="dc-home__eyebrow">Reported client outcomes</p><h2 id="dc-home-proof-title">See what changed when owners built more control.</h2></div>
        <p>These are client-reported experiences from their recorded stories. Results vary with the business and the work implemented.</p>
      </div>
      <div class="dc-home-proof__grid">
        <article class="dc-home-proof__card"><p class="dc-home-proof__focus">Turnover and operations</p><h3>Marek</h3><p>Marek reports turnover of just over £1 million before joining, then doubling within a year, alongside improvements to operations and marketing.</p><p class="dc-home-proof__source">Client-reported recorded story</p></article>
        <article class="dc-home-proof__card"><p class="dc-home-proof__focus">Systems and owner time</p><h3>Richard</h3><p>Richard reports turnover moving from about £750,000 to £1.1 million as systems, delegation and professional branding freed more time.</p><p class="dc-home-proof__source">Client-reported recorded story</p></article>
        <article class="dc-home-proof__card"><p class="dc-home-proof__focus">CRM and lead handling</p><h3>Jordan Stubley</h3><p>Jordan says better CRM processes and lead handling improved day-to-day organisation and saved the team hours of work.</p><p class="dc-home-proof__source">Client-reported recorded story</p></article>
      </div>
      <a class="dc-home-proof__link" href="/client-wins/">Explore all client stories and source videos →</a>
    </div>
  </section>

  <section class="dc-home-method" aria-labelledby="dc-home-method-title">
    <div class="dc-home__wrap">
      <div class="dc-home-method__head"><p class="dc-home__eyebrow dc-home__eyebrow--light">How the coaching works</p><h2 id="dc-home-method-title">Find the constraint. Build the system. Review the result.</h2></div>
      <div class="dc-home-method__steps">
        <article class="dc-home-method__step"><span>STEP 01</span><h3>Diagnose</h3><p>Map the current numbers, pressure points and goals to identify the part of the business that needs attention first.</p></article>
        <article class="dc-home-method__step"><span>STEP 02</span><h3>Build</h3><p>Install a practical process, tool or team rhythm that fits the way your construction business actually operates.</p></article>
        <article class="dc-home-method__step"><span>STEP 03</span><h3>Review</h3><p>Track what changed, remove the next constraint and keep the business moving towards more profit and control.</p></article>
      </div>
      <div class="dc-home-method__cta"><p>Not sure which part of the business should come first? Use a call to map the next twelve months and decide whether the Mastermind is the right fit.</p><a class="dc-home__button" href="/schedule-a-call/">Schedule a call</a></div>
    </div>
  </section>

  <section class="dc-home-about" aria-labelledby="dc-home-about-title">
    <div class="dc-home__wrap dc-home-about__grid">
      <div class="dc-home-about__image"><img src="/wp-content/uploads/2023/01/Greg-Wilkes.jpg" alt="Greg Wilkes, construction business coach and founder of Develop Coaching" width="682" height="711" loading="lazy"></div>
      <div class="dc-home-about__copy"><p class="dc-home__eyebrow">Built from construction experience</p><h2 id="dc-home-about-title">Coaching from someone who understands life on the tools and in the office.</h2><p>Greg Wilkes started with a trade apprenticeship, built construction businesses and experienced the pressure of growing while still carrying too much of the work himself. Develop Coaching turns those lessons into practical systems for construction business owners.</p><p><a href="/about-greg-wilkes/">Read Greg's construction business story →</a></p></div>
    </div>
  </section>

  <section class="dc-home-faq" aria-labelledby="dc-home-faq-title">
    <div class="dc-home__wrap dc-home-faq__grid">
      <div class="dc-home-faq__intro"><p class="dc-home__eyebrow">Construction coaching questions</p><h2 id="dc-home-faq-title">Straight answers before you take the next step.</h2><p>Use these answers to understand what construction business coaching covers and whether it matches the stage your company is at.</p></div>
      <div>{FAQ_HTML}
      </div>
    </div>
  </section>
</main>'''


def replace_once(document: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, document, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Missing or ambiguous {label}")
    return updated


def update_schema(document: str) -> str:
    pattern = re.compile(
        r'<script type="application/ld\+json" class="rank-math-schema-pro">(.*?)</script>',
        re.DOTALL,
    )
    match = pattern.search(document)
    if not match:
        raise ValueError("Rank Math schema not found")
    schema = json.loads(match.group(1))
    graph = schema.get("@graph", [])
    webpage = next(
        (
            node
            for node in graph
            if node.get("@id") == "https://develop-coaching.com/#webpage"
        ),
        None,
    )
    if not webpage:
        raise ValueError("Homepage WebPage schema not found")
    node_types = webpage.get("@type", [])
    if isinstance(node_types, str):
        node_types = [node_types]
    if "WebPage" not in node_types:
        node_types.insert(0, "WebPage")
    if "FAQPage" not in node_types:
        node_types.append("FAQPage")
    webpage["@type"] = node_types
    webpage["name"] = TITLE
    webpage["description"] = DESCRIPTION
    webpage["dateModified"] = "2026-08-28T00:00:00+10:00"
    webpage["mainEntity"] = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        }
        for question, answer in FAQS
    ]
    replacement = (
        '<script type="application/ld+json" class="rank-math-schema-pro">'
        + json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
        + "</script>"
    )
    return document[: match.start()] + replacement + document[match.end() :]


def transform(document: str) -> str:
    document = replace_once(document, r"<title>.*?</title>", f"<title>{TITLE}</title>", "title")
    for name, value in (
        ("description", DESCRIPTION),
        ("og:title", TITLE),
        ("og:description", DESCRIPTION),
        ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        if name.startswith("og:"):
            pattern = rf'(<meta property="{re.escape(name)}" content=")[^"]*("\s*/?>)'
        else:
            pattern = rf'(<meta name="{re.escape(name)}" content=")[^"]*("\s*/?>)'
        document = replace_once(document, pattern, rf"\g<1>{value}\g<2>", name)

    style_pattern = rf'<style id="{STYLE_ID}">.*?</style>'
    if re.search(style_pattern, document, flags=re.DOTALL):
        document = replace_once(document, style_pattern, STYLES, "homepage styles")
    else:
        if "</head>" not in document:
            raise ValueError("Head insertion point not found")
        document = document.replace("</head>", STYLES + "\n</head>", 1)

    document = replace_once(
        document,
        r'<main id="content"[^>]*>.*?</main>',
        MAIN,
        "homepage main",
    )
    return update_schema(document)


def main() -> None:
    original = PAGE.read_text(encoding="utf-8")
    PAGE.write_text(transform(original), encoding="utf-8")


if __name__ == "__main__":
    main()
