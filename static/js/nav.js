// Nav avatar dropdown: click toggles, outside click and Escape close.
document.addEventListener('DOMContentLoaded', function () {
  var menu = document.querySelector('.nav-user-menu');
  if (!menu) return; // signed-out pages

  var btn = menu.querySelector('.nav-avatar-btn');

  function setOpen(open) {
    menu.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  btn.addEventListener('click', function () {
    setOpen(!menu.classList.contains('open'));
  });

  document.addEventListener('click', function (e) {
    if (menu.classList.contains('open') && !menu.contains(e.target)) {
      setOpen(false);
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) {
      setOpen(false);
      btn.focus();
    }
  });
});
