(() => {
  const key = 'bmb-preview-cart-v1';

  function readCart() {
    try { return JSON.parse(localStorage.getItem(key) || '[]'); }
    catch (_) { return []; }
  }

  function writeCart(cart) {
    localStorage.setItem(key, JSON.stringify(cart));
    updateCount(cart);
  }

  function updateCount(cart = readCart()) {
    document.querySelectorAll('[data-cart-count]').forEach((el) => {
      el.textContent = String(cart.length);
    });
  }

  function add(slug, name) {
    const cart = readCart();
    if (!cart.some((item) => item.slug === slug)) cart.push({ slug, name });
    writeCart(cart);
  }

  function remove(slug) {
    writeCart(readCart().filter((item) => item.slug !== slug));
    renderCart();
  }

  function renderCart() {
    const panel = document.querySelector('[data-cart-panel]');
    if (!panel) return;
    const cart = readCart();
    const items = panel.querySelector('[data-cart-items]');
    const empty = panel.querySelector('[data-cart-empty]');
    const checkout = panel.querySelector('[data-cart-checkout]');
    items.innerHTML = '';
    if (!cart.length) {
      empty.hidden = false;
      checkout.hidden = true;
      return;
    }
    empty.hidden = true;
    checkout.hidden = false;
    cart.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'cart-row';
      row.innerHTML = `<a href="/products/${item.slug}"></a><button type="button">Remove</button>`;
      row.querySelector('a').textContent = item.name;
      row.querySelector('button').addEventListener('click', () => remove(item.slug));
      items.appendChild(row);
    });
  }

  document.querySelectorAll('[data-add-to-cart]').forEach((button) => {
    button.addEventListener('click', () => {
      add(button.dataset.productSlug, button.dataset.productName);
      const original = button.textContent;
      button.textContent = 'Added to preview cart';
      setTimeout(() => { button.textContent = original; }, 1400);
    });
  });

  updateCount();
  renderCart();
})();
