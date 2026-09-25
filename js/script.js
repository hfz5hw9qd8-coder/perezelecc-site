/*
============================================================
PEREZELECC — JAVASCRIPT
============================================================

Fonctions :
- menu mobile
- chatbot de démonstration
- fermeture du chatbot

CONNEXION DIFY
------------------------------------------------------------
Le chatbot n'appelle pas encore Dify.

Pour une vraie connexion :
Navigateur
    ↓
Backend sécurisé
    ↓
API Dify
    ↓
Agent PEREZELECC

Ne mets jamais une clé API Dify dans ce fichier public.
============================================================
*/


/* ============================================================
   MENU MOBILE
   ============================================================ */

const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");

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


/* ============================================================
   CHATBOT
   ============================================================ */

const chatButton = document.getElementById("chat-button");
const chatModal = document.getElementById("chat-modal");
const chatClose = document.getElementById("chat-close");

const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatMessages = document.getElementById("chat-messages");


/* Ouvrir */
function openChat() {
    chatModal.classList.add("open");
    chatInput.focus();
}


/* Fermer */
function closeChat() {
    chatModal.classList.remove("open");
}


/* Ajouter un message */
function addChatMessage(text, type) {

    const message = document.createElement("div");

    message.classList.add("chat-message", type);

    /*
        textContent est volontairement utilisé pour empêcher
        l'injection de HTML par l'utilisateur.
    */
    message.textContent = text;

    chatMessages.appendChild(message);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}


/* ============================================================
   ENVOI DU MESSAGE
   ============================================================ */

function sendMessage() {

    const text = chatInput.value.trim();

    if (!text) {
        return;
    }

    addChatMessage(text, "user");

    chatInput.value = "";


    /*
        --------------------------------------------------------
        RÉPONSE DE DÉMONSTRATION
        --------------------------------------------------------

        À remplacer plus tard par une requête vers ton backend
        qui appellera Dify.
    */

    setTimeout(function () {

        addChatMessage(
            "Merci pour votre demande. L'assistant PEREZELECC pourra être connecté à Dify pour vous répondre automatiquement.",
            "bot"
        );

    }, 450);
}


/* Événements */
chatButton.addEventListener("click", openChat);
chatClose.addEventListener("click", closeChat);
chatSend.addEventListener("click", sendMessage);


/* Entrée clavier */
chatInput.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {
        sendMessage();
    }

});


/* Fermer en cliquant à l'extérieur */
chatModal.addEventListener("click", function (event) {

    if (event.target === chatModal) {
        closeChat();
    }

});


/* Touche Échap */
document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {
        closeChat();
    }

});
