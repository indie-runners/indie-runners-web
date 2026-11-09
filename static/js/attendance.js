(function () {
  // Only the event page's action bar carries [data-action] buttons; tiles show
  // a read-only status since W-096.
  function updateActionBar(bar, data) {
    const userStatus = data.user_status;
    const eventId = bar.dataset.eventId;
    const occurrenceId = bar.dataset.occurrenceId;
    const existing = bar.querySelector('.attendance-status, .attendance-buttons, .attendance-buttons--row');
    const oidAttr = 'data-occurrence-id="' + occurrenceId + '"';

    let newHtml;
    if (userStatus) {
      const toggleAction = userStatus === 'going' ? 'interested' : 'going';
      const label = userStatus === 'going' ? 'You are going' : 'You are interested';
      newHtml = '<div class="attendance-status">'
        + '<span class="attendance-status-label">' + label + '</span>'
        + '<div class="attendance-actions">'
        + '<button class="attendance-change" data-event-id="' + eventId + '" ' + oidAttr + ' data-action="' + toggleAction + '">Change</button>'
        + '<button class="attendance-remove" data-event-id="' + eventId + '" ' + oidAttr + ' data-action="remove">Remove</button>'
        + '</div></div>';
    } else {
      newHtml = '<div class="attendance-buttons attendance-buttons--row">'
        + '<button class="attendance-btn attendance-btn--going" data-event-id="' + eventId + '" ' + oidAttr + ' data-action="going">Going</button>'
        + '<button class="attendance-btn attendance-btn--interested" data-event-id="' + eventId + '" ' + oidAttr + ' data-action="interested">Interested</button>'
        + '</div>';
    }

    if (existing) {
      existing.outerHTML = newHtml;
    } else {
      bar.insertAdjacentHTML('beforeend', newHtml);
    }
  }

  // Offered once, at the moment of going; never left on the page (Paulo, W-023).
  function offerCalendar(bar) {
    const dialog = document.querySelector('.gcal-dialog');
    const url = bar.dataset.gcalUrl;
    if (!dialog || !url || !dialog.showModal) return;
    dialog.querySelector('.gcal-dialog-save').href = url;
    dialog.showModal();
  }

  document.addEventListener('click', function (e) {
    const dialog = e.target.closest('.gcal-dialog');
    if (!dialog) return;
    // The save link opens a new tab and closes too; a click on the backdrop lands on the dialog itself.
    if (e.target === dialog || e.target.closest('.gcal-dialog-close, .gcal-dialog-save')) dialog.close();
  });

  function flashError(btn) {
    btn.style.outline = '2px solid red';
    setTimeout(function () { btn.style.outline = ''; }, 2000);
  }

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;
    const eventId = btn.dataset.eventId;
    const occurrenceId = btn.dataset.occurrenceId;
    if (!eventId || !occurrenceId) return;

    const bar = btn.closest('.event-attendance');
    const url = '/events/' + eventId + '/' + occurrenceId + '/attendance';

    if (action === 'remove') {
      fetch(url, { method: 'DELETE' })
        .then(function (r) {
          if (r.status === 401) { window.location.href = '/auth/google'; return null; }
          if (!r.ok) { flashError(btn); return null; }
          return r.json();
        })
        .then(function (data) { if (data) updateActionBar(bar, data); });
    } else {
      const body = new URLSearchParams({ status: action });
      fetch(url, { method: 'POST', body: body })
        .then(function (r) {
          if (r.status === 401) { window.location.href = '/auth/google'; return null; }
          if (!r.ok) { flashError(btn); return null; }
          return r.json();
        })
        .then(function (data) {
          if (!data) return;
          updateActionBar(bar, data);
          if (action === 'going' && data.user_status === 'going') offerCalendar(bar);
        });
    }
  });

  // Mobile tile reveal: first tap reveals info, second tap anywhere on the tile
  // navigates via the stretched .tile-link
  if (window.matchMedia('(hover: none)').matches) {
    document.addEventListener('click', function (e) {
      var tile = e.target.closest('.tile');

      if (tile) {
        if (!tile.classList.contains('tile--revealed')) {
          // First tap: reveal the tile, do not navigate even if a link was tapped
          document.querySelectorAll('.tile--revealed').forEach(function (t) {
            t.classList.remove('tile--revealed');
          });
          tile.classList.add('tile--revealed');
          e.preventDefault();
          return;
        }
        // Tile is revealed: the stretched .tile-link navigates natively; the
        // overlay is pointer-events: none so taps fall through to it except
        // on its buttons/links, which handle themselves
        return;
      }

      // Tap outside any tile collapses all revealed tiles
      document.querySelectorAll('.tile--revealed').forEach(function (t) {
        t.classList.remove('tile--revealed');
      });
    }, true);
  }

  // The hover panel has no room to grow: show the pills that fit, then +N
  function fitDistances(tile) {
    var rows = tile.querySelector('.hover-rows');
    var box = tile.querySelector('.dist-pills');
    if (!box) return;
    var more = box.querySelector('.dist-pill--more');
    if (more) more.remove();
    var pills = Array.prototype.slice.call(box.querySelectorAll('.dist-pill'));
    pills.forEach(function (p) { p.hidden = false; });
    if (rows.scrollHeight <= rows.clientHeight) return;

    more = document.createElement('span');
    more.className = 'dist-pill dist-pill--more';
    box.appendChild(more);
    for (var shown = pills.length - 1; shown >= 1; shown--) {
      pills[shown].hidden = true;
      more.textContent = '+' + (pills.length - shown);
      if (rows.scrollHeight <= rows.clientHeight) return;
    }

    // Hiding did not help, so the pills were not what overflowed
    more.remove();
    pills.forEach(function (p) { p.hidden = false; });
  }

  function fitAllDistances() {
    document.querySelectorAll('.tile').forEach(fitDistances);
  }

  var grid = document.querySelector('.race-grid');
  if (grid) {
    new ResizeObserver(fitAllDistances).observe(grid);
    document.fonts.ready.then(fitAllDistances);
  }
}());
