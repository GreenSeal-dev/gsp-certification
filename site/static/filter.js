// Progressive filtering for the practices list. The page works without it.
(function () {
  var form = document.getElementById('filters');
  if (!form) return;
  var rows = Array.prototype.slice.call(document.querySelectorAll('.practice-row'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('.category'));
  var count = form.querySelector('.filter-count');
  var empty = document.getElementById('empty');
  form.hidden = false;

  // Initial values from the URL, e.g. ?level=1 from the home page.
  var params = new URLSearchParams(window.location.search);
  ['q', 'level', 'category', 'priority'].forEach(function (name) {
    if (params.has(name) && form.elements[name]) form.elements[name].value = params.get(name);
  });

  function apply() {
    var q = form.elements.q.value.trim().toLowerCase();
    var level = form.elements.level ? form.elements.level.value : '';
    var category = form.elements.category.value;
    var priority = form.elements.priority.value;
    var shown = 0;
    sections.forEach(function (section) {
      var inCategory = !category || section.dataset.category === category;
      var visible = 0;
      section.querySelectorAll('.practice-row').forEach(function (row) {
        var ok = inCategory &&
          (!q || row.dataset.text.indexOf(q) !== -1) &&
          (!level || row.dataset.levels.split(' ').indexOf(level) !== -1) &&
          (!priority || row.dataset.priority === priority);
        row.hidden = !ok;
        if (ok) visible++;
      });
      section.hidden = visible === 0;
      shown += visible;
    });
    count.textContent = shown === rows.length ? rows.length + ' practices' : shown + ' of ' + rows.length + ' practices';
    empty.hidden = shown !== 0;

    var next = new URLSearchParams();
    if (q) next.set('q', q);
    if (level) next.set('level', level);
    if (category) next.set('category', category);
    if (priority) next.set('priority', priority);
    var query = next.toString();
    history.replaceState(null, '', window.location.pathname + (query ? '?' + query : '') + window.location.hash);
  }

  form.addEventListener('input', apply);
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  apply();
})();
