// ===========================
// STATE
// ===========================
let currentPeriod = "week";

// ===========================
// DOM
// ===========================
const rankingList = document.getElementById("ranking-list");
const tabs = document.querySelectorAll(".tab");
const loader = document.getElementById("loader");

// ===========================
// API
// ===========================
async function fetchRanking(period) {
  const res = await fetch(`/api/ranking/${period}`);
  if (!res.ok) throw new Error("Erreur lors du chargement du classement.");
  return await res.json();
}

// ===========================
// RENDER
// ===========================
function getMedalClass(rank) {
  if (rank === 1) return "gold";
  if (rank === 2) return "silver";
  if (rank === 3) return "bronze";
  return "";
}

function getTopClass(rank) {
  if (rank === 1) return "top1";
  if (rank === 2) return "top2";
  if (rank === 3) return "top3";
  return "";
}

function getPeriodLabel(period) {
  const labels = {
    day: "aujourd'hui",
    week: "cette semaine",
    month: "ce mois-ci",
    year: "cette année",
  };
  return labels[period] || period;
}

function renderRanking(data, period) {
  rankingList.innerHTML = "";

  if (!data || data.length === 0) {
    rankingList.innerHTML = `
      <div style="text-align:center; color: var(--text-muted); padding: 40px 0;">
        Aucun vote ${getPeriodLabel(period)} pour le moment.<br>
        <a href="/" style="color: var(--accent); margin-top: 12px; display:inline-block;">
          Aller voter →
        </a>
      </div>`;
    return;
  }

  data.forEach((item) => {
    const medalClass = getMedalClass(item.rank);
    const topClass = getTopClass(item.rank);

    const el = document.createElement("div");
    el.className = `ranking-item ${topClass}`;
    el.style.animationDelay = `${(item.rank - 1) * 0.05}s`;

    el.innerHTML = `
      <div class="rank-number ${medalClass}">${
      item.rank === 1
        ? "🥇"
        : item.rank === 2
        ? "🥈"
        : item.rank === 3
        ? "🥉"
        : `#${item.rank}`
    }</div>
      <img
        class="rank-photo"
        src="/media/${item.person.filename}"
        alt="${item.person.name}"
        loading="lazy"
      >
      <div class="rank-info">
        <div class="rank-name">${item.person.name}</div>
        <div class="rank-stats">
          ${item.wins}V · ${item.losses}D · ${item.games} comparaisons
        </div>
      </div>
      <div class="rank-elo">${item.elo}</div>
    `;

    rankingList.appendChild(el);
  });
}

// ===========================
// TABS
// ===========================
function setActiveTab(period) {
  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.period === period);
  });
}

async function loadPeriod(period) {
  currentPeriod = period;
  setActiveTab(period);

  loader.classList.remove("hidden");
  rankingList.innerHTML = "";

  try {
    const data = await fetchRanking(period);
    renderRanking(data, period);
  } catch (e) {
    rankingList.innerHTML = `
      <div style="text-align:center; color: var(--accent); padding: 40px 0;">
        ${e.message}
      </div>`;
  } finally {
    loader.classList.add("hidden");
  }
}

// ===========================
// EVENTS
// ===========================
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const period = tab.dataset.period;
    if (period !== currentPeriod) loadPeriod(period);
  });
});

// ===========================
// INIT
// ===========================
document.addEventListener("DOMContentLoaded", () => {
  // Charge la semaine par défaut
  loadPeriod("week");
});
