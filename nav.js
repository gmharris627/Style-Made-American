/**
 * nav.js — Style Made American shared navigation
 *
 * Every page includes a <div id="site-header"></div> placeholder and
 * <script src="/nav.js"></script>. This script builds the header once
 * and injects it, so nav changes only need to happen in this one file.
 */
(function () {
  var path = window.location.pathname;

  // Returns true if the given href matches the current page.
  function isActive(href) {
    if (href === '/') {
      return path === '/' || path === '/index.html';
    }
    return path.startsWith(href);
  }

  // Builds an <a> tag, adding class="active" when the link matches the page.
  function link(href, label, extraClass, extraAttrs) {
    var classes = [];
    if (extraClass) classes.push(extraClass);
    if (isActive(href)) classes.push('active');
    var cls = classes.length ? ' class="' + classes.join(' ') + '"' : '';
    return '<a href="' + href + '"' + cls + (extraAttrs || '') + '>' + label + '</a>';
  }

  var html = [
    '<header class="site-header">',
    '  <div class="container">',
    '    <a href="/" class="wordmark-link" aria-label="Style Made American — home">',
    '      <span class="wordmark">Style Made American</span>',
    '    </a>',
    '    <nav class="site-nav" aria-label="Primary">',
    '      ' + link('/', 'Database'),
    '      ' + link('/categories/', 'Categories'),
    '      ' + link('/brands/', 'Brands'),
    '      <a href="#">Reviews</a>',
    '      ' + link('/articles/', 'Articles'),
    '      ' + link('/about.html', 'About'),
    '      <a href="https://stylemadeamerican.substack.com/subscribe" target="_blank" class="nav-cta">Subscribe</a>',
    '    </nav>',
    '  </div>',
    '</header>'
  ].join('\n');

  var placeholder = document.getElementById('site-header');
  if (placeholder) placeholder.outerHTML = html;
})();
