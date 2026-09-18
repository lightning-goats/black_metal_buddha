(() => {
  const marker = document.querySelector('[data-order-complete]');
  if (!marker || !window.BMBCart) return;
  const active = sessionStorage.getItem('bmb-active-order');
  if (active && active === marker.dataset.orderNumber) {
    window.BMBCart.clear();
    sessionStorage.removeItem('bmb-active-order');
  }
})();
