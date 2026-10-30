if (window.isSecureContext && navigator.clipboard?.writeText) {
  for (const block of document.querySelectorAll('pre[data-copy-label]')) {
    const code = block.querySelector('code');
    const controls = document.createElement('div');
    controls.className = 'code-controls';
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', block.dataset.copyLabel);
    const status = document.createElement('span');
    status.setAttribute('role', 'status');
    controls.append(status, button);
    block.before(controls);
    block.classList.add('with-copy');

    button.addEventListener('click', async () => {
      button.disabled = true;
      status.textContent = '';
      try {
        await navigator.clipboard.writeText(code.textContent);
        status.textContent = 'Copied';
      } catch {
        status.textContent = 'Couldn’t copy. Select the command below.';
      } finally {
        button.disabled = false;
      }
    });
  }
}
