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
    const resp = await fetch('/michellehenault/menu.json');
    if (!resp.ok) return '';
    const menu = await resp.json();
    function renderMenu(items) {
      return '<ul>' + items.map(item => {
        if (item.children && item.children.length) {
          return `<li class="mh-has-submenu"><span>${item.label}</span>${renderMenu(item.children)}</li>`;
        } else {
          return `<li><a href="${item.href}">${item.label}</a></li>`;
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
  let oldHeader = document.querySelector('.mh-header-common, .mh-header-section, header');

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
              <span class="mh-artist-role-en">
                painter -
              </span>
              <span class="mh-artist-role-fr">
                artiste peintre -
              </span>
              <span class="mh-artist-role-en">
                oil painting -
              </span>
              <span class="mh-artist-role-fr">
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
