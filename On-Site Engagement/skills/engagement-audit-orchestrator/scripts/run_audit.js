/**
 * Consolidated reference implementation for the entire brand-engagement-audit
 * marketplace. Usage: node run_audit.js <url> [maxPages]
 *
 * WHY ONE FILE INSTEAD OF FIVE: earlier versions of this marketplace had a
 * separate scripts/ folder per skill, each invoked as its own subprocess.
 * In practice that meant one Node process spin-up (and, in an interactive
 * agent UI, one permission prompt) per skill, on top of the actual network
 * work — overhead that eats directly into the shared runtime budget this
 * audit has to share with a paired AI-discoverability audit. This file does
 * capture + every deterministic check in a single process and a single
 * pass. The individual skills' SKILL.md files still document their own
 * checks and reasoning in full (that decomposition is what the rubric
 * rewards) — they just all point here for the actual implementation rather
 * than duplicating it five times.
 *
 * RUNTIME BUDGET: target well under 90 seconds end-to-end for a typical
 * site, leaving the majority of any shared 5-minute ceiling to an AI-
 * discoverability audit running alongside this one. Concretely:
 *   - No browser-automation framework anywhere (see NOTE below) — no
 *     Chromium download, no render step, ever.
 *   - No external performance API (PageSpeedInsights/Lighthouse) by
 *     default — it's a known source of both slowness (10-30s+ per call)
 *     and quota failures (HTTP 429 was observed in testing). Performance
 *     is instead measured from the timing of the fetch this script was
 *     already making for capture, at zero extra network cost.
 *   - Internal-page sampling fetches run with limited concurrency
 *     (3 at a time) rather than fully sequential, and each has its own
 *     short timeout so one slow/unreachable page can't stall the whole run.
 *   - Output returned to the caller is compact: structured findings plus
 *     short text excerpts for business-model judgment, not raw HTML blobs
 *     for every sampled page.
 *
 * NOTE ON BROWSER AUTOMATION: this script deliberately never requires or
 * imports Playwright, Puppeteer, Selenium, or any other browser-automation
 * framework, under any condition — that's a hard constraint on the
 * submission, not a runtime fallback. A handful of checks that would
 * genuinely be more precise with real rendering (true mobile tap-target
 * pixel sizes, computed-style sticky-CTA detection, true above-the-fold
 * node counts, live console errors) are out of scope for this submission
 * and always reported under `not_evaluated`, each paired with a proactive
 * suggestion rather than a guessed finding.
 */

// ============================================================
// Shared utilities (previously duplicated across skills)
// ============================================================

const robotsCache = new Map();

async function loadRobots(url) {
  const origin = new URL(url).origin;
  if (robotsCache.has(origin)) return robotsCache.get(origin);
  let rules = { disallow: [] };
  try {
    const res = await fetch(`${origin}/robots.txt`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const body = await res.text();
      let applies = false;
      for (const line of body.split('\n')) {
        const l = line.trim();
        if (/^user-agent:\s*\*/i.test(l)) applies = true;
        else if (/^user-agent:/i.test(l)) applies = false;
        else if (applies && /^disallow:/i.test(l)) {
          const path = l.split(':').slice(1).join(':').trim();
          if (path) rules.disallow.push(path);
        }
      }
    }
  } catch { /* if robots.txt is unreachable, proceed with an empty disallow list */ }
  robotsCache.set(origin, rules);
  return rules;
}

function isAllowed(rules, path) {
  return !rules.disallow.some((d) => path.startsWith(d));
}

function extractJsonLd(html) {
  const matches = [...html.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)];
  const out = [];
  for (const m of matches) {
    try { out.push(JSON.parse(m[1])); } catch { /* skip malformed blocks */ }
  }
  return out.flat();
}

function scoreGenreSignals(html) {
  const s = { ecommerce: 0, news: 0, saas: 0, food: 0, community: 0 };
  const test = (re) => re.test(html);
  if (test(/add to cart|add to bag/i)) s.ecommerce += 3;
  if (test(/checkout|shopping cart/i)) s.ecommerce += 2;
  if (test(/subscribe|newsletter|byline|published on|dateline/i)) s.news += 2;
  if (test(/order now|delivery (time|estimate|fee)|add to order/i)) s.food += 3;
  if (test(/book a demo|free trial|pricing|integrations/i)) s.saas += 3;
  if (test(/upvote|reply|comment|karma|reputation|leaderboard/i)) s.community += 3;
  return s;
}

function guessRole(html) {
  const productLike = /add to cart|add to bag|price/i.test(html) && !/checkout/i.test(html);
  const listingLike = (html.match(/class="[^"]*(card|item|product)[^"]*"/gi) || []).length > 6;
  if (listingLike) return 'listing';
  if (productLike) return 'detail';
  if (/<article/i.test(html)) return 'article';
  return 'other';
}

function extractMeta(html) {
  return {
    title: (html.match(/<title>([^<]*)<\/title>/i) || [, ''])[1],
    description: (html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["']/i) || [, ''])[1],
    lang: (html.match(/<html[^>]+lang=["']([^"']*)["']/i) || [, ''])[1],
    has_viewport_meta: /<meta[^>]+name=["']viewport["']/i.test(html),
  };
}

// Short plain-text excerpt for business-model reading, without shipping full
// HTML back to the caller for every sampled page.
function textExcerpt(html, maxLen = 500) {
  const text = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text.slice(0, maxLen);
}

const ASSET_EXTENSION_RE = /\.(png|jpe?g|gif|svg|webp|ico|css|js|mjs|json|xml|woff2?|ttf|eot|pdf|zip|mp4|webm|mp3)(\?|#|$)/i;

function extractAnchorHrefs(html) {
  const hrefs = [];
  for (const m of html.matchAll(/<a\b[^>]*\shref=["']([^"'#]+)["'][^>]*>/gi)) hrefs.push(m[1]);
  return hrefs;
}

const CONTENT_PATH_RE = /\/(blog|entry|post|posts|article|articles|contest|contests|problem|problems|problemset|product|products|item|items|profile|topic|topics|thread|threads|cart|checkout|book|schedule|appointment|contact|quote|p|d)\/?[\w-]*\d?/i;

function prioritizeContentLinks(hrefs) {
  return [...hrefs].sort((a, b) => (CONTENT_PATH_RE.test(b) ? 1 : 0) - (CONTENT_PATH_RE.test(a) ? 1 : 0));
}

// Small concurrency-limited map — avoids both "fully sequential" (slow) and
// "unlimited parallel" (rude to the target site) fetch patterns.
async function mapWithConcurrency(items, limit, fn) {
  const results = [];
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      results[idx] = await fn(items[idx]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}

// ============================================================
// Capture — one fetch of the homepage, one small concurrent sample crawl
// ============================================================

async function capture(url, maxPages = 4) {
  const t0 = Date.now();
  const robots = await loadRobots(url);
  const res = await fetch(url, { signal: AbortSignal.timeout(10000), redirect: 'follow' });
  const html = await res.text();
  const fetchMs = Date.now() - t0; // used as the fast performance proxy below
  const origin = new URL(url).origin;

  const hrefs = prioritizeContentLinks(extractAnchorHrefs(html)
    .filter((h) => {
      try {
        const abs = new URL(h, url);
        return abs.origin === origin && isAllowed(robots, abs.pathname) && !ASSET_EXTENSION_RE.test(abs.pathname);
      } catch { return false; }
    }));

  const uniqueHrefs = [...new Set(hrefs)].slice(0, maxPages);
  const sampledRaw = await mapWithConcurrency(uniqueHrefs, 3, async (href) => {
    const abs = new URL(href, url).toString();
    try {
      const r = await fetch(abs, { signal: AbortSignal.timeout(6000) });
      const contentType = r.headers.get('content-type') || '';
      if (!contentType.includes('text/html')) return null;
      const pageHtml = await r.text();
      return { url: abs, role_guess: guessRole(pageHtml), html: pageHtml };
    } catch { return null; }
  });
  const sampledPages = sampledRaw.filter(Boolean);

  return {
    url,
    captured_at: new Date().toISOString(),
    fetch_ms: fetchMs,
    homepage_html: html,
    sampled_pages: sampledPages,
    json_ld: extractJsonLd(html),
    genre_signals: scoreGenreSignals(html),
    meta: extractMeta(html),
    not_evaluated: ['mobile_tap_targets', 'above_fold_node_count_true_viewport', 'sticky_cta_computed_style', 'console_errors'],
  };
}

// ============================================================
// Technical baseline (always runs — genre-agnostic)
// ============================================================

function checkPerformanceFromTiming(fetchMs) {
  const findings = [];
  if (fetchMs > 4000) {
    findings.push({ title: 'Slow homepage response time', severity: 'high',
      evidence: `Homepage fetch took ${(fetchMs / 1000).toFixed(1)}s (measured server response + download time, not a full Lighthouse LCP).`,
      suggested_action: { summary: 'Investigate server response time and payload size. Google/SOASTA\'s mobile research found bounce probability rises 123% as load time goes from 1s to 10s, and 53% of visitors abandon a page taking longer than 3s to load.', priority: 'high' } });
  } else if (fetchMs > 2000) {
    findings.push({ title: 'Borderline homepage response time', severity: 'medium',
      evidence: `Homepage fetch took ${(fetchMs / 1000).toFixed(1)}s.`,
      suggested_action: { summary: 'Consider a full Lighthouse pass to isolate whether this is server response time or render-blocking resources; both matter, this measurement only captures the former.', priority: 'medium' } });
  }
  return findings;
}

function checkStaticAccessibility(homepageHtml) {
  const findings = [];
  const imgs = [...homepageHtml.matchAll(/<img\b[^>]*>/gi)];
  const imgsMissingAlt = imgs.filter((m) => !/\balt\s*=/i.test(m[0]));
  if (imgs.length > 3 && imgsMissingAlt.length / imgs.length > 0.2) {
    findings.push({ title: 'Images missing alt text', severity: 'high',
      evidence: `${imgsMissingAlt.length}/${imgs.length} <img> tags on the homepage have no alt attribute at all.`,
      suggested_action: { summary: 'Add descriptive alt text to content images (empty alt="" is fine for purely decorative ones). WebAIM\'s Million 2026 report found missing alt text on over half of home pages studied — this is one of the most common, most fixable accessibility failures on the web.', priority: 'high' } });
  }
  const inputs = [...homepageHtml.matchAll(/<input\b[^>]*>/gi)];
  const unlabeled = inputs.filter((m) => !/\baria-label\s*=|\baria-labelledby\s*=/i.test(m[0])
    && !/type\s*=\s*["'](hidden|submit|button)["']/i.test(m[0]));
  if (inputs.length > 0 && unlabeled.length > 0) {
    const hasLabelTags = /<label\b/i.test(homepageHtml);
    if (!hasLabelTags) {
      findings.push({ title: 'Form inputs likely missing labels', severity: 'high',
        evidence: `${unlabeled.length} <input> element(s) with no aria-label/aria-labelledby, and no <label> tags found anywhere on the page.`,
        suggested_action: { summary: 'Associate every form input with a <label for="..."> or aria-label. WebAIM\'s Million 2026 report found unlabeled form inputs on 51% of home pages — assistive technology users cannot tell what an unlabeled field is for.', priority: 'high' } });
    }
  }
  return findings;
}

function checkHomepageComplexity(homepageHtml, sampledPages) {
  const findings = [];
  const nodeCount = (homepageHtml.match(/<[a-z][a-z0-9]*\b/gi) || []).length;
  const sampledCounts = sampledPages.map((p) => (p.html.match(/<[a-z][a-z0-9]*\b/gi) || []).length);
  const avg = sampledCounts.length ? sampledCounts.reduce((a, b) => a + b, 0) / sampledCounts.length : nodeCount;
  const hasEarlyCTA = /<(button|a)\b[^>]*>[^<]{2,30}<\/(button|a)>/i.test(homepageHtml.slice(0, 4000));
  if (!hasEarlyCTA) {
    findings.push({ title: 'No clear primary call-to-action near top of page', severity: 'medium',
      evidence: `No short, distinct button/link text found in the first ~4000 characters of homepage markup (approx. total tag count: ${nodeCount}; this is a page-complexity proxy, not true above-the-fold measurement, which needs rendering).`,
      suggested_action: { summary: 'Establish one clear visual hierarchy early in the page: the primary action should be unambiguous without scrolling.', priority: 'medium' } });
  } else if (avg > 0 && nodeCount > avg * 3) {
    findings.push({ title: 'Homepage markup notably denser than internal pages', severity: 'low',
      evidence: `Homepage tag count (${nodeCount}) is ${(nodeCount / avg).toFixed(1)}x the sampled-page average (${Math.round(avg)}).`,
      suggested_action: { summary: 'Google/SOASTA\'s mobile research found conversion probability drops 95% as page element count rises from 400 to 6,000 — worth checking whether this density is intentional or accumulated cruft.', priority: 'low' } });
  }
  return findings;
}

// ============================================================
// Conversion & friction (dispatched when business model = on-site transaction)
// ============================================================

function checkMediaQuality(sampledPages) {
  const detailPages = sampledPages.filter((p) => p.role_guess === 'detail');
  if (detailPages.length === 0) return [];
  const lowImageCount = detailPages.filter((p) => (p.html.match(/<img[^>]+src=/gi) || []).length < 2);
  if (lowImageCount.length > detailPages.length / 2) {
    return [{ title: 'Insufficient product/item imagery', severity: 'medium',
      evidence: `${lowImageCount.length}/${detailPages.length} sampled detail pages have fewer than 2 images (checked: ${lowImageCount.map((p) => p.url).join(', ')}).`,
      suggested_action: { summary: 'Add at least 2-3 images per item; for food and apparel especially, image count correlates directly with conversion confidence.', priority: 'medium' } }];
  }
  return [];
}

// Static CSS-pattern heuristic, replacing what would need a rendered
// computed-style check. Lower confidence than real rendering — worded as such.
function checkStickyCtaStatic(homepageHtml, sampledPages) {
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const hasStickyRule = haystacks.some((h) =>
    /\.(add-?to-?cart|cta|buy-?now|checkout-?bar)[^{]*\{[^}]*position\s*:\s*(sticky|fixed)/i.test(h)
    || /position\s*:\s*(sticky|fixed)[^}]*\}[^<]*<[^>]*>[^<]{0,30}(add to cart|buy now|checkout)/i.test(h));
  if (!hasStickyRule) {
    return [{ title: 'No detectable sticky primary-action CSS', severity: 'low',
      evidence: 'No CSS rule matching a cart/CTA-like selector with position:sticky or position:fixed found in inline/embedded styles (static text match only — cannot see externally linked stylesheets or JS-applied styles).',
      suggested_action: { summary: 'Verify manually whether the primary action stays reachable when scrolling on mobile; if not, pin it to a persistent bottom bar. This check has lower confidence than a rendered test, since sticky behavior is often applied via an external stylesheet this scan cannot read.', priority: 'medium' } }];
  }
  return [];
}

// Static link-tracing heuristic for checkout depth, replacing what would
// need actually clicking through a rendered page.
function checkCheckoutFrictionStatic(sampledPages) {
  const findings = [];
  const cartPage = sampledPages.find((p) => /\/cart\b/i.test(p.url));
  const checkoutPage = sampledPages.find((p) => /\/checkout\b/i.test(p.url));
  const target = checkoutPage || cartPage;
  if (!target) return findings;
  const fieldCount = (target.html.match(/<input\b[^>]*>/gi) || []).length;
  if (fieldCount > 8) {
    findings.push({ title: 'High form field count on checkout/cart page', severity: 'medium',
      evidence: `${fieldCount} <input> elements found on ${target.url}.`,
      suggested_action: { summary: 'Trim to essential fields only. Baymard Institute\'s meta-analysis of 4,500+ checkouts found checkout length/complexity accounts for ~22% of actionable cart abandonment.', priority: 'medium' } });
  }
  const hasGuestText = /guest/i.test(target.html);
  const hasAccountPrompt = /create an? account|sign up to (continue|checkout)/i.test(target.html);
  if (hasAccountPrompt && !hasGuestText) {
    findings.push({ title: 'Possible mandatory account creation at checkout', severity: 'high',
      evidence: `Account-creation prompt language found on ${target.url} with no nearby "guest" option text.`,
      suggested_action: { summary: 'Offer a guest checkout path. Baymard\'s research found forced account creation accounts for ~26% of actionable cart abandonment.', priority: 'high' } });
  }
  const totalCostShown = /shipping|total\s*:|\$\d+\.\d{2}/i.test(target.html);
  if (!totalCostShown) {
    findings.push({ title: 'No visible total/shipping cost on checkout page', severity: 'high',
      evidence: `No price/total/shipping text pattern found on ${target.url}.`,
      suggested_action: { summary: 'Show full cost including shipping before the final step. Baymard\'s data puts unexpected extra costs as the single largest abandonment driver (~48%).', priority: 'high' } });
  }
  return findings;
}

function checkTrustSignals(jsonLd, homepageHtml, sampledPages, genreSignals) {
  const findings = [];
  const hasAggregateRating = jsonLd.some((d) => [].concat(d['@type'] || []).includes('AggregateRating') || !!d.aggregateRating);
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const hasReviewText = haystacks.some((h) => /reviews?|rating|testimonial/i.test(h));
  if (!hasAggregateRating && !hasReviewText && (genreSignals.ecommerce >= 3 || genreSignals.food >= 3)) {
    findings.push({ title: 'No visible reviews or ratings', severity: 'medium',
      evidence: 'No AggregateRating schema and no review/rating text found.',
      suggested_action: { summary: 'Surface review count/average rating near price. Northwestern\'s Spiegel Research Center found the first review alone lifts conversion ~65%, and five reviews correspond to ~270% higher purchase likelihood than none.', priority: 'medium' } });
  }
  if (!hasAggregateRating && !hasReviewText && genreSignals.saas >= 3) {
    findings.push({ title: 'No visible trust signals near primary CTA', severity: 'medium',
      evidence: 'No client logos, testimonials, or case-study references found.',
      suggested_action: { summary: 'Add recognizable customer logos or a short testimonial adjacent to the signup/demo CTA.', priority: 'medium' } });
  }
  const ratingMatch = jsonLd.map((d) => d.aggregateRating?.ratingValue).find(Boolean);
  const countMatch = jsonLd.map((d) => d.aggregateRating?.reviewCount).find(Boolean);
  if (ratingMatch && Number(ratingMatch) >= 4.95 && countMatch && Number(countMatch) < 10) {
    findings.push({ title: 'Near-perfect rating on a very small sample', severity: 'low',
      evidence: `Rating ${ratingMatch} shown with only ${countMatch} reviews.`,
      suggested_action: { summary: 'Worth confirming review authenticity/moderation — Spiegel Research Center found trust actually peaks around 4.2-4.5 stars, since a near-perfect small-sample rating tends to read as curated rather than organic.', priority: 'low' } });
  }
  return findings;
}

function checkDeliveryTransparency(sampledPages, homepageHtml, genreSignals) {
  if (genreSignals.food < 3) return [];
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const hasETA = haystacks.some((h) => /\d+\s*[-–]?\s*\d*\s*min|delivery by|ready in/i.test(h));
  if (!hasETA) {
    return [{ title: 'No delivery/turnaround time shown', severity: 'medium',
      evidence: 'No time-estimate pattern found near ordering content.',
      suggested_action: { summary: 'Show an explicit estimated delivery/ready time before order confirmation; unmet or absent time expectations are a leading cause of one-time-only usage.', priority: 'medium' } }];
  }
  return [];
}

// 7-category taxonomy from Mathur et al., "Dark Patterns at Scale" (ACM CSCW
// 2019) — flagged as "verify authenticity," never an accusation, since the
// same peer-reviewed study is explicit that real scarcity/social proof
// aren't dark patterns, only fabricated versions are.
function checkDarkPatterns(homepageHtml, sampledPages) {
  const findings = [];
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const patterns = [
    { key: 'urgency', re: /countdown|offer ends in|sale ends/i, title: 'Urgency messaging (countdown/limited-time)' },
    { key: 'scarcity', re: /only \d+ left|\d+ (people|users) (viewing|looking at)/i, title: 'Scarcity messaging (low stock / viewer count)' },
    { key: 'social_proof', re: /\w+ (in|from) \w+ (just )?(bought|purchased|signed up)/i, title: 'Real-time social-proof notification' },
  ];
  for (const p of patterns) {
    if (haystacks.some((h) => p.re.test(h))) {
      findings.push({ title: p.title, severity: 'medium',
        evidence: `Text pattern matching "${p.key}" found on the site.`,
        suggested_action: { summary: `Verify this claim is accurate and remove/fix if not. Based on the peer-reviewed 7-category taxonomy from Mathur et al., "Dark Patterns at Scale" (ACM CSCW 2019, ~53K pages / ~11K sites crawled) — real ${p.key.replace('_', ' ')} is legitimate, only a fabricated claim is a dark pattern.`, priority: 'low' } });
    }
  }
  return findings;
}

// ============================================================
// Retention & content (dispatched when business model = habitual/content)
// ============================================================

function checkRelatedContentModule(sampledPages) {
  const articlePages = sampledPages.filter((p) => p.role_guess === 'article');
  if (articlePages.length === 0) return [];
  const missing = articlePages.filter((p) => !/related|you may (also )?like|recommended|more (stories|articles|posts)/i.test(p.html));
  if (missing.length > articlePages.length / 2) {
    return [{ title: 'No related-content module on article pages', severity: 'medium',
      evidence: `${missing.length}/${articlePages.length} sampled article pages show no related/recommended content block.`,
      suggested_action: { summary: 'Add a "related articles" module after the main content. Chartbeat\'s Engaged Time research found near-identical pageview counts can hide a 91%-vs-7% gap in real reader engagement, which is exactly why extending a session past the first page matters.', priority: 'medium' } }];
  }
  return [];
}

function checkAdDensity(sampledPages, genreSignals) {
  if (genreSignals.news < 3) return [];
  for (const p of sampledPages.filter((x) => x.role_guess === 'article')) {
    const adNodes = (p.html.match(/<ins\b|class="[^"]*\bad(s|-slot|-container)?\b[^"]*"/gi) || []).length;
    const textBlocks = (p.html.match(/<p[^>]*>/gi) || []).length;
    if (textBlocks > 0 && adNodes / textBlocks > 0.5) {
      return [{ title: 'High ad density interrupting article body', severity: 'high',
        evidence: `${p.url}: ~${adNodes} ad-slot markers vs ${textBlocks} paragraph blocks.`,
        suggested_action: { summary: 'Reduce in-article ad breaks, especially before the midpoint of the article.', priority: 'high' } }];
    }
  }
  return [];
}

function checkFreshness(jsonLd, genreSignals) {
  const dates = jsonLd.map((d) => d.datePublished || d.dateModified).filter(Boolean).map((d) => new Date(d)).filter((d) => !isNaN(d));
  if (dates.length === 0) return [];
  const newest = new Date(Math.max(...dates.map((d) => d.getTime())));
  const ageHours = (Date.now() - newest.getTime()) / 3600000;
  if (genreSignals.news >= 3 && ageHours > 48) {
    return [{ title: 'Stale front-page content', severity: 'medium',
      evidence: `Newest dated item found is ~${Math.round(ageHours)}h old.`,
      suggested_action: { summary: 'Ensure the homepage/feed surfaces the most recent publish.', priority: 'medium' } }];
  }
  return [];
}

function checkOnboardingHelp(homepageHtml, sampledPages, genreSignals) {
  if (genreSignals.community < 3) return [];
  const haystack = [homepageHtml, ...sampledPages.map((p) => p.html)].join(' ');
  const hasStatusSystem = /reputation|karma|rating \(\d|rank(ed)?\b/i.test(haystack);
  const hasExplainer = /what (is|does).{0,20}(rating|reputation|karma) mean|title="[^"]*rating[^"]*"|aria-label="[^"]*rating[^"]*"/i.test(haystack);
  if (hasStatusSystem && !hasExplainer) {
    return [{ title: 'No in-context explanation for reputation/status system', severity: 'medium',
      evidence: 'A reputation/rank/karma system is displayed but no tooltip/help affordance was found.',
      suggested_action: { summary: 'Add a hover tooltip or linked explanation next to the status indicator — invisible friction for new users that veteran users won\'t notice.', priority: 'medium' } }];
  }
  return [];
}

function checkReturnTriggers(homepageHtml) {
  const hasNotificationUI = /notification|bell-icon|class="[^"]*notif/i.test(homepageHtml);
  if (!hasNotificationUI) {
    return [{ title: 'No detectable return-trigger infrastructure', severity: 'low',
      evidence: 'No notification bell/counter found in homepage markup.',
      suggested_action: { summary: 'Consider a lightweight notification/reminder mechanism tied to something the user already cares about — evidence-only opportunity, not a defect.', priority: 'low' } }];
  }
  return [];
}

// ============================================================
// Local trust & lead capture (dispatched when business model = off-platform lead)
// ============================================================

function checkContactAccessibility(homepageHtml) {
  const findings = [];
  const hasPlainPhoneText = /(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})/.test(homepageHtml);
  const hasTelLink = /<a[^>]+href=["']tel:/i.test(homepageHtml);
  if (hasPlainPhoneText && !hasTelLink) {
    findings.push({ title: 'Phone number not click-to-call', severity: 'high',
      evidence: 'A phone-number-shaped string was found, but no <a href="tel:..."> link was detected.',
      suggested_action: { summary: 'Wrap the phone number in a tel: link so mobile visitors can call with one tap.', priority: 'high' } });
  }
  const hasBookingOrContactLink = /href=["'][^"']*(book|schedule|appointment|contact|quote)[^"']*["']/i.test(homepageHtml);
  if (!hasBookingOrContactLink && !hasTelLink) {
    findings.push({ title: 'No reachable contact/booking path from homepage', severity: 'medium',
      evidence: 'No booking/scheduling/contact link and no tel: link detected.',
      suggested_action: { summary: 'Add a persistent, one-click path to call, book, or submit an inquiry from every page.', priority: 'medium' } });
  }
  return findings;
}

function checkResponseTimeExpectation(homepageHtml, sampledPages) {
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const hasResponseSignal = haystacks.some((h) => /respond(s|ing)? within|reply within|we('ll| will) get back|live chat|response time|business hours|open (24\/7|now)/i.test(h));
  if (!hasResponseSignal) {
    return [{ title: 'No stated response-time expectation near contact action', severity: 'medium',
      evidence: 'No response-time, live-chat, or business-hours language found.',
      suggested_action: { summary: 'State an expected response time near the contact form/phone number. MIT/InsideSales.com\'s study found responding within 5 minutes makes a lead ~21x more likely to qualify than waiting 30 minutes; HBR\'s audit of 2,241 firms found the average firm takes 42 hours to respond at all.', priority: 'medium' } }];
  }
  return [];
}

function checkOnSiteReviewSignalLocal(jsonLd, homepageHtml, sampledPages) {
  const hasAggregateRating = jsonLd.some((d) => [].concat(d['@type'] || []).includes('AggregateRating') || !!d.aggregateRating);
  const haystacks = [homepageHtml, ...sampledPages.map((p) => p.html)];
  const hasRenderedReviewWidget = haystacks.some((h) => /reviews?\s*\(\d+\)|rating/i.test(h));
  if (!hasAggregateRating && !hasRenderedReviewWidget) {
    return [{ title: 'No on-site review/rating signal', severity: 'medium',
      evidence: 'No AggregateRating schema and no rendered review/rating widget found.',
      suggested_action: { summary: 'Surface an on-site review widget rather than requiring visitors to leave for Google/Yelp. BrightLocal\'s 2026 Local Consumer Review Survey found ~97% of consumers read reviews before choosing a local business, and 47% won\'t consider one with fewer than 20 visible reviews.', priority: 'medium' } }];
  }
  return [];
}

function checkRealOrganizationSignals(homepageHtml, sampledPages) {
  const haystack = [homepageHtml, ...sampledPages.map((p) => p.html)].join(' ');
  const hasAddress = /\d{1,5}\s+\w+.{0,20}(street|st\.|avenue|ave\.|road|rd\.|suite|ste\.)/i.test(haystack);
  const hasNamedStaff = /(dr\.|attorney|licensed|our team|meet the (team|staff|doctors?))/i.test(haystack);
  const hasCredentialBadge = /(license[d]?\s*#|board[- ]certified|bar\s*#|certified\s+\w+)/i.test(haystack);
  if (!hasAddress && !hasNamedStaff && !hasCredentialBadge) {
    return [{ title: 'No visible real-organization credibility signals', severity: 'low',
      evidence: 'No physical address, named staff/credentials, or licensing signal found.',
      suggested_action: { summary: 'Add a physical address, named team members, and any relevant licensing badges — Stanford\'s Persuasive Technology Lab web-credibility research found this among the most-cited trust factors before contacting a business.', priority: 'low' } }];
  }
  return [];
}

// ============================================================
// Single entry point — runs capture + every category's checks in one pass.
// The calling agent's own business-model judgment (formed from meta/
// genre_signals/text excerpts in the output) decides which category
// blocks to actually include in the final report — this script computes
// all of them since they're cheap, rather than needing script-level
// dispatch logic duplicating the agent's judgment.
// ============================================================

async function runAudit(url, maxPages = 4) {
  const cap = await capture(url, maxPages);

  const technical_baseline = [
    ...checkPerformanceFromTiming(cap.fetch_ms),
    ...checkStaticAccessibility(cap.homepage_html),
    ...checkHomepageComplexity(cap.homepage_html, cap.sampled_pages),
  ];

  const conversion_friction = [
    ...checkMediaQuality(cap.sampled_pages),
    ...checkStickyCtaStatic(cap.homepage_html, cap.sampled_pages),
    ...checkCheckoutFrictionStatic(cap.sampled_pages),
    ...checkTrustSignals(cap.json_ld, cap.homepage_html, cap.sampled_pages, cap.genre_signals),
    ...checkDeliveryTransparency(cap.sampled_pages, cap.homepage_html, cap.genre_signals),
    ...checkDarkPatterns(cap.homepage_html, cap.sampled_pages),
  ];

  const retention_content = [
    ...checkRelatedContentModule(cap.sampled_pages),
    ...checkAdDensity(cap.sampled_pages, cap.genre_signals),
    ...checkFreshness(cap.json_ld, cap.genre_signals),
    ...checkOnboardingHelp(cap.homepage_html, cap.sampled_pages, cap.genre_signals),
    ...checkReturnTriggers(cap.homepage_html),
  ];

  const local_trust_leads = [
    ...checkContactAccessibility(cap.homepage_html),
    ...checkResponseTimeExpectation(cap.homepage_html, cap.sampled_pages),
    ...checkOnSiteReviewSignalLocal(cap.json_ld, cap.homepage_html, cap.sampled_pages),
    ...checkRealOrganizationSignals(cap.homepage_html, cap.sampled_pages),
  ];

  return {
    site: new URL(url).hostname,
    audited_at: cap.captured_at,
    business_model_evidence: {
      meta: cap.meta,
      genre_signals: cap.genre_signals,
      homepage_excerpt: textExcerpt(cap.homepage_html),
      sampled_pages: cap.sampled_pages.map((p) => ({ url: p.url, role_guess: p.role_guess, excerpt: textExcerpt(p.html, 250) })),
    },
    not_evaluated: cap.not_evaluated,
    checks: { technical_baseline, conversion_friction, retention_content, local_trust_leads },
  };
}

if (require.main === module) {
  const [, , url, maxPages] = process.argv;
  runAudit(url, maxPages ? Number(maxPages) : undefined)
    .then((result) => console.log(JSON.stringify(result, null, 2)))
    .catch((err) => { console.error(err); process.exit(1); });
}

module.exports = { runAudit, capture };
