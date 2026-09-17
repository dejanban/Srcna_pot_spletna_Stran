"""Functional browser checks. Run against `python3 -m http.server 4173`.
Optional dependency: playwright (and its Chromium browser).
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get('TEST_URL', 'http://127.0.0.1:4173')
ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
    page = context.new_page()
    errors, missing = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: missing.append(response.url) if response.status >= 400 and response.url.startswith(BASE) else None)
    page.goto(BASE, wait_until='networkidle')
    assert page.locator('html').get_attribute('lang') == 'sl'
    assert page.locator('#route-distance').inner_text() == '4,63 km'
    assert page.locator('#route-elevation').inner_text() == '144–183 m'
    assert page.locator('#points-list li').count() == 11
    assert page.locator('.partners li').count() == 6
    assert page.evaluate("Object.entries(TRANSLATIONS).every(([lang,d]) => Object.keys(TRANSLATIONS.sl).every(k => k in d))")
    assert page.evaluate("[...document.querySelectorAll('[data-i18n]')].every(el=>!!TRANSLATIONS.sl[el.dataset.i18n])")
    # Every supplied route coordinate is present in the generated dataset.
    assert page.evaluate('ROUTES.short.segments.flat().length') == 373
    assert page.evaluate('ROUTES.long.segments.flat().length') == 391
    with page.expect_download() as download:
        page.locator('#gpx-download').click()
    assert download.value.suggested_filename == 'ribja-pot.gpx'
    page.locator('[data-route="long"]').click()
    assert page.locator('#route-distance').inner_text() == '12,27 km'
    assert page.locator('#route-elevation').inner_text() == '140–168 m'
    assert page.locator('[data-route="long"]').get_attribute('aria-pressed') == 'true'
    assert '810587126' in page.locator('#outdoor-link').get_attribute('href')
    with page.expect_download() as download:
        page.locator('#gpx-download').click()
    assert download.value.suggested_filename == 'ucna-pot.gpx'
    page.locator('#profile-position').focus()
    page.keyboard.press('End')
    assert page.locator('#profile-readout').inner_text().startswith('12,27 km')
    page.locator('#fit-map').click()
    # Switching language must preserve the chosen route, translate all keys,
    # and produce no horizontal scrolling at phone, tablet and desktop widths.
    for language in ['en','de','es','sl']:
        page.select_option('#language',language)
        assert page.locator('html').get_attribute('lang') == language
        assert page.locator('[data-route="long"]').get_attribute('aria-pressed') == 'true'
        assert 'undefined' not in page.locator('body').inner_text()
        for width in [1440,768,390,320]:
            page.set_viewport_size({'width':width,'height':900})
            page.wait_for_timeout(120)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), (language,width,'overflow')
        page.set_viewport_size({'width':1440,'height':1000})
    page.select_option('#language','de')
    page.reload(wait_until='networkidle')
    assert page.locator('html').get_attribute('lang') == 'de'
    page.goto(BASE+'/?lang=en',wait_until='networkidle')
    assert page.locator('html').get_attribute('lang') == 'en'
    assert page.locator('#headline-distance').inner_text() == '4.6'
    page.locator('#open-brochure').click()
    assert page.locator('#brochure-dialog').is_visible()
    assert page.locator('.brochure-pages img').count() == 4
    page.locator('#embedded-pdf summary').click()
    page.wait_for_function("document.querySelector('#pdf-frame').getAttribute('src') !== null")
    assert page.locator('#pdf-frame').get_attribute('src').endswith('.pdf')
    with page.expect_download() as download:
        page.locator('.dialog-actions [download]').click()
    assert download.value.suggested_filename == 'vaje-za-razgibavanje.pdf'
    assert Path(download.value.path()).read_bytes().startswith(b'%PDF')
    page.keyboard.press('Escape')
    assert not page.locator('#brochure-dialog').is_visible()
    assert page.locator('#open-brochure').evaluate('(el)=>el===document.activeElement')
    page.locator('#open-brochure').click()
    page.locator('#close-brochure').click()
    assert not page.locator('#brochure-dialog').is_visible()
    page.locator('[data-i18n="fullDescription"]').click()
    assert page.locator('.itinerary').is_visible()
    page.locator('[data-i18n="originalBoard"]').click()
    assert page.locator('.board-image').is_visible()
    page.locator('.partners').scroll_into_view_if_needed()
    page.wait_for_function("[...document.querySelectorAll('.partners img')].every(i=>i.complete&&i.naturalWidth>0)")
    # Every local link must resolve, including fonts, PDFs, GPX and artwork.
    links=page.evaluate("[...document.querySelectorAll('[src],link[href],a[href]')].map(el=>el.src||el.href).filter(u=>u&&u.startsWith(location.origin)&&!u.includes('#'))")
    for url in set(links):
        assert context.request.get(url).ok, url
    assert not errors, errors
    assert not missing, missing
    # An unavailable online base map must leave local route geometry usable.
    offline=context.new_page()
    offline.route('https://tile.openstreetmap.org/**',lambda route:route.abort())
    offline.goto(BASE+'/?lang=sl',wait_until='networkidle')
    assert offline.locator('#map-status').is_visible()
    assert offline.locator('.leaflet-overlay-pane path').count() > 0
    offline.locator('[data-route="long"]').click()
    assert offline.locator('#route-distance').inner_text() == '12,27 km'
    # Capture fully loaded pages for manual review.
    page.goto(BASE+'/?lang=sl',wait_until='networkidle')
    for y in range(0,page.evaluate('document.body.scrollHeight'),650):
        page.evaluate('(y)=>scrollTo(0,y)',y)
        page.wait_for_timeout(80)
    page.evaluate('scrollTo(0,0)')
    page.screenshot(path='/tmp/tabla-desktop-final.png',full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.goto(BASE+'/?lang=sl',wait_until='networkidle')
    for y in range(0,page.evaluate('document.body.scrollHeight'),650):
        page.evaluate('(y)=>scrollTo(0,y)',y)
        page.wait_for_timeout(80)
    page.evaluate('scrollTo(0,0)')
    page.screenshot(path='/tmp/tabla-mobile-final.png',full_page=True)
    print('PASS: 4 languages × 4 widths, persistence, both GPX routes/downloads, elevation interaction, PDF preview/download, modal keyboard behavior, 11 points, 6 contributors, local assets and offline map fallback.')
    print('JavaScript errors: 0. Missing local assets: 0.')
    browser.close()
