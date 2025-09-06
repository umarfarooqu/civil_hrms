// Site-wide maroon theme for Django Admin (Jazzmin + stock admin)
(function () {
  const css = `
  :root{
    --maroon-50:#faf3f4; --maroon-100:#f1dde1; --maroon-200:#e7c1c8;
    --maroon-300:#d896a1; --maroon-400:#c66d7c; --maroon-500:#b04a5f;
    --maroon-600:#8f394d; --maroon-700:#732d3e; --maroon-800:#5b2433; --maroon-900:#3b1721;
  }
  /* Header / Navbar */
  .navbar, .main-header, header.navbar { background-color: var(--maroon-700) !important; }
  .navbar .nav-link, .navbar a, .brand-link, .main-header a { color: #fff !important; }
  .brand-link { background-color: var(--maroon-800) !important; }

  /* Buttons */
  .btn-primary, .btn-info, .submit-row input.default, .button.default, .object-tools a.addlink {
    background-color: var(--maroon-700) !important; border-color: var(--maroon-700) !important; color:#fff !important;
  }
  .btn-primary:hover, .btn-info:hover, .submit-row input.default:hover, .object-tools a.addlink:hover {
    background-color: var(--maroon-800) !important; border-color: var(--maroon-800) !important;
  }

  /* Links */
  a { color: var(--maroon-700); }
  a:hover { color: var(--maroon-800); }

  /* Focus ring */
  :focus { outline-color: var(--maroon-600); }
  `;
  const style = document.createElement('style');
  style.innerHTML = css;
  document.head.appendChild(style);
})();
