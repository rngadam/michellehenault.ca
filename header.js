// header.js : Injection d'un en-tête commun avec navigation dynamique

// Configuration des liens sociaux
const socials = [
  {
    href: 'https://www.instagram.com/henault.michelle/?hl=en',
    img: 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png',
    alt: 'Instagram',
    class: 'mh-instagram-icon'
  },
  {
    href: 'https://www.facebook.com/michellehenaultartistepeintre',
    img: 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg',
    alt: 'Facebook',
    class: 'mh-facebook-icon'
  },
  {
    href: 'https://www.linkedin.com/in/michelle-h%C3%A9nault',
    img: 'https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png',
    alt: 'LinkedIn',
    class: 'mh-linkedin-icon'
  }
];

// Fonction pour générer le HTML des liens sociaux
function socialsHTML() {
  return `<div class="mh-social">` +
    socials.map(s => `<a href="${s.href}" target="_blank" rel="noopener noreferrer"><img src="${s.img}" alt="${s.alt}" class="${s.class}"/></a>`).join('') +
    `</div>`;
}

// Fonction pour générer le menu de navigation à partir d'un fichier JSON avec sous-menus
async function navHTML() {
  try {
    const resp = await fetch('menu.json');
    if (!resp.ok) return '';
    const menu = await resp.json();
    function renderMenu(items) {
      let isPreview = window.location.pathname.includes('/pr-preview/');
      let basePreviewPath = '';
      if (isPreview) {
        const pathParts = window.location.pathname.split('/');
        // Assuming path is like /pr-preview/NUMBER/...
        if (pathParts.length >= 3 && pathParts[1] === 'pr-preview') {
          basePreviewPath = '/' + pathParts[1] + '/' + pathParts[2]; // e.g., /pr-preview/123
        }
      }

      return '<ul>' + items.map(item => {
        let finalHref = item.href;
        // Ensure item.href exists before trying to manipulate it
        if (isPreview && basePreviewPath && item.href && item.href.startsWith('/')) {
          // basePreviewPath will be like /pr-preview/123
          // item.href will be like /some-page/index.html or /
          // Result: /pr-preview/123/some-page/index.html or /pr-preview/123/
          finalHref = basePreviewPath + item.href;
        }

        if (item.children && item.children.length) {
          let labelContent = item.label;
          if (item.href) { // If parent itself is a link
             // Use finalHref here as well, in case the parent link needs modification
             labelContent = `<a href="${finalHref}">${item.label}</a>`;
          } else {
             labelContent = `<span>${item.label}</span>`;
          }
          return `<li class="mh-has-submenu">${labelContent}${renderMenu(item.children)}</li>`;
        } else {
          // Ensure finalHref is used for items without children too
          return `<li><a href="${finalHref}">${item.label}</a></li>`;
        }
      }).join('') + '</ul>';
    }
    return `<nav class="mh-nav">${renderMenu(menu)}</nav>`;
  } catch (e) {
    return '';
  }
}

// Fonction principale d'injection du header
async function injectHeader() {
  // Chercher un header existant (par classe ou balise header)
  let oldHeader = document.querySelector('header');

  oldHeader.innerHTML = `
    <div class="mh-header-inner">
      <div class="mh-header-block">
        <div class="mh-header-title">
          <span class="mh-artist-name">Michelle Hénault</span>
          <span class="mh-title-desc">
          <span>
            <br/>
              <span class="mh-artist-role">
                artiste peintre -
              </span>
              <span>
               <br/>
               <span>
                peinture à l'huile-oil painting
               </span>
              </span>
          </span>
        </div>
        ${socialsHTML()}
      </div>
    </div>
  `;
  // Générer et ajouter la navigation
  const nav = document.createElement('div');
  nav.innerHTML = await navHTML();
  oldHeader.appendChild(nav);
  // Insérer en haut du body
  document.body.insertBefore(header, document.body.firstChild);
}

document.addEventListener('DOMContentLoaded', injectHeader);
