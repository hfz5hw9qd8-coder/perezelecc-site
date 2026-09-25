/*
============================================================
PEREZELECC — JAVASCRIPT
============================================================

Fonction :
- menu mobile

Le chatbot est désormais géré par Dify via son widget local.
============================================================
*/


/* ============================================================
   MENU MOBILE
   ============================================================ */

const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");

if (mobileMenuButton && mobileMenu) {

    mobileMenuButton.addEventListener("click", function () {

        const isOpen = mobileMenu.classList.toggle("open");

        mobileMenuButton.setAttribute(
            "aria-expanded",
            isOpen ? "true" : "false"
        );

    });


    /* Fermer le menu après clic */
    document.querySelectorAll("#mobile-menu a").forEach(function (link) {

        link.addEventListener("click", function () {
            mobileMenu.classList.remove("open");
            mobileMenuButton.setAttribute("aria-expanded", "false");
        });

    });

}
