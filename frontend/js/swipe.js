// ===========================
// CONFIG
// ===========================
const INITIAL_COUNT = 5;
const SWIPE_THRESHOLD = 80; // px avant de confirmer le vote

// ===========================
// STATE
// ===========================
let counter = INITIAL_COUNT;
let isInfinite = false;
let isAnimating = false;
let currentPair = null;

// Touch / Mouse tracking
let startX = 0;
let currentX = 0;
let isDragging = false;

// ===========================
// DOM
// ===========================
const cardContainer = document.getElementById("card-container");
const counterValue = document.getElementById("counter-value");
const counterWrapper = document.getElementById("counter-wrapper");
const actionsEl = document.getElementById("actions");
const stickyResults = document.getElementById("sticky-results");
const btnContinue = document.getElementById("btn-continue");
const btnResults = document.getElementById("btn-results");
const btnResultsSticky = document.getElementById("btn-results-sticky");

// ===========================
// API
// ===========================
async function fetchPair() {
  const res = await fetch("/api/votes/pair");
  if (!res.ok) throw new Error("Pas assez de candidats.");
  return await res.json();
}

async function submitVote(winnerId, loserId) {
  const res = await fetch("/api/votes/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ winner_id: winnerId, loser_id: loserId }),
  });
  if (!res.ok && res.status !== 429) {
    console.warn("Erreur lors du vote", await res.text());
  }
}

// ===========================
// CARD BUILDER
// ===========================
function buildCard(pair) {
  currentPair = pair;

  const card = document.createElement("div");
  card.className = "swipe-card";
  card.id = "swipe-card";

  card.innerHTML = `
    <div class="card-half left">
      <img src="/media/${pair.left.filename}" alt="${pair.left.name}" draggable="false">
    </div>
    <div class="card-half right">
      <img src="/media/${pair.right.filename}" alt="${pair.right.name}" draggable="false">
    </div>
    <div class="card-divider"></div>
    <div class="card-overlay left-overlay">👑</div>
    <div class="card-overlay right-overlay">👑</div>
    <div class="card-label left">${pair.left.name}</div>
    <div class="card-label right">${pair.right.name}</div>
  `;

  // Events souris
  card.addEventListener("mousedown", onDragStart);
  card.addEventListener("mousemove", onDragMove);
  card.addEventListener("mouseup", onDragEnd);
  card.addEventListener("mouseleave", onDragEnd);

  // Events tactile
  card.addEventListener("touchstart", onTouchStart, { passive: true });
  card.addEventListener("touchmove", onTouchMove, { passive: true });
  card.addEventListener("touchend", onTouchEnd);

  return card;
}

async function loadNewCard() {
  // Vide le container
  cardContainer.innerHTML = "";

  try {
    const pair = await fetchPair();
    const card = buildCard(pair);
    cardContainer.appendChild(card);
  } catch (e) {
    showToast(e.message);
  }
}

// ===========================
// DRAG — SOURIS
// ===========================
function onDragStart(e) {
  if (isAnimating) return;
  isDragging = true;
  startX = e.clientX;
}

function onDragMove(e) {
  if (!isDragging || isAnimating) return;
  currentX = e.clientX - startX;
  updateCardState(currentX);
}

function onDragEnd(e) {
  if (!isDragging || isAnimating) return;
  isDragging = false;
  finalizeSwipe(currentX);
}

// ===========================
// DRAG — TACTILE
// ===========================
function onTouchStart(e) {
  if (isAnimating) return;
  isDragging = true;
  startX = e.touches[0].clientX;
}

function onTouchMove(e) {
  if (!isDragging || isAnimating) return;
  currentX = e.touches[0].clientX - startX;
  updateCardState(currentX);
}

function onTouchEnd() {
  if (!isDragging || isAnimating) return;
  isDragging = false;
  finalizeSwipe(currentX);
}

// ===========================
// LOGIQUE SWIPE
// ===========================
function updateCardState(deltaX) {
  const card = document.getElementById("swipe-card");
  if (!card) return;

  card.classList.remove("swiping-left", "swiping-right");

  if (deltaX < -10) card.classList.add("swiping-left");
  if (deltaX > 10) card.classList.add("swiping-right");
}

function finalizeSwipe(deltaX) {
  const card = document.getElementById("swipe-card");
  if (!card || !currentPair) return;

  if (deltaX < -SWIPE_THRESHOLD) {
    // Swipe gauche → vote pour la gauche
    confirmVote(card, "left");
  } else if (deltaX > SWIPE_THRESHOLD) {
    // Swipe droite → vote pour la droite
    confirmVote(card, "right");
  } else {
    // Pas assez loin → reset
    card.classList.remove("swiping-left", "swiping-right");
    currentX = 0;
  }
}

async function confirmVote(card, direction) {
  isAnimating = true;

  const winnerId =
    direction === "left" ? currentPair.left.id : currentPair.right.id;
  const loserId =
    direction === "left" ? currentPair.right.id : currentPair.left.id;

  // Animation de sortie
  card.classList.add(direction === "left" ? "vote-left" : "vote-right");

  // Envoi du vote en parallèle de l'animation
  submitVote(winnerId, loserId);

  // Attendre la fin de l'animation (350ms)
  await wait(350);

  // Mise à jour du compteur
  updateCounter();

  // Recharge une nouvelle carte
  await loadNewCard();

  isAnimating = false;
  currentX = 0;
}

// ===========================
// COMPTEUR
// ===========================
function updateCounter() {
  if (isInfinite) return; // mode infini → pas de compteur

  counter--;

  // Animation bump
  counterValue.classList.remove("bump");
  void counterValue.offsetWidth; // reflow pour relancer l'animation
  counterValue.classList.add("bump");
  counterValue.textContent = counter;

  if (counter <= 0) {
    showActions();
  }
}

function showActions() {
  counterWrapper.classList.add("hidden");
  actionsEl.classList.remove("hidden");
}

// ===========================
// BOUTONS ACTIONS
// ===========================
btnContinue.addEventListener("click", () => {
  isInfinite = true;
  counter = 0;

  actionsEl.classList.add("hidden");
  counterWrapper.classList.add("hidden");

  // Affiche le bouton résultats sticky après scroll
  showStickyOnScroll();
});

btnResults.addEventListener("click", () => {
  window.location.href = "/results";
});

btnResultsSticky.addEventListener("click", () => {
  window.location.href = "/results";
});

// Bouton sticky visible après que l'utilisateur scroll un peu
function showStickyOnScroll() {
  const handler = () => {
    if (window.scrollY > 100) {
      stickyResults.classList.add("visible");
    } else {
      stickyResults.classList.remove("visible");
    }
  };
  window.addEventListener("scroll", handler);
}

// ===========================
// UTILITAIRES
// ===========================
function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showToast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ===========================
// INIT
// ===========================
document.addEventListener("DOMContentLoaded", async () => {
  counterValue.textContent = counter;
  await loadNewCard();
});
