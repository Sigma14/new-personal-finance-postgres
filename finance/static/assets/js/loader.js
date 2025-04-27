window.addEventListener("load", () => {
  const loader = document.querySelector('.my-loader');

  loader.classList.add('my-loader-hidden');

  loader.addEventListener("transitionend", () => {
    document.body.removeChild(loader); 
  })
})