(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const dictionary = window.TRANSLATIONS;
  let language = 'sl';
  try {
    const requested = new URLSearchParams(location.search).get('lang');
    const saved = localStorage.getItem('srcna-language');
    language = dictionary[requested] ? requested : dictionary[saved] ? saved : 'sl';
  } catch (_) { /* Local files and private browsers may restrict storage. */ }
  let selected = 'short';
  let map, routeLayer, positionMarker, startMarker, directionMarker, zoomControl;
  let points = [];
  let tileFailed = false;
  let chartWidth = 1000;
  const t = (key) => dictionary[language][key];
  const number = (value, digits = 0) => new Intl.NumberFormat(language, {minimumFractionDigits:digits,maximumFractionDigits:digits}).format(value);
  const externalMaps = {
    short:'https://map.slovenia-outdoor.com/sl/tour/pohodniska-pot/ribja-pot-srcna-pot-svibnik/810597577/#dm=1',
    long:'https://map.slovenia-outdoor.com/sl/tour/pohodniska-pot/ucna-pot-srcna-pot-svibnik/810587126/#dm=1'
  };
  function applyLanguage(next) {
    if (!dictionary[next]) return;
    language = next;
    document.documentElement.lang = next;
    document.title = t('title');
    $('meta[name="description"]').content = t('heroDescription');
    $('#language').value = next;
    $('#headline-distance').textContent = number(4.6,1);
    document.querySelectorAll('[data-i18n]').forEach(el => { el.innerHTML = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-alt]').forEach(el => { el.alt = t(el.dataset.i18nAlt); });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label',t(el.dataset.i18nAria)); });
    $('#points-list').replaceChildren(...t('points').map(label => {
      const li = document.createElement('li'); li.textContent = label; return li;
    }));
    document.querySelectorAll('.brochure-pages img').forEach((img,i) => {
      img.alt = `${[t('warmup'),t('strength'),t('strength'),t('stretch')][i]} · ${i+1}/4`;
    });
    try { localStorage.setItem('srcna-language',next); } catch (_) {}
    updateRoute(false);
    updateMapLabels();
  }
  function initializeMap() {
    if (!window.L) {
      $('#map-status').hidden = false;
      $('#map-status').textContent = t('tilesError');
      return;
    }
    map = L.map('map', {scrollWheelZoom:false,zoomControl:false});
    zoomControl = L.control.zoom({position:'topleft',zoomInTitle:t('zoomIn'),zoomOutTitle:t('zoomOut')}).addTo(map);
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom:19,
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
    }).addTo(map);
    tiles.on('tileerror', () => { tileFailed = true; updateMapLabels(); });
    tiles.on('loading', () => { tileFailed = false; $('#map-status').hidden = true; });
    tiles.on('load', () => updateMapLabels());
    L.control.scale({imperial:false,position:'bottomleft'}).addTo(map);
    routeLayer = L.polyline([], {color:'#b60000',weight:4.5,opacity:.92,lineJoin:'round'}).addTo(map);
    positionMarker = L.circleMarker([0,0], {radius:6,color:'#00582a',fillColor:'#fff',fillOpacity:1,weight:3});
  }
  function updateMapLabels() {
    if (startMarker) startMarker.setPopupContent(t('startTrack'));
    if (directionMarker) directionMarker.setTooltipContent(t('direction'));
    if (map) {
      const zoomIn = $('.leaflet-control-zoom-in'), zoomOut = $('.leaflet-control-zoom-out');
      zoomIn.title = t('zoomIn'); zoomIn.setAttribute('aria-label', t('zoomIn'));
      zoomOut.title = t('zoomOut'); zoomOut.setAttribute('aria-label', t('zoomOut'));
      const startIcon = startMarker?.getElement();
      if (startIcon) startIcon.setAttribute('aria-label',t('startTrack'));
    }
    $('#map-status').textContent = t('tilesError');
    $('#map-status').hidden = !tileFailed && !!map;
  }
  function updateRoute(fit = true) {
    const data = window.ROUTES[selected];
    points = data.segments.flat();
    $('#route-title').textContent = t(selected === 'short' ? 'shortTitle':'longTitle');
    $('#route-summary').textContent = t(selected === 'short' ? 'shortSummary':'longSummary');
    $('#route-difficulty').textContent = t(selected === 'short' ? 'easy':'longDifficulty');
    $('#route-distance').textContent = `${number(data.distance/1000,2)} km`;
    $('#route-elevation').textContent = `${number(data.min)}–${number(data.max)} m`;
    $('#route-ascent').textContent = `+${number(data.ascent)} m`;
    $('#route-descent').textContent = `−${number(data.descent)} m`;
    $('#gpx-download').href = data.file;
    $('#outdoor-link').href = externalMaps[selected];
    document.querySelectorAll('[data-route]').forEach(button => {
      const active = button.dataset.route === selected;
      button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active));
    });
    if (map) {
      const latlngs = data.segments.map(segment => segment.map(point => [point[0],point[1]]));
      routeLayer.setLatLngs(latlngs).setStyle({color:selected === 'short' ? '#b60000':'#087b9b'});
      if (startMarker) map.removeLayer(startMarker);
      startMarker = L.marker(latlngs[0][0], {
        icon:L.divIcon({className:'start-marker',html:'S',iconSize:[26,26],iconAnchor:[13,13]}),
        title:t('startTrack'),alt:t('startTrack')
      }).addTo(map).bindPopup(t('startTrack'));
      if (directionMarker) map.removeLayer(directionMarker);
      const i = Math.min(35, points.length-2), a = points[i], b = points[i+1];
      const angle = Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI;
      const color = selected === 'short' ? '#b60000':'#087b9b';
      directionMarker = L.marker([a[0],a[1]],{interactive:false,icon:L.divIcon({className:'direction-marker',html:`<span style="display:block;transform:rotate(${angle}deg);color:${color}">▲</span>`,iconSize:[20,20],iconAnchor:[10,10]})}).addTo(map).bindTooltip(t('direction'));
      positionMarker.remove();
      if (fit) map.fitBounds(routeLayer.getBounds(),{padding:[35,35]});
    }
    $('#profile-position').max = points.length - 1;
    $('#profile-position').value = 0;
    drawProfile();
    setProfilePosition(0,false);
    updateMapLabels();
  }
  function drawProfile() {
    const data = window.ROUTES[selected];
    chartWidth = Math.max(280, $('#elevation-chart').clientWidth);
    $('#elevation-chart').setAttribute('viewBox',`0 0 ${chartWidth} 170`);
    const endX = chartWidth - 12;
    const min = Math.floor(data.min/10)*10, max = Math.ceil(data.max/10)*10;
    const x = p => 45 + p[3]/data.distance*(endX-45);
    const y = p => 130-(p[2]-min)/(max-min)*110;
    const polyline = points.map(p => `${x(p).toFixed(2)},${y(p).toFixed(2)}`).join(' ');
    const grid = [min,(min+max)/2,max].map(value => {
      const height = 130-(value-min)/(max-min)*110;
      return `<line x1="45" y1="${height}" x2="${endX}" y2="${height}" stroke="#dce2d6" stroke-dasharray="3 5"/><text x="0" y="${height+4}">${number(value)} m</text>`;
    }).join('');
    const fractions = chartWidth < 450 ? [0,.5,1] : [0,.25,.5,.75,1];
    const labels = fractions.map(fraction => `<text x="${45+(endX-45)*fraction}" y="160" text-anchor="${fraction===0?'start':fraction===1?'end':'middle'}">${number(data.distance/1000*fraction,1)} km</text>`).join('');
    $('#elevation-chart').innerHTML = `<defs><linearGradient id="profile-fill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#8eaf76" stop-opacity=".5"/><stop offset="1" stop-color="#8eaf76" stop-opacity=".03"/></linearGradient></defs>${grid}<polygon points="45,130 ${polyline} ${endX},130" fill="url(#profile-fill)"/><polyline points="${polyline}" fill="none" stroke="#4c793d" stroke-width="2"/>${labels}<line id="profile-cursor" x1="45" x2="45" y1="12" y2="134" stroke="#00582a" stroke-dasharray="3 3"/><circle id="profile-dot" cx="45" cy="${y(points[0])}" r="4" fill="#00582a" stroke="white" stroke-width="2"/>`;
  }
  function setProfilePosition(index, showOnMap = true) {
    const p = points[index], data = window.ROUTES[selected];
    if (!p) return;
    const min = Math.floor(data.min/10)*10, max = Math.ceil(data.max/10)*10;
    const x = 45+p[3]/data.distance*(chartWidth-57), y = 130-(p[2]-min)/(max-min)*110;
    $('#profile-cursor').setAttribute('x1',x); $('#profile-cursor').setAttribute('x2',x);
    $('#profile-dot').setAttribute('cx',x); $('#profile-dot').setAttribute('cy',y);
    const readout = `${number(p[3]/1000,2)} km · ${number(p[2])} m`;
    $('#profile-readout').textContent = readout;
    $('#profile-position').setAttribute('aria-valuetext',readout);
    if (map && showOnMap) positionMarker.setLatLng([p[0],p[1]]).addTo(map);
  }
  $('#language').addEventListener('change',event => {
    applyLanguage(event.target.value);
    try {
      const url = new URL(location.href); url.searchParams.set('lang',language);
      history.replaceState(null,'',url);
    } catch (_) {}
  });
  function selectRoute(route) { selected = route; updateRoute(); }
  document.querySelectorAll('[data-route]').forEach(button => button.addEventListener('click',() => selectRoute(button.dataset.route)));
  $('#choose-long').addEventListener('click',() => selectRoute('long'));
  $('#fit-map').addEventListener('click',() => map?.fitBounds(routeLayer.getBounds(),{padding:[35,35]}));
  $('#profile-position').addEventListener('input',event => setProfilePosition(Number(event.target.value)));
  $('#elevation-chart').addEventListener('pointermove',event => {
    if (event.pointerType === 'touch') return;
    const rect = event.currentTarget.getBoundingClientRect();
    const fraction = Math.max(0,Math.min(1,((event.clientX-rect.left)/rect.width*chartWidth-45)/(chartWidth-57)));
    const target = fraction*window.ROUTES[selected].distance;
    const index = points.reduce((best,point,i) => Math.abs(point[3]-target)<Math.abs(points[best][3]-target)?i:best,0);
    $('#profile-position').value = index; setProfilePosition(index);
  });
  const dialog = $('#brochure-dialog');
  $('#open-brochure').addEventListener('click',() => dialog.showModal());
  $('#close-brochure').addEventListener('click',() => dialog.close());
  $('#embedded-pdf').addEventListener('toggle', event => {
    if (event.target.open && !$('#pdf-frame').getAttribute('src')) {
      $('#pdf-frame').src = 'assets/documents/vaje-za-razgibavanje.pdf';
    }
  });
  dialog.addEventListener('click',event => {
    const rect = dialog.getBoundingClientRect();
    if (event.clientX<rect.left || event.clientX>rect.right || event.clientY<rect.top || event.clientY>rect.bottom) dialog.close();
  });
  initializeMap();
  applyLanguage(language);
  if (map) {
    new ResizeObserver(() => {
      map.invalidateSize();
      map.fitBounds(routeLayer.getBounds(),{padding:[35,35],animate:false});
    }).observe($('#map'));
  }
  new ResizeObserver(() => {
    drawProfile();
    setProfilePosition(Number($('#profile-position').value),false);
  }).observe($('#elevation-chart'));
})();
